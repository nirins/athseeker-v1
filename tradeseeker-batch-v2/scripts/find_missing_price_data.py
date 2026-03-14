#!/usr/bin/env python3
"""
Find stocks with missing price data but existing moving averages
"""

import boto3
from boto3.dynamodb.conditions import Attr

def find_missing_price_data():
    """Find stocks with moving averages but no price data"""
    try:
        dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-1')
        table = dynamodb.Table('ts-batch-v2-dev-stock-prices')
        
        print("Scanning for stocks with missing price data...")
        
        # Scan the table for items with moving averages but no price data
        response = table.scan(
            FilterExpression=Attr('moving_averages').exists() & Attr('price_data').size().eq(0),
            ProjectionExpression='symbol, market_code, moving_averages, price_data, latest_date',
            Limit=10  # Limit to first 10 items for testing
        )
        
        items = response['Items']
        
        print(f"\nFound {len(items)} stocks with missing price data:")
        
        for item in items:
            symbol = item.get('symbol', 'N/A')
            market = item.get('market_code', 'N/A')
            ma_count = len(item.get('moving_averages', []))
            price_count = len(item.get('price_data', []))
            latest_date = item.get('latest_date', 'N/A')
            
            print(f"  {symbol} ({market}): {ma_count} MAs, {price_count} prices, latest: {latest_date}")
        
        # Continue scanning if there are more items
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                FilterExpression=Attr('moving_averages').exists() & Attr('price_data').size().eq(0),
                ProjectionExpression='symbol, market_code, moving_averages, price_data, latest_date',
                ExclusiveStartKey=response['LastEvaluatedKey'],
                Limit=10
            )
            
            batch_items = response['Items']
            items.extend(batch_items)
            
            print(f"Found {len(batch_items)} more items (total: {len(items)})")
            
            for item in batch_items:
                symbol = item.get('symbol', 'N/A')
                market = item.get('market_code', 'N/A')
                ma_count = len(item.get('moving_averages', []))
                price_count = len(item.get('price_data', []))
                latest_date = item.get('latest_date', 'N/A')
                
                print(f"  {symbol} ({market}): {ma_count} MAs, {price_count} prices, latest: {latest_date}")
        
        print(f"\nTotal stocks with missing price data: {len(items)}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    find_missing_price_data()