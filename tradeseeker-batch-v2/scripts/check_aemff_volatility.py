#!/usr/bin/env python3
"""
Test the updated AEMFF volatility filter (more restrictive)
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lambdas', 'downloader'))

from ath_detector import ATHDetector

def test_restrictive_filter():
    """Test the new restrictive volatility filter"""
    
    print("🔍 Testing Restrictive Volatility Filter")
    print("=" * 50)
    
    # Create detector with 50% threshold
    detector = ATHDetector('test', max_daily_volatility=50.0)
    print(f"Volatility threshold: {detector.max_daily_volatility}%")
    print("New behavior: Reject ENTIRE stock if ANY day in 360-day history exceeds threshold")
    print()
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "AEMFF-like: One high volatility day",
            "data": [
                {"date": "2026-03-01", "high": 10.00, "low": 8.00, "close": 9.00},   # 25% volatility
                {"date": "2026-03-02", "high": 11.00, "low": 9.50, "close": 10.50}, # 15.8% volatility
                {"date": "2026-03-03", "high": 12.00, "low": 10.00, "close": 11.50}, # 20% volatility
                {"date": "2026-03-04", "high": 15.00, "low": 8.00, "close": 12.00}, # 87.5% volatility (HIGH!)
                {"date": "2026-03-05", "high": 16.00, "low": 14.00, "close": 15.50}, # 14.3% volatility
                {"date": "2026-03-06", "high": 17.00, "low": 15.00, "close": 16.50}, # 13.3% volatility
                {"date": "2026-03-07", "high": 18.00, "low": 16.00, "close": 17.50}, # 12.5% volatility (ATH)
            ]
        },
        {
            "name": "Clean stock: All days under threshold",
            "data": [
                {"date": "2026-03-01", "high": 10.00, "low": 8.00, "close": 9.00},   # 25% volatility
                {"date": "2026-03-02", "high": 11.00, "low": 9.50, "close": 10.50}, # 15.8% volatility
                {"date": "2026-03-03", "high": 12.00, "low": 10.00, "close": 11.50}, # 20% volatility
                {"date": "2026-03-04", "high": 13.00, "low": 11.00, "close": 12.00}, # 18.2% volatility
                {"date": "2026-03-05", "high": 14.00, "low": 12.50, "close": 13.50}, # 12% volatility
                {"date": "2026-03-06", "high": 15.00, "low": 13.00, "close": 14.50}, # 15.4% volatility
                {"date": "2026-03-07", "high": 16.00, "low": 14.00, "close": 15.50}, # 14.3% volatility (ATH)
            ]
        }
    ]
    
    for scenario in test_scenarios:
        print(f"📊 Scenario: {scenario['name']}")
        print("Date       | High   | Low    | Close  | Volatility | Status")
        print("-" * 65)
        
        max_volatility = 0
        for record in scenario['data']:
            high = record['high']
            low = record['low']
            close = record['close']
            
            if low > 0:
                volatility = ((high - low) / low) * 100
                max_volatility = max(max_volatility, volatility)
                status = "HIGH" if volatility > 50.0 else "OK"
                print(f"{record['date']} | ${high:6.2f} | ${low:6.2f} | ${close:6.2f} | {volatility:8.1f}% | {status}")
        
        print(f"Max volatility in recent period: {max_volatility:.1f}%")
        
        # Test ATH detection with new restrictive filter
        result = detector.check_ath_detection("TEST.US", "US", scenario['data'])
        
        if result:
            print(f"✅ ATH Detected: ${result['ath_price']:.2f} on {result['detection_date']}")
        else:
            print("❌ Stock REJECTED entirely due to high volatility in recent history")
        
        print()
    
    print("💡 New Filter Behavior:")
    print("   - Checks ALL days in the full 360-day price history")
    print("   - If ANY single day exceeds 50% volatility, REJECT the entire stock")
    print("   - Extremely restrictive - only allows consistently stable stocks")
    print("   - Should eliminate all volatile stocks like AEMFF, AEBI, etc.")

if __name__ == "__main__":
    test_restrictive_filter()