"""
Watchlist handler for TradeSeekerAPI v2.

GET  /watchlist?user_id=xxx        -> list watchlist symbols
POST /watchlist                    -> add symbol  { user_id, symbol }
DELETE /watchlist                  -> remove symbol { user_id, symbol }
"""

import logging
import os
from typing import Dict, Any

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from src.formatters import success_response, error_response

logger = logging.getLogger(__name__)

WATCHLIST_TABLE = os.environ.get('WATCHLIST_TABLE', 'ts-api-v2-dev-watchlist')


def _get_table():
    region = os.environ.get('LAMBDA_REGION', 'ap-southeast-1')
    dynamodb = boto3.resource('dynamodb', region_name=region)
    return dynamodb.Table(WATCHLIST_TABLE)


def handle_get_watchlist(query_params: Dict[str, Any]) -> dict:
    user_id = (query_params or {}).get('user_id', '').strip()
    if not user_id:
        return error_response("user_id is required", 400)

    try:
        table = _get_table()
        result = table.query(
            KeyConditionExpression=Key('user_id').eq(user_id)
        )
        items = result.get('Items', [])
        # Sort by added_at descending (latest first), fall back to beauty_score
        items.sort(key=lambda x: x.get('added_at', ''), reverse=True)
        symbols = [item['symbol'] for item in items]
        beauty_scores = {
            item['symbol']: float(item['beauty_score'])
            for item in items
            if 'beauty_score' in item
        }

        return success_response({'symbols': symbols, 'beauty_scores': beauty_scores, 'count': len(symbols)})
    except ClientError as e:
        logger.error(f"DynamoDB error getting watchlist: {e}")
        return error_response("Failed to get watchlist", 500)


def handle_add_to_watchlist(body: Dict[str, Any]) -> dict:
    user_id = (body or {}).get('user_id', '').strip()
    symbol = (body or {}).get('symbol', '').strip().upper()
    beauty_score = (body or {}).get('beauty_score')

    if not user_id:
        return error_response("user_id is required", 400)
    if not symbol:
        return error_response("symbol is required", 400)

    try:
        from decimal import Decimal
        from datetime import datetime, timezone
        item = {
            'user_id': user_id,
            'symbol': symbol,
            'added_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        }
        if beauty_score is not None:
            item['beauty_score'] = Decimal(str(beauty_score))
        table = _get_table()
        table.put_item(Item=item)
        return success_response({'user_id': user_id, 'symbol': symbol, 'action': 'added'})
    except ClientError as e:
        logger.error(f"DynamoDB error adding to watchlist: {e}")
        return error_response("Failed to add to watchlist", 500)


def handle_remove_from_watchlist(body: Dict[str, Any]) -> dict:
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
        logger.error(f"DynamoDB error removing from watchlist: {e}")
        return error_response("Failed to remove from watchlist", 500)
