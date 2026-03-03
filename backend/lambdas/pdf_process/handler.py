"""
Lambda handler for PDF processing and analysis.

This handler processes PDF documents using:
- Amazon Textract for OCR/text extraction
- Amazon Bedrock (Claude 3 Sonnet) for summarization
- Amazon S3 for storage
"""

import json
import os
import sys
import base64
import logging
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from utils.response import success_response, error_response, lambda_response
from utils.aws.textract import extract_text_from_pdf
from utils.s3_client import upload_pdf
from utils.processing.summarization import generate_summary, extract_key_points

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for PDF processing endpoint.
    
    Expected event (API Gateway with binary media):
    - body: base64-encoded PDF file OR JSON with base64 PDF
    - headers: Content-Type, Content-Length, x-filename (optional)
    
    Returns:
    {
        "success": true,
        "data": {
            "extracted_text": "string",
            "summary": "string",
            "points": ["string"],
            "s3_key": "string"
        }
    }
    """
    try:
        logger.info("PDF process handler invoked")
        
        # Parse PDF from request
        pdf_bytes = None
        body = {}
        
        if event.get("isBase64Encoded"):
            pdf_bytes = base64.b64decode(event["body"])
        elif isinstance(event.get("body"), str):
            try:
                # Try parsing as JSON first
                body = json.loads(event["body"])
                if "file" in body:
                    pdf_bytes = base64.b64decode(body["file"])
                else:
                    pdf_bytes = base64.b64decode(event["body"])
            except (json.JSONDecodeError, ValueError):
                return lambda_response(
                    400,
                    error_response("Invalid PDF format")
                )
        else:
            body = event.get("body", {})
            if isinstance(body, dict) and "file" in body:
                pdf_bytes = base64.b64decode(body["file"])
            else:
                return lambda_response(
                    400,
                    error_response("PDF file is required")
                )
        
        if not pdf_bytes:
            return lambda_response(
                400,
                error_response("Could not extract PDF data")
            )
        
        # Basic validation
        logger.info(f"Document received: {len(pdf_bytes)} bytes")
        
        # Get filename from headers or body
        filename = (
            event.get("headers", {}).get("x-filename") or
            event.get("headers", {}).get("X-Filename") or
            (body.get("filename") if isinstance(body, dict) else None) or
            "document.pdf"
        )
        
        # Step 1: Upload PDF to S3
        logger.info(f"Uploading PDF to S3: {filename}")
        try:
            s3_key = upload_pdf(pdf_bytes, filename)
            logger.info(f"PDF uploaded to S3: {s3_key}")
        except Exception as e:
            logger.error(f"Failed to upload PDF to S3: {str(e)}")
            # Continue processing even if S3 upload fails
            s3_key = None
        
        # Step 2: Extract text using Textract
        logger.info("Extracting text using Textract...")
        try:
            extracted_text = extract_text_from_pdf(pdf_bytes)
            
            if not extracted_text or len(extracted_text.strip()) < 50:
                logger.warning("Extracted text is too short")
                return lambda_response(
                    400,
                    error_response("Could not extract sufficient text from PDF. The PDF may be image-only or corrupted.")
                )
            
            logger.info(f"Extracted {len(extracted_text)} characters from PDF")
            
        except Exception as e:
            logger.error(f"Textract error: {str(e)}")
            return lambda_response(
                500,
                error_response(f"Failed to extract text from PDF: {str(e)}")
            )
        
        # Step 3: Generate summary using Claude
        logger.info("Generating summary...")
        try:
            summary = generate_summary(extracted_text)
        except Exception as e:
            logger.error(f"Summary generation error: {str(e)}")
            # Fallback: Use first 500 characters as summary
            summary = extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text
        
        # Step 4: Extract key points
        logger.info("Extracting key points...")
        try:
            key_points = extract_key_points(extracted_text, max_points=7)
            # Fallback if extraction fails
            if not key_points:
                # Simple fallback: split by sentences and take first few
                sentences = extracted_text.split(". ")[:5]
                key_points = [s.strip() + "." for s in sentences if s.strip()]
        except Exception as e:
            logger.error(f"Key points extraction error: {str(e)}")
            key_points = []
        
        logger.info("PDF processing completed successfully")
        
        # Return results
        return lambda_response(
            200,
            success_response({
                "extracted_text": extracted_text,
                "summary": summary,
                "points": key_points,
                "s3_key": s3_key
            })
        )
        
    except base64.binascii.Error as e:
        logger.error(f"Base64 decode error: {str(e)}")
        return lambda_response(
            400,
            error_response("Invalid base64 encoding")
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return lambda_response(
            500,
            error_response(f"Internal server error: {str(e)}")
        )
