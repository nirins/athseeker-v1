"""
Lambda handler entry point for TradeSeekerAPI v2.

This module serves as the AWS Lambda function entry point, parsing API Gateway
proxy integration events and routing requests to appropriate handlers.
"""

import json
import logging
from typing import Any, Dict

from src.router import route_request
from src.formatters import error_response

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> dict:
    """
    AWS Lambda handler function for API Gateway proxy integration.
    
    Parses API Gateway events, extracts HTTP method, path, and parameters,
    routes to appropriate handler, and catches all unhandled exceptions.
    
    Args:
        event: API Gateway proxy integration event containing:
            - httpMethod: HTTP method (GET, POST, etc.)
            - path: Request path
            - queryStringParameters: Query parameters dict (or None)
            - pathParameters: Path parameters dict (or None)
            - requestContext: Request context with requestId
        context: Lambda context object with request_id, function_name, etc.
        
    Returns:
        API Gateway proxy integration response with:
            - statusCode: HTTP status code
            - headers: Response headers dict
            - body: JSON string response body
    """
    # Extract request ID for logging context
    request_id = context.request_id if hasattr(context, 'request_id') else 'unknown'
    
    try:
        # Log incoming request
        logger.info(
            f"Request {request_id}: {event.get('httpMethod')} {event.get('path')}",
            extra={
                'request_id': request_id,
                'method': event.get('httpMethod'),
                'path': event.get('path')
            }
        )
        
        # Extract HTTP method
        method = event.get('httpMethod', '')
        if not method:
            logger.error(f"Request {request_id}: Missing httpMethod in event")
            return error_response("Invalid request: missing HTTP method", 400)
        
        # Extract path
        path = event.get('path', '')
        if not path:
            logger.error(f"Request {request_id}: Missing path in event")
            return error_response("Invalid request: missing path", 400)
        
        # Extract query parameters (handle None case)
        query_params = event.get('queryStringParameters') or {}
        
        # Extract path parameters (handle None case)
        path_params = event.get('pathParameters') or {}
        
        # Extract request body for POST/DELETE requests
        body = {}
        if method in ('POST', 'DELETE'):
            body_str = event.get('body', '')
            if body_str:
                try:
                    body = json.loads(body_str)
                except json.JSONDecodeError as e:
                    logger.error(f"Request {request_id}: Invalid JSON in request body: {e}")
                    return error_response("Invalid JSON in request body", 400)
        
        # Route request to appropriate handler
        response = route_request(method, path, query_params, path_params, body)
        
        # Log response status
        logger.info(
            f"Request {request_id}: Response {response.get('statusCode')}",
            extra={
                'request_id': request_id,
                'status_code': response.get('statusCode')
            }
        )
        
        return response
        
    except Exception as e:
        # Catch all unhandled exceptions
        logger.error(
            f"Request {request_id}: Unhandled exception: {str(e)}",
            exc_info=True,
            extra={
                'request_id': request_id,
                'error_type': type(e).__name__,
                'error_message': str(e)
            }
        )
        
        # Return 500 error response
        return error_response(
            "Internal server error",
            500
        )
