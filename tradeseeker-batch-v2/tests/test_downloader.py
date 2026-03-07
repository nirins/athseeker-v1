"""Unit tests for Stock Downloader"""

import json
import gzip
import sys
import os
import pytest
import requests
from unittest.mock import Mock, patch, MagicMock

# Add lambdas/downloader to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambdas', 'downloader'))
from downloader import StockDownloader


@pytest.fixture
def downloader():
    """Create StockDownloader instance with mocked AWS clients"""
    with patch('downloader.boto3'):
        dl = StockDownloader(
            environment='dev',
            s3_bucket='test-bucket',
            dynamodb_table='test-table'
        )
        
        # Mock AWS clients
        dl.s3 = Mock()
        dl.dynamodb = Mock()
        dl.ssm = Mock()
        dl.secretsmanager = Mock()
        
        return dl


class TestAPIClient:
    """Tests for EODHD API client"""
    
    def test_call_eodhd_api_success(self, downloader):
        """Test successful API call to EODHD"""
        # Arrange
        task = {
            'symbol': 'AAPL',
            'marketCode': 'US',
            'date': '2024-01-15'
        }
        api_token = 'test-token'
        
        expected_data = [
            {
                'date': '2024-01-15',
                'open': 100.0,
                'high': 105.0,
                'low': 99.0,
                'close': 103.0,
                'adjusted_close': 103.0,
                'volume': 1000000
            }
        ]
        
        downloader._api_endpoints = {
            'stockPriceUrl': 'https://eodhd.com/api/eod/{SYMBOL}.{MARKET_CODE}'
        }
        
        with patch('downloader.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = expected_data
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            # Act
            result = downloader.call_eodhd_api(task, api_token)
            
            # Assert
            assert result == expected_data
            mock_get.assert_called_once()
            call_url = mock_get.call_args[0][0]
            assert 'AAPL.US' in call_url
            assert api_token in call_url


class TestRetryLogic:
    """Tests for retry logic with exponential backoff"""
    
    def test_fetch_with_retry_success_first_attempt(self, downloader):
        """Test successful fetch on first attempt"""
        # Arrange
        task = {'symbol': 'AAPL', 'marketCode': 'US', 'date': '2024-01-15'}
        expected_data = [{'date': '2024-01-15', 'close': 100.0}]
        
        downloader._api_token = 'test-token'
        downloader._api_endpoints = {
            'stockPriceUrl': 'https://eodhd.com/api/eod/{SYMBOL}.{MARKET_CODE}'
        }
        
        with patch('downloader.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = expected_data
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            # Act
            result = downloader.fetch_with_retry(task)
            
            # Assert
            assert result == expected_data
            assert mock_get.call_count == 1
    
    def test_fetch_with_retry_429_rate_limit(self, downloader):
        """Test retry on 429 rate limit error"""
        # Arrange
        task = {'symbol': 'AAPL', 'marketCode': 'US', 'date': '2024-01-15'}
        expected_data = [{'date': '2024-01-15', 'close': 100.0}]
        
        downloader._api_token = 'test-token'
        downloader._api_endpoints = {
            'stockPriceUrl': 'https://eodhd.com/api/eod/{SYMBOL}.{MARKET_CODE}'
        }
        
        with patch('downloader.requests.get') as mock_get, \
             patch('downloader.time.sleep'):
            
            # First call raises 429, second succeeds
            mock_response_error = Mock()
            mock_response_error.status_code = 429
            
            mock_response_success = Mock()
            mock_response_success.json.return_value = expected_data
            mock_response_success.raise_for_status = Mock()
            
            mock_get.side_effect = [
                requests.exceptions.HTTPError(response=mock_response_error),
                mock_response_success
            ]
            
            # Act
            result = downloader.fetch_with_retry(task, max_retries=3)
            
            # Assert
            assert result == expected_data
            assert mock_get.call_count == 2
    
    def test_fetch_with_retry_max_retries_exceeded(self, downloader):
        """Test that max retries are respected"""
        # Arrange
        task = {'symbol': 'AAPL', 'marketCode': 'US', 'date': '2024-01-15'}
        
        downloader._api_token = 'test-token'
        downloader._api_endpoints = {
            'stockPriceUrl': 'https://eodhd.com/api/eod/{SYMBOL}.{MARKET_CODE}'
        }
        
        with patch('downloader.requests.get') as mock_get, \
             patch('downloader.time.sleep'):
            
            # Always raise 429
            mock_response = Mock()
            mock_response.status_code = 429
            mock_get.side_effect = requests.exceptions.HTTPError(response=mock_response)
            
            # Act & Assert
            with pytest.raises(requests.exceptions.HTTPError):
                downloader.fetch_with_retry(task, max_retries=2)
            
            assert mock_get.call_count == 3  # Initial + 2 retries
    
    def test_fetch_with_retry_non_retriable_error(self, downloader):
        """Test that non-retriable errors (400, 404) are not retried"""
        # Arrange
        task = {'symbol': 'INVALID', 'marketCode': 'US', 'date': '2024-01-15'}
        
        downloader._api_token = 'test-token'
        downloader._api_endpoints = {
            'stockPriceUrl': 'https://eodhd.com/api/eod/{SYMBOL}.{MARKET_CODE}'
        }
        
        with patch('downloader.requests.get') as mock_get:
            # Raise 404 error
            mock_response = Mock()
            mock_response.status_code = 404
            mock_get.side_effect = requests.exceptions.HTTPError(response=mock_response)
            
            # Act & Assert
            with pytest.raises(requests.exceptions.HTTPError):
                downloader.fetch_with_retry(task, max_retries=3)
            
            assert mock_get.call_count == 1  # No retries for 404
    
    def test_fetch_with_retry_timeout(self, downloader):
        """Test retry on timeout error"""
        # Arrange
        task = {'symbol': 'AAPL', 'marketCode': 'US', 'date': '2024-01-15'}
        expected_data = [{'date': '2024-01-15', 'close': 100.0}]
        
        downloader._api_token = 'test-token'
        downloader._api_endpoints = {
            'stockPriceUrl': 'https://eodhd.com/api/eod/{SYMBOL}.{MARKET_CODE}'
        }
        
        with patch('downloader.requests.get') as mock_get, \
             patch('downloader.time.sleep'):
            
            # First call times out, second succeeds
            mock_response_success = Mock()
            mock_response_success.json.return_value = expected_data
            mock_response_success.raise_for_status = Mock()
            
            mock_get.side_effect = [
                requests.exceptions.Timeout(),
                mock_response_success
            ]
            
            # Act
            result = downloader.fetch_with_retry(task, max_retries=3)
            
            # Assert
            assert result == expected_data
            assert mock_get.call_count == 2


class TestGzipCompression:
    """Tests for gzip compression of JSON data"""
    
    def test_upload_to_s3_compression(self, downloader):
        """Test that data is properly compressed before S3 upload"""
        # Arrange
        task = {
            'symbol': 'AAPL',
            'marketCode': 'US',
            'date': '2024-01-15'
        }
        
        price_data = [
            {
                'date': '2024-01-15',
                'open': 100.0,
                'high': 105.0,
                'low': 99.0,
                'close': 103.0,
                'adjusted_close': 103.0,
                'volume': 1000000
            }
        ]
        
        # Act
        downloader.upload_to_s3(task, price_data)
        
        # Assert
        downloader.s3.put_object.assert_called_once()
        call_args = downloader.s3.put_object.call_args[1]
        
        # Verify compression
        compressed_body = call_args['Body']
        decompressed = gzip.decompress(compressed_body).decode('utf-8')
        decompressed_data = json.loads(decompressed)
        
        assert decompressed_data == price_data
        assert call_args['ContentEncoding'] == 'gzip'
        assert call_args['ContentType'] == 'application/json'
    
    def test_upload_to_s3_compression_reduces_size(self, downloader):
        """Test that compression actually reduces data size"""
        # Arrange
        task = {
            'symbol': 'AAPL',
            'marketCode': 'US',
            'date': '2024-01-15'
        }
        
        # Large dataset
        price_data = [
            {
                'date': f'2024-01-{i:02d}',
                'open': 100.0 + i,
                'high': 105.0 + i,
                'low': 99.0 + i,
                'close': 103.0 + i,
                'adjusted_close': 103.0 + i,
                'volume': 1000000 + i * 1000
            }
            for i in range(1, 31)
        ]
        
        # Act
        downloader.upload_to_s3(task, price_data)
        
        # Assert
        call_args = downloader.s3.put_object.call_args[1]
        compressed_body = call_args['Body']
        
        original_size = len(json.dumps(price_data).encode('utf-8'))
        compressed_size = len(compressed_body)
        
        assert compressed_size < original_size
