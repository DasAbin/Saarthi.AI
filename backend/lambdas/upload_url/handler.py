"""
Lambda handler for generating S3 presigned upload URLs.

This endpoint is used by the frontend to obtain a temporary URL
for directly uploading large documents to S3, bypassing API Gateway
payload limits.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

# Add parent directory to path for shared utils
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from utils.response import error_response, lambda_response, success_response

logger = logging.getLogger()
logger.setLevel(logging.INFO)

from botocore.config import Config

S3_REGION = os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "ap-south-1"))
PDF_BUCKET = os.getenv("PDF_BUCKET")

s3_client = boto3.client(
    "s3", 
    region_name=S3_REGION,
    endpoint_url=f"https://s3.{S3_REGION}.amazonaws.com",
    config=Config(
        signature_version="s3v4",
        s3={"addressing_style": "virtual"}
    )
)


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Generate a presigned S3 PUT URL for document upload.

    Expected JSON body:
    {
        "filename": "document.pdf",
        "contentType": "application/pdf"
    }

    Returns:
    {
        "success": true,
        "data": {
            "uploadUrl": "...",
            "key": "documents/<timestamp>_<filename>"
        }
    }
    """
    logger.info("upload-url handler invoked")

    if not PDF_BUCKET:
        logger.error("PDF_BUCKET environment variable is not set")
        return lambda_response(
            500,
            error_response("Server configuration error: PDF bucket is not configured"),
        )

    try:
        body = event.get("body") or "{}"
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON body for upload-url")
                return lambda_response(
                    400, error_response("Request body must be valid JSON")
                )

        filename = (body or {}).get("filename")
        content_type = (body or {}).get("contentType")

        if not filename or not isinstance(filename, str):
            return lambda_response(
                400, error_response("Field 'filename' is required")
            )

        if not content_type or not isinstance(content_type, str):
            return lambda_response(
                400, error_response("Field 'contentType' is required")
            )

        # Basic content-type sanity check
        if not (
            content_type.startswith("application/")
            or content_type.startswith("image/")
            or content_type.startswith("text/")
        ):
            logger.warning("Rejected unsupported content type: %s", content_type)
            return lambda_response(
                400, error_response("Unsupported content type for upload")
            )

        # Construct a deterministic key
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        key = f"documents/{timestamp}_{filename}"

        logger.info("Generating presigned URL for bucket=%s key=%s", PDF_BUCKET, key)

        try:
            upload_url = s3_client.generate_presigned_url(
                ClientMethod="put_object",
                Params={
                    "Bucket": PDF_BUCKET,
                    "Key": key,
                    "ContentType": content_type,
                },
                ExpiresIn=900,  # 15 minutes
            )
        except ClientError as e:
            logger.error("Failed to generate presigned URL: %s", str(e), exc_info=True)
            return lambda_response(
                500, error_response("Failed to generate upload URL")
            )

        payload = {
            "uploadUrl": upload_url,
            "key": key,
        }

        return lambda_response(200, success_response(payload))

    except Exception as e:
        logger.error("Unexpected error in upload-url handler: %s", str(e), exc_info=True)
        return lambda_response(500, error_response("Internal server error"))

