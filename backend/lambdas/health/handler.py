"""
Lambda handler for health check endpoint.

Provides diagnostic info like models, features, and version.
"""

import json
import os
import sys
import logging
from datetime import datetime, timezone
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from utils.response import success_response, lambda_response

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for health check endpoint.
    """
    try:
        logger.info("Health check handler invoked")
        
        payload = {
            "status": "healthy",
            "service": "Saarthi.AI",
            "version": "1.0.0",
            "region": os.getenv("AWS_REGION", "ap-south-1"),
            "features": ["rag-query", "pdf-analyze", "scheme-recommend", "voice-stt", "voice-tts", "grievance-writer"],
            "models": {
                "text": os.getenv("TEXT_MODEL_ID", "apac.amazon.nova-micro-v1:0"),
                "embedding": os.getenv("EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0")
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        return lambda_response(
            200,
            success_response(payload)
        )
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return lambda_response(
            500,
            {
                "success": False,
                "message": f"Health check failed: {str(e)}"
            }
        )
