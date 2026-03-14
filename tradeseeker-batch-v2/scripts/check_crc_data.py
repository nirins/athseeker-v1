#!/usr/bin/env python3
"""
Check CRC.US data structure in detail
"""

import json
import boto3
from decimal import Decimal

def decimal_to_float(obj):
    """Convert Decimal objects to float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_float(item) for item in obj]
    return obj

def check_crc_data():
    """Check CRC.US data structure"""
    try:
        dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-1')
        table = dynamodb.Table('ts-batch-v2-dev-stock-prices')
        
        response = table.get_item(Key={'symbol': 'CRC.US'})
        
        if 'Item' not in response:
            print("CRC.US not found in database")
            return
            
        item = decimal_to_float(response['Item'])
        
        print("=== CRC.US Data Structure ===")
        print(f"Symbol: {item.get('symbol')}")
        print(f"Market Code: {item.get('market_code')}")
        print(f"Last Updated: {item.get('last_updated')}")
        print(f"Beauty Score: {item.get('beauty_score')}")
        
        # Check all top-level keys
        print(f"\nTop-level keys: {list(item.keys())}")
        
        # Check price_data
        price_data = item.get('price_data', [])
        print(f"\nPrice data: {len(price_data)} records")
        if price_data:
            print(f"First price record: {price_data[0]}")
            print(f"Last price record: {price_data[-1]}")
        
        # Check moving_averages
        moving_averages = item.get('moving_averages', [])
        print(f"\nMoving averages: {len(moving_averages)} records")
        if moving_averages:
            print(f"First MA record: {moving_averages[0]}")
            print(f"Last MA record: {moving_averages[-1]}")
            
            # Check recent MA records for EMA values
            recent_ma = moving_averages[-5:]
            print(f"\nRecent MA records (last 5):")
            for i, ma in enumerate(recent_ma):
                print(f"  {i+1}. Date: {ma.get('date')}")
                print(f"     EMA7: {ma.get('ema_7')}, EMA30: {ma.get('ema_30')}")
                print(f"     EMA50: {ma.get('ema_50')}, EMA200: {ma.get('ema_200')}")
        
        # Check other fields
        other_fields = ['beauty_score_details', 'cross_signals', 'ath_detections']
        for field in other_fields:
            if field in item:
                value = item[field]
                if isinstance(value, list):
                    print(f"\n{field}: {len(value)} records")
                else:
                    print(f"\n{field}: {value}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_crc_data()