"""
Stock refresh endpoint handler for TradeSeekerAPI v2.

POST /stocks/{symbol}/refresh
  -> Sends a single-symbol download task to SQS so the downloader
     Lambda picks it up and fetches the latest data from EODHD.

The symbol must include the market suffix, e.g. AAPL.US, BH.BK, BTC-USD.CC
If the user omits the suffix, we default to .US.
"""

import json
import logging
import os
from datetime import datetime

import boto3
from botocore.exceptions import ClientError

from src.formatters import success_response, error_response

logger = logging.getLogger(__name__)

SQS_QUEUE_URL_PARAM = os.environ.get('DOWNLOAD_QUEUE_URL', '')
AWS_REGION         = os.environ.get('LAMBDA_REGION', 'ap-southeast-1')


def _get_queue_url() -> str:
    """Resolve queue URL from env var or SSM."""
    if SQS_QUEUE_URL_PARAM:
        return SQS_QUEUE_URL_PARAM

    # Fallback: look up from SSM
    ssm = boto3.client('ssm', region_name=AWS_REGION)
    try:
        env = os.environ.get('ENVIRONMENT', 'dev')
        param_name = f'/ts-batch-v2/{env}/download-queue-url'
        response = ssm.get_parameter(Name=param_name)
        return response['Parameter']['Value']
    except Exception as e:
        logger.error(f'Could not resolve SQS queue URL: {e}')
        return ''


def handle_stock_refresh(symbol: str) -> dict:
    """
    Send a refresh task for the given symbol to the SQS download queue.

    Args:
        symbol: Stock symbol, e.g. AAPL.US or AAPL

    Returns:
        Response dict with statusCode and body
    """
    if not symbol:
        return error_response('symbol is required', 400)

    # Normalise: uppercase, split on dot to get market code
    symbol_upper = symbol.upper().strip()

    if '.' in symbol_upper:
        parts = symbol_upper.rsplit('.', 1)
        stock_code  = parts[0]
        market_code = parts[1]
    else:
        # Default to US market
        stock_code  = symbol_upper
        market_code = 'US'

    symbol_with_market = f'{stock_code}.{market_code}'
    today = datetime.utcnow().strftime('%Y-%m-%d')

    task = {
        'symbol':     stock_code,
        'marketCode': market_code,
        'date':       today,
    }

    queue_url = _get_queue_url()
    if not queue_url:
        logger.error('SQS queue URL not configured')
        return error_response('Refresh service not configured', 503)

    try:
        sqs = boto3.client('sqs', region_name=AWS_REGION)
        sqs.send_message(
            QueueUrl    = queue_url,
            MessageBody = json.dumps(task),
        )
        logger.info(f'Refresh task queued for {symbol_with_market}')
        return success_response({
            'symbol':  symbol_with_market,
            'status':  'queued',
            'message': f'Refresh task queued for {symbol_with_market}. Data will be updated in ~1–2 minutes.',
        })
    except ClientError as e:
        logger.error(f'SQS error queuing refresh for {symbol_with_market}: {e}')
        return error_response('Failed to queue refresh task', 500)
    except Exception as e:
        logger.error(f'Unexpected error in stock_refresh: {e}', exc_info=True)
        return error_response('Internal server error', 500)
