#!/usr/bin/env python3
"""
Debug beauty score calculation for specific symbols
"""

import json
import boto3
import sys
import os
from decimal import Decimal
from typing import Dict, List, Any

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from beauty_models.model_factory import BeautyModelFactory

def decimal_to_float(obj):
    """Convert Decimal objects to float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_float(item) for item in obj]
    return obj

def get_stock_data(symbol: str, environment: str = 'dev') -> Dict:
    """Get stock data from DynamoDB"""
    try:
        dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-1')
        table_name = f"ts-batch-v2-{environment}-stock-prices"
        table = dynamodb.Table(table_name)
        
        response = table.get_item(Key={'symbol': symbol})
        
        if 'Item' not in response:
            print(f"No data found for {symbol}")
            return None
            
        return decimal_to_float(response['Item'])
        
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None

def debug_beauty_score(symbol: str):
    """Debug beauty score calculation for a specific symbol"""
    print(f"=== Debugging Beauty Score for {symbol} ===\n")
    
    # Get stock data
    stock_data = get_stock_data(symbol)
    if not stock_data:
        return
    
    print(f"Stock data found: {len(stock_data.get('price_data', []))} price records")
    print(f"Moving averages: {len(stock_data.get('moving_averages', []))} records")
    print(f"Beauty score: {stock_data.get('beauty_score', 'N/A')}")
    print(f"Last updated: {stock_data.get('last_updated', 'N/A')}")
    
    # Check if we have sufficient data
    price_data = stock_data.get('price_data', [])
    if len(price_data) < 10:
        print(f"\n❌ ISSUE: Insufficient price data ({len(price_data)} records)")
        print("   Beauty score calculation requires at least 10 records")
        return
    
    # Check moving averages
    moving_averages = stock_data.get('moving_averages', [])
    if len(moving_averages) < 10:
        print(f"\n❌ ISSUE: Insufficient moving averages data ({len(moving_averages)} records)")
        print("   Beauty score calculation requires EMA data")
        return
    
    # Check for EMA values in recent data
    recent_ma = moving_averages[-5:] if moving_averages else []
    print(f"\n=== Recent Moving Averages (last 5 days) ===")
    for i, ma in enumerate(recent_ma):
        print(f"Day {i+1}: Date={ma.get('date', 'N/A')}")
        print(f"  EMA7={ma.get('ema_7', 'N/A')}, EMA30={ma.get('ema_30', 'N/A')}")
        print(f"  EMA50={ma.get('ema_50', 'N/A')}, EMA200={ma.get('ema_200', 'N/A')}")
    
    # Check for missing EMA values
    missing_emas = []
    for ma in recent_ma:
        for ema in ['ema_7', 'ema_30', 'ema_50', 'ema_200']:
            if ma.get(ema) is None:
                missing_emas.append(f"{ema} on {ma.get('date', 'unknown date')}")
    
    if missing_emas:
        print(f"\n❌ ISSUE: Missing EMA values:")
        for missing in missing_emas:
            print(f"   - {missing}")
        print("   Beauty score calculation requires all EMA values")
        return
    
    # Try to calculate beauty score manually
    print(f"\n=== Attempting Beauty Score Calculation ===")
    try:
        # Get the beauty model
        factory = BeautyModelFactory()
        model = factory.get_active_model()
        print(f"Using model: {model.model_name} v{model.version}")
        
        # Prepare data for calculation (simulate breakout scenario)
        if len(price_data) >= 10 and len(moving_averages) >= 10:
            # Use last 7 days as pre-breakout, last day as breakout, and simulate post-breakout
            pre_breakout = price_data[-8:-1]  # 7 days before last
            breakout_day = price_data[-1]     # Last day
            post_breakout = [price_data[-1]]  # Use last day as post-breakout (minimal)
            
            print(f"Pre-breakout: {len(pre_breakout)} days")
            print(f"Breakout day: {breakout_day.get('date', 'N/A')}")
            print(f"Post-breakout: {len(post_breakout)} days")
            
            # Calculate beauty score
            result = model.calculate_beauty_score(pre_breakout, breakout_day, post_breakout)
            
            print(f"\n=== Beauty Score Result ===")
            print(json.dumps(result, indent=2))
            
        else:
            print("❌ Insufficient data for beauty score calculation")
            
    except Exception as e:
        print(f"❌ Error calculating beauty score: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    symbol = sys.argv[1] if len(sys.argv) > 1 else "CRC.US"
    debug_beauty_score(symbol)