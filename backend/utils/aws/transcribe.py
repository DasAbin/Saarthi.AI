"""
Amazon Transcribe client utilities for Speech-to-Text.

Handles audio transcription using async Transcribe jobs with S3 storage.
"""

import boto3
import os
import uuid
import time
import logging
import json
import urllib.request
from typing import Optional
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize clients
transcribe_client = boto3.client("transcribe", region_name=os.getenv("AWS_REGION", "ap-south-1"))
s3_client = boto3.client("s3", region_name=os.getenv("AWS_REGION", "ap-south-1"))

# Temp bucket for audio files
TEMP_AUDIO_BUCKET = os.getenv("TEMP_AUDIO_BUCKET", "saarthi-temp-audio")


def detect_audio_format(audio_bytes: bytes) -> str:
    """
    Detect audio format from bytes.
    
    Args:
        audio_bytes: Audio file bytes
        
    Returns:
        Format string (webm, mp3, wav, etc.)
    """
    # Check magic bytes
    if audio_bytes.startswith(b"RIFF") and b"WAVE" in audio_bytes[:12]:
        return "wav"
    elif audio_bytes.startswith(b"\xff\xfb") or audio_bytes.startswith(b"ID3"):
        return "mp3"
    elif audio_bytes.startswith(b"\x1aE\xdf\xa3"):
        return "webm"
    elif audio_bytes.startswith(b"fLaC"):
        return "flac"
    else:
        # Default to webm (common for browser recordings)
        return "webm"


def transcribe_audio(audio_bytes: bytes, language_code: str = "en-US") -> str:
    """
    Transcribe audio using Amazon Transcribe (async job).
    
    Args:
        audio_bytes: Audio file bytes
        language_code: Language code (en-US, hi-IN, mr-IN, etc.)
        
    Returns:
        Transcribed text
    """
    try:
        if not audio_bytes or len(audio_bytes) < 100:
            raise ValueError("Audio file is too small or empty")
        
        # Detect audio format (still used for S3 content-type and key)
        audio_format = detect_audio_format(audio_bytes)
        logger.info(f"Detected audio format: {audio_format}")
        
        # Generate unique job name and S3 key
        job_name = f"transcribe-{uuid.uuid4().hex[:16]}"
        audio_key = f"audio/{job_name}.{audio_format}"
        
        # Upload audio to S3
        logger.info(f"Uploading audio to S3: {audio_key}")
        try:
            s3_client.put_object(
                Bucket=TEMP_AUDIO_BUCKET,
                Key=audio_key,
                Body=audio_bytes,
                ContentType=f"audio/{audio_format}"
            )
        except ClientError as e:
            logger.error(f"Failed to upload audio to S3: {str(e)}")
            raise Exception(f"Failed to upload audio: {str(e)}")
        
        # Start transcription job
        media_uri = f"s3://{TEMP_AUDIO_BUCKET}/{audio_key}"
        audio_uri = media_uri
        logger.info(f"Starting Transcribe job: {job_name} (language: {language_code})")
        print("Starting transcription:", job_name)
        print("Language:", language_code)
        print("Audio URI:", audio_uri)

        try:
            # Use the detected audio format so Transcribe receives a matching MediaFormat.
            transcribe_client.start_transcription_job(
                TranscriptionJobName=job_name,
                LanguageCode=language_code,
                Media={
                    "MediaFileUri": media_uri
                },
                MediaFormat=audio_format,
                Settings={
                    "ShowSpeakerLabels": False
                }
            )
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "ConflictException":
                # Job name already exists, generate new one
                job_name = f"transcribe-{uuid.uuid4().hex[:16]}"
                audio_key = f"audio/{job_name}.{audio_format}"
                media_uri = f"s3://{TEMP_AUDIO_BUCKET}/{audio_key}"
                audio_uri = media_uri

                # Re-upload with new key
                s3_client.put_object(
                    Bucket=TEMP_AUDIO_BUCKET,
                    Key=audio_key,
                    Body=audio_bytes,
                    ContentType=f"audio/{audio_format}"
                )

                print("Starting transcription:", job_name)
                print("Language:", language_code)
                print("Audio URI:", audio_uri)

                transcribe_client.start_transcription_job(
                    TranscriptionJobName=job_name,
                    LanguageCode=language_code,
                    Media={
                        "MediaFileUri": media_uri
                    },
                    MediaFormat=audio_format,
                    Settings={
                        "ShowSpeakerLabels": False
                    }
                )
            else:
                raise
        
        # Poll for completion
        max_attempts = 60  # 2 minutes max wait
        logger.info("Polling for transcription completion...")
        
        for attempt in range(max_attempts):
            try:
                response = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
                status = response["TranscriptionJob"]["TranscriptionJobStatus"]
                
                if status == "COMPLETED":
                    # Get transcript URI
                    transcript_uri = response["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
                    logger.info(f"Transcription completed. Fetching transcript from: {transcript_uri}")
                    
                    # Download transcript using stdlib urllib (requests is not in Lambda)
                    with urllib.request.urlopen(transcript_uri, timeout=10) as resp:
                        transcript_data = json.loads(resp.read().decode("utf-8"))
                    
                    # Extract text
                    transcript_text = transcript_data["results"]["transcripts"][0]["transcript"]
                    
                    # Cleanup
                    cleanup_transcription_job(job_name, audio_key)
                    
                    logger.info(f"Transcription successful: {len(transcript_text)} characters")
                    return transcript_text
                    
                elif status == "FAILED":
                    error_message = response["TranscriptionJob"].get("FailureReason", "Unknown error")
                    logger.error(f"Transcription job failed: {error_message}")
                    cleanup_transcription_job(job_name, audio_key)
                    raise Exception(f"Transcription failed: {error_message}")
                
                # Wait before next poll
                if attempt < max_attempts - 1:
                    time.sleep(2)
                    
            except ClientError as e:
                logger.error(f"Error polling transcription job: {str(e)}")
                cleanup_transcription_job(job_name, audio_key)
                raise Exception(f"Transcribe error: {str(e)}")
        
        # Timeout
        logger.error("Transcription job timed out")
        cleanup_transcription_job(job_name, audio_key)
        raise Exception("Transcription job timed out after 2 minutes")
        
    except Exception as e:
        logger.error(f"Error in transcription: {str(e)}")
        raise


def cleanup_transcription_job(job_name: str, audio_key: str):
    """
    Clean up transcription job and temporary audio file.
    
    Args:
        job_name: Transcription job name
        audio_key: S3 audio file key
    """
    try:
        # Delete transcription job
        try:
            transcribe_client.delete_transcription_job(TranscriptionJobName=job_name)
            logger.debug(f"Deleted transcription job: {job_name}")
        except ClientError:
            pass  # Job may not exist or already deleted
        
        # Delete audio file from S3
        try:
            s3_client.delete_object(Bucket=TEMP_AUDIO_BUCKET, Key=audio_key)
            logger.debug(f"Deleted audio file: {audio_key}")
        except ClientError:
            pass  # File may not exist or already deleted
            
    except Exception as e:
        logger.warning(f"Error during cleanup: {str(e)}")
        # Don't raise - cleanup errors shouldn't fail the request
