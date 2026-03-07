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
from src.handlers.openai_summary import handle_openai_summary
from src.formatters import error_response

logger = logging.getLogger(__name__)


def route_request(
    method: str,
    path: str,
    query_params: Dict[str, Any],
    path_params: Dict[str, Any]
) -> dict:
    """
    Routes request to appropriate handler.
    
    Supported routes:
    - GET /golden-crosses -> golden_crosses_handler
    - GET /death-crosses -> death_crosses_handler
    - GET /ath -> ath_stocks_handler
    - GET /openai-summary -> openai_summary_handler
    - GET /stocks/{symbol} -> stock_price_handler
    - GET /stocks/{symbol}/history -> stock_history_handler
    
    Args:
        method: HTTP method (GET, POST, etc.)
        path: Request path
        query_params: Query string parameters
        path_params: Path parameters
        
    Returns:
        Handler response dict with statusCode and body
    """
    logger.info(f"Routing request: {method} {path}")
    
    # Check if method is supported
    if method != 'GET':
        logger.warning(f"Unsupported HTTP method: {method}")
        return error_response(
            f"Method {method} not allowed",
            405
        )
    
    # Normalize path (remove trailing slash)
    normalized_path = path.rstrip('/')
    
    # Route: GET /golden-crosses
    if normalized_path == '/golden-crosses':
        logger.info("Routing to golden_crosses handler")
        return handle_golden_crosses(query_params)
    
    # Route: GET /death-crosses
    if normalized_path == '/death-crosses':
        logger.info("Routing to death_crosses handler")
        return handle_death_crosses(query_params)
    
    # Route: GET /ath
    if normalized_path == '/ath':
        logger.info("Routing to ath_stocks handler")
        return handle_ath_stocks(query_params)
    
    # Route: GET /openai-summary
    if normalized_path == '/openai-summary':
        logger.info("Routing to openai_summary handler")
        return handle_openai_summary(query_params)
    
    # Route: GET /stocks/{symbol}/history
    history_pattern = r'^/stocks/([^/]+)/history$'
    history_match = re.match(history_pattern, normalized_path)
    
    if history_match:
        symbol = history_match.group(1)
        logger.info(f"Routing to stock_history handler with symbol={symbol}")
        return handle_stock_history(symbol, query_params)
    
    # Route: GET /stocks/{symbol}
    stock_pattern = r'^/stocks/([^/]+)$'
    match = re.match(stock_pattern, normalized_path)
    
    if match:
        symbol = match.group(1)
        logger.info(f"Routing to stock_price handler with symbol={symbol}")
        return handle_stock_price(symbol, query_params)
    
    # Unknown path - return 404
    logger.warning(f"Unknown path: {path}")
    return error_response(
        f"Endpoint not found: {path}",
        404
    )
