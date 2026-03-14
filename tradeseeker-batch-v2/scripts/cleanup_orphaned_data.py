#!/usr/bin/env python3
"""
Clean up orphaned moving averages data (records with MAs but no price data)
"""

import boto3
from boto3.dynamodb.conditions import Attr
import json

def cleanup_orphaned_data(dry_run=True):
    """
    Clean up records that have moving averages but no price data
    
    Args:
        dry_run: If True, only report what would be deleted without actually deleting
    """
    try:
        dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-1')
        table = dynamodb.Table('ts-batch-v2-dev-stock-prices')
        
        print("Scanning for orphaned records (moving averages but no price data)...")
        
        orphaned_records = []
        
        # Scan the table for items with moving averages but no price data
        response = table.scan(
            FilterExpression=Attr('moving_averages').exists() & (
                Attr('price_data').not_exists() | Attr('price_data').size().eq(0)
            ),
            ProjectionExpression='symbol, market_code, moving_averages, price_data, latest_date'
        )
        
        orphaned_records.extend(response['Items'])
        
        # Continue scanning if there are more items
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                FilterExpression=Attr('moving_averages').exists() & (
                    Attr('price_data').not_exists() | Attr('price_data').size().eq(0)
                ),
                ProjectionExpression='symbol, market_code, moving_averages, price_data, latest_date',
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            
            orphaned_records.extend(response['Items'])
        
        print(f"\nFound {len(orphaned_records)} orphaned records:")
        
        for record in orphaned_records:
            symbol = record.get('symbol', 'N/A')
            market = record.get('market_code', 'N/A')
            ma_count = len(record.get('moving_averages', []))
            price_count = len(record.get('price_data', []))
            latest_date = record.get('latest_date', 'N/A')
            
            print(f"  {symbol} ({market}): {ma_count} MAs, {price_count} prices, latest: {latest_date}")
        
        if not orphaned_records:
            print("No orphaned records found!")
            return
        
        if dry_run:
            print(f"\n🔍 DRY RUN: Would delete {len(orphaned_records)} orphaned records")
            print("Run with dry_run=False to actually delete these records")
        else:
            print(f"\n🗑️  DELETING {len(orphaned_records)} orphaned records...")
            
            deleted_count = 0
            for record in orphaned_records:
                try:
                    # Delete the record
                    table.delete_item(Key={'symbol': record['symbol']})
                    deleted_count += 1
                    
                    if deleted_count % 10 == 0:
                        print(f"  Deleted {deleted_count}/{len(orphaned_records)} records...")
                        
                except Exception as e:
                    print(f"  ❌ Error deleting {record['symbol']}: {e}")
            
            print(f"✅ Successfully deleted {deleted_count} orphaned records")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def get_affected_ath_stocks():
    """Get list of ATH stocks that might be affected by missing price data"""
    try:
        dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-1')
        ath_table = dynamodb.Table('ts-batch-v2-dev-ath-detections')
        
        print("Checking ATH stocks for zero beauty scores...")
        
        # Scan ATH table for US market stocks with zero beauty scores
        response = ath_table.scan(
            FilterExpression=Attr('market_code').eq('US') & Attr('beauty_score').eq(0),
            ProjectionExpression='symbol, beauty_score, detection_date, ath_price'
        )
        
        zero_beauty_stocks = response['Items']
        
        # Continue scanning if there are more items
        while 'LastEvaluatedKey' in response:
            response = ath_table.scan(
                FilterExpression=Attr('market_code').eq('US') & Attr('beauty_score').eq(0),
                ProjectionExpression='symbol, beauty_score, detection_date, ath_price',
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            
            zero_beauty_stocks.extend(response['Items'])
        
        print(f"\nFound {len(zero_beauty_stocks)} ATH stocks with zero beauty scores:")
        
        for stock in zero_beauty_stocks[:10]:  # Show first 10
            symbol = stock.get('symbol', 'N/A')
            detection_date = stock.get('detection_date', 'N/A')
            ath_price = stock.get('ath_price', 'N/A')
            
            print(f"  {symbol}: ATH ${ath_price} on {detection_date}")
        
        if len(zero_beauty_stocks) > 10:
            print(f"  ... and {len(zero_beauty_stocks) - 10} more")
        
        return [stock['symbol'] for stock in zero_beauty_stocks]
        
    except Exception as e:
        print(f"Error checking ATH stocks: {e}")
        return []

if __name__ == "__main__":
    import sys
    
    # Check command line arguments
    dry_run = True
    if len(sys.argv) > 1 and sys.argv[1] == "--delete":
        dry_run = False
        print("⚠️  DELETION MODE ENABLED - Will actually delete orphaned records!")
    else:
        print("🔍 DRY RUN MODE - Use --delete flag to actually delete records")
    
    print("\n" + "="*60)
    print("STEP 1: Find orphaned records")
    print("="*60)
    cleanup_orphaned_data(dry_run=dry_run)
    
    print("\n" + "="*60)
    print("STEP 2: Check affected ATH stocks")
    print("="*60)
    affected_stocks = get_affected_ath_stocks()
    
    if affected_stocks:
        print(f"\n📋 Summary: {len(affected_stocks)} ATH stocks may need re-processing")
        print("These stocks should be re-run through the downloader after cleanup")