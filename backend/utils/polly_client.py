"""
Amazon Polly client utilities for Text-to-Speech.
"""

import boto3
import os
import base64
from typing import Optional
from botocore.exceptions import ClientError

polly_client = boto3.client("polly", region_name=os.getenv("AWS_REGION", "us-east-1"))

# Voice mapping for languages
VOICE_MAP = {
    "en": "Joanna",
    "hi": "Aditi",
    "mr": "Aditi",  # Marathi uses Hindi voice
}


def synthesize_speech(text: str, language_code: str = "en") -> bytes:
    """
    Synthesize speech using Amazon Polly.
    
    Args:
        text: Text to synthesize
        language_code: Language code (en, hi, mr)
        
    Returns:
        Audio bytes (MP3 format)
    """
    voice_id = VOICE_MAP.get(language_code, "Joanna")
    
    # Map language codes to Polly language codes
    language_map = {
        "en": "en-US",
        "hi": "hi-IN",
        "mr": "hi-IN",  # Marathi uses Hindi
    }
    
    try:
        response = polly_client.synthesize_speech(
            Text=text,
            OutputFormat="mp3",
            VoiceId=voice_id,
            LanguageCode=language_map.get(language_code, "en-US")
        )
        
        audio_stream = response["AudioStream"]
        return audio_stream.read()
        
    except ClientError as e:
        raise Exception(f"Polly error: {str(e)}")


def synthesize_speech_base64(text: str, language_code: str = "en") -> str:
    """
    Synthesize speech and return as base64-encoded string.
    
    Args:
        text: Text to synthesize
        language_code: Language code
        
    Returns:
        Base64-encoded audio string
    """
    audio_bytes = synthesize_speech(text, language_code)
    return base64.b64encode(audio_bytes).decode("utf-8")
