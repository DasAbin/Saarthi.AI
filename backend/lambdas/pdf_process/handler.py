"""
Lambda handler for document processing and analysis.

This handler processes documents using:
- Amazon Textract for text extraction (PDFs and images)
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
from utils.s3_client import PDF_BUCKET
from utils.document_parser import extract_text_with_textract
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
    Lambda handler for document processing endpoint.
    
    New production flow (S3-based):
    - body: JSON { "s3Key": "documents/...", "filename": "original.ext" }
    
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
        logger.info("Document process handler invoked")
        
       # Parse JSON body
        body = event.get("body") or "{}"
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON body for document processing")
                return lambda_response(
                    400,
                    error_response("Request body must be valid JSON"),
                )

        if not isinstance(body, dict):
            return lambda_response(
                400,
                error_response("Request body must be a JSON object"),
            )

        s3_key = body.get("s3Key")
        filename = body.get("filename") or "document.pdf"

        if not s3_key:
            logger.warning("Missing 's3Key' in request body")
            return lambda_response(
                400,
                error_response("Field 's3Key' is required"),
            )

        logger.info("Processing document from S3: key=%s filename=%s", s3_key, filename)

        # Step 0: Validate file type before processing
        # IMPORTANT: Do NOT rely on HTTP Content-Type headers for validation.
        # Presigned S3 uploads often have missing/incorrect Content-Type (e.g. application/octet-stream).
        # Use filename / S3 object key extension instead.
        normalized_filename = (filename or "").strip().lower()
        normalized_s3_key = (s3_key or "").strip().lower()

        # Prefer filename extension; fall back to S3 object key extension.
        file_extension = ""
        if "." in normalized_filename:
            file_extension = normalized_filename.rsplit(".", 1)[-1]
        else:
            s3_basename = os.path.basename(normalized_s3_key)
            if "." in s3_basename:
                file_extension = s3_basename.rsplit(".", 1)[-1]

        # Supported formats for Textract DetectDocumentText.
        # (Allow tif as a common alias for tiff)
        SUPPORTED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "tiff", "tif", "bmp"}

        # Debug logging BEFORE validation (requested)
        request_headers = event.get("headers") or {}
        content_type = (
            request_headers.get("Content-Type")
            or request_headers.get("content-type")
            or ""
        )
        logger.info(
            "File validation inputs - s3_key=%s filename=%s content_type=%s detected_extension=%s",
            s3_key,
            filename,
            content_type,
            file_extension or "unknown",
        )

        # Validate extension
        if not file_extension or file_extension not in SUPPORTED_EXTENSIONS:
            error_msg = "Unsupported document type. Supported formats: PDF, PNG, JPG, JPEG, TIFF, BMP"
            logger.warning(
                "File type validation failed - s3_key=%s filename=%s detected_extension=%s",
                s3_key,
                filename,
                file_extension or "unknown",
            )
            return lambda_response(400, error_response(error_msg))

        # Choose extraction pipeline (always Textract for PDFs + images)
        logger.info(
            "File type validated - extension=%s pipeline=%s",
            file_extension,
            "textract.detect_document_text",
        )

        # Derive a stable document identifier
        document_id = s3_key or f"doc-{uuid.uuid4().hex}"

        # Step 1: Extract text using Amazon Textract (Production pipeline)
        # Textract reads directly from S3, no need to download to /tmp
        # Textract DetectDocumentText supports both PDFs and images
        logger.info(
            "Starting Textract extraction - extension=%s s3_key=%s",
            file_extension,
            s3_key,
        )
        try:
            extracted_text = extract_text_with_textract(PDF_BUCKET, s3_key)
        except Exception as e:
            error_message = str(e)
            logger.error(f"Textract extraction failed: {error_message}", exc_info=True)
            return lambda_response(
                400,
                error_response(error_message),
            )

        # Log extraction results
        raw_text = extracted_text or ""
        logger.info(f"Textract extraction completed: {len(raw_text)} characters extracted")
        logger.debug(f"Extracted text preview (first 500 chars): {raw_text[:500]}")

        # Validation: fail if no text extracted
        if not extracted_text or len(extracted_text.strip()) == 0:
            message = "Document text extraction failed: No text found in document"
            logger.warning(message)
            return lambda_response(400, error_response(message))

        if len(extracted_text.strip()) < 10:
            print("Warning: very small extracted text, continuing anyway")

        logger.info("Extracted %d characters from document (raw)", len(raw_text))

        # Step 3: Clean text (remove OCR noise, merge broken lines, etc.)
        cleaned_text = clean_text(extracted_text)

        # Debug logging for cleaned text
        cleaned_preview_source = cleaned_text or ""
        print("Cleaned text length:", len(cleaned_preview_source))
        print(cleaned_preview_source[:500])

        # Again, only fail if cleaning produced no text at all
        if not cleaned_text:
            message = "No text remaining after cleaning extracted document text"
            logger.warning(message)
            return lambda_response(400, error_response(message))

        if len(cleaned_text.strip()) < 10:
            print("Warning: very small cleaned text, continuing anyway")

        logger.info(
            "Cleaned text is %d characters after normalization", len(cleaned_text)
        )

        # Step 4: Chunk cleaned text for embeddings
        logger.info("Chunking cleaned text for embeddings...")
        # Use fixed-size character-based chunks (2000 chars with 200 char overlap)
        chunks = chunk_text(cleaned_text, chunk_size=2000, overlap=200)

        if not chunks:
            message = (
                "No text chunks could be generated from the document. It may be empty or unsupported."
            )
            logger.warning(message)
            return lambda_response(400, error_response(message))

        logger.info("Generated %d chunks", len(chunks))

        # Step 4: Generate embeddings and store chunk metadata in DynamoDB
        # NOTE: This step can be expensive for large documents. To avoid API Gateway
        # 29-second timeouts, we make it configurable and disable it by default.
        enable_embeddings = os.getenv("ENABLE_EMBEDDINGS", "false").lower() == "true"
        if not enable_embeddings:
            logger.info(
                "ENABLE_EMBEDDINGS is false; skipping embedding generation and chunk storage "
                "in this synchronous Lambda invocation."
            )
        else:
            logger.info("Generating embeddings and storing chunks in DynamoDB...")
            for index, chunk in enumerate(chunks):
                try:
                    embedding = generate_embedding(chunk)
                    chunk_id = f"{document_id}#chunk-{index}"

                    # DynamoDB table expects:
                    # - partition key: document_id
                    # - sort key: metadata
                    # Plus additional attributes for each chunk.
                    metadata = {
                        "document_id": document_id,
                        "metadata": f"chunk-{index}",
                        "chunk_index": index,
                        "source": filename,
                        "s3_key": s3_key,
                    }

                    ok = store_chunk(
                        chunk_id=chunk_id,
                        text=chunk,
                        embedding=embedding,
                        metadata=metadata,
                    )
                    if ok:
                        logger.info(
                            "Stored chunk %s for document %s",
                            index,
                            document_id,
                        )
                    else:
                        logger.warning(
                            "store_chunk returned False for chunk %s of document %s",
                            index,
                            document_id,
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
        # To avoid API Gateway/Lambda timeout, only send the first 8k characters
        analysis_text = cleaned_text[:8000]
        logger.info(
            "Sending %d characters to Bedrock for analysis",
            len(analysis_text),
        )
        analysis = analyze_document(analysis_text)

        logger.info("PDF processing and analysis completed successfully")

        # Build payload matching PDFProcessResponse type
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

        # Return standardized ApiResponse wrapper
        return lambda_response(
            200,
            success_response(
                payload,
                message="Document processed successfully",
            ),
        )
        
    except base64.binascii.Error as e:
        logger.error(f"Base64 decode error: {str(e)}")
        return lambda_response(
            400,
            error_response("Invalid base64 encoding"),
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return lambda_response(
            500,
            error_response(f"Internal server error: {str(e)}"),
        )
