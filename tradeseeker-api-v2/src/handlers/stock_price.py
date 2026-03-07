"""
Stock price endpoint handler for TradeSeekerAPI v2.

This module handles GET /stocks/{symbol} requests to retrieve
detailed stock price history with technical indicators.
"""

import logging
from typing import Dict, Any

from botocore.exceptions import ClientError

from src.validators import validate_stock_price_params
from src.formatters import success_response, error_response
from src.db.dynamodb_client import DynamoDBClient

logger = logging.getLogger(__name__)


def handle_stock_price(symbol: str, query_params: Dict[str, Any]) -> dict:
    """
    Handles GET /stocks/{symbol} requests.
    
    Retrieves stock price data from DynamoDB with optional filters:
    - start_date: Filter prices to dates >= start_date (YYYY-MM-DD)
    - end_date: Filter prices to dates <= end_date (YYYY-MM-DD)
    - limit: Return only N most recent price records
    
    Args:
        symbol: Stock symbol with market code (e.g., AAPL.US)
        query_params: Dict with optional query parameters
        
    Returns:
        Response dict with statusCode and body containing data object
    """
    # Validate symbol and query parameters
    validated_symbol, validated_params, validation_errors = validate_stock_price_params(
        symbol, query_params
    )
    
    if validation_errors:
        logger.warning(f"Validation errors for symbol={symbol}: {validation_errors}")
        return error_response("Invalid parameters", 400, validation_errors)
    
    # Extract validated parameters
    start_date = validated_params.get('start_date')
    end_date = validated_params.get('end_date')
    limit = validated_params.get('limit')
    
    logger.info(
        f"Processing stock price request: symbol={validated_symbol}, "
        f"start_date={start_date}, end_date={end_date}, limit={limit}"
    )
    
    try:
        # Initialize DynamoDB client
        db_client = DynamoDBClient()
        
        # Execute DynamoDB GetItem
        stock_data = db_client.get_stock_price(validated_symbol)
        
        # Return 404 if symbol not found
        if not stock_data:
            logger.info(f"Symbol not found: {validated_symbol}")
            return error_response(f"Symbol '{validated_symbol}' not found", 404)
        
        # Filter prices array based on date range
        if start_date or end_date:
            stock_data = _filter_prices_by_date(stock_data, start_date, end_date)
        
        # Apply limit to return N most recent records
        if limit:
            stock_data = _apply_limit(stock_data, limit)
        
        logger.info(f"Returning stock data for {validated_symbol}")
        
        return success_response(stock_data)
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        if error_code == 'ProvisionedThroughputExceededException':
            logger.error(f"DynamoDB throttling: {error_message}")
            return error_response(
                "Service temporarily unavailable, please retry",
                503
            )
        elif error_code == 'ResourceNotFoundException':
            logger.error(f"DynamoDB table not found: {error_message}")
            return error_response("Service configuration error", 500)
        else:
            logger.error(f"DynamoDB error: {error_code} - {error_message}")
            return error_response("Database query failed", 500)
            
    except Exception as e:
        logger.error(f"Unhandled exception in stock_price handler: {e}", exc_info=True)
        return error_response("Internal server error", 500)


def _filter_prices_by_date(
    stock_data: dict,
    start_date: str = None,
    end_date: str = None
) -> dict:
    """
    Filter prices and moving_averages arrays based on start_date and end_date.
    
    Args:
        stock_data: Stock data dict with prices and moving_averages arrays
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)
        
    Returns:
        Stock data dict with filtered prices and moving_averages arrays, sorted old to new
    """
    result = stock_data.copy()
    
    # Filter prices array
    if 'prices' in stock_data:
        filtered_prices = []
        
        for price in stock_data['prices']:
            price_date = price.get('date')
            
            # Skip if no date field
            if not price_date:
                continue
            
            # Apply start_date filter
            if start_date and price_date < start_date:
                continue
            
            # Apply end_date filter
            if end_date and price_date > end_date:
                continue
            
            filtered_prices.append(price)
        
        # Sort filtered prices from old to new (ascending)
        sorted_prices = sorted(filtered_prices, key=lambda p: p.get('date', ''))
        result['prices'] = sorted_prices
        
        logger.info(
            f"Filtered prices from {len(stock_data['prices'])} to {len(sorted_prices)} records"
        )
    
    # Filter moving_averages array with same logic
    if 'moving_averages' in stock_data:
        filtered_ma = []
        
        for ma in stock_data['moving_averages']:
            ma_date = ma.get('date')
            
            # Skip if no date field
            if not ma_date:
                continue
            
            # Apply start_date filter
            if start_date and ma_date < start_date:
                continue
            
            # Apply end_date filter
            if end_date and ma_date > end_date:
                continue
            
            filtered_ma.append(ma)
        
        # Sort filtered moving_averages from old to new (ascending)
        sorted_ma = sorted(filtered_ma, key=lambda ma: ma.get('date', ''))
        result['moving_averages'] = sorted_ma
        
        logger.info(
            f"Filtered moving_averages from {len(stock_data['moving_averages'])} to {len(sorted_ma)} records"
        )
    
    return result


def _apply_limit(stock_data: dict, limit: int) -> dict:
    """
    Apply limit to return N most recent price records.
    
    Args:
        stock_data: Stock data dict with prices array
        limit: Maximum number of records to return
        
    Returns:
        Stock data dict with limited prices and moving_averages arrays, sorted old to new
    """
    result = stock_data.copy()
    
    # Apply limit to prices array
    if 'prices' in stock_data:
        prices = stock_data['prices']
        
        # Sort by date descending to get most recent first, then take N records
        sorted_prices_desc = sorted(prices, key=lambda p: p.get('date', ''), reverse=True)
        limited_prices = sorted_prices_desc[:limit]
        
        # Now sort the limited results from old to new (ascending)
        final_prices = sorted(limited_prices, key=lambda p: p.get('date', ''))
        result['prices'] = final_prices
        
        logger.info(f"Limited prices from {len(prices)} to {len(final_prices)} records")
    
    # Apply same limit and sorting to moving_averages array
    if 'moving_averages' in stock_data:
        moving_averages = stock_data['moving_averages']
        
        # Sort by date descending to get most recent first, then take N records
        sorted_ma_desc = sorted(moving_averages, key=lambda ma: ma.get('date', ''), reverse=True)
        limited_ma = sorted_ma_desc[:limit]
        
        # Now sort the limited results from old to new (ascending)
        final_ma = sorted(limited_ma, key=lambda ma: ma.get('date', ''))
        result['moving_averages'] = final_ma
        
        logger.info(f"Limited moving_averages from {len(moving_averages)} to {len(final_ma)} records")
    
    return result
