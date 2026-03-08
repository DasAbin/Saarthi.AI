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

from utils.response import lambda_response
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
        
        # ── Parse request body ──────────────────────────────────────────
        # New flow: frontend sends JSON { "audio": "<base64>", "language": "en" }
        # Legacy flow: raw binary multipart (isBase64Encoded=True)
        audio_bytes = None
        body = {}

        raw_body = event.get("body") or ""

        # Try JSON parse first (preferred path)
        if isinstance(raw_body, str) and raw_body.strip().startswith("{"):
            try:
                body = json.loads(raw_body)
            except json.JSONDecodeError:
                pass

        if isinstance(body, dict) and "audio" in body:
            # JSON body with base64 audio field (new frontend flow)
            try:
                audio_bytes = base64.b64decode(body["audio"])
            except Exception:
                return lambda_response(400, {"success": False, "error": "Invalid base64 audio data"})
        elif event.get("isBase64Encoded") and raw_body:
            # Legacy: API Gateway passed raw binary body as base64
            try:
                audio_bytes = base64.b64decode(raw_body)
            except Exception:
                return lambda_response(400, {"success": False, "error": "Invalid base64 encoded body"})
        else:
            return lambda_response(400, {"success": False, "error": "Audio file is required"})
        
        if not audio_bytes:
            return lambda_response(
                400,
                error_response("Could not extract audio data")
            )
        
        logger.info(f"Audio received: {len(audio_bytes)} bytes")
        
        # Get language from request and map to AWS Transcribe language code
        headers = event.get("headers", {}) or {}

        language = None
        if isinstance(body, dict):
            language = body.get("language")

        if not language:
            language = headers.get("x-language-code") or headers.get("X-Language-Code")

        if language == "hi":
            language_code = "hi-IN"
        elif language == "mr":
            language_code = "mr-IN"
        else:
            language_code = "en-IN"

        logger.info(f"Processing audio with language: {language_code}")
        
        # Transcribe audio with safe fallback
        try:
            transcript = transcribe_audio(audio_bytes, language_code)
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}", exc_info=True)
            return lambda_response(
                200,
                {
                    "success": False,
                    "error": "Speech recognition failed"
                }
            )

        if not transcript or not transcript.strip():
            logger.warning("Empty transcript received")
            return lambda_response(
                200,
                {
                    "success": False,
                    "error": "Speech recognition failed"
                }
            )

        transcript = transcript.strip()
        logger.info(f"Transcription successful: {len(transcript)} characters")

        return lambda_response(
            200,
            {
                "success": True,
                "text": transcript
            }
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
