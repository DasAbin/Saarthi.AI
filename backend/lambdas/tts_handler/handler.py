"""
Lambda handler for Text-to-Speech using Amazon Polly.

This handler converts text to speech using:
- Amazon Polly for speech synthesis
- Supports multiple languages (en, hi, mr)
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
from utils.aws.polly import synthesize_speech_base64

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for TTS endpoint.
    
    Expected event body:
    {
        "text": "Hello, how can I help you?",
        "language": "en" | "hi" | "mr"
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "audio": "base64-encoded MP3 audio"
        }
    }
    """
    try:
        logger.info("TTS handler invoked")
        
        # Parse request body
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        else:
            body = event.get("body", {})
        
        # Validate input
        text = body.get("text", "").strip()
        language = body.get("language", "en")
        
        if not text:
            logger.warning("Empty text received")
            return lambda_response(
                400,
                error_response("Text is required")
            )
        
        if language not in ["en", "hi", "mr"]:
            logger.warning(f"Invalid language: {language}")
            return lambda_response(
                400,
                error_response("Language must be 'en', 'hi', or 'mr'")
            )
        
        # Limit text length (Polly has limits)
        max_length = 3000
        if len(text) > max_length:
            logger.warning(f"Text truncated from {len(text)} to {max_length} characters")
            text = text[:max_length] + "..."
        
        logger.info(f"Processing TTS: {len(text)} characters (language: {language})")
        
        # Synthesize speech using Polly
        try:
            audio_base64 = synthesize_speech_base64(text, language)
            
            logger.info("TTS synthesis successful")
            
            return lambda_response(
                200,
                success_response({
                    "audio": audio_base64
                })
            )
            
        except Exception as e:
            logger.error(f"TTS synthesis error: {str(e)}")
            error_message = str(e)
            
            # Provide user-friendly error messages
            if "access denied" in error_message.lower():
                error_message = "Polly access denied. Please check IAM permissions."
            elif "TextLengthExceededException" in error_message:
                error_message = "Text exceeds maximum length (3000 characters). Please shorten the text."
            elif "InvalidParameterException" in error_message:
                error_message = f"Invalid language or voice: {language}. Please use 'en', 'hi', or 'mr'."
            
            return lambda_response(
                500,
                error_response(f"Failed to synthesize speech: {error_message}")
            )
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return lambda_response(
            400,
            error_response("Invalid JSON in request body")
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return lambda_response(
            500,
            error_response(f"Internal server error: {str(e)}")
        )
