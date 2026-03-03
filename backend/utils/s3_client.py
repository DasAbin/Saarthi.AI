"""
S3 client utilities for document storage.
"""

import boto3
import os
import logging
from typing import Optional
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

s3_client = boto3.client("s3", region_name=os.getenv("AWS_REGION", "us-east-1"))

PDF_BUCKET = os.getenv("PDF_BUCKET", "saarthi-pdfs")
EMBEDDINGS_BUCKET = os.getenv("EMBEDDINGS_BUCKET", "saarthi-embeddings")


def upload_pdf(file_content: bytes, filename: str) -> str:
    """
    Upload PDF file to S3.
    
    Args:
        file_content: PDF file bytes
        filename: Original filename
        
    Returns:
        S3 object key
    """
    import uuid
    from datetime import datetime
    
    # Generate unique key
    timestamp = datetime.utcnow().strftime("%Y%m%d")
    unique_id = str(uuid.uuid4())[:8]
    key = f"pdfs/{timestamp}/{unique_id}_{filename}"
    
    try:
        s3_client.put_object(
            Bucket=PDF_BUCKET,
            Key=key,
            Body=file_content,
            ContentType="application/pdf"
        )
        return key
    except ClientError as e:
        raise Exception(f"Failed to upload PDF: {str(e)}")


def download_pdf(key: str) -> bytes:
    """
    Download PDF from S3.
    
    Args:
        key: S3 object key
        
    Returns:
        PDF file bytes
    """
    try:
        response = s3_client.get_object(Bucket=PDF_BUCKET, Key=key)
        return response["Body"].read()
    except ClientError as e:
        raise Exception(f"Failed to download PDF: {str(e)}")


def save_embeddings(embeddings_data: dict, key: str) -> bool:
    """
    Save embeddings metadata to S3.
    
    Args:
        embeddings_data: Dictionary containing embeddings and metadata
        key: S3 object key
        
    Returns:
        True if successful
    """
    import json
    
    try:
        s3_client.put_object(
            Bucket=EMBEDDINGS_BUCKET,
            Key=key,
            Body=json.dumps(embeddings_data),
            ContentType="application/json"
        )
        return True
    except ClientError as e:
        print(f"Failed to save embeddings: {str(e)}")
        return False


def load_embeddings(key: str) -> Optional[dict]:
    """
    Load embeddings metadata from S3.
    
    Args:
        key: S3 object key
        
    Returns:
        Embeddings data dictionary or None
    """
    import json
    
    try:
        response = s3_client.get_object(Bucket=EMBEDDINGS_BUCKET, Key=key)
        return json.loads(response["Body"].read())
    except ClientError:
        return None


def load_faiss_index() -> Optional[dict]:
    """
    Legacy stub kept for backward compatibility.
    Vector storage is now handled via DynamoDB, so this always returns None.
    """
    logger.info("load_faiss_index called but FAISS support is disabled; returning None")
    return None


def save_faiss_index(index, metadata: dict) -> bool:
    """
    Legacy stub kept for backward compatibility.
    Vector storage is now handled via DynamoDB, so this is a no-op.
    """
    logger.info("save_faiss_index called but FAISS support is disabled; returning False")
    return False
