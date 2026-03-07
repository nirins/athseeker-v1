#!/usr/bin/env python3
"""
Query golden crosses from DynamoDB

Usage:
    python scripts/query_golden_crosses.py --all
    python scripts/query_golden_crosses.py --date 2024-02-15
    python scripts/query_golden_crosses.py --market US
    python scripts/query_golden_crosses.py --days 3
    python scripts/query_golden_crosses.py --all --json output/golden_crosses.json
"""

import boto3
import json
import sys
import argparse
from decimal import Decimal
from datetime import datetime, timedelta
from typing import List, Dict


def decimal_default(obj):
    """Convert Decimal to float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


def get_all_golden_crosses(table_name: str) -> List[Dict]:
    """
    Scan all golden crosses with pagination
    
    Args:
        table_name: DynamoDB table name
        
    Returns:
        List of golden cross items
    """
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-1')
    table = dynamodb.Table(table_name)
    
    items = []
    response = table.scan()
    items.extend(response['Items'])
    
    # Handle pagination
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response['Items'])
    
    return items


def get_golden_crosses_by_date(table_name: str, date: str) -> List[Dict]:
    """
    Query golden crosses for specific date using GSI
    
    Args:
        table_name: DynamoDB table name
        date: Date in YYYY-MM-DD format
        
    Returns:
        List of golden cross items
    """
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-1')
    table = dynamodb.Table(table_name)
    
    response = table.query(
        IndexName='cross_date-index',
        KeyConditionExpression='cross_date = :date',
        ExpressionAttributeValues={':date': date}
    )
    
    return response['Items']


def get_golden_crosses_by_market(table_name: str, market_code: str) -> List[Dict]:
    """
    Query golden crosses for specific market using GSI
    
    Args:
        table_name: DynamoDB table name
        market_code: Market code (US, BK, CC)
        
    Returns:
        List of golden cross items
    """
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-1')
    table = dynamodb.Table(table_name)
    
    items = []
    response = table.query(
        IndexName='market_code-cross_date-index',
        KeyConditionExpression='market_code = :market',
        ExpressionAttributeValues={':market': market_code}
    )
    items.extend(response['Items'])
    
    # Handle pagination
    while 'LastEvaluatedKey' in response:
        response = table.query(
            IndexName='market_code-cross_date-index',
            KeyConditionExpression='market_code = :market',
            ExpressionAttributeValues={':market': market_code},
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        items.extend(response['Items'])
    
    return items


def get_golden_crosses_last_n_days(table_name: str, days: int) -> List[Dict]:
    """
    Get golden crosses from last N days
    
    Args:
        table_name: DynamoDB table name
        days: Number of days to look back
        
    Returns:
        List of golden cross items
    """
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    # Get all and filter (since we can't do range query on GSI without sort key)
    all_items = get_all_golden_crosses(table_name)
    
    return [item for item in all_items if item['cross_date'] >= cutoff_date]


def display_golden_crosses(items: List[Dict], json_output: str = None, min_green_pct: float = None, max_red_candle_pct: float = None):
    """
    Display golden crosses in formatted output
    
    Args:
        items: List of golden cross items
        json_output: Optional path to save JSON output
        min_green_pct: Minimum green days percentage (e.g., 70.0)
        max_red_candle_pct: Maximum red candle percentage (e.g., -3.0)
    """
    if not items:
        print("No golden crosses found")
        return
    
    # Apply filters if specified
    if min_green_pct is not None or max_red_candle_pct is not None:
        original_count = len(items)
        filtered_items = []
        
        for item in items:
            # Check if metrics exist
            if 'green_days_30d_pct' not in item or 'max_red_candle_30d_pct' not in item:
                continue
            
            green_pct = float(item['green_days_30d_pct'])
            red_candle_pct = float(item['max_red_candle_30d_pct'])
            
            # Apply filters
            passes_green = min_green_pct is None or green_pct >= min_green_pct
            passes_red = max_red_candle_pct is None or red_candle_pct >= max_red_candle_pct
            
            if passes_green and passes_red:
                filtered_items.append(item)
        
        items = filtered_items
        print(f"\nFiltered: {len(items)} / {original_count} symbols")
        if min_green_pct:
            print(f"  - Green days >= {min_green_pct}%")
        if max_red_candle_pct:
            print(f"  - Max red candle >= {max_red_candle_pct}% (no big loss)")
    
    if not items:
        print("No golden crosses match the filter criteria")
        return
    
    # Sort by date (newest first)
    items = sorted(items, key=lambda x: x['cross_date'], reverse=True)
    
    # Save to JSON if requested
    if json_output:
        import os
        output_dir = os.path.dirname(json_output)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        with open(json_output, 'w') as f:
            json.dump(items, f, indent=2, default=decimal_default)
        print(f"✅ Saved {len(items)} golden crosses to: {json_output}\n")
    
    # Display summary
    print(f"\n{'='*80}")
    print(f"Found {len(items)} Golden Crosses")
    print(f"{'='*80}\n")
    
    # Group by date
    by_date = {}
    for item in items:
        date = item['cross_date']
        if date not in by_date:
            by_date[date] = []
        by_date[date].append(item)
    
    # Display by date
    for date in sorted(by_date.keys(), reverse=True):
        crosses = by_date[date]
        print(f"📅 {date} ({len(crosses)} symbols)")
        print("-" * 80)
        
        for item in crosses:
            symbol = item['symbol']
            market = item['market_code']
            ema_50 = float(item['ema_50'])
            ema_200 = float(item['ema_200'])
            strength = float(item['crossover_strength'])
            
            # Display candle metrics if available
            metrics_str = ""
            if 'green_days_30d_pct' in item and 'max_red_candle_30d_pct' in item:
                green_pct = float(item['green_days_30d_pct'])
                red_pct = float(item['max_red_candle_30d_pct'])
                metrics_str = f"  Green: {green_pct:>5.1f}%  MaxRed: {red_pct:>6.2f}%"
            
            print(f"  {symbol:<15} Market: {market:<5} EMA50: {ema_50:>10.2f}  EMA200: {ema_200:>10.2f}  Strength: {strength:>8.2f}{metrics_str}")
        
        print()
    
    # Summary by market
    print(f"\n{'='*80}")
    print("Summary by Market")
    print(f"{'='*80}")
    
    by_market = {}
    for item in items:
        market = item['market_code']
        by_market[market] = by_market.get(market, 0) + 1
    
    for market, count in sorted(by_market.items()):
        print(f"  {market}: {count} golden crosses")
    
    print()


def main():
    parser = argparse.ArgumentParser(
        description='Query golden crosses from DynamoDB',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get all golden crosses (past 30 days)
  python3 scripts/query_golden_crosses.py --all
  
  # Get golden crosses for specific date
  python scripts/query_golden_crosses.py --date 2024-02-15
  
  # Get golden crosses for specific market
  python scripts/query_golden_crosses.py --market US
  
  # Get golden crosses from last 3 days
  python scripts/query_golden_crosses.py --days 3
  
  # Save to JSON file
  python3 scripts/query_golden_crosses.py --all --json output/golden_crosses.json
  
  # Filter: >= 70% green days, no red candle > 3%
  python3 scripts/query_golden_crosses.py --all --min-green 70 --max-red-candle -3
        """
    )
    
    parser.add_argument('--all', action='store_true', help='Get all golden crosses (past 30 days)')
    parser.add_argument('--date', help='Get golden crosses for specific date (YYYY-MM-DD)')
    parser.add_argument('--market', help='Get golden crosses for specific market (US, BK, CC)')
    parser.add_argument('--days', type=int, help='Get golden crosses from last N days')
    parser.add_argument('--json', dest='json_output', help='Save output to JSON file')
    parser.add_argument('--table', default='ts-batch-v2-dev-golden-crosses', help='DynamoDB table name')
    parser.add_argument('--env', choices=['dev', 'uat', 'prod'], default='dev', help='Environment (default: dev)')
    parser.add_argument('--min-green', type=float, help='Minimum green days percentage (e.g., 70.0)')
    parser.add_argument('--max-red-candle', type=float, help='Maximum red candle percentage (e.g., -3.0 means no loss bigger than 3%%)')
    
    args = parser.parse_args()
    
    # Construct table name from environment if not explicitly provided
    if args.table == 'ts-batch-v2-dev-golden-crosses' and args.env != 'dev':
        args.table = f'ts-batch-v2-{args.env}-golden-crosses'
    
    try:
        # Determine which query to run
        if args.date:
            print(f"Querying golden crosses for date: {args.date}...")
            items = get_golden_crosses_by_date(args.table, args.date)
        elif args.market:
            print(f"Querying golden crosses for market: {args.market}...")
            items = get_golden_crosses_by_market(args.table, args.market)
        elif args.days:
            print(f"Querying golden crosses from last {args.days} days...")
            items = get_golden_crosses_last_n_days(args.table, args.days)
        elif args.all:
            print("Querying all golden crosses (past 30 days)...")
            items = get_all_golden_crosses(args.table)
        else:
            # Default: last 30 days
            print("Querying all golden crosses (past 30 days)...")
            items = get_all_golden_crosses(args.table)
        
        # Display results
        display_golden_crosses(items, args.json_output, args.min_green, args.max_red_candle)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
