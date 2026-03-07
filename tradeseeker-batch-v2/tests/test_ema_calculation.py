"""Unit tests for EMA calculation functions"""

import sys
import os
import pytest
from unittest.mock import Mock, patch

# Add lambdas/downloader to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambdas', 'downloader'))
from downloader import StockDownloader


@pytest.fixture
def downloader():
    """Create StockDownloader instance for EMA testing"""
    with patch('downloader.boto3'):
        dl = StockDownloader(
            environment='dev',
            s3_bucket='test-bucket',
            dynamodb_table='test-table'
        )
        return dl


class TestEMACalculation:
    """Tests for Exponential Moving Average calculation"""
    
    def test_calculate_ema_series_basic(self, downloader):
        """Test EMA calculation with simple dataset"""
        # Arrange
        data = [
            {'date': '2024-01-01', 'close': 100.0},
            {'date': '2024-01-02', 'close': 102.0},
            {'date': '2024-01-03', 'close': 101.0},
            {'date': '2024-01-04', 'close': 103.0},
            {'date': '2024-01-05', 'close': 105.0},
            {'date': '2024-01-06', 'close': 104.0},
            {'date': '2024-01-07', 'close': 106.0},
        ]
        period = 7
        
        # Act
        result = downloader.calculate_ema_series(data, period)
        
        # Assert
        assert len(result) == len(data)
        
        # First 6 values should be None (insufficient data)
        for i in range(period - 1):
            assert result[i] is None
        
        # 7th value should be SMA of first 7 prices
        expected_sma = sum(d['close'] for d in data[:7]) / 7
        assert result[6] == pytest.approx(expected_sma)
    
    def test_calculate_ema_series_insufficient_data(self, downloader):
        """Test EMA calculation with insufficient data points"""
        # Arrange
        data = [
            {'date': '2024-01-01', 'close': 100.0},
            {'date': '2024-01-02', 'close': 102.0},
            {'date': '2024-01-03', 'close': 101.0},
        ]
        period = 7
        
        # Act
        result = downloader.calculate_ema_series(data, period)
        
        # Assert
        assert len(result) == len(data)
        assert all(v is None for v in result)
    
    def test_calculate_ema_series_progression(self, downloader):
        """Test that EMA values progress correctly"""
        # Arrange
        data = [
            {'date': f'2024-01-{i:02d}', 'close': 100.0 + i}
            for i in range(1, 11)
        ]
        period = 5
        
        # Act
        result = downloader.calculate_ema_series(data, period)
        
        # Assert
        # First 4 should be None
        for i in range(4):
            assert result[i] is None
        
        # 5th value is SMA
        expected_sma = sum(d['close'] for d in data[:5]) / 5
        assert result[4] == pytest.approx(expected_sma)
        
        # Subsequent values should use EMA formula
        k = 2 / (period + 1)
        ema = result[4]
        
        for i in range(5, len(data)):
            price = data[i]['close']
            expected_ema = (price * k) + (ema * (1 - k))
            assert result[i] == pytest.approx(expected_ema)
            ema = expected_ema
    
    def test_calculate_ema_series_period_7(self, downloader):
        """Test EMA-7 calculation"""
        # Arrange
        data = [
            {'date': '2024-01-01', 'close': 100.0},
            {'date': '2024-01-02', 'close': 101.0},
            {'date': '2024-01-03', 'close': 102.0},
            {'date': '2024-01-04', 'close': 103.0},
            {'date': '2024-01-05', 'close': 104.0},
            {'date': '2024-01-06', 'close': 105.0},
            {'date': '2024-01-07', 'close': 106.0},
            {'date': '2024-01-08', 'close': 107.0},
        ]
        period = 7
        
        # Act
        result = downloader.calculate_ema_series(data, period)
        
        # Assert
        k = 2 / (period + 1)
        
        # First EMA is SMA of first 7 prices
        sma = sum(d['close'] for d in data[:7]) / 7
        assert result[6] == pytest.approx(sma)
        
        # Second EMA uses formula
        expected_ema = (data[7]['close'] * k) + (sma * (1 - k))
        assert result[7] == pytest.approx(expected_ema)
    
    def test_calculate_ema_series_period_30(self, downloader):
        """Test EMA-30 calculation with larger dataset"""
        # Arrange
        data = [
            {'date': f'2024-01-{i:02d}', 'close': 100.0 + i * 0.5}
            for i in range(1, 35)
        ]
        period = 30
        
        # Act
        result = downloader.calculate_ema_series(data, period)
        
        # Assert
        # First 29 should be None
        for i in range(29):
            assert result[i] is None
        
        # 30th value is SMA
        expected_sma = sum(d['close'] for d in data[:30]) / 30
        assert result[29] == pytest.approx(expected_sma)
        
        # Remaining values should exist
        for i in range(30, len(data)):
            assert result[i] is not None
    
    def test_calculate_ema_series_period_200(self, downloader):
        """Test EMA-200 calculation with large dataset"""
        # Arrange
        data = [
            {'date': f'2024-{(i//30)+1:02d}-{(i%30)+1:02d}', 'close': 100.0 + i * 0.1}
            for i in range(250)
        ]
        period = 200
        
        # Act
        result = downloader.calculate_ema_series(data, period)
        
        # Assert
        # First 199 should be None
        for i in range(199):
            assert result[i] is None
        
        # 200th value is SMA
        expected_sma = sum(d['close'] for d in data[:200]) / 200
        assert result[199] == pytest.approx(expected_sma)
        
        # Remaining values should exist
        for i in range(200, len(data)):
            assert result[i] is not None
    
    def test_calculate_ema_series_formula_correctness(self, downloader):
        """Test EMA formula: EMA = (Price × k) + (EMA_prev × (1 - k))"""
        # Arrange
        data = [
            {'date': '2024-01-01', 'close': 10.0},
            {'date': '2024-01-02', 'close': 11.0},
            {'date': '2024-01-03', 'close': 12.0},
            {'date': '2024-01-04', 'close': 13.0},
            {'date': '2024-01-05', 'close': 14.0},
        ]
        period = 3
        k = 2 / (period + 1)  # k = 0.5
        
        # Act
        result = downloader.calculate_ema_series(data, period)
        
        # Assert
        # First 2 should be None
        assert result[0] is None
        assert result[1] is None
        
        # 3rd value is SMA = (10 + 11 + 12) / 3 = 11.0
        assert result[2] == pytest.approx(11.0)
        
        # 4th value: EMA = (13 × 0.5) + (11 × 0.5) = 12.0
        assert result[3] == pytest.approx(12.0)
        
        # 5th value: EMA = (14 × 0.5) + (12 × 0.5) = 13.0
        assert result[4] == pytest.approx(13.0)
