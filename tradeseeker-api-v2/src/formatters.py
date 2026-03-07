"""Response formatting utilities for API Gateway responses."""

import json
from decimal import Decimal
from typing import Any, Optional


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder that converts Decimal to float."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def success_response(data: Any, status_code: int = 200) -> dict:
    """
    Creates successful API Gateway response.
    
    Args:
        data: Response data (will be JSON serialized)
        status_code: HTTP status code
        
    Returns:
        API Gateway response dict with statusCode, headers, and body
    """
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        },
        "body": json.dumps({"data": data}, cls=DecimalEncoder)
    }


def error_response(
    message: str, 
    status_code: int = 400, 
    errors: Optional[list] = None
) -> dict:
    """
    Creates error API Gateway response.
    
    Args:
        message: Error message
        status_code: HTTP status code
        errors: Optional list of detailed errors
        
    Returns:
        API Gateway response dict with statusCode, headers, and body
    """
    body = {"error": message}
    if errors:
        body["details"] = errors
    
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        },
        "body": json.dumps(body)
    }
