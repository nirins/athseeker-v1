#!/usr/bin/env python3
"""
Script to query CloudWatch logs for specific symbol processing
"""

import boto3
import json
from datetime import datetime, timedelta

def query_logs_for_symbol(symbol, hours_back=2):
    """
    Query CloudWatch logs for a specific symbol
    
    Args:
        symbol: Symbol to search for (e.g., 'ABBRF.US')
        hours_back: How many hours back to search
    """
    
    # Initialize CloudWatch Logs client
    logs_client = boto3.client('logs', region_name='ap-southeast-1')
    
    # Log group name for the downloader lambda
    log_group = '/aws/lambda/ts-batch-v2-dev-downloader'
    
    # Calculate time range (in milliseconds)
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours_back)
    
    start_time_ms = int(start_time.timestamp() * 1000)
    end_time_ms = int(end_time.timestamp() * 1000)
    
    print(f"Searching CloudWatch logs for '{symbol}' in the last {hours_back} hours...")
    print(f"Log Group: {log_group}")
    print(f"Time Range: {start_time} to {end_time}")
    print("=" * 80)
    
    try:
        # Query logs using filter pattern
        response = logs_client.filter_log_events(
            logGroupName=log_group,
            startTime=start_time_ms,
            endTime=end_time_ms,
            filterPattern=symbol,
            limit=100
        )
        
        events = response.get('events', [])
        
        if not events:
            print(f"No log entries found for '{symbol}' in the specified time range.")
            return
        
        print(f"Found {len(events)} log entries for '{symbol}':")
        print("=" * 80)
        
        for event in events:
            timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
            message = event['message'].strip()
            
            print(f"[{timestamp}] {message}")
            print("-" * 80)
        
        # Look for specific patterns
        print("\n" + "=" * 80)
        print("ANALYSIS:")
        
        ath_logs = [e for e in events if 'ATH detected' in e['message'] or 'beauty score' in e['message'].lower()]
        error_logs = [e for e in events if 'ERROR' in e['message'] or 'Error' in e['message']]
        beauty_logs = [e for e in events if 'beauty' in e['message'].lower() or 'Beauty' in e['message']]
        
        if ath_logs:
            print(f"✅ Found {len(ath_logs)} ATH-related log entries")
        else:
            print("❌ No ATH detection logs found")
        
        if beauty_logs:
            print(f"✅ Found {len(beauty_logs)} beauty score log entries")
        else:
            print("❌ No beauty score logs found")
        
        if error_logs:
            print(f"⚠️  Found {len(error_logs)} error log entries")
            for error in error_logs:
                timestamp = datetime.fromtimestamp(error['timestamp'] / 1000)
                print(f"   [{timestamp}] {error['message'].strip()}")
        else:
            print("✅ No errors found")
            
    except Exception as e:
        print(f"Error querying CloudWatch logs: {str(e)}")

def query_recent_logs(minutes_back=30):
    """Query recent logs for any processing activity"""
    
    logs_client = boto3.client('logs', region_name='ap-southeast-1')
    log_group = '/aws/lambda/ts-batch-v2-dev-downloader'
    
    end_time = datetime.now()
    start_time = end_time - timedelta(minutes=minutes_back)
    
    start_time_ms = int(start_time.timestamp() * 1000)
    end_time_ms = int(end_time.timestamp() * 1000)
    
    print(f"Searching for recent processing activity in the last {minutes_back} minutes...")
    print("=" * 80)
    
    try:
        # Query for processing logs
        response = logs_client.filter_log_events(
            logGroupName=log_group,
            startTime=start_time_ms,
            endTime=end_time_ms,
            filterPattern='Processing',
            limit=50
        )
        
        events = response.get('events', [])
        
        if events:
            print(f"Found {len(events)} recent processing events:")
            for event in events:
                timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                message = event['message'].strip()
                print(f"[{timestamp}] {message}")
        else:
            print("No recent processing activity found.")
            
    except Exception as e:
        print(f"Error querying recent logs: {str(e)}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        symbol = sys.argv[1]
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 2
        query_logs_for_symbol(symbol, hours)
    else:
        print("Usage: python3 query-cloudwatch-logs.py <SYMBOL> [HOURS_BACK]")
        print("Example: python3 query-cloudwatch-logs.py ABBRF.US 2")
        print("\nOr run without arguments to see recent processing activity:")
        query_recent_logs()