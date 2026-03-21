"""
Request router for TradeSeekerAPI v2.

This module routes incoming requests to appropriate handlers based on
HTTP method and path.
"""

import logging
import re
from typing import Dict, Any

from src.handlers.golden_crosses import handle_golden_crosses
from src.handlers.death_crosses import handle_death_crosses
from src.handlers.stock_price import handle_stock_price
from src.handlers.stock_history import handle_stock_history
from src.handlers.ath_stocks import handle_ath_stocks
from src.handlers.near_ath_stocks import handle_near_ath_stocks
from src.handlers.openai_summary import handle_openai_summary
from src.handlers.watchlist import handle_get_watchlist, handle_add_to_watchlist, handle_remove_from_watchlist
from src.formatters import error_response

logger = logging.getLogger(__name__)


def route_request(
    method: str,
    path: str,
    query_params: Dict[str, Any],
    path_params: Dict[str, Any],
    body: Dict[str, Any] = None
) -> dict:
    """
    Routes request to appropriate handler.
    
    Supported routes:
    - GET /golden-crosses -> golden_crosses_handler
    - GET /death-crosses -> death_crosses_handler
    - GET /ath -> ath_stocks_handler
    - GET /near-ath -> near_ath_stocks_handler
    - GET /openai-summary -> openai_summary_handler
    - GET /stocks/{symbol} -> stock_price_handler
    - GET /stocks/{symbol}/history -> stock_history_handler
    - GET /watchlist -> watchlist_handler (get)
    - POST /watchlist -> watchlist_handler (add)
    - DELETE /watchlist -> watchlist_handler (remove)
    - POST /training-data/save-by-grade -> save_training_data_handler
    
    Args:
        method: HTTP method (GET, POST, etc.)
        path: Request path
        query_params: Query string parameters
        path_params: Path parameters
        body: Request body (for POST requests)
        
    Returns:
        Handler response dict with statusCode and body
    """
    logger.info(f"Routing request: {method} {path}")
    
    # Normalize path (remove trailing slash)
    normalized_path = path.rstrip('/')
    
    # Handle GET requests
    if method == 'GET':
        return _route_get_request(normalized_path, query_params)
    
    # Handle POST requests
    elif method == 'POST':
        return _route_post_request(normalized_path, body or {})

    # Handle DELETE requests
    elif method == 'DELETE':
        return _route_delete_request(normalized_path, body or {})

    # Unsupported method
    else:
        logger.warning(f"Unsupported HTTP method: {method}")
        return error_response(
            f"Method {method} not allowed",
            405
        )


def _route_get_request(path: str, query_params: Dict[str, Any]) -> dict:
    """Route GET requests to appropriate handlers."""
    
    # Route: GET /golden-crosses
    if path == '/golden-crosses':
        logger.info("Routing to golden_crosses handler")
        return handle_golden_crosses(query_params)
    
    # Route: GET /death-crosses
    if path == '/death-crosses':
        logger.info("Routing to death_crosses handler")
        return handle_death_crosses(query_params)
    
    # Route: GET /ath
    if path == '/ath':
        logger.info("Routing to ath_stocks handler")
        return handle_ath_stocks(query_params)
    
    # Route: GET /near-ath
    if path == '/near-ath':
        logger.info("Routing to near_ath_stocks handler")
        return handle_near_ath_stocks(query_params)
    
    # Route: GET /openai-summary
    if path == '/openai-summary':
        logger.info("Routing to openai_summary handler")
        return handle_openai_summary(query_params)

    # Route: GET /watchlist
    if path == '/watchlist':
        logger.info("Routing to watchlist handler (get)")
        return handle_get_watchlist(query_params)

    # Route: GET /stocks/{symbol}/history
    history_pattern = r'^/stocks/([^/]+)/history$'
    history_match = re.match(history_pattern, path)
    
    if history_match:
        symbol = history_match.group(1)
        logger.info(f"Routing to stock_history handler with symbol={symbol}")
        return handle_stock_history(symbol, query_params)
    
    # Route: GET /stocks/{symbol}
    stock_pattern = r'^/stocks/([^/]+)$'
    match = re.match(stock_pattern, path)
    
    if match:
        symbol = match.group(1)
        logger.info(f"Routing to stock_price handler with symbol={symbol}")
        return handle_stock_price(symbol, query_params)
    
    # Unknown GET path - return 404
    logger.warning(f"Unknown GET path: {path}")
    return error_response(
        f"Endpoint not found: {path}",
        404
    )


def _route_post_request(path: str, body: Dict[str, Any]) -> dict:
    """Route POST requests to appropriate handlers."""

    # Route: POST /watchlist
    if path == '/watchlist':
        logger.info("Routing to watchlist handler (add)")
        return handle_add_to_watchlist(body)

    # Route: POST /training-data/save-by-grade
    if path == '/training-data/save-by-grade':
        logger.info("Routing to save_training_data handler")
        from src.handlers.save_training_data import lambda_handler as save_training_data_handler
        mock_event = {
            'body': body,
            'httpMethod': 'POST',
            'path': path
        }
        return save_training_data_handler(mock_event, None)

    # Unknown POST path - return 404
    logger.warning(f"Unknown POST path: {path}")
    return error_response(f"Endpoint not found: {path}", 404)


def _route_delete_request(path: str, body: Dict[str, Any]) -> dict:
    """Route DELETE requests to appropriate handlers."""

    # Route: DELETE /watchlist
    if path == '/watchlist':
        logger.info("Routing to watchlist handler (remove)")
        return handle_remove_from_watchlist(body)

    logger.warning(f"Unknown DELETE path: {path}")
    return error_response(f"Endpoint not found: {path}", 404)

