"""
Positions handler for TradeSeekerAPI v2.

Tracks whether the user holds a position in a symbol — independent of the
watchlist (you can hold something you don't watch, and removing a symbol
from the watchlist never touches its position flag).

GET  /positions?user_id=xxx        -> list symbols with a position
POST /positions                    -> mark a position  { user_id, symbol }
DELETE /positions                  -> clear a position  { user_id, symbol }
"""

import logging
import os
from typing import Dict, Any

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from src.formatters import success_response, error_response

logger = logging.getLogger(__name__)

POSITIONS_TABLE = os.environ.get('POSITIONS_TABLE', 'ts-api-v2-dev-positions')


def _get_table():
    region = os.environ.get('LAMBDA_REGION', 'ap-southeast-1')
    dynamodb = boto3.resource('dynamodb', region_name=region)
    return dynamodb.Table(POSITIONS_TABLE)


def handle_get_positions(query_params: Dict[str, Any]) -> dict:
    user_id = (query_params or {}).get('user_id', '').strip()
    if not user_id:
        return error_response("user_id is required", 400)

    try:
        table = _get_table()
        result = table.query(
            KeyConditionExpression=Key('user_id').eq(user_id)
        )
        items = result.get('Items', [])
        items.sort(key=lambda x: x.get('added_at', ''), reverse=True)
        symbols = [item['symbol'] for item in items]

        return success_response({'symbols': symbols, 'count': len(symbols)})
    except ClientError as e:
        logger.error(f"DynamoDB error getting positions: {e}")
        return error_response("Failed to get positions", 500)


def handle_add_position(body: Dict[str, Any]) -> dict:
    user_id = (body or {}).get('user_id', '').strip()
    symbol = (body or {}).get('symbol', '').strip().upper()

    if not user_id:
        return error_response("user_id is required", 400)
    if not symbol:
        return error_response("symbol is required", 400)

    try:
        from datetime import datetime, timezone
        item = {
            'user_id': user_id,
            'symbol': symbol,
            'added_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        }
        table = _get_table()
        table.put_item(Item=item)
        return success_response({'user_id': user_id, 'symbol': symbol, 'action': 'added'})
    except ClientError as e:
        logger.error(f"DynamoDB error adding position: {e}")
        return error_response("Failed to add position", 500)


def handle_remove_position(body: Dict[str, Any]) -> dict:
    user_id = (body or {}).get('user_id', '').strip()
    symbol = (body or {}).get('symbol', '').strip().upper()

    if not user_id:
        return error_response("user_id is required", 400)
    if not symbol:
        return error_response("symbol is required", 400)

    try:
        table = _get_table()
        table.delete_item(Key={'user_id': user_id, 'symbol': symbol})
        return success_response({'user_id': user_id, 'symbol': symbol, 'action': 'removed'})
    except ClientError as e:
        logger.error(f"DynamoDB error removing position: {e}")
        return error_response("Failed to remove position", 500)
