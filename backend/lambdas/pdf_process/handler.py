"""
Lambda handler for PDF processing and analysis.
"""

import json
import os
import sys
import base64
from typing import Dict, Any

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from utils.textract_client import extract_text_from_pdf
from utils.s3_client import upload_pdf
from utils.bedrock_client import invoke_claude
from utils.response import success_response, error_response, lambda_response


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for PDF processing endpoint.
    
    Expected event (API Gateway with binary media):
    - body: base64-encoded PDF file
    - headers: Content-Type, Content-Length
    """
    try:
        # Parse PDF from request
        if event.get("isBase64Encoded"):
            pdf_bytes = base64.b64decode(event["body"])
        elif isinstance(event.get("body"), str):
            # Try to decode if it's a base64 string
            try:
                pdf_bytes = base64.b64decode(event["body"])
            except:
                return lambda_response(
                    400,
                    error_response("Invalid PDF format")
                )
        else:
            return lambda_response(
                400,
                error_response("PDF file is required")
            )
        
        # Validate PDF
        if not pdf_bytes.startswith(b"%PDF"):
            return lambda_response(
                400,
                error_response("Invalid PDF file")
            )
        
        # Extract text using Textract
        extracted_text = extract_text_from_pdf(pdf_bytes)
        
        if not extracted_text or len(extracted_text.strip()) < 50:
            return lambda_response(
                400,
                error_response("Could not extract sufficient text from PDF")
            )
        
        # Upload PDF to S3
        filename = event.get("headers", {}).get("x-filename", "document.pdf")
        s3_key = upload_pdf(pdf_bytes, filename)
        
        # Generate summary using Claude
        summary_prompt = f"""Summarize the following government policy document. Provide:
1. A concise summary (2-3 paragraphs)
2. Key points as a bulleted list
3. Important dates, deadlines, or eligibility criteria if mentioned

Document text:
{extracted_text[:8000]}  # Limit to avoid token limits
"""
        
        summary_response = invoke_claude(
            prompt=summary_prompt,
            system_prompt="You are an expert at summarizing government policy documents. Extract key information clearly.",
            max_tokens=2048,
            temperature=0.3
        )
        
        # Extract summary and key points
        # Simple parsing - in production, use structured output
        lines = summary_response.split("\n")
        summary_lines = []
        key_points = []
        in_points = False
        
        for line in lines:
            if "key points" in line.lower() or "important points" in line.lower():
                in_points = True
                continue
            if in_points and (line.strip().startswith("-") or line.strip().startswith("•") or line.strip().startswith("*")):
                point = line.strip().lstrip("-•*").strip()
                if point:
                    key_points.append(point)
            elif not in_points and line.strip():
                summary_lines.append(line.strip())
        
        summary = "\n".join(summary_lines)
        
        # If no key points extracted, generate them separately
        if not key_points:
            points_prompt = f"""Extract 5-7 key points from this government document:

{extracted_text[:6000]}

Return only a bulleted list of key points."""
            
            points_response = invoke_claude(
                prompt=points_prompt,
                max_tokens=512,
                temperature=0.3
            )
            
            key_points = [
                p.strip().lstrip("-•*").strip()
                for p in points_response.split("\n")
                if p.strip() and (p.strip().startswith("-") or p.strip().startswith("•") or p.strip().startswith("*"))
            ][:7]
        
        return lambda_response(
            200,
            success_response({
                "extracted_text": extracted_text,
                "summary": summary,
                "points": key_points[:7],  # Limit to 7 points
                "s3_key": s3_key
            })
        )
        
    except Exception as e:
        print(f"Error in pdf_process handler: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return lambda_response(
            500,
            error_response(f"Internal server error: {str(e)}")
        )
