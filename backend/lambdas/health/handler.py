"""
Lambda handler for health check endpoint.

Simple endpoint to verify Lambda function is running correctly.
"""

import json
import os
import sys
import logging
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
    
    Returns:
    {
        "success": true,
        "data": {
            "status": "ok"
        }
    }
    """
    try:
        logger.info("Health check handler invoked")
        
        return lambda_response(
            200,
            success_response({"status": "ok"})
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
