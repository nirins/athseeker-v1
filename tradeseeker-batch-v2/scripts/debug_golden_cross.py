#!/usr/bin/env python3
"""
Debug script to check golden cross detection

Usage:
    python3 scripts/debug_golden_cross.py AAPL.US
"""

import boto3
import sys
from decimal import Decimal
from datetime import datetime, timedelta


def check_symbol(symbol: str):
    """Check a symbol for golden cross detection"""
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-1')
    table = dynamodb.Table('ts-batch-v2-dev-stock-prices')
    
    try:
        response = table.get_item(Key={'symbol': symbol})
        
        if 'Item' not in response:
            print(f"❌ Symbol {symbol} not found in DynamoDB")
            return
        
        item = response['Item']
        
        print(f"\n{'='*80}")
        print(f"Symbol: {symbol}")
        print(f"{'='*80}")
        
        # Basic info
        print(f"\nTotal records: {item.get('total_records', 'N/A')}")
        print(f"Stored records: {item.get('stored_records', 'N/A')}")
        print(f"Oldest date: {item.get('oldest_date', 'N/A')}")
        print(f"Latest date: {item.get('latest_date', 'N/A')}")
        
        # Cross detection results
        print(f"\nGolden Cross: {item.get('golden_cross', 'None')}")
        print(f"Golden Cross Date: {item.get('golden_cross_date', 'None')}")
        print(f"Death Cross Date: {item.get('death_cross_date', 'None')}")
        
        # Check moving averages
        moving_averages = item.get('moving_averages', [])
        
        if not moving_averages:
            print("\n❌ No moving averages found")
            return
        
        print(f"\nMoving averages count: {len(moving_averages)}")
        
        # Check how many have both EMA 50 and 200
        valid_emas = [ma for ma in moving_averages 
                      if ma.get('ema_50') is not None and ma.get('ema_200') is not None]
        
        print(f"Records with both EMA 50 and 200: {len(valid_emas)}")
        
        if len(valid_emas) < 2:
            print("\n❌ Not enough data points with both EMAs to detect crosses")
            return
        
        # Show last 10 days of EMAs
        print(f"\n{'='*80}")
        print("Last 10 days of EMA data:")
        print(f"{'='*80}")
        print(f"{'Date':<12} {'EMA 50':>10} {'EMA 200':>10} {'Diff':>10} {'Status':<15}")
        print("-" * 80)
        
        for ma in moving_averages[-10:]:
            date = ma['date']
            ema_50 = float(ma['ema_50']) if ma.get('ema_50') else None
            ema_200 = float(ma['ema_200']) if ma.get('ema_200') else None
            
            if ema_50 and ema_200:
                diff = ema_50 - ema_200
                status = "50 > 200" if ema_50 > ema_200 else "50 < 200"
                print(f"{date:<12} {ema_50:>10.2f} {ema_200:>10.2f} {diff:>10.2f} {status:<15}")
            else:
                print(f"{date:<12} {'N/A':>10} {'N/A':>10} {'N/A':>10} {'Insufficient data':<15}")
        
        # Manually check for crosses in last 30 days
        print(f"\n{'='*80}")
        print("Checking for crosses in last 30 days:")
        print(f"{'='*80}")
        
        cutoff_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        recent_mas = [ma for ma in moving_averages if ma['date'] >= cutoff_date]
        
        print(f"Records in last 30 days: {len(recent_mas)}")
        
        crosses_found = []
        
        for i in range(1, len(recent_mas)):
            today = recent_mas[i]
            yesterday = recent_mas[i-1]
            
            if (today.get('ema_50') is None or today.get('ema_200') is None or
                yesterday.get('ema_50') is None or yesterday.get('ema_200') is None):
                continue
            
            today_50 = float(today['ema_50'])
            today_200 = float(today['ema_200'])
            yesterday_50 = float(yesterday['ema_50'])
            yesterday_200 = float(yesterday['ema_200'])
            
            # Golden Cross
            if today_50 > today_200 and yesterday_50 <= yesterday_200:
                crosses_found.append({
                    'type': 'GOLDEN_CROSS',
                    'date': today['date'],
                    'ema_50': today_50,
                    'ema_200': today_200
                })
            
            # Death Cross
            elif today_50 < today_200 and yesterday_50 >= yesterday_200:
                crosses_found.append({
                    'type': 'DEATH_CROSS',
                    'date': today['date'],
                    'ema_50': today_50,
                    'ema_200': today_200
                })
        
        if crosses_found:
            print(f"\n✅ Found {len(crosses_found)} cross(es):")
            for cross in crosses_found:
                print(f"  {cross['type']} on {cross['date']}")
                print(f"    EMA 50: {cross['ema_50']:.2f}, EMA 200: {cross['ema_200']:.2f}")
        else:
            print("\n❌ No crosses found in last 30 days")
            print("\nThis could mean:")
            print("  - The trend has been consistent (no crossovers)")
            print("  - The last cross was more than 30 days ago")
            print("  - Try checking the full 10-year data in the main table")
        
        print()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/debug_golden_cross.py SYMBOL")
        print("Example: python3 scripts/debug_golden_cross.py AAPL.US")
        sys.exit(1)
    
    symbol = sys.argv[1]
    check_symbol(symbol)
