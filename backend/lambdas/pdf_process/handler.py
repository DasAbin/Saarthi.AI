"""
Lambda handler for PDF processing and analysis.

This handler processes PDF documents using:
- PyMuPDF (fitz) for local text extraction
- Amazon Bedrock (Nova/Titan) for summarization
- Amazon S3 for storage
- DynamoDB for chunk metadata + embeddings
"""

import base64
import json
import logging
import os
import sys
import uuid
from typing import Any, Dict

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from utils.response import error_response, lambda_response, success_response
from utils.s3_client import upload_pdf
from utils.document_parser import extract_text as generic_extract_text
from utils.chunker import chunk_text
from utils.aws.dynamodb import store_chunk
from utils.text_cleaner import clean_text
from services.document_analyzer import analyze_document
from rag.embedding_service import generate_embedding

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

        # Derive a stable document identifier
        document_id = s3_key or f"doc-{uuid.uuid4().hex}"

        # Step 2: Write document to /tmp and extract text using generic parser
        tmp_dir = "/tmp"
        os.makedirs(tmp_dir, exist_ok=True)

        # Preserve original extension if available so the parser can detect type
        _, ext = os.path.splitext(filename)
        ext = ext or ".bin"
        tmp_path = os.path.join(tmp_dir, f"{uuid.uuid4().hex}{ext}")

        try:
            with open(tmp_path, "wb") as f:
                f.write(pdf_bytes)

            logger.info("Extracting text from document using multi-format parser...")
            extracted_text = generic_extract_text(tmp_path, filename)
        finally:
            # Best-effort cleanup; Lambda /tmp is ephemeral but we keep it tidy
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass

        # If very little text was extracted, treat as low-quality OCR.
        if not extracted_text or len(extracted_text.strip()) < 50:
            message = (
                "Document text could not be extracted clearly. "
                "Please upload a higher quality document."
            )
            logger.warning(message)
            return lambda_response(400, error_response(message))

        logger.info("Extracted %d characters from document (raw)", len(extracted_text))

        # Step 3: Clean text (remove OCR noise, merge broken lines, etc.)
        cleaned_text = clean_text(extracted_text)

        if not cleaned_text or len(cleaned_text.strip()) < 50:
            message = (
                "Document text could not be extracted clearly. "
                "Please upload a higher quality document."
            )
            logger.warning(message)
            return lambda_response(400, error_response(message))

        logger.info(
            "Cleaned text is %d characters after normalization", len(cleaned_text)
        )

        # Step 4: Chunk cleaned text for embeddings
        logger.info("Chunking cleaned text for embeddings...")
        chunks = chunk_text(cleaned_text, chunk_size=800, overlap=100)

        if not chunks:
            message = (
                "No text chunks could be generated from the document. It may be empty or unsupported."
            )
            logger.warning(message)
            return lambda_response(
                400,
                error_response(message),
            )

        logger.info("Generated %d chunks", len(chunks))

        # Step 4: Generate embeddings and store chunk metadata in DynamoDB
        logger.info("Generating embeddings and storing chunks in DynamoDB...")
        for index, chunk in enumerate(chunks):
            try:
                embedding = generate_embedding(chunk)
                chunk_id = f"{document_id}#chunk-{index}"

                metadata = {
                    "document_id": document_id,
                    "chunk_index": index,
                    "source": filename,
                }

                store_chunk(
                    chunk_id=chunk_id,
                    text=chunk,
                    embedding=embedding,
                    metadata=metadata,
                )
            except Exception as e:
                logger.error(
                    "Failed to store chunk %s for document %s: %s",
                    index,
                    document_id,
                    str(e),
                )
                # Continue with other chunks; partial ingestion is better than none
                continue
        
        # Step 5: Structured document analysis via Bedrock
        logger.info("Analyzing document content with Bedrock...")
        analysis = analyze_document(cleaned_text)

        logger.info("PDF processing and analysis completed successfully")

        # Return structured results
        payload = {
            "document_type": analysis.get("document_type", "Unknown"),
            "purpose": analysis.get("purpose", ""),
            "key_points": analysis.get("key_points", []),
            "instructions": analysis.get("instructions", []),
            "summary": analysis.get("summary", ""),
            "extracted_text": cleaned_text,
            "s3_key": s3_key,
            "document_id": document_id,
            "chunk_count": len(chunks),
        }

        return lambda_response(200, success_response(payload))
        
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
