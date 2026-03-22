"""
Batch stock price endpoint handler.
GET /stocks/batch?symbols=AAPL.US,MSFT.US,...
Reads from stock-prices-lite table (360 days) for fast response.
"""

import logging
from typing import Dict, Any

from src.formatters import success_response, error_response
from src.db.dynamodb_client import DynamoDBClient

logger = logging.getLogger(__name__)

MAX_SYMBOLS = 100


def handle_stock_batch(query_params: Dict[str, Any]) -> dict:
    symbols_param = query_params.get('symbols', '')
    if not symbols_param:
        return error_response("Missing required parameter: symbols", 400)

    symbols = [s.strip() for s in symbols_param.split(',') if s.strip()]
    if not symbols:
        return error_response("No valid symbols provided", 400)

    if len(symbols) > MAX_SYMBOLS:
        return error_response(f"Too many symbols. Maximum is {MAX_SYMBOLS}", 400)

    logger.info(f"Batch stock request for {len(symbols)} symbols")

    try:
        db_client = DynamoDBClient()
        items = db_client.batch_get_stock_prices_lite(symbols)

        results = {item['symbol']: item for item in items}

        return success_response({
            'results': results,
            'count': len(results),
            'requested': len(symbols)
        })

    except Exception as e:
        logger.error(f"Error in batch stock handler: {e}", exc_info=True)
        return error_response("Internal server error", 500)
