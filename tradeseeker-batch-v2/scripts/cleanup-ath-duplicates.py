#!/usr/bin/env python3
"""
Cleanup script to remove duplicate ATH records and keep only the highest ATH per symbol
"""

import boto3
from decimal import Decimal
from collections import defaultdict

def cleanup_ath_duplicates():
    """Remove duplicate ATH records, keeping only the highest ATH per symbol"""
    
    # Initialize DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-1')
    table = dynamodb.Table('ts-batch-v2-dev-ath')
    
    print("Scanning ATH table for duplicates...")
    
    # Scan all records
    response = table.scan()
    items = response['Items']
    
    # Continue scanning if there are more items
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response['Items'])
    
    print(f"Found {len(items)} total ATH records")
    
    # Group records by symbol
    symbol_records = defaultdict(list)
    for item in items:
        symbol_records[item['symbol']].append(item)
    
    # Find symbols with duplicates
    duplicates_found = 0
    records_to_delete = []
    
    for symbol, records in symbol_records.items():
        if len(records) > 1:
            duplicates_found += 1
            print(f"\nFound {len(records)} records for {symbol}:")
            
            # Find the highest ATH
            highest_record = None
            highest_price = 0
            
            for record in records:
                price = float(record['ath_price'])
                print(f"  - {record['detection_date']}: ${price} (+{record['ath_percentage_gain']}%)")
                
                if price > highest_price:
                    highest_price = price
                    highest_record = record
            
            # Mark lower ATH records for deletion
            for record in records:
                if record != highest_record:
                    records_to_delete.append({
                        'symbol': record['symbol'],
                        'detection_date': record['detection_date'],
                        'price': float(record['ath_price'])
                    })
            
            print(f"  → Keeping: {highest_record['detection_date']} (${highest_price})")
    
    print(f"\nFound {duplicates_found} symbols with duplicates")
    print(f"Will delete {len(records_to_delete)} lower ATH records")
    
    if records_to_delete:
        confirm = input("\nProceed with cleanup? (y/N): ")
        if confirm.lower() == 'y':
            print("\nDeleting duplicate records...")
            
            for record in records_to_delete:
                try:
                    table.delete_item(
                        Key={
                            'symbol': record['symbol'],
                            'detection_date': record['detection_date']
                        }
                    )
                    print(f"✓ Deleted {record['symbol']} - {record['detection_date']} (${record['price']})")
                except Exception as e:
                    print(f"✗ Error deleting {record['symbol']}: {e}")
            
            print(f"\nCleanup complete! Deleted {len(records_to_delete)} duplicate records.")
        else:
            print("Cleanup cancelled.")
    else:
        print("No duplicates found to clean up.")

if __name__ == "__main__":
    cleanup_ath_duplicates()