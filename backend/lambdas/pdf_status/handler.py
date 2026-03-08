"""
Lambda handler for document status polling — GET /pdf/{document_id}

Flow:
  1. Load job metadata from S3 (jobs/{document_id}/meta.json)
  2. For async PDF jobs: call Textract GetDocumentTextDetection
     - If IN_PROGRESS → return { status: "processing" }
     - If SUCCEEDED   → collect all blocks, clean text, run Bedrock, save result, return full payload
     - If FAILED      → return { status: "error", error: "..." }
  3. For sync image jobs: run Textract DetectDocumentText synchronously, run Bedrock, return result
  4. Results are cached in S3 (jobs/{document_id}/result.json) so repeated polls are fast
"""

import json
import logging
import os
import sys
import boto3

from typing import Any, Dict

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from utils.response import error_response, lambda_response, success_response
from utils.s3_client import PDF_BUCKET
from utils.text_cleaner import clean_text
from utils.chunker import chunk_text
from services.document_analyzer import analyze_document

logger = logging.getLogger()
logger.setLevel(logging.INFO)

textract = boto3.client("textract", region_name=os.getenv("AWS_REGION", "ap-south-1"))
s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION", "ap-south-1"))


def _extract_lines_from_blocks(blocks) -> str:
    """Collect LINE blocks into a single string."""
    lines = []
    for block in blocks or []:
        if block.get("BlockType") == "LINE":
            text = (block.get("Text") or "").strip()
            if text:
                lines.append(text)
    return "\n".join(lines)


def _get_all_textract_blocks(job_id: str) -> list:
    """Fetch all blocks for a completed Textract job (handles pagination)."""
    resp = textract.get_document_text_detection(JobId=job_id)
    blocks = list(resp.get("Blocks", []))
    next_token = resp.get("NextToken")
    while next_token:
        page = textract.get_document_text_detection(JobId=job_id, NextToken=next_token)
        blocks.extend(page.get("Blocks", []))
        next_token = page.get("NextToken")
    return blocks


