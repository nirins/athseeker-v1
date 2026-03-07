"""
Technical Analysis module for stock price calculations
"""

from typing import Dict, List
from decimal import Decimal
import logging

logger = logging.getLogger()


def calculate_ema_series(data: List[Dict], period: int) -> List[float]:
    """
    Calculate EMA series for all data points
    
    EMA formula:
    - EMA(today) = (Price(today) × k) + (EMA(yesterday) × (1 - k))
    - k = 2 / (period + 1)
    - First EMA = SMA of first 'period' prices
    
    Args:
        data: List of price records sorted by date
        period: EMA period (e.g., 7, 30, 50, 200)
        
    Returns:
        List of EMA values (None for insufficient data points)
    """
    if len(data) < period:
        return [None] * len(data)
    
    k = 2 / (period + 1)
    ema_values = []
    
    # Calculate initial SMA for first EMA value
    initial_prices = [data[i]['close'] for i in range(period)]
    ema = sum(initial_prices) / period
    
    # Fill None for insufficient data points
    for i in range(period - 1):
        ema_values.append(None)
    
    # First EMA value
    ema_values.append(ema)
    
    # Calculate EMA for remaining data points
    for i in range(period, len(data)):
        price = data[i]['close']
        ema = (price * k) + (ema * (1 - k))
        ema_values.append(ema)
    
    return ema_values


def calculate_candle_metrics(price_data: List[Dict], days: int = 30) -> Dict:
    """
    Calculate candle metrics for the last N days
    
    Args:
        price_data: List of price records sorted by date
        days: Number of recent days to analyze (default: 30)
        
    Returns:
        dict with green_days_pct and max_red_candle_pct as Decimal types
    """
    if len(price_data) < days:
        return None
    
    # Get last N days
    recent_data = price_data[-days:]
    
    green_days = 0
    max_red_candle_pct = 0.0  # Track the largest red candle (most negative)
    
    for record in recent_data:
        open_price = record['open']
        close_price = record['close']
        
        # Check if green day (close > open)
        if close_price > open_price:
            green_days += 1
        
        # Calculate candle percentage change
        if open_price > 0:
            candle_pct = ((close_price - open_price) / open_price) * 100
            
            # Track the most negative (largest red candle)
            if candle_pct < max_red_candle_pct:
                max_red_candle_pct = candle_pct
    
    # Calculate green days percentage
    green_days_pct = (green_days / days) * 100
    
    return {
        'green_days_pct': Decimal(str(round(green_days_pct, 2))),
        'max_red_candle_pct': Decimal(str(round(max_red_candle_pct, 2)))
    }