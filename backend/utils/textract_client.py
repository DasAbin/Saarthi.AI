"""
Amazon Textract client utilities for PDF OCR.
"""

import boto3
import os
from typing import List, Dict, Any
from botocore.exceptions import ClientError

textract_client = boto3.client("textract", region_name=os.getenv("AWS_REGION", "us-east-1"))


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract text from PDF using Amazon Textract.
    
    Args:
        pdf_bytes: PDF file bytes
        
    Returns:
        Extracted text as string
    """
    try:
        # Textract AnalyzeDocument API
        response = textract_client.analyze_document(
            Document={"Bytes": pdf_bytes},
            FeatureTypes=["TABLES", "FORMS"]
        )
        
        # Extract text from blocks
        text_blocks = []
        for block in response.get("Blocks", []):
            if block.get("BlockType") == "LINE":
                text_blocks.append(block.get("Text", ""))
        
        return "\n".join(text_blocks)
        
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code == "InvalidParameterException":
            # Fallback: try DetectDocumentText for simpler documents
            try:
                response = textract_client.detect_document_text(
                    Document={"Bytes": pdf_bytes}
                )
                text_blocks = []
                for block in response.get("Blocks", []):
                    if block.get("BlockType") == "LINE":
                        text_blocks.append(block.get("Text", ""))
                return "\n".join(text_blocks)
            except Exception as fallback_error:
                raise Exception(f"Textract failed: {str(fallback_error)}")
        else:
            raise Exception(f"Textract error: {str(e)}")


def extract_text_async(s3_bucket: str, s3_key: str) -> str:
    """
    Extract text from PDF in S3 using async Textract job.
    
    Args:
        s3_bucket: S3 bucket name
        s3_key: S3 object key
        
    Returns:
        Extracted text (after job completion)
    """
    import time
    
    try:
        # Start async job
        response = textract_client.start_document_text_detection(
            DocumentLocation={
                "S3Object": {
                    "Bucket": s3_bucket,
                    "Name": s3_key
                }
            }
        )
        
        job_id = response["JobId"]
        
        # Poll for completion
        max_attempts = 60
        for _ in range(max_attempts):
            response = textract_client.get_document_text_detection(JobId=job_id)
            status = response["JobStatus"]
            
            if status == "SUCCEEDED":
                # Extract text from results
                text_blocks = []
                for block in response.get("Blocks", []):
                    if block.get("BlockType") == "LINE":
                        text_blocks.append(block.get("Text", ""))
                return "\n".join(text_blocks)
            elif status == "FAILED":
                raise Exception("Textract job failed")
            
            time.sleep(2)
        
        raise Exception("Textract job timed out")
        
    except ClientError as e:
        raise Exception(f"Textract async error: {str(e)}")
