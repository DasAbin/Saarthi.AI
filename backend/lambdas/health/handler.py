"""
Lambda handler for health check endpoint.
"""

import json
from typing import Dict, Any

from utils.response import success_response, lambda_response


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for health check endpoint.
    """
    return lambda_response(
        200,
        success_response({"status": "ok"})
    )
