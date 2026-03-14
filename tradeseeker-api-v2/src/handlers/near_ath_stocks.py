"""
Near all-time high stocks endpoint handler for TradeSeekerAPI v2.

This module handles GET /near-ath requests filtered by market code.
"""

import logging
from typing import Dict, Any

from botocore.exceptions import ClientError

from src.validators import validate_near_ath_stocks_params
from src.formatters import success_response, error_response
from src.db.dynamodb_client import DynamoDBClient

logger = logging.getLogger(__name__)


def handle_near_ath_stocks(query_params: Dict[str, Any]) -> dict:
    """
    Handles GET /near-ath requests.
    
    Queries near all-time high stock records from DynamoDB filtered by market:
    - market: Market code filter (US, BK, CC) - required
    - max_distance: Maximum distance from ATH percentage (default: 10)
    - min_gain: Minimum percentage gain filter (default: 0)
    - limit: Maximum number of results (default: 50, max: 100)
    - offset: Number of results to skip (default: 0)
    
    Args:
        query_params: Dict with optional query parameters
        
    Returns:
        Response dict with statusCode and body containing data array
    """
    validated_params, validation_errors = validate_near_ath_stocks_params(query_params)
    
    if validation_errors:
        logger.warning(f"Validation errors: {validation_errors}")
        return error_response("Invalid parameters", 400, validation_errors)
    
    market = validated_params.get('market')
    max_distance = validated_params['max_distance']
    min_gain = validated_params['min_gain']
    limit = validated_params['limit']
    offset = validated_params['offset']
    
    logger.info(
        f"Processing Near ATH stocks request: market={market}, "
        f"max_distance={max_distance}, min_gain={min_gain}, limit={limit}, offset={offset}"
    )
    
    try:
        db_client = DynamoDBClient()
        
        if market:
            results = db_client.query_near_ath_stocks_by_beauty_score(market, limit)
        else:
            logger.warning("No market filter provided - performing table scan.")
            results = db_client.scan_near_ath_stocks(None, limit=limit, offset=offset)
        
        filtered_results = _apply_filters(results, max_distance, min_gain)
        
        logger.info(f"Returning {len(filtered_results)} results (filtered from {len(results)} records)")
        
        return success_response(filtered_results)
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        if error_code == 'ProvisionedThroughputExceededException':
            logger.error(f"DynamoDB throttling: {error_message}")
            return error_response("Service temporarily unavailable, please retry", 503)
        elif error_code == 'ResourceNotFoundException':
            logger.error(f"DynamoDB table not found: {error_message}")
            return error_response("Service configuration error", 500)
        else:
            logger.error(f"DynamoDB error: {error_code} - {error_message}")
            return error_response("Database query failed", 500)
            
    except Exception as e:
        logger.error(f"Unhandled exception in near_ath_stocks handler: {e}", exc_info=True)
        return error_response("Internal server error", 500)


def _apply_filters(records: list[dict], max_distance: float, min_gain: float) -> list[dict]:
    """Apply in-memory filtering for distance_from_ath_percentage and percentage_gain."""
    return [
        r for r in records
        if r.get('distance_from_ath_percentage', 100) <= max_distance
        and r.get('percentage_gain', 0) >= min_gain
    ]
