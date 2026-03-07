#!/usr/bin/env python3
"""
Check AEBI.US volatility to understand why it wasn't filtered out
"""

import requests
import json
from datetime import datetime, timedelta

def check_aebi_volatility():
    """Check AEBI.US recent price data and calculate volatility"""
    
    # Sample price data structure (you would get this from your API or database)
    # For now, let's simulate what the volatility calculation would look like
    
    print("🔍 Checking AEBI.US Volatility")
    print("=" * 50)
    
    # Example calculation for a stock with high volatility
    # Let's say AEBI.US had these prices on a recent day:
    sample_data = [
        {"date": "2026-03-07", "high": 15.50, "low": 8.25, "close": 12.30},
        {"date": "2026-03-06", "high": 9.80, "low": 7.50, "close": 8.90},
        {"date": "2026-03-05", "high": 8.20, "low": 6.10, "close": 7.80},
    ]
    
    print("Sample AEBI.US price data:")
    print("Date       | High   | Low    | Close  | Daily Volatility")
    print("-" * 55)
    
    for record in sample_data:
        high = record['high']
        low = record['low']
        close = record['close']
        
        # Calculate daily volatility: ((High - Low) / Low) * 100
        if low > 0:
            daily_volatility = ((high - low) / low) * 100
            status = "FILTERED" if daily_volatility > 100 else "ALLOWED"
            
            print(f"{record['date']} | ${high:6.2f} | ${low:6.2f} | ${close:6.2f} | {daily_volatility:6.1f}% ({status})")
        else:
            print(f"{record['date']} | ${high:6.2f} | ${low:6.2f} | ${close:6.2f} | N/A (zero low)")
    
    print()
    print("💡 Volatility Filter Logic:")
    print("   - Daily Volatility = ((High - Low) / Low) × 100")
    print("   - Current threshold: 100% (MAX_DAILY_VOLATILITY)")
    print("   - Records with volatility > 100% are filtered out")
    print()
    print("🎯 Possible reasons AEBI.US wasn't filtered:")
    print("   1. Daily volatility was ≤ 100% on ATH detection day")
    print("   2. ATH was detected on a day with normal volatility")
    print("   3. The filter only applies to individual daily records, not the overall ATH")
    print()
    print("📊 To check actual AEBI.US data:")
    print("   1. Look at CloudWatch logs for ATH detection")
    print("   2. Check the specific day AEBI.US was detected as ATH")
    print("   3. Verify the high/low/close prices for that day")

if __name__ == "__main__":
    check_aebi_volatility()