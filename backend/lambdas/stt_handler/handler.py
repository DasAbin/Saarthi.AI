"""
Lambda handler for Speech-to-Text using Amazon Transcribe.
"""

import json
import os
import sys
import base64
from typing import Dict, Any

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from utils.transcribe_client import transcribe_audio
from utils.response import success_response, error_response, lambda_response


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for STT endpoint.
    
    Expected event:
    - body: base64-encoded audio file
    - headers: Content-Type, x-language-code (optional)
    """
    try:
        # Parse audio from request
        if event.get("isBase64Encoded"):
            audio_bytes = base64.b64decode(event["body"])
        elif isinstance(event.get("body"), str):
            try:
                audio_bytes = base64.b64decode(event["body"])
            except:
                return lambda_response(
                    400,
                    error_response("Invalid audio format")
                )
        else:
            return lambda_response(
                400,
                error_response("Audio file is required")
            )
        
        # Get language code from headers or default
        headers = event.get("headers", {})
        language_code = headers.get("x-language-code", "en-US")
        
        # Map language codes
        language_map = {
            "en": "en-US",
            "hi": "hi-IN",
            "mr": "mr-IN",
        }
        
        if language_code in language_map:
            language_code = language_map[language_code]
        
        # Transcribe audio
        transcript = transcribe_audio(audio_bytes, language_code)
        
        return lambda_response(
            200,
            success_response({
                "text": transcript
            })
        )
        
    except Exception as e:
        print(f"Error in stt_handler: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return lambda_response(
            500,
            error_response(f"Internal server error: {str(e)}")
        )
