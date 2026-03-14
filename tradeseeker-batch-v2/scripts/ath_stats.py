#!/usr/bin/env python3
"""
Get ATH statistics for US market
"""

import boto3
from collections import Counter
from decimal import Decimal

def get_ath_stats():
    """Get ATH statistics for US market"""
    try:
        dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-1')
        table = dynamodb.Table('ts-batch-v2-dev-ath')
        
        print("=== US Market ATH Statistics ===\n")
        
        # Scan for US market ATH stocks
        response = table.scan(
            FilterExpression='market_code = :market',
            ExpressionAttributeValues={':market': 'US'}
        )
        
        items = response['Items']
        
        # Continue scanning if there are more items
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                FilterExpression='market_code = :market',
                ExpressionAttributeValues={':market': 'US'},
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            items.extend(response['Items'])
        
        print(f"Total ATH stocks in US market: {len(items)}")
        
        # Beauty score statistics
        beauty_scores = []
        zero_beauty_scores = 0
        
        for item in items:
            beauty_score = float(item.get('beauty_score', 0))
            beauty_scores.append(beauty_score)
            if beauty_score == 0:
                zero_beauty_scores += 1
        
        if beauty_scores:
            avg_beauty = sum(beauty_scores) / len(beauty_scores)
            max_beauty = max(beauty_scores)
            min_beauty = min(beauty_scores)
            
            print(f"\nBeauty Score Statistics:")
            print(f"  Average: {avg_beauty:.1f}")
            print(f"  Maximum: {max_beauty:.1f}")
            print(f"  Minimum: {min_beauty:.1f}")
            print(f"  Zero scores: {zero_beauty_scores} ({zero_beauty_scores/len(items)*100:.1f}%)")
        
        # Beauty score distribution
        score_ranges = {
            'A (80-100)': 0,
            'B (70-79)': 0,
            'C (60-69)': 0,
            'D (50-59)': 0,
            'F (0-49)': 0
        }
        
        for score in beauty_scores:
            if score >= 80:
                score_ranges['A (80-100)'] += 1
            elif score >= 70:
                score_ranges['B (70-79)'] += 1
            elif score >= 60:
                score_ranges['C (60-69)'] += 1
            elif score >= 50:
                score_ranges['D (50-59)'] += 1
            else:
                score_ranges['F (0-49)'] += 1
        
        print(f"\nBeauty Score Distribution:")
        for grade, count in score_ranges.items():
            percentage = (count / len(items)) * 100 if items else 0
            print(f"  {grade}: {count} stocks ({percentage:.1f}%)")
        
        # Recent ATH detections (last 7 days)
        from datetime import datetime, timedelta
        recent_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        recent_aths = [item for item in items if item.get('detection_date', '') >= recent_date]
        print(f"\nRecent ATH detections (last 7 days): {len(recent_aths)}")
        
        # Top 10 by beauty score
        sorted_by_beauty = sorted(items, key=lambda x: float(x.get('beauty_score', 0)), reverse=True)
        print(f"\nTop 10 ATH stocks by beauty score:")
        for i, item in enumerate(sorted_by_beauty[:10]):
            symbol = item.get('symbol', 'N/A')
            beauty = float(item.get('beauty_score', 0))
            ath_gain = float(item.get('ath_percentage_gain', 0))
            detection_date = item.get('detection_date', 'N/A')
            print(f"  {i+1:2d}. {symbol:12s} - Beauty: {beauty:5.1f}, Gain: {ath_gain:7.1f}%, Date: {detection_date}")
        
        # Stocks with zero beauty scores
        if zero_beauty_scores > 0:
            zero_beauty_stocks = [item for item in items if float(item.get('beauty_score', 0)) == 0]
            print(f"\nStocks with zero beauty scores ({len(zero_beauty_stocks)}):")
            for item in zero_beauty_stocks[:10]:  # Show first 10
                symbol = item.get('symbol', 'N/A')
                ath_gain = float(item.get('ath_percentage_gain', 0))
                detection_date = item.get('detection_date', 'N/A')
                print(f"  {symbol:12s} - Gain: {ath_gain:7.1f}%, Date: {detection_date}")
            
            if len(zero_beauty_stocks) > 10:
                print(f"  ... and {len(zero_beauty_stocks) - 10} more")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    get_ath_stats()