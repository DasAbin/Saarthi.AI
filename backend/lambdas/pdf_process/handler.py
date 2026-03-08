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
import boto3
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

# Initialize AWS clients
textract_client = boto3.client("textract", region_name=os.getenv("AWS_REGION", "ap-south-1"))
s3_client = boto3.client("s3", region_name=os.getenv("AWS_REGION", "ap-south-1"))


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

        # ── Input size guard ────────────────────────────────────────────────
        # A base64-encoded 10MB file is ~13.5MB of text. Reject anything
        # larger to prevent the Lambda from OOM-killing mid-decode.
        MAX_BASE64_BYTES = 15 * 1024 * 1024  # 15MB base64 ≈ ~10MB file
        body_raw = event.get("body", "") or ""
        if isinstance(body_raw, str) and len(body_raw) > MAX_BASE64_BYTES:
            return lambda_response(
                400,
                error_response("File too large. Maximum supported size is 10MB."),
            )

        # Parse JSON body
        body = body_raw or "{}"
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
        language = body.get("language", "en")

        if not s3_key:
            logger.warning("Missing 's3Key' in request body")
            return lambda_response(
                400,
                error_response("Field 's3Key' is required"),
            )

        logger.info("Processing document from S3: key=%s filename=%s language=%s", s3_key, filename, language)

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

        # Generate a unique document_id/jobId for this processing job
        document_id = f"doc-{uuid.uuid4().hex[:16]}"
        logger.info("Generated document_id=%s for s3_key=%s language=%s", document_id, s3_key, language)

        # Step 1: Start async Textract job for PDFs (images can use sync)
        # For PDFs, use async Textract to avoid Lambda timeout
        # For images, we can use sync Textract (DetectDocumentText)
        if file_extension == "pdf":
            logger.info(
                "Starting async Textract job for PDF - extension=%s s3_key=%s",
                file_extension,
                s3_key,
            )
            try:
                # Start async Textract job
                textract_response = textract_client.start_document_text_detection(
                    DocumentLocation={
                        "S3Object": {
                            "Bucket": PDF_BUCKET,
                            "Name": s3_key,
                        }
                    }
                )
                textract_job_id = textract_response.get("JobId")
                if not textract_job_id:
                    raise Exception("Textract did not return a JobId")
                
                logger.info("Started Textract async job: job_id=%s", textract_job_id)

                # Save job metadata to S3 for status polling
                job_metadata = {
                    "document_id": document_id,
                    "s3_key": s3_key,
                    "filename": filename,
                    "file_extension": file_extension,
                    "textract_job_id": textract_job_id,
                    "job_type": "async",
                    "status": "processing",
                    "language": language,
                }
                meta_key = f"jobs/{document_id}/meta.json"
                s3_client.put_object(
                    Bucket=PDF_BUCKET,
                    Key=meta_key,
                    Body=json.dumps(job_metadata),
                    ContentType="application/json",
                )
                logger.info("Saved job metadata to s3://%s/%s", PDF_BUCKET, meta_key)

                # Return jobId immediately - frontend will poll for status
                return lambda_response(
                    202,
                    success_response(
                        {
                            "jobId": document_id,
                            "status": "processing",
                            "message": "Document processing started",
                        },
                        message="Document processing started successfully",
                    ),
                )
            except Exception as e:
                error_message = str(e)
                logger.error(f"Failed to start Textract async job: {error_message}", exc_info=True)
                return lambda_response(
                    500,
                    error_response(f"Failed to start document processing: {error_message}"),
                )
        
        # For images, use synchronous Textract (existing flow)
        logger.info(
            "Starting sync Textract extraction for image - extension=%s s3_key=%s language=%s",
            file_extension,
            s3_key,
            language,
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
        # To avoid API Gateway/Lambda timeout, only send the first 5k characters
        # (Textract takes ~24-25s, so we need to keep Bedrock analysis under 4-5s)
        analysis_text = cleaned_text[:5000]
        logger.info(
            "Sending %d characters to Bedrock for analysis",
            len(analysis_text),
        )
        analysis = analyze_document(analysis_text, language=language)

        logger.info("PDF processing and analysis completed successfully")

        # Build payload with new structured intelligence report
        # Maintain backward compatibility by including legacy fields derived from new structure
        payload = {
            # New structured fields
            "document_overview": analysis.get("document_overview", ""),
            "scheme_facts": analysis.get("scheme_facts", {}),
            "eligibility_and_coverage": analysis.get("eligibility_and_coverage", []),
            "healthcare_benefits": analysis.get("healthcare_benefits", []),
            "operational_workflow": analysis.get("operational_workflow", []),
            "stakeholders_and_roles": analysis.get("stakeholders_and_roles", []),
            "community_impact": analysis.get("community_impact", []),
            "policy_insights": analysis.get("policy_insights", []),
            "key_contacts": analysis.get("key_contacts", []),
            "frequently_asked_questions": analysis.get("frequently_asked_questions", []),
            "summary": analysis.get("summary", ""),
            # Legacy fields for backward compatibility (derived from new structure)
            "document_type": analysis.get("scheme_facts", {}).get("scheme_name", "Unknown") or "Government Document",
            "purpose": analysis.get("document_overview", ""),
            "key_points": analysis.get("eligibility_and_coverage", [])[:5] + analysis.get("healthcare_benefits", [])[:3],
            "instructions": analysis.get("operational_workflow", []),
            # Metadata
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
