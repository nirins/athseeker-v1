#!/usr/bin/env python3
"""
Debug ATH ordering by beauty score
"""

import boto3
import json
from decimal import Decimal
from boto3.dynamodb.conditions import Key

def decimal_default(obj):
    """Convert Decimal to float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def main():
    # Initialize DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-1')
    table = dynamodb.Table('ts-batch-v2-dev-ath')
    
    print("🔍 Debugging ATH Beauty Score Ordering")
    print("=" * 50)
    
    # Query using beauty_score GSI
    print("\n1. Querying using beauty_score-index GSI (should be ordered by beauty score desc):")
    try:
        response = table.query(
            IndexName='beauty_score-index',
            KeyConditionExpression=Key('market_code').eq('US'),
            ScanIndexForward=False,  # Descending order
            Limit=10
        )
        
        items = response.get('Items', [])
        print(f"Found {len(items)} items from GSI:")
        
        for i, item in enumerate(items):
            symbol = item.get('symbol', 'N/A')
            beauty_score = float(item.get('beauty_score', 0))
            detection_date = item.get('detection_date', 'N/A')
            print(f"  {i+1:2d}. {symbol:<12} Beauty: {beauty_score:6.1f} Date: {detection_date}")
            
    except Exception as e:
        print(f"Error querying GSI: {e}")
    
    # Scan all records and sort manually
    print("\n2. Scanning all records and sorting manually:")
    try:
        response = table.scan(
            FilterExpression=Key('market_code').eq('US')
        )
        
        items = response.get('Items', [])
        print(f"Found {len(items)} total items")
        
        # Sort by beauty_score descending
        sorted_items = sorted(items, key=lambda x: float(x.get('beauty_score', 0)), reverse=True)
        
        print("Top 10 by beauty score (manual sort):")
        for i, item in enumerate(sorted_items[:10]):
            symbol = item.get('symbol', 'N/A')
            beauty_score = float(item.get('beauty_score', 0))
            detection_date = item.get('detection_date', 'N/A')
            print(f"  {i+1:2d}. {symbol:<12} Beauty: {beauty_score:6.1f} Date: {detection_date}")
            
        # Check if AAOI.US is in the data
        print(f"\n3. Looking for AAOI.US specifically:")
        aaoi_items = [item for item in items if item.get('symbol') == 'AAOI.US']
        if aaoi_items:
            for item in aaoi_items:
                beauty_score = float(item.get('beauty_score', 0))
                detection_date = item.get('detection_date', 'N/A')
                print(f"   AAOI.US Beauty: {beauty_score:6.1f} Date: {detection_date}")
        else:
            print("   AAOI.US not found in ATH table")
            
        # Check if ACNFF.US is in the data
        print(f"\n4. Looking for ACNFF.US specifically:")
        acnff_items = [item for item in items if item.get('symbol') == 'ACNFF.US']
        if acnff_items:
            for item in acnff_items:
                beauty_score = float(item.get('beauty_score', 0))
                detection_date = item.get('detection_date', 'N/A')
                print(f"   ACNFF.US Beauty: {beauty_score:6.1f} Date: {detection_date}")
        else:
            print("   ACNFF.US not found in ATH table")
            
    except Exception as e:
        print(f"Error scanning table: {e}")
    
    # Check GSI status
    print(f"\n5. Checking GSI status:")
    try:
        table_desc = table.meta.client.describe_table(TableName='ts-batch-v2-dev-ath')
        gsis = table_desc.get('Table', {}).get('GlobalSecondaryIndexes', [])
        
        for gsi in gsis:
            if gsi['IndexName'] == 'beauty_score-index':
                print(f"   beauty_score-index status: {gsi['IndexStatus']}")
                print(f"   Key schema: {gsi['KeySchema']}")
                break
        else:
            print("   beauty_score-index not found!")
            
    except Exception as e:
        print(f"Error checking GSI: {e}")

if __name__ == "__main__":
    main()