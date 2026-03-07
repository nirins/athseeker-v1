"""Unit tests for S3 key formatting"""

import sys
import os
import pytest
from unittest.mock import Mock, patch

# Add lambdas/downloader to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambdas', 'downloader'))
from downloader import StockDownloader


@pytest.fixture
def downloader():
    """Create StockDownloader instance for S3 key testing"""
    with patch('downloader.boto3'):
        dl = StockDownloader(
            environment='dev',
            s3_bucket='test-bucket',
            dynamodb_table='test-table'
        )
        dl.s3 = Mock()
        return dl


class TestS3KeyFormatting:
    """Tests for S3 key structure and formatting"""
    
    def test_s3_key_format_us_market(self, downloader):
        """Test S3 key format for US market"""
        # Arrange
        task = {
            'symbol': 'AAPL',
            'marketCode': 'US',
            'date': '2024-01-15'
        }
        price_data = [{'date': '2024-01-15', 'close': 100.0}]
        
        # Act
        downloader.upload_to_s3(task, price_data)
        
        # Assert
        call_args = downloader.s3.put_object.call_args[1]
        s3_key = call_args['Key']
        
        expected_key = 'prices/market=US/dt=2024-01-15/symbol=AAPL/data.json.gz'
        assert s3_key == expected_key
    
    def test_s3_key_format_thailand_market(self, downloader):
        """Test S3 key format for Thailand market"""
        # Arrange
        task = {
            'symbol': 'PTT',
            'marketCode': 'BK',
            'date': '2024-01-15'
        }
        price_data = [{'date': '2024-01-15', 'close': 50.0}]
        
        # Act
        downloader.upload_to_s3(task, price_data)
        
        # Assert
        call_args = downloader.s3.put_object.call_args[1]
        s3_key = call_args['Key']
        
        expected_key = 'prices/market=BK/dt=2024-01-15/symbol=PTT/data.json.gz'
        assert s3_key == expected_key
    
    def test_s3_key_format_crypto_market(self, downloader):
        """Test S3 key format for cryptocurrency market"""
        # Arrange
        task = {
            'symbol': 'BTC-USD',
            'marketCode': 'CC',
            'date': '2024-01-15'
        }
        price_data = [{'date': '2024-01-15', 'close': 45000.0}]
        
        # Act
        downloader.upload_to_s3(task, price_data)
        
        # Assert
        call_args = downloader.s3.put_object.call_args[1]
        s3_key = call_args['Key']
        
        expected_key = 'prices/market=CC/dt=2024-01-15/symbol=BTC-USD/data.json.gz'
        assert s3_key == expected_key
    
    def test_s3_key_partitioning_structure(self, downloader):
        """Test that S3 key follows partitioned structure for efficient querying"""
        # Arrange
        task = {
            'symbol': 'MSFT',
            'marketCode': 'US',
            'date': '2024-02-20'
        }
        price_data = [{'date': '2024-02-20', 'close': 400.0}]
        
        # Act
        downloader.upload_to_s3(task, price_data)
        
        # Assert
        call_args = downloader.s3.put_object.call_args[1]
        s3_key = call_args['Key']
        
        # Verify partitioning structure
        assert s3_key.startswith('prices/')
        assert 'market=US' in s3_key
        assert 'dt=2024-02-20' in s3_key
        assert 'symbol=MSFT' in s3_key
        assert s3_key.endswith('data.json.gz')
    
    def test_s3_key_consistency_same_inputs(self, downloader):
        """Test that same inputs always produce same S3 key (idempotency)"""
        # Arrange
        task = {
            'symbol': 'GOOGL',
            'marketCode': 'US',
            'date': '2024-01-15'
        }
        price_data = [{'date': '2024-01-15', 'close': 150.0}]
        
        # Act - call twice
        downloader.upload_to_s3(task, price_data)
        first_key = downloader.s3.put_object.call_args[1]['Key']
        
        downloader.upload_to_s3(task, price_data)
        second_key = downloader.s3.put_object.call_args[1]['Key']
        
        # Assert
        assert first_key == second_key
    
    def test_s3_key_different_dates(self, downloader):
        """Test that different dates produce different S3 keys"""
        # Arrange
        task1 = {
            'symbol': 'AAPL',
            'marketCode': 'US',
            'date': '2024-01-15'
        }
        task2 = {
            'symbol': 'AAPL',
            'marketCode': 'US',
            'date': '2024-01-16'
        }
        price_data = [{'date': '2024-01-15', 'close': 100.0}]
        
        # Act
        downloader.upload_to_s3(task1, price_data)
        key1 = downloader.s3.put_object.call_args[1]['Key']
        
        downloader.upload_to_s3(task2, price_data)
        key2 = downloader.s3.put_object.call_args[1]['Key']
        
        # Assert
        assert key1 != key2
        assert 'dt=2024-01-15' in key1
        assert 'dt=2024-01-16' in key2
    
    def test_s3_key_different_symbols(self, downloader):
        """Test that different symbols produce different S3 keys"""
        # Arrange
        task1 = {
            'symbol': 'AAPL',
            'marketCode': 'US',
            'date': '2024-01-15'
        }
        task2 = {
            'symbol': 'MSFT',
            'marketCode': 'US',
            'date': '2024-01-15'
        }
        price_data = [{'date': '2024-01-15', 'close': 100.0}]
        
        # Act
        downloader.upload_to_s3(task1, price_data)
        key1 = downloader.s3.put_object.call_args[1]['Key']
        
        downloader.upload_to_s3(task2, price_data)
        key2 = downloader.s3.put_object.call_args[1]['Key']
        
        # Assert
        assert key1 != key2
        assert 'symbol=AAPL' in key1
        assert 'symbol=MSFT' in key2
    
    def test_s3_key_different_markets(self, downloader):
        """Test that different markets produce different S3 keys"""
        # Arrange
        task1 = {
            'symbol': 'AAPL',
            'marketCode': 'US',
            'date': '2024-01-15'
        }
        task2 = {
            'symbol': 'AAPL',
            'marketCode': 'BK',
            'date': '2024-01-15'
        }
        price_data = [{'date': '2024-01-15', 'close': 100.0}]
        
        # Act
        downloader.upload_to_s3(task1, price_data)
        key1 = downloader.s3.put_object.call_args[1]['Key']
        
        downloader.upload_to_s3(task2, price_data)
        key2 = downloader.s3.put_object.call_args[1]['Key']
        
        # Assert
        assert key1 != key2
        assert 'market=US' in key1
        assert 'market=BK' in key2
