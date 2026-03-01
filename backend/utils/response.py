"""
Standardized Lambda response utilities.
"""

import json
from typing import Any, Dict, Optional


def success_response(data: Any, message: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a successful API response.
    
    Args:
        data: Response data
        message: Optional success message
        
    Returns:
        Formatted response dictionary
    """
    response = {
        "success": True,
        "data": data
    }
    
    if message:
        response["message"] = message
    
    return response


def error_response(message: str, status_code: int = 400) -> Dict[str, Any]:
    """
    Create an error API response.
    
    Args:
        message: Error message
        status_code: HTTP status code
        
    Returns:
        Formatted error response dictionary
    """
    return {
        "success": False,
        "message": message
    }


def lambda_response(
    status_code: int,
    body: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Create a Lambda proxy integration response.
    
    Args:
        status_code: HTTP status code
        body: Response body
        headers: Optional headers
        
    Returns:
        Lambda response dictionary
    """
    default_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS"
    }
    
    if headers:
        default_headers.update(headers)
    
    return {
        "statusCode": status_code,
        "headers": default_headers,
        "body": json.dumps(body)
    }
