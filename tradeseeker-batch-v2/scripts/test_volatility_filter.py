#!/usr/bin/env python3
"""
Test script for ATH volatility filtering
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lambdas', 'downloader'))

from ath_detector import ATHDetector

def test_volatility_filter():
    """Test the volatility filtering functionality"""
    
    # Create ATH detector with 50% max volatility for testing
    detector = ATHDetector('test', max_daily_volatility=50.0)
    
    # Test data with various volatility levels
    test_data = [
        # Normal volatility (5% range)
        {'date': '2026-03-01', 'close': 100.0, 'high': 102.5, 'low': 97.5},
        {'date': '2026-03-02', 'close': 105.0, 'high': 107.0, 'low': 103.0},
        
        # High volatility (150% range) - should be filtered
        {'date': '2026-03-03', 'close': 110.0, 'high': 200.0, 'low': 80.0},
        
        # Normal ATH
        {'date': '2026-03-04', 'close': 115.0, 'high': 117.0, 'low': 113.0},
    ]
    
    print("Testing ATH detection with volatility filter...")
    print(f"Max allowed volatility: {detector.max_daily_volatility}%")
    print()
    
    # Test ATH detection
    result = detector.check_ath_detection('TEST.US', 'US', test_data)
    
    if result:
        print("✅ ATH Detection Result:")
        print(f"   Symbol: {result['symbol']}")
        print(f"   Date: {result['detection_date']}")
        print(f"   Price: ${result['ath_price']}")
        print(f"   Gain: {result['ath_percentage_gain']}%")
    else:
        print("❌ No ATH detected (or filtered out)")
    
    print()
    print("Expected: ATH should be detected on 2026-03-04 at $115")
    print("Expected: 2026-03-03 should be filtered out due to 150% volatility")

if __name__ == "__main__":
    test_volatility_filter()