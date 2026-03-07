"""
Stock history endpoint handler for TradeSeekerAPI v2.

This module handles GET /stocks/{symbol}/history requests to retrieve
full stock price history from EODHD API with calculated EMAs.
"""

import logging
import os
import requests
import boto3
import json
from typing import Dict, Any, List
from datetime import datetime, timedelta

from src.validators import validate_stock_price_params
from src.formatters import success_response, error_response

logger = logging.getLogger(__name__)


def handle_stock_history(symbol: str, query_params: Dict[str, Any]) -> dict:
    """
    Handles GET /stocks/{symbol}/history requests.
    
    Fetches full price history from EODHD API and calculates EMAs:
    - start_date: Start date for price data (YYYY-MM-DD, default: 2 years ago)
    - end_date: End date for price data (YYYY-MM-DD, default: today)
    - period: Time period (d=daily, w=weekly, m=monthly, default: d)
    
    Args:
        symbol: Stock symbol with market code (e.g., AAPL.US)
        query_params: Dict with optional query parameters
        
    Returns:
        Response dict with statusCode and body containing full price history and EMAs
    """
    # Validate symbol and query parameters
    validated_symbol, validated_params, validation_errors = validate_stock_price_params(
        symbol, query_params
    )
    
    if validation_errors:
        logger.warning(f"Validation errors for symbol={symbol}: {validation_errors}")
        return error_response("Invalid parameters", 400, validation_errors)
    
    # Extract validated parameters with defaults
    end_date = validated_params.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    start_date = validated_params.get('start_date', 
                                    (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d'))
    period = query_params.get('period', 'd')  # d=daily, w=weekly, m=monthly
    
    logger.info(
        f"Processing stock history request: symbol={validated_symbol}, "
        f"start_date={start_date}, end_date={end_date}, period={period}"
    )
    
    try:
        # Fetch price data from EODHD API
        price_data = _fetch_eodhd_data(validated_symbol, start_date, end_date, period)
        
        if not price_data:
            logger.info(f"No price data found for symbol: {validated_symbol}")
            return error_response(f"No price data found for symbol '{validated_symbol}'", 404)
        
        # Calculate EMAs
        ema_data = _calculate_emas(price_data)
        
        # Format response
        response_data = {
            'symbol': validated_symbol,
            'market_code': validated_symbol.split('.')[-1] if '.' in validated_symbol else 'US',
            'period': period,
            'start_date': start_date,
            'end_date': end_date,
            'prices': price_data,
            'moving_averages': ema_data,
            'total_records': len(price_data)
        }
        
        logger.info(f"Returning {len(price_data)} price records for {validated_symbol}")
        
        return success_response(response_data)
        
    except requests.RequestException as e:
        logger.error(f"EODHD API error: {e}")
        return error_response("External API error", 503)
        
    except Exception as e:
        logger.error(f"Unhandled exception in stock_history handler: {e}", exc_info=True)
        return error_response("Internal server error", 500)


def _fetch_eodhd_data(symbol: str, start_date: str, end_date: str, period: str) -> List[Dict]:
    """
    Fetch price data from EODHD API.
    
    Args:
        symbol: Stock symbol (e.g., AAPL.US)
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        period: Period (d, w, m)
        
    Returns:
        List of price records sorted by date ascending
    """
    # Get API token from AWS Secrets Manager
    api_token = _get_eodhd_api_token()
    
    # EODHD API endpoint
    url = f"https://eodhd.com/api/eod/{symbol}"
    
    params = {
        'api_token': api_token,
        'from': start_date,
        'to': end_date,
        'period': period,
        'fmt': 'json'
    }
    
    logger.info(f"Fetching EODHD data for {symbol} from {start_date} to {end_date}")
    
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    
    # Convert EODHD format to our format
    price_records = []
    for record in data:
        price_records.append({
            'date': record['date'],
            'open': float(record['open']),
            'high': float(record['high']),
            'low': float(record['low']),
            'close': float(record['close']),
            'volume': int(record['volume']) if record['volume'] else 0
        })
    
    # Sort by date ascending (oldest first)
    price_records.sort(key=lambda x: x['date'])
    
    logger.info(f"Fetched {len(price_records)} price records from EODHD")
    
    return price_records


def _get_eodhd_api_token() -> str:
    """
    Retrieve EODHD API token from AWS Secrets Manager.
    
    Returns:
        API token string
        
    Raises:
        ValueError: If secret name not configured or secret not found
        Exception: If unable to retrieve secret
    """
    secret_name = os.environ.get('EODHD_SECRET_NAME')
    if not secret_name:
        raise ValueError("EODHD_SECRET_NAME environment variable not set")
    
    try:
        # Create Secrets Manager client
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=os.environ.get('DYNAMODB_REGION', 'ap-southeast-1')
        )
        
        # Retrieve secret
        response = client.get_secret_value(SecretId=secret_name)
        secret_data = json.loads(response['SecretString'])
        
        # Extract API token from secret
        api_token = secret_data.get('api_token')
        if not api_token:
            raise ValueError(f"'api_token' key not found in secret '{secret_name}'")
        
        logger.info(f"Successfully retrieved EODHD API token from secret '{secret_name}'")
        return api_token
        
    except Exception as e:
        logger.error(f"Failed to retrieve EODHD API token from secret '{secret_name}': {e}")
        raise


def _calculate_emas(price_data: List[Dict]) -> List[Dict]:
    """
    Calculate EMAs (7, 30, 50, 200) for the price data.
    
    Args:
        price_data: List of price records with 'date' and 'close' fields
        
    Returns:
        List of EMA records with date and EMA values
    """
    if not price_data:
        return []
    
    # EMA periods to calculate
    periods = [7, 30, 50, 200]
    
    # Initialize EMA tracking
    emas = {period: None for period in periods}
    ema_records = []
    
    # EMA smoothing factor: 2 / (period + 1)
    smoothing = {period: 2.0 / (period + 1) for period in periods}
    
    for i, price in enumerate(price_data):
        close_price = price['close']
        date = price['date']
        
        ema_record = {'date': date}
        
        for period in periods:
            if emas[period] is None:
                # First EMA value is the close price
                emas[period] = close_price
            else:
                # EMA = (Close * smoothing) + (Previous EMA * (1 - smoothing))
                emas[period] = (close_price * smoothing[period]) + (emas[period] * (1 - smoothing[period]))
            
            # Only include EMA if we have enough data points
            if i >= period - 1:
                ema_record[f'ema_{period}'] = round(emas[period], 4)
        
        # Only add record if it has at least one EMA value
        if len(ema_record) > 1:  # More than just 'date'
            ema_records.append(ema_record)
    
    logger.info(f"Calculated EMAs for {len(ema_records)} records")
    
    return ema_records