#!/usr/bin/env python3
"""
Script to check ATH records in DynamoDB table
"""

import boto3
from decimal import Decimal

def check_ath_records(symbol=None):
    """Check ATH records in the table"""
    
    # Initialize DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-1')
    table = dynamodb.Table('ts-batch-v2-dev-ath')
    
    if symbol:
        print(f"Checking ATH records for {symbol}...")
        # Query specific symbol
        response = table.query(
            KeyConditionExpression='symbol = :symbol',
            ExpressionAttributeValues={':symbol': symbol}
        )
        items = response.get('Items', [])
    else:
        print("Scanning all ATH records...")
        # Scan all records
        response = table.scan()
        items = response['Items']
        
        # Continue scanning if there are more items
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response['Items'])
    
    print(f"Found {len(items)} ATH records")
    print("=" * 80)
    
    for item in items:
        print(f"Symbol: {item['symbol']}")
        print(f"Detection Date: {item['detection_date']}")
        print(f"ATH Price: ${item['ath_price']}")
        print(f"Percentage Gain: {item['ath_percentage_gain']}%")
        print(f"Market Code: {item['market_code']}")
        print(f"Detected At: {item['detected_at']}")
        
        # Check for beauty score fields
        beauty_fields = ['beauty_score', 'grade', 'consolidation_score', 'volume_score', 
                        'momentum_score', 'green_candle_score', 'gap_score']
        
        beauty_found = []
        for field in beauty_fields:
            if field in item:
                beauty_found.append(f"{field}: {item[field]}")
        
        if beauty_found:
            print("Beauty Score Fields:")
            for field in beauty_found:
                print(f"  {field}")
        else:
            print("❌ No beauty score fields found")
        
        print("-" * 80)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        symbol = sys.argv[1]
        check_ath_records(symbol)
    else:
        check_ath_records()