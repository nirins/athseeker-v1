"""
All-time high stocks endpoint handler for TradeSeekerAPI v2.

This module handles GET /ath-stocks requests with flexible filtering
for all-time high stock signals.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from botocore.exceptions import ClientError

from src.validators import validate_ath_stocks_params
from src.formatters import success_response, error_response
from src.db.dynamodb_client import DynamoDBClient

logger = logging.getLogger(__name__)


def handle_ath_stocks(query_params: Dict[str, Any]) -> dict:
    """
    Handles GET /ath-stocks requests.
    
    Queries all-time high stock records from DynamoDB with optional filters:
    - market: Market code filter (US, BK, CC)
    - date: Specific date filter (YYYY-MM-DD)
    - days: Filter to last N days
    - min_gain: Minimum percentage gain filter (default: 0)
    - limit: Maximum number of results (default: 50, max: 100)
    - offset: Number of results to skip (default: 0)
    
    Args:
        query_params: Dict with optional query parameters
        
    Returns:
        Response dict with statusCode and body containing data array
    """
    # Validate query parameters
    validated_params, validation_errors = validate_ath_stocks_params(query_params)
    
    if validation_errors:
        logger.warning(f"Validation errors: {validation_errors}")
        return error_response("Invalid parameters", 400, validation_errors)
    
    # Extract validated parameters
    market = validated_params.get('market')
    date = validated_params.get('date')
    days = validated_params.get('days')
    min_gain = validated_params['min_gain']
    limit = validated_params['limit']
    offset = validated_params['offset']
    
    logger.info(
        f"Processing ATH stocks request: market={market}, date={date}, "
        f"days={days}, min_gain={min_gain}, limit={limit}, offset={offset}"
    )
    
    try:
        # Initialize DynamoDB client
        db_client = DynamoDBClient()
        
        # Determine optimal query strategy and execute
        results = _execute_query(db_client, date, days, market, limit, offset)
        
        # Apply in-memory filtering for min_gain
        filtered_results = _apply_filters(results, min_gain)
        
        # Sort by beauty_score descending only if not already ordered by GSI
        # The beauty_score GSI already returns results in correct order
        if market and not date and not days:
            # Results from beauty_score GSI are already ordered correctly
            sorted_results = filtered_results
        else:
            # Sort by beauty_score descending (highest beauty score first)
            # Fall back to detection_date if beauty_score is missing
            sorted_results = sorted(
                filtered_results, 
                key=lambda x: (x.get('beauty_score', 0), x.get('detection_date', '')), 
                reverse=True
            )
        
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
        logger.error(f"Unhandled exception in ath_stocks handler: {e}", exc_info=True)
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
    - If no date filters and market specified: Use beauty_score-index GSI (ordered by beauty score)
    - If date + market: Use market_code-detection_date-index GSI
    - If date only: Use detection_date-index GSI
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
        List of ATH stock records from DynamoDB
    """
    # Strategy 1: Specific date query (most efficient)
    if date:
        logger.info(f"Using date-based query strategy for date={date}")
        return db_client.query_ath_stocks_by_date(date, market)
    
    # Strategy 2: Date range query (days parameter)
    if days:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        logger.info(f"Using date range query strategy for last {days} days")
        return db_client.query_ath_stocks_by_date_range(start_date, end_date, market)
    
    # Strategy 3: Beauty score query (no date filters, market specified)
    if market and not date and not days:
        logger.info(f"Using beauty score query strategy for market={market}")
        return db_client.query_ath_stocks_by_beauty_score(market, limit)
    
    # Strategy 4: Scan (least efficient, use with caution)
    logger.warning(
        "No date filter provided - performing table scan. "
        "Consider adding date or days parameter for better performance."
    )
    return db_client.scan_ath_stocks(market, limit=limit, offset=offset)


def _apply_filters(
    records: list[dict],
    min_gain: float
) -> list[dict]:
    """
    Apply in-memory filtering for ath_percentage_gain.
    
    Args:
        records: List of ATH stock records from DynamoDB
        min_gain: Minimum percentage gain threshold
        
    Returns:
        Filtered list of records meeting the criteria
    """
    filtered = []
    
    for record in records:
        percentage_gain = record.get('ath_percentage_gain', 0)
        
        # Apply filter: percentage_gain >= min_gain
        if percentage_gain >= min_gain:
            filtered.append(record)
    
    return filtered