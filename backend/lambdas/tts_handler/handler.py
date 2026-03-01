"""
Lambda handler for Text-to-Speech using Amazon Polly.
"""

import json
import os
import sys
from typing import Dict, Any

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from utils.polly_client import synthesize_speech_base64
from utils.response import success_response, error_response, lambda_response


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for TTS endpoint.
    
    Expected event body:
    {
        "text": "Hello, how can I help you?",
        "language": "en"
    }
    """
    try:
        # Parse request body
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        else:
            body = event.get("body", {})
        
        text = body.get("text", "").strip()
        language = body.get("language", "en")
        
        if not text:
            return lambda_response(
                400,
                error_response("Text is required")
            )
        
        # Limit text length (Polly has limits)
        if len(text) > 3000:
            text = text[:3000] + "..."
        
        # Synthesize speech
        audio_base64 = synthesize_speech_base64(text, language)
        
        return lambda_response(
            200,
            success_response({
                "audio": audio_base64
            })
        )
        
    except Exception as e:
        print(f"Error in tts_handler: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return lambda_response(
            500,
            error_response(f"Internal server error: {str(e)}")
        )
