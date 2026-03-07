#!/usr/bin/env python3
"""
Query stock data from DynamoDB table

Usage:
    python scripts/query_stock.py AAPL.US
    python scripts/query_stock.py AAPL.US --latest 10
    python scripts/query_stock.py AAPL.US --date 2024-01-15
    python scripts/query_stock.py --list
"""

import boto3
import json
import sys
import argparse
from decimal import Decimal
from typing import Optional


def decimal_default(obj):
    """Convert Decimal to float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


def query_symbol(table_name: str, symbol: str, latest: int = 5, date: Optional[str] = None, json_output: Optional[str] = None):
    """
    Query stock data for a specific symbol
    
    Args:
        table_name: DynamoDB table name
        symbol: Stock symbol (e.g., AAPL.US)
        latest: Number of latest records to show
        date: Specific date to filter (YYYY-MM-DD)
        json_output: Path to save JSON output file
    """
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-1')
    table = dynamodb.Table(table_name)
    
    try:
        response = table.get_item(Key={'symbol': symbol})
        
        if 'Item' not in response:
            print(f"❌ Symbol '{symbol}' not found in table")
            return
        
        item = response['Item']
        
        # Save to JSON file if requested
        if json_output is not None:
            # If json_output is empty string, auto-generate filename
            if not json_output:
                json_output = f"output/{symbol.replace('.', '_')}.json"
            
            # Ensure output directory exists
            import os
            output_dir = os.path.dirname(json_output)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            with open(json_output, 'w') as f:
                json.dump(item, f, indent=2, default=decimal_default)
            print(f"✅ Saved full data to: {json_output}\n")
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"Symbol: {item['symbol']}")
        print(f"Market: {item['market_code']}")
        print(f"Updated: {item['updated_at']}")
        print(f"Total records: {len(item['prices'])}")
        print(f"{'='*60}\n")
        
        prices = item['prices']
        moving_averages = item['moving_averages']
        
        # Filter by date if specified
        if date:
            prices = [p for p in prices if p['date'] == date]
            moving_averages = [ma for ma in moving_averages if ma['date'] == date]
            
            if not prices:
                print(f"❌ No data found for date {date}")
                return
            
            print(f"Data for date: {date}\n")
        else:
            # Show latest N records
            prices = prices[-latest:]
            moving_averages = moving_averages[-latest:]
            print(f"Latest {latest} records:\n")
        
        # Print prices
        print("📊 OHLCV Data:")
        print("-" * 60)
        for p in prices:
            print(f"Date: {p['date']}")
            print(f"  Open:      {float(p['open']):>12.4f}")
            print(f"  High:      {float(p['high']):>12.4f}")
            print(f"  Low:       {float(p['low']):>12.4f}")
            print(f"  Close:     {float(p['close']):>12.4f}")
            print(f"  Adj Close: {float(p['adjusted_close']):>12.4f}")
            print(f"  Volume:    {p['volume']:>12,}")
            print()
        
        # Print moving averages
        print("\n📈 Exponential Moving Averages:")
        print("-" * 60)
        for ma in moving_averages:
            print(f"Date: {ma['date']}")
            
            ema_7 = float(ma['ema_7']) if ma['ema_7'] is not None else None
            ema_30 = float(ma['ema_30']) if ma['ema_30'] is not None else None
            ema_50 = float(ma['ema_50']) if ma['ema_50'] is not None else None
            ema_200 = float(ma['ema_200']) if ma['ema_200'] is not None else None
            
            print(f"  EMA 7:     {ema_7:>12.4f}" if ema_7 else "  EMA 7:     Not available")
            print(f"  EMA 30:    {ema_30:>12.4f}" if ema_30 else "  EMA 30:    Not available")
            print(f"  EMA 50:    {ema_50:>12.4f}" if ema_50 else "  EMA 50:    Not available")
            print(f"  EMA 200:   {ema_200:>12.4f}" if ema_200 else "  EMA 200:   Not available")
            print()
        
        # Print JSON option
        print("\n💾 To export as JSON:")
        print(f"aws dynamodb get-item --table-name {table_name} --key '{{\"symbol\":{{\"S\":\"{symbol}\"}}}}' --region ap-southeast-1 > {symbol.replace('.', '_')}.json")
        
    except Exception as e:
        print(f"❌ Error querying DynamoDB: {str(e)}")
        sys.exit(1)


def list_symbols(table_name: str, limit: int = 20, json_output: Optional[str] = None):
    """
    List all symbols in the table
    
    Args:
        table_name: DynamoDB table name
        limit: Maximum number of symbols to show
        json_output: Path to save JSON output file
    """
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-1')
    table = dynamodb.Table(table_name)
    
    try:
        print(f"\n📋 Symbols in table (showing first {limit}):\n")
        print(f"{'Symbol':<20} {'Market':<10} {'Records':<10} {'Updated'}")
        print("-" * 70)
        
        response = table.scan(
            ProjectionExpression='symbol, market_code, updated_at, prices',
            Limit=limit
        )
        
        symbols_list = []
        
        for item in response['Items']:
            symbol = item['symbol']
            market = item['market_code']
            record_count = len(item['prices'])
            updated = item['updated_at'][:19]  # Trim milliseconds
            
            symbols_list.append({
                'symbol': symbol,
                'market_code': market,
                'record_count': record_count,
                'updated_at': updated
            })
            
            print(f"{symbol:<20} {market:<10} {record_count:<10} {updated}")
        
        # Save to JSON file if requested
        if json_output:
            with open(json_output, 'w') as f:
                json.dump(symbols_list, f, indent=2, default=decimal_default)
            print(f"\n✅ Saved list to: {json_output}")
        
        # Get total count
        count_response = table.scan(Select='COUNT')
        total = count_response['Count']
        
        print("-" * 70)
        print(f"Total symbols in table: {total}")
        
        if total > limit:
            print(f"\n💡 Showing first {limit} of {total} symbols")
            print(f"   Use --limit to show more")
        
    except Exception as e:
        print(f"❌ Error scanning DynamoDB: {str(e)}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Query stock data from DynamoDB',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Query specific symbol (show latest 5 records)
  python scripts/query_stock.py AAPL.US
  
  # Show latest 10 records
  python scripts/query_stock.py AAPL.US --latest 10
  
  # Show data for specific date
  python scripts/query_stock.py AAPL.US --date 2024-01-15
  
  # Save to JSON file (auto-generates output/AAPL_US.json)
  python scripts/query_stock.py AAPL.US --json
  
  # Save to custom path
  python scripts/query_stock.py AAPL.US --json custom/path.json
  
  # List all symbols in table
  python scripts/query_stock.py --list
  
  # List and save to JSON
  python scripts/query_stock.py --list --limit 50 --json output/symbols.json
        """
    )
    
    parser.add_argument('symbol', nargs='?', help='Stock symbol (e.g., AAPL.US)')
    parser.add_argument('--latest', type=int, default=5, help='Number of latest records to show (default: 5)')
    parser.add_argument('--date', help='Specific date to query (YYYY-MM-DD)')
    parser.add_argument('--list', action='store_true', help='List all symbols in table')
    parser.add_argument('--limit', type=int, default=20, help='Limit for list command (default: 20)')
    parser.add_argument('--table', default='ts-batch-v2-dev-stock-prices', help='DynamoDB table name')
    parser.add_argument('--env', choices=['dev', 'uat', 'prod'], default='dev', help='Environment (default: dev)')
    parser.add_argument('--json', dest='json_output', nargs='?', const='', help='Save output to JSON file (auto-generates filename in output/ if no path provided)')
    
    args = parser.parse_args()
    
    # Construct table name from environment if not explicitly provided
    if args.table == 'ts-batch-v2-dev-stock-prices' and args.env != 'dev':
        args.table = f'ts-batch-v2-{args.env}-stock-prices'
    
    if args.list:
        list_symbols(args.table, args.limit, args.json_output)
    elif args.symbol:
        query_symbol(args.table, args.symbol, args.latest, args.date, args.json_output)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
