"""
Unit tests for Near ATH detector
"""

import pytest
from datetime import datetime, timedelta
from lambdas.downloader.near_ath_detector import NearATHDetector


class TestNearATHDetector:
    """Test cases for Near ATH detection"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.detector = NearATHDetector('test', max_daily_volatility=100.0, near_ath_threshold=10.0)
    
    def test_near_ath_detection_basic(self):
        """Test basic near ATH detection"""
        # Create price data where ATH is $100 and current price is $95 (5% below ATH)
        price_data = [
            {'date': '2024-01-01', 'close': 80.0, 'high': 82.0, 'low': 78.0},
            {'date': '2024-01-02', 'close': 85.0, 'high': 87.0, 'low': 83.0},
            {'date': '2024-01-03', 'close': 90.0, 'high': 92.0, 'low': 88.0},
            {'date': '2024-01-04', 'close': 100.0, 'high': 102.0, 'low': 98.0},  # ATH
            {'date': '2024-01-05', 'close': 98.0, 'high': 100.0, 'low': 96.0},
            {'date': '2024-01-06', 'close': 95.0, 'high': 97.0, 'low': 93.0},   # Near ATH (5% below)
        ]
        
        result = self.detector.check_near_ath_detection('AAPL.US', 'US', price_data)
        
        assert result is not None
        assert result['symbol'] == 'AAPL.US'
        assert result['current_price'] == 95.0
        assert result['ath_price'] == 100.0
        assert result['ath_date'] == '2024-01-04'
        assert result['distance_from_ath_percentage'] == 5.0
        assert result['market_code'] == 'US'
    
    def test_no_near_ath_detection_too_far(self):
        """Test no detection when price is too far from ATH"""
        # Create price data where current price is 15% below ATH (beyond 10% threshold)
        price_data = [
            {'date': '2024-01-01', 'close': 80.0, 'high': 82.0, 'low': 78.0},
            {'date': '2024-01-02', 'close': 100.0, 'high': 102.0, 'low': 98.0},  # ATH
            {'date': '2024-01-03', 'close': 85.0, 'high': 87.0, 'low': 83.0},   # 15% below ATH
        ]
        
        result = self.detector.check_near_ath_detection('AAPL.US', 'US', price_data)
        
        assert result is None
    
    def test_no_near_ath_detection_at_ath(self):
        """Test no detection when price equals ATH (should be handled by ATH detector)"""
        price_data = [
            {'date': '2024-01-01', 'close': 80.0, 'high': 82.0, 'low': 78.0},
            {'date': '2024-01-02', 'close': 100.0, 'high': 102.0, 'low': 98.0},  # ATH
            {'date': '2024-01-03', 'close': 100.0, 'high': 102.0, 'low': 98.0},  # Same as ATH
        ]
        
        result = self.detector.check_near_ath_detection('AAPL.US', 'US', price_data)
        
        assert result is None
    
    def test_excessive_volatility_rejection(self):
        """Test rejection of stocks with excessive volatility"""
        # Create price data with one day having >100% volatility
        price_data = [
            {'date': '2024-01-01', 'close': 80.0, 'high': 82.0, 'low': 78.0},
            {'date': '2024-01-02', 'close': 100.0, 'high': 250.0, 'low': 50.0},  # 400% volatility
            {'date': '2024-01-03', 'close': 95.0, 'high': 97.0, 'low': 93.0},
        ]
        
        result = self.detector.check_near_ath_detection('VOLATILE.US', 'US', price_data)
        
        assert result is None
    
    def test_custom_threshold(self):
        """Test custom near ATH threshold"""
        detector = NearATHDetector('test', near_ath_threshold=5.0)  # 5% threshold
        
        # Price 7% below ATH should not trigger with 5% threshold
        price_data = [
            {'date': '2024-01-01', 'close': 100.0, 'high': 102.0, 'low': 98.0},  # ATH
            {'date': '2024-01-02', 'close': 93.0, 'high': 95.0, 'low': 91.0},   # 7% below ATH
        ]
        
        result = detector.check_near_ath_detection('AAPL.US', 'US', price_data)
        
        assert result is None
        
        # Price 3% below ATH should trigger with 5% threshold
        price_data[1]['close'] = 97.0  # 3% below ATH
        
        result = detector.check_near_ath_detection('AAPL.US', 'US', price_data)
        
        assert result is not None
        assert result['distance_from_ath_percentage'] == 3.0
    
    def test_insufficient_data(self):
        """Test handling of insufficient data"""
        price_data = [
            {'date': '2024-01-01', 'close': 100.0, 'high': 102.0, 'low': 98.0}
        ]
        
        result = self.detector.check_near_ath_detection('AAPL.US', 'US', price_data)
        
        assert result is None
    
    def test_closest_approach_selection(self):
        """Test that the closest approach to ATH is selected"""
        price_data = [
            {'date': '2024-01-01', 'close': 100.0, 'high': 102.0, 'low': 98.0},  # ATH
            {'date': '2024-01-02', 'close': 95.0, 'high': 97.0, 'low': 93.0},   # 5% below
            {'date': '2024-01-03', 'close': 92.0, 'high': 94.0, 'low': 90.0},   # 8% below
            {'date': '2024-01-04', 'close': 97.0, 'high': 99.0, 'low': 95.0},   # 3% below (closest)
        ]
        
        result = self.detector.check_near_ath_detection('AAPL.US', 'US', price_data)
        
        assert result is not None
        assert result['current_price'] == 97.0
        assert result['distance_from_ath_percentage'] == 3.0
        assert result['detection_date'] == '2024-01-04'