def _build_full_payload(s3_key: str, filename: str, document_id: str,
                        extracted_text: str, num_chunks: int,
                        analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Build the full response payload from analysis results."""
    return {
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
        # Legacy compat fields
        "document_type": analysis.get("scheme_facts", {}).get("scheme_name", "") or "Government Document",
        "purpose": analysis.get("document_overview", ""),
        "key_points": (analysis.get("eligibility_and_coverage", [])[:5]
                       + analysis.get("healthcare_benefits", [])[:3]),
        "instructions": analysis.get("operational_workflow", []),
        # Metadata
        "extracted_text": extracted_text,
        "s3_key": s3_key,
        "document_id": document_id,
        "chunk_count": num_chunks,
        "status": "done",
    }


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Check status of an async document processing job."""
    try:
        logger.info("pdf_status handler invoked")

        # ── Extract document_id from path parameters ────────────────────
        path_params = event.get("pathParameters") or {}
        document_id = path_params.get("document_id") or path_params.get("documentId")

        if not document_id:
            return lambda_response(400, error_response("Missing document_id in path"))

        logger.info("Checking status for document_id=%s", document_id)

        # ── Check for cached result first ───────────────────────────────
        result_key = f"jobs/{document_id}/result.json"
        try:
            obj = s3.get_object(Bucket=PDF_BUCKET, Key=result_key)
            cached = json.loads(obj["Body"].read())
            logger.info("Returning cached result for document_id=%s", document_id)
            return lambda_response(200, success_response(cached, message="Document processed successfully"))
        except s3.exceptions.NoSuchKey:
            pass  # Not cached yet, continue
        except Exception:
            pass  # Ignore cache read errors

        # ── Load job metadata ───────────────────────────────────────────
        meta_key = f"jobs/{document_id}/meta.json"
        try:
            obj = s3.get_object(Bucket=PDF_BUCKET, Key=meta_key)
            job_meta = json.loads(obj["Body"].read())
        except Exception as e:
            logger.error("Failed to load job metadata: %s", str(e))
            return lambda_response(404, error_response("Document job not found"))

        s3_key = job_meta["s3_key"]
        filename = job_meta.get("filename", "document")
        file_extension = job_meta.get("file_extension", "pdf")
        textract_job_id = job_meta["textract_job_id"]
        job_type = job_meta.get("job_type", "async")

        # ── Handle async PDF job ────────────────────────────────────────
        if job_type == "async":
            resp = textract.get_document_text_detection(JobId=textract_job_id)
            status = resp.get("JobStatus", "")
            logger.info("Textract job %s status: %s", textract_job_id, status)

            if status == "IN_PROGRESS":
                return lambda_response(
                    202,
                    success_response(
                        {"document_id": document_id, "status": "processing"},
                        message="Document is still being processed",
                    ),
                )

            if status == "FAILED":
                error_msg = resp.get("StatusMessage") or "Textract job failed"
                logger.error("Textract job failed: %s", error_msg)
                return lambda_response(
                    500,
                    success_response(
                        {"document_id": document_id, "status": "error", "error": error_msg},
                        message="Document processing failed",
                    ),
                )

            # SUCCEEDED — collect all blocks
            logger.info("Textract job succeeded, collecting blocks")
            blocks = _get_all_textract_blocks(textract_job_id)
            logger.info("Collected %d blocks from Textract", len(blocks))
            raw_text = _extract_lines_from_blocks(blocks)

        # ── Handle sync image job ───────────────────────────────────────
        elif job_type == "sync_image":
            logger.info("Running sync Textract for image: s3://%s/%s", PDF_BUCKET, s3_key)
            s3_obj = s3.get_object(Bucket=PDF_BUCKET, Key=s3_key)
            image_bytes = s3_obj["Body"].read()
            resp = textract.detect_document_text(Document={"Bytes": image_bytes})
            blocks = resp.get("Blocks", [])
            raw_text = _extract_lines_from_blocks(blocks)
        else:
            return lambda_response(500, error_response(f"Unknown job_type: {job_type}"))

        # ── Validate extraction ─────────────────────────────────────────
        if not raw_text or len(raw_text.strip()) == 0:
            return lambda_response(400, error_response("No text found in document"))

        logger.info("Extracted %d characters from document", len(raw_text))

        # ── Clean text ──────────────────────────────────────────────────
        cleaned_text = clean_text(raw_text)
        if not cleaned_text or len(cleaned_text.strip()) == 0:
            return lambda_response(400, error_response("No text remaining after cleaning"))

        logger.info("Cleaned text: %d characters", len(cleaned_text))

        # ── Chunk (for metadata only, embeddings disabled by default) ───
        chunks = chunk_text(cleaned_text, chunk_size=2000, overlap=200)
        logger.info("Generated %d chunks", len(chunks))

        # ── Bedrock analysis ────────────────────────────────────────────
        analysis_text = cleaned_text[:5000]
        logger.info("Running Bedrock analysis on %d characters", len(analysis_text))
        analysis = analyze_document(analysis_text)

        # ── Build final payload ─────────────────────────────────────────
        payload = _build_full_payload(
            s3_key=s3_key,
            filename=filename,
            document_id=document_id,
            extracted_text=cleaned_text,
            num_chunks=len(chunks),
            analysis=analysis,
        )

        # ── Cache result in S3 so repeat polls are instant ──────────────
        try:
            s3.put_object(
                Bucket=PDF_BUCKET,
                Key=result_key,
                Body=json.dumps(payload),
                ContentType="application/json",
            )
            logger.info("Cached result at s3://%s/%s", PDF_BUCKET, result_key)
        except Exception as cache_err:
            logger.warning("Failed to cache result: %s", str(cache_err))

        logger.info("Document processing completed successfully for document_id=%s", document_id)
        return lambda_response(200, success_response(payload, message="Document processed successfully"))

    except Exception as e:
        logger.error("Unexpected error in pdf_status handler: %s", str(e), exc_info=True)
        return lambda_response(500, error_response(f"Internal server error: {str(e)}"))
