"""
Amazon Polly client utilities for Text-to-Speech.

Supports multiple languages and voices for natural speech synthesis.
"""

import boto3
import os
import base64
import logging
from typing import Optional
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize Polly client
polly_client = boto3.client("polly", region_name=os.getenv("AWS_REGION", "us-east-1"))

# Voice mapping for languages
VOICE_MAP = {
    "en": "Joanna",  # Female, US English
    "hi": "Aditi",   # Female, Hindi
    "mr": "Aditi",   # Marathi uses Hindi voice (Aditi supports both)
    "ta": "Valli",   # Tamil
    "te": "Vani",    # Telugu (if unsupported, Polly will fall back)
    "bn": "Aditi",   # Bengali approximation via Aditi
}

# Language code mapping
LANGUAGE_CODE_MAP = {
    "en": "en-US",
    "hi": "hi-IN",
    "mr": "hi-IN",   # Marathi uses Hindi language code
    "ta": "ta-IN",
    "te": "te-IN",
    "bn": "bn-IN",
}


def synthesize_speech(
    text: str,
    language_code: str = "en",
    voice_id: Optional[str] = None,
    output_format: str = "mp3",
    engine: str = "neural"  # Use neural engine for better quality
) -> bytes:
    """
    Synthesize speech using Amazon Polly.
    
    Args:
        text: Text to synthesize (max 3000 characters)
        language_code: Language code (en, hi, mr)
        voice_id: Optional voice ID (overrides language mapping)
        output_format: Audio format (mp3, ogg_vorbis, pcm)
        engine: Engine type (standard, neural)
        
    Returns:
        Audio bytes
    """
    try:
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        # Get voice ID
        if not voice_id:
            voice_id = VOICE_MAP.get(language_code, "Joanna")
        
        # Get language code
        polly_language_code = LANGUAGE_CODE_MAP.get(language_code, "en-US")
        
        # Validate text length (Polly limit: 3000 characters for SSML, 150k for plain text)
        max_length = 3000
        if len(text) > max_length:
            logger.warning(f"Text truncated from {len(text)} to {max_length} characters")
            text = text[:max_length] + "..."
        
        logger.info(f"Synthesizing speech: {len(text)} chars, voice: {voice_id}, language: {polly_language_code}")
        
        # Prepare synthesis parameters
        synthesis_params = {
            "Text": text,
            "OutputFormat": output_format,
            "VoiceId": voice_id,
        }
        
        # Add language code if not US English
        if polly_language_code != "en-US":
            synthesis_params["LanguageCode"] = polly_language_code
        
        # Use neural engine if available for the voice
        # Note: Not all voices support neural engine
        neural_voices = ["Joanna", "Matthew", "Amy", "Brian", "Emma", "Aditi"]
        if engine == "neural" and voice_id in neural_voices:
            synthesis_params["Engine"] = "neural"
        
        # Synthesize speech
        response = polly_client.synthesize_speech(**synthesis_params)
        
        # Read audio stream
        audio_stream = response["AudioStream"]
        audio_bytes = audio_stream.read()
        
        logger.info(f"Generated audio: {len(audio_bytes)} bytes")
        return audio_bytes
        
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code == "InvalidParameterException":
            logger.error("Invalid Polly parameters")
            raise Exception(f"Invalid synthesis parameters: {str(e)}")
        elif error_code == "TextLengthExceededException":
            logger.error("Text too long for Polly")
            raise Exception("Text exceeds maximum length (3000 characters)")
        else:
            logger.error(f"Polly error: {error_code}")
            raise Exception(f"Polly error: {str(e)}")
    except Exception as e:
        logger.error(f"Error synthesizing speech: {str(e)}")
        raise


def synthesize_speech_base64(
    text: str,
    language_code: str = "en",
    voice_id: Optional[str] = None
) -> str:
    """
    Synthesize speech and return as base64-encoded string.
    
    Args:
        text: Text to synthesize
        language_code: Language code (en, hi, mr)
        voice_id: Optional voice ID
        
    Returns:
        Base64-encoded audio string
    """
    audio_bytes = synthesize_speech(text, language_code, voice_id)
    return base64.b64encode(audio_bytes).decode("utf-8")


def get_available_voices(language_code: Optional[str] = None) -> list:
    """
    Get list of available voices.
    
    Args:
        language_code: Optional language code to filter
        
    Returns:
        List of voice dictionaries
    """
    try:
        params = {}
        if language_code:
            polly_language_code = LANGUAGE_CODE_MAP.get(language_code, language_code)
            params["LanguageCode"] = polly_language_code
        
        response = polly_client.describe_voices(**params)
        return response.get("Voices", [])
    except Exception as e:
        logger.error(f"Error getting voices: {str(e)}")
        return []
