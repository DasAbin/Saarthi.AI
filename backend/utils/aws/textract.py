"""
Amazon Textract client utilities for PDF OCR and text extraction.
"""

import boto3
import os
import logging
from typing import List, Dict, Any, Optional
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize Textract client
textract_client = boto3.client("textract", region_name=os.getenv("AWS_REGION", "us-east-1"))


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract text from PDF using Amazon Textract AnalyzeDocument API.
    
    Args:
        pdf_bytes: PDF file bytes
        
    Returns:
        Extracted text as string
    """
    try:
        if not pdf_bytes or len(pdf_bytes) < 100:
            raise ValueError("Document is too small or empty")
        
        # Treat input as a generic document (PDF or image)
        logger.info(f"Extracting text from document ({len(pdf_bytes)} bytes)")
        
        # Textract AnalyzeDocument API (synchronous, good for small-medium PDFs)
        response = textract_client.analyze_document(
            Document={"Bytes": pdf_bytes},
            FeatureTypes=["TABLES", "FORMS"]
        )
        
        # Extract text from blocks
        text_blocks = []
        for block in response.get("Blocks", []):
            if block.get("BlockType") == "LINE":
                text = block.get("Text", "").strip()
                if text:
                    text_blocks.append(text)
        
        extracted_text = "\n".join(text_blocks)
        
        if not extracted_text or len(extracted_text.strip()) < 50:
            logger.warning("Extracted text is too short, trying DetectDocumentText")
            # Fallback to simpler API
            return extract_text_simple(pdf_bytes)
        
        logger.info(f"Extracted {len(extracted_text)} characters from document")
        return extracted_text
        
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code == "InvalidParameterException":
            # Try simpler API for basic text extraction
            logger.info("Trying simpler text extraction API")
            return extract_text_simple(pdf_bytes)
        elif error_code == "AccessDeniedException":
            logger.error("Textract access denied")
            raise Exception("Textract access denied. Please check IAM permissions.")
        else:
            logger.error(f"Textract error: {error_code}")
            raise Exception(f"Textract error: {str(e)}")
    except Exception as e:
        logger.error(f"Error extracting text: {str(e)}")
        raise


def extract_text_simple(pdf_bytes: bytes) -> str:
    """
    Extract text using simpler DetectDocumentText API (fallback).
    
    Args:
        pdf_bytes: PDF file bytes
        
    Returns:
        Extracted text
    """
    try:
        response = textract_client.detect_document_text(
            Document={"Bytes": pdf_bytes}
        )
        
        text_blocks = []
        for block in response.get("Blocks", []):
            if block.get("BlockType") == "LINE":
                text = block.get("Text", "").strip()
                if text:
                    text_blocks.append(text)
        
        extracted_text = "\n".join(text_blocks)
        logger.info(f"Extracted {len(extracted_text)} characters using simple API")
        return extracted_text
        
    except Exception as e:
        logger.error(f"Error in simple text extraction: {str(e)}")
        raise Exception(f"Failed to extract text: {str(e)}")


def extract_text_async(s3_bucket: str, s3_key: str) -> str:
    """
    Extract text from PDF in S3 using async Textract job (for large PDFs).
    
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
        logger.info(f"Started Textract job: {job_id}")
        
        # Poll for completion
        max_attempts = 60  # 2 minutes max wait
        for attempt in range(max_attempts):
            response = textract_client.get_document_text_detection(JobId=job_id)
            status = response["JobStatus"]
            
            if status == "SUCCEEDED":
                # Extract text from results
                text_blocks = []
                for block in response.get("Blocks", []):
                    if block.get("BlockType") == "LINE":
                        text = block.get("Text", "").strip()
                        if text:
                            text_blocks.append(text)
                
                extracted_text = "\n".join(text_blocks)
                logger.info(f"Async extraction completed: {len(extracted_text)} characters")
                return extracted_text
                
            elif status == "FAILED":
                error_message = response.get("StatusMessage", "Unknown error")
                raise Exception(f"Textract job failed: {error_message}")
            
            # Wait before next poll
            time.sleep(2)
        
        raise Exception("Textract job timed out")
        
    except ClientError as e:
        logger.error(f"Textract async error: {str(e)}")
        raise Exception(f"Textract error: {str(e)}")
    except Exception as e:
        logger.error(f"Error in async extraction: {str(e)}")
        raise
