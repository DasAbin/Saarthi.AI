"""
Amazon Transcribe client utilities for Speech-to-Text.
"""

import boto3
import os
from typing import Optional
from botocore.exceptions import ClientError

transcribe_client = boto3.client("transcribe", region_name=os.getenv("AWS_REGION", "us-east-1"))


def transcribe_audio(audio_bytes: bytes, language_code: str = "en-US") -> str:
    """
    Transcribe audio using Amazon Transcribe.
    
    Args:
        audio_bytes: Audio file bytes
        language_code: Language code (en-US, hi-IN, mr-IN, etc.)
        
    Returns:
        Transcribed text
    """
    import uuid
    import time
    import json
    
    # Upload audio to S3 temporarily
    s3_client = boto3.client("s3", region_name=os.getenv("AWS_REGION", "us-east-1"))
    temp_bucket = os.getenv("TEMP_AUDIO_BUCKET", "saarthi-temp-audio")
    job_name = f"transcribe-{uuid.uuid4()}"
    audio_key = f"audio/{job_name}.webm"
    
    try:
        # Upload audio
        s3_client.put_object(
            Bucket=temp_bucket,
            Key=audio_key,
            Body=audio_bytes,
            ContentType="audio/webm"
        )
        
        # Start transcription job
        media_uri = f"s3://{temp_bucket}/{audio_key}"
        
        transcribe_client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={"MediaFileUri": media_uri},
            MediaFormat="webm",
            LanguageCode=language_code
        )
        
        # Poll for completion
        max_attempts = 60
        for _ in range(max_attempts):
            response = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
            status = response["TranscriptionJob"]["TranscriptionJobStatus"]
            
            if status == "COMPLETED":
                # Get transcript URI
                transcript_uri = response["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
                
                # Download transcript
                import requests
                transcript_response = requests.get(transcript_uri)
                transcript_data = transcript_response.json()
                
                # Extract text
                transcript_text = transcript_data["results"]["transcripts"][0]["transcript"]
                
                # Cleanup
                transcribe_client.delete_transcription_job(TranscriptionJobName=job_name)
                s3_client.delete_object(Bucket=temp_bucket, Key=audio_key)
                
                return transcript_text
            elif status == "FAILED":
                error = response["TranscriptionJob"].get("FailureReason", "Unknown error")
                raise Exception(f"Transcription failed: {error}")
            
            time.sleep(2)
        
        raise Exception("Transcription job timed out")
        
    except ClientError as e:
        raise Exception(f"Transcribe error: {str(e)}")
