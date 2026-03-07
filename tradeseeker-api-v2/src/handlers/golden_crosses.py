"""
Golden cross endpoint handler for TradeSeekerAPI v2.

This module handles GET /golden-crosses requests with flexible filtering
for golden cross signals based on technical indicators.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from botocore.exceptions import ClientError

from src.validators import validate_golden_cross_params
from src.formatters import success_response, error_response
from src.db.dynamodb_client import DynamoDBClient

logger = logging.getLogger(__name__)


def handle_golden_crosses(query_params: Dict[str, Any]) -> dict:
    """
    Handles GET /golden-crosses requests.
    
    Queries golden cross signals from DynamoDB with optional filters:
    - min_green: Minimum percentage of green days (default 70)
    - max_red_candle: Maximum red candle percentage (default -8)
    - market: Market code filter (US, BK, CC)
    - date: Specific date filter (YYYY-MM-DD)
    - days: Filter to last N days
    - limit: Maximum number of results (default: 50, max: 100)
    - offset: Number of results to skip (default: 0)
    
    Args:
        query_params: Dict with optional query parameters
        
    Returns:
        Response dict with statusCode and body containing data array
    """
    # Validate query parameters
    validated_params, validation_errors = validate_golden_cross_params(query_params)
    
    if validation_errors:
        logger.warning(f"Validation errors: {validation_errors}")
        return error_response("Invalid parameters", 400, validation_errors)
    
    # Extract validated parameters
    min_green = validated_params['min_green']
    max_red_candle = validated_params['max_red_candle']
    market = validated_params.get('market')
    date = validated_params.get('date')
    days = validated_params.get('days')
    limit = validated_params['limit']
    offset = validated_params['offset']
    
    logger.info(
        f"Processing golden crosses request: min_green={min_green}, "
        f"max_red_candle={max_red_candle}, market={market}, date={date}, days={days}, "
        f"limit={limit}, offset={offset}"
    )
    
    try:
        # Initialize DynamoDB client
        db_client = DynamoDBClient()
        
        # Determine optimal query strategy and execute
        results = _execute_query(db_client, date, days, market, limit, offset)
        
        # Apply in-memory filtering for green_days and max_red_candle
        filtered_results = _apply_filters(results, min_green, max_red_candle)
        
        # Sort by cross_date descending (most recent first)
        sorted_results = sorted(filtered_results, key=lambda x: x.get('cross_date', ''), reverse=True)
        
        logger.info(
            f"Returning {len(sorted_results)} results "
            f"(filtered from {len(results)} records)"
        )
        
        return success_response(sorted_results)
        
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
        logger.error(f"Unhandled exception in golden_crosses handler: {e}", exc_info=True)
        return error_response("Internal server error", 500)


def _execute_query(
    db_client: DynamoDBClient,
    date: str = None,
    days: int = None,
    market: str = None,
    limit: int = 50,
    offset: int = 0
) -> list[dict]:
    """
    Execute optimal DynamoDB query based on parameters.
    
    Query strategy:
    - If date + market: Use market_code-cross_date-index GSI
    - If date only: Use cross_date-index GSI
    - If days: Calculate date range and use GSI
    - Otherwise: Scan table (with warning)
    
    Args:
        db_client: DynamoDB client instance
        date: Specific date filter (YYYY-MM-DD)
        days: Number of days to look back
        market: Market code filter
        limit: Maximum number of results to return
        offset: Number of results to skip
        
    Returns:
        List of golden cross records from DynamoDB
    """
    # Strategy 1: Specific date query (most efficient)
    if date:
        logger.info(f"Using date-based query strategy for date={date}")
        return db_client.query_golden_crosses_by_date(date, market)
    
    # Strategy 2: Date range query (days parameter)
    if days:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        logger.info(f"Using date range query strategy for last {days} days")
        return db_client.query_golden_crosses_by_date_range(start_date, end_date, market)
    
    # Strategy 3: Scan (least efficient, use with caution)
    logger.warning(
        "No date filter provided - performing table scan. "
        "Consider adding date or days parameter for better performance."
    )
    return db_client.scan_golden_crosses(market, limit=limit, offset=offset)


def _apply_filters(
    records: list[dict],
    min_green: float,
    max_red_candle: float
) -> list[dict]:
    """
    Apply in-memory filtering for green_days_30d_pct and max_red_candle_30d_pct.
    
    Args:
        records: List of golden cross records from DynamoDB
        min_green: Minimum green days percentage threshold
        max_red_candle: Maximum red candle percentage threshold
        
    Returns:
        Filtered list of records meeting both criteria
    """
    filtered = []
    
    for record in records:
        green_days = record.get('green_days_30d_pct', 0)
        red_candle = record.get('max_red_candle_30d_pct', 0)
        
        # Apply filters: green_days >= min_green AND red_candle >= max_red_candle
        if green_days >= min_green and red_candle >= max_red_candle:
            filtered.append(record)
    
    return filtered
