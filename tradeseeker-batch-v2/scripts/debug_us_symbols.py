#!/usr/bin/env python3
"""
Debug script to analyze US symbols from EODHD API
"""

import json
import boto3
import requests
from collections import Counter
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

def get_api_token(environment='dev'):
    """Get API token from AWS Secrets Manager"""
    try:
        secretsmanager = boto3.client('secretsmanager')
        secret_name = f"ts-batch-v2-{environment}-eodhd-api-token"
        
        response = secretsmanager.get_secret_value(SecretId=secret_name)
        secret = json.loads(response['SecretString'])
        return secret['api_token']
    except Exception as e:
        print(f"Error getting API token: {e}")
        return None

def get_api_endpoints(environment='dev'):
    """Get API endpoints from SSM"""
    try:
        ssm = boto3.client('ssm')
        parameter_name = f"/ts-batch-v2/{environment}/api-endpoints"
        
        response = ssm.get_parameter(Name=parameter_name)
        endpoints = json.loads(response['Parameter']['Value'])
        return endpoints
    except Exception as e:
        print(f"Error getting API endpoints: {e}")
        return None

def analyze_us_symbols():
    """Analyze US symbols from EODHD API"""
    
    # Get configuration
    api_token = get_api_token()
    endpoints = get_api_endpoints()
    
    if not api_token or not endpoints:
        print("Failed to get API configuration")
        return
    
    # Build URL
    url = endpoints['symbolListUrl'].replace('{MARKET_CODE}', 'US')
    url += f'?api_token={api_token}&fmt=json'
    
    print(f"Fetching from: {url.replace(api_token, '***')}")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        all_symbols = response.json()
        print(f"\nTotal symbols fetched: {len(all_symbols)}")
        
        # Analyze symbol types
        type_counter = Counter()
        exchange_counter = Counter()
        sample_by_type = {}
        
        for symbol in all_symbols:
            symbol_type = symbol.get('Type', 'Unknown')
            exchange = symbol.get('Exchange', 'Unknown')
            
            type_counter[symbol_type] += 1
            exchange_counter[exchange] += 1
            
            # Keep samples of each type
            if symbol_type not in sample_by_type:
                sample_by_type[symbol_type] = []
            if len(sample_by_type[symbol_type]) < 5:
                sample_by_type[symbol_type].append({
                    'Code': symbol.get('Code', 'N/A'),
                    'Name': symbol.get('Name', 'N/A'),
                    'Type': symbol.get('Type', 'N/A'),
                    'Exchange': symbol.get('Exchange', 'N/A')
                })
        
        # Print analysis
        print(f"\n=== SYMBOL TYPES ===")
        for symbol_type, count in type_counter.most_common():
            print(f"{symbol_type}: {count}")
        
        print(f"\n=== EXCHANGES ===")
        for exchange, count in exchange_counter.most_common():
            print(f"{exchange}: {count}")
        
        print(f"\n=== SAMPLES BY TYPE ===")
        for symbol_type, samples in sample_by_type.items():
            print(f"\n{symbol_type} ({type_counter[symbol_type]} total):")
            for sample in samples:
                print(f"  {sample['Code']} - {sample['Name']} ({sample['Exchange']})")
        
        # Test current filtering logic
        print(f"\n=== TESTING CURRENT FILTER ===")
        
        filtered_symbols = []
        filter_stats = {
            'total': len(all_symbols),
            'wrong_type': 0,
            'special_chars': 0,
            'too_long': 0,
            'derivative_suffix': 0,
            'excluded_keywords': 0,
            'has_numbers': 0,
            'wrong_exchange': 0,
            'passed_all': 0
        }
        
        for symbol in all_symbols:
            code = symbol.get('Code', '')
            name = symbol.get('Name', '')
            symbol_type = symbol.get('Type', '')
            exchange = symbol.get('Exchange', '')
            
            # Primary filter: Must be Common Stock type
            if symbol_type != 'Common Stock':
                filter_stats['wrong_type'] += 1
                continue
            
            # Filter out symbols with special characters (warrants, rights, etc.)
            if any(char in code for char in ['.', '-', '/', '^', '~', '+']):
                filter_stats['special_chars'] += 1
                continue
            
            # Filter out symbols longer than 5 characters (usually derivatives)
            if len(code) > 5:
                filter_stats['too_long'] += 1
                continue
            
            # Filter out symbols ending with common suffixes for derivatives
            derivative_suffixes = ['W', 'WS', 'WT', 'WD', 'R', 'RT', 'U', 'V', 'P', 'PR']
            if any(code.endswith(suffix) for suffix in derivative_suffixes):
                filter_stats['derivative_suffix'] += 1
                continue
            
            # Filter out symbols that are clearly ETFs, REITs, or funds by name
            name_lower = name.lower()
            excluded_keywords = [
                'etf', 'fund', 'trust', 'reit', 'index', 'spdr', 'ishares', 
                'vanguard', 'invesco', 'proshares', 'direxion', 'leveraged',
                'inverse', '2x', '3x', 'ultra', 'bear', 'bull', 'volatility'
            ]
            
            if any(keyword in name_lower for keyword in excluded_keywords):
                filter_stats['excluded_keywords'] += 1
                continue
            
            # Filter out symbols with numbers (often special classes or derivatives)
            if any(char.isdigit() for char in code):
                filter_stats['has_numbers'] += 1
                continue
            
            # Only include symbols from major exchanges
            major_exchanges = ['NASDAQ', 'NYSE', 'AMEX', 'NYSE MKT', 'NYSE American']
            if exchange not in major_exchanges:
                filter_stats['wrong_exchange'] += 1
                continue
            
            # If it passes all filters, it's likely a common stock
            filter_stats['passed_all'] += 1
            filtered_symbols.append(symbol)
        
        print(f"Filter results:")
        for key, value in filter_stats.items():
            percentage = (value / filter_stats['total']) * 100 if filter_stats['total'] > 0 else 0
            print(f"  {key}: {value} ({percentage:.1f}%)")
        
        print(f"\nFinal filtered count: {len(filtered_symbols)}")
        
        # Show some examples of what passed
        print(f"\nSample symbols that passed all filters:")
        for i, symbol in enumerate(filtered_symbols[:10]):
            print(f"  {symbol['Code']} - {symbol['Name']} ({symbol['Exchange']})")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze_us_symbols()