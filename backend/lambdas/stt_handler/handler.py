"""
Lambda handler for Speech-to-Text using Amazon Transcribe.

This handler converts audio to text using:
- Amazon Transcribe for speech recognition
- Amazon S3 for temporary audio storage
"""

import json
import os
import sys
import base64
import logging
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from utils.response import success_response, error_response, lambda_response
from utils.aws.transcribe import transcribe_audio

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for STT endpoint.
    
    Expected event:
    - body: base64-encoded audio file OR JSON with base64 audio
    - headers: Content-Type, x-language-code (optional)
    
    Returns:
    {
        "success": true,
        "data": {
            "text": "transcribed text"
        }
    }
    """
    try:
        logger.info("STT handler invoked")
        
        # Parse audio from request
        audio_bytes = None
        body = {}
        
        if event.get("isBase64Encoded"):
            audio_bytes = base64.b64decode(event["body"])
        elif isinstance(event.get("body"), str):
            try:
                body = json.loads(event["body"])
                if "audio" in body:
                    audio_bytes = base64.b64decode(body["audio"])
                else:
                    audio_bytes = base64.b64decode(event["body"])
            except (json.JSONDecodeError, ValueError):
                return lambda_response(
                    400,
                    error_response("Invalid audio format")
                )
        else:
            body = event.get("body", {})
            if isinstance(body, dict) and "audio" in body:
                audio_bytes = base64.b64decode(body["audio"])
            else:
                return lambda_response(
                    400,
                    error_response("Audio file is required")
                )
        
        if not audio_bytes:
            return lambda_response(
                400,
                error_response("Could not extract audio data")
            )
        
        logger.info(f"Audio received: {len(audio_bytes)} bytes")
        
        # Get language code from headers or body
        headers = event.get("headers", {})
        language_code = (
            headers.get("x-language-code") or
            headers.get("X-Language-Code") or
            (body.get("language") if isinstance(body, dict) else None) or
            "en-US"
        )
        
        # Map language codes
        language_map = {
            "en": "en-US",
            "hi": "hi-IN",
            "mr": "mr-IN",
        }
        
        if language_code in language_map:
            language_code = language_map[language_code]
        
        logger.info(f"Processing audio with language: {language_code}")
        
        # Transcribe audio
        try:
            transcript = transcribe_audio(audio_bytes, language_code)
            
            if not transcript or not transcript.strip():
                logger.warning("Empty transcript received")
                return lambda_response(
                    400,
                    error_response("Could not transcribe audio. Please ensure the audio contains clear speech.")
                )
            
            logger.info(f"Transcription successful: {len(transcript)} characters")
            
            return lambda_response(
                200,
                success_response({
                    "text": transcript
                })
            )
            
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            error_message = str(e)
            
            # Provide user-friendly error messages
            if "access denied" in error_message.lower():
                error_message = "Transcribe access denied. Please check IAM permissions."
            elif "timeout" in error_message.lower():
                error_message = "Transcription timed out. Please try with a shorter audio clip."
            elif "language" in error_message.lower():
                error_message = f"Unsupported language: {language_code}. Please use en-US, hi-IN, or mr-IN."
            
            return lambda_response(
                500,
                error_response(f"Failed to transcribe audio: {error_message}")
            )
        
    except base64.binascii.Error as e:
        logger.error(f"Base64 decode error: {str(e)}")
        return lambda_response(
            400,
            error_response("Invalid base64 encoding")
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return lambda_response(
            500,
            error_response(f"Internal server error: {str(e)}")
        )
