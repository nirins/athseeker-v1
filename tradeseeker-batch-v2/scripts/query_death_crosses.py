#!/usr/bin/env python3
"""
Query death crosses from DynamoDB

Usage:
    python3 scripts/query_death_crosses.py --all
    python3 scripts/query_death_crosses.py --date 2024-02-15
    python3 scripts/query_death_crosses.py --market US
    python3 scripts/query_death_crosses.py --days 3
    python3 scripts/query_death_crosses.py --all --json output/death_crosses.json
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


def get_all_death_crosses(table_name: str) -> List[Dict]:
    """
    Scan all death crosses with pagination
    
    Args:
        table_name: DynamoDB table name
        
    Returns:
        List of death cross items
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


def get_death_crosses_by_date(table_name: str, date: str) -> List[Dict]:
    """
    Query death crosses for specific date using GSI
    
    Args:
        table_name: DynamoDB table name
        date: Date in YYYY-MM-DD format
        
    Returns:
        List of death cross items
    """
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-1')
    table = dynamodb.Table(table_name)
    
    response = table.query(
        IndexName='cross_date-index',
        KeyConditionExpression='cross_date = :date',
        ExpressionAttributeValues={':date': date}
    )
    
    return response['Items']


def get_death_crosses_by_market(table_name: str, market_code: str) -> List[Dict]:
    """
    Query death crosses for specific market using GSI
    
    Args:
        table_name: DynamoDB table name
        market_code: Market code (US, BK, CC)
        
    Returns:
        List of death cross items
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


def get_death_crosses_last_n_days(table_name: str, days: int) -> List[Dict]:
    """
    Get death crosses from last N days
    
    Args:
        table_name: DynamoDB table name
        days: Number of days to look back
        
    Returns:
        List of death cross items
    """
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    # Get all and filter (since we can't do range query on GSI without sort key)
    all_items = get_all_death_crosses(table_name)
    
    return [item for item in all_items if item['cross_date'] >= cutoff_date]


def display_death_crosses(items: List[Dict], json_output: str = None):
    """
    Display death crosses in formatted output
    
    Args:
        items: List of death cross items
        json_output: Optional path to save JSON output
    """
    if not items:
        print("No death crosses found")
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
        print(f"✅ Saved {len(items)} death crosses to: {json_output}\n")
    
    # Display summary
    print(f"\n{'='*80}")
    print(f"Found {len(items)} Death Crosses (Bearish)")
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
            
            print(f"  {symbol:<15} Market: {market:<5} EMA50: {ema_50:>10.2f}  EMA200: {ema_200:>10.2f}  Strength: {strength:>8.2f}")
        
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
        print(f"  {market}: {count} death crosses")
    
    print()


def main():
    parser = argparse.ArgumentParser(
        description='Query death crosses from DynamoDB',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get all death crosses (past 360 days)
  python3 scripts/query_death_crosses.py --all
  
  # Get death crosses for specific date
  python3 scripts/query_death_crosses.py --date 2024-02-15
  
  # Get death crosses for specific market
  python3 scripts/query_death_crosses.py --market US
  
  # Get death crosses from last 3 days
  python3 scripts/query_death_crosses.py --days 3
  
  # Save to JSON file
  python3 scripts/query_death_crosses.py --all --json output/death_crosses.json
        """
    )
    
    parser.add_argument('--all', action='store_true', help='Get all death crosses (past 360 days)')
    parser.add_argument('--date', help='Get death crosses for specific date (YYYY-MM-DD)')
    parser.add_argument('--market', help='Get death crosses for specific market (US, BK, CC)')
    parser.add_argument('--days', type=int, help='Get death crosses from last N days')
    parser.add_argument('--json', dest='json_output', help='Save output to JSON file')
    parser.add_argument('--table', default='ts-batch-v2-dev-death-crosses', help='DynamoDB table name')
    parser.add_argument('--env', choices=['dev', 'uat', 'prod'], default='dev', help='Environment (default: dev)')
    
    args = parser.parse_args()
    
    # Construct table name from environment if not explicitly provided
    if args.table == 'ts-batch-v2-dev-death-crosses' and args.env != 'dev':
        args.table = f'ts-batch-v2-{args.env}-death-crosses'
    
    try:
        # Determine which query to run
        if args.date:
            print(f"Querying death crosses for date: {args.date}...")
            items = get_death_crosses_by_date(args.table, args.date)
        elif args.market:
            print(f"Querying death crosses for market: {args.market}...")
            items = get_death_crosses_by_market(args.table, args.market)
        elif args.days:
            print(f"Querying death crosses from last {args.days} days...")
            items = get_death_crosses_last_n_days(args.table, args.days)
        elif args.all:
            print("Querying all death crosses (past 360 days)...")
            items = get_all_death_crosses(args.table)
        else:
            # Default: last 360 days
            print("Querying all death crosses (past 360 days)...")
            items = get_all_death_crosses(args.table)
        
        # Display results
        display_death_crosses(items, args.json_output)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
