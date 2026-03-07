"""Unit tests for DynamoDB save logic"""

import sys
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add lambdas/downloader to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambdas', 'downloader'))
from downloader import StockDownloader


@pytest.fixture
def downloader():
    """Create StockDownloader instance for DynamoDB testing"""
    with patch('downloader.boto3'):
        dl = StockDownloader(
            environment='dev',
            s3_bucket='test-bucket',
            dynamodb_table='test-table'
        )
        
        # Mock DynamoDB
        dl.dynamodb = Mock()
        mock_table = Mock()
        dl.dynamodb.Table.return_value = mock_table
        
        return dl


class TestDynamoDBSaveLogic:
    """Tests for DynamoDB save operations"""
    
    def test_save_to_dynamodb_basic_structure(self, downloader):
        """Test basic DynamoDB item structure"""
        # Arrange
        task = {
            'symbol': 'AAPL',
            'marketCode': 'US',
            'date': '2024-01-15'
        }
        
        price_data = [
            {
                'date': '2024-01-01',
                'open': 100.0,
                'high': 105.0,
                'low': 99.0,
                'close': 103.0,
                'adjusted_close': 103.0,
                'volume': 1000000
            }
        ]
        
        # Act
        downloader.save_to_dynamodb(task, price_data)
        
        # Assert
        mock_table = downloader.dynamodb.Table.return_value
        mock_table.put_item.assert_called_once()
        
        call_args = mock_table.put_item.call_args[1]
        item = call_args['Item']
        
        # Verify item structure
        assert item['symbol'] == 'AAPL.US'
        assert item['market_code'] == 'US'
        assert 'prices' in item
        assert 'moving_averages' in item
        assert 'updated_at' in item
    
    def test_save_to_dynamodb_prices_list(self, downloader):
        """Test that prices are saved as nested list"""
        # Arrange
        task = {
            'symbol': 'MSFT',
            'marketCode': 'US',
            'date': '2024-01-15'
        }
        
        price_data = [
            {
                'date': '2024-01-01',
                'open': 100.0,
                'high': 105.0,
                'low': 99.0,
                'close': 103.0,
                'adjusted_close': 103.0,
                'volume': 1000000
            },
            {
                'date': '2024-01-02',
                'open': 103.0,
                'high': 107.0,
                'low': 102.0,
                'close': 106.0,
                'adjusted_close': 106.0,
                'volume': 1200000
            }
        ]
        
        # Act
        downloader.save_to_dynamodb(task, price_data)
        
        # Assert
        mock_table = downloader.dynamodb.Table.return_value
        item = mock_table.put_item.call_args[1]['Item']
        
        prices = item['prices']
        assert len(prices) == 2
        
        # Verify first price record
        assert prices[0]['date'] == '2024-01-01'
        assert prices[0]['open'] == 100.0
        assert prices[0]['high'] == 105.0
        assert prices[0]['low'] == 99.0
        assert prices[0]['close'] == 103.0
        assert prices[0]['adjusted_close'] == 103.0
        assert prices[0]['volume'] == 1000000
    
    def test_save_to_dynamodb_moving_averages_list(self, downloader):
        """Test that moving averages are saved as nested list"""
        # Arrange
        task = {
            'symbol': 'GOOGL',
            'marketCode': 'US',
            'date': '2024-01-15'
        }
        
        # Create dataset with enough data for EMA-7
        price_data = [
            {
                'date': f'2024-01-{i:02d}',
                'open': 100.0 + i,
                'high': 105.0 + i,
                'low': 99.0 + i,
                'close': 103.0 + i,
                'adjusted_close': 103.0 + i,
                'volume': 1000000
            }
            for i in range(1, 11)
        ]
        
        # Act
        downloader.save_to_dynamodb(task, price_data)
        
        # Assert
        mock_table = downloader.dynamodb.Table.return_value
        item = mock_table.put_item.call_args[1]['Item']
        
        moving_averages = item['moving_averages']
        assert len(moving_averages) == 10
        
        # Verify structure
        ma_record = moving_averages[0]
        assert 'date' in ma_record
        assert 'ema_7' in ma_record
        assert 'ema_30' in ma_record
        assert 'ema_50' in ma_record
        assert 'ema_200' in ma_record
    
    def test_save_to_dynamodb_symbol_with_market(self, downloader):
        """Test that symbol is stored with market code suffix"""
        # Arrange
        task = {
            'symbol': 'PTT',
            'marketCode': 'BK',
            'date': '2024-01-15'
        }
        
        price_data = [
            {
                'date': '2024-01-01',
                'open': 50.0,
                'high': 52.0,
                'low': 49.0,
                'close': 51.0,
                'adjusted_close': 51.0,
                'volume': 500000
            }
        ]
        
        # Act
        downloader.save_to_dynamodb(task, price_data)
        
        # Assert
        mock_table = downloader.dynamodb.Table.return_value
        item = mock_table.put_item.call_args[1]['Item']
        
        assert item['symbol'] == 'PTT.BK'
        assert item['market_code'] == 'BK'
    
    def test_save_to_dynamodb_data_sorting(self, downloader):
        """Test that price data is sorted by date before saving"""
        # Arrange
        task = {
            'symbol': 'AAPL',
            'marketCode': 'US',
            'date': '2024-01-15'
        }
        
        # Unsorted data
        price_data = [
            {
                'date': '2024-01-03',
                'open': 103.0,
                'high': 107.0,
                'low': 102.0,
                'close': 106.0,
                'adjusted_close': 106.0,
                'volume': 1200000
            },
            {
                'date': '2024-01-01',
                'open': 100.0,
                'high': 105.0,
                'low': 99.0,
                'close': 103.0,
                'adjusted_close': 103.0,
                'volume': 1000000
            },
            {
                'date': '2024-01-02',
                'open': 102.0,
                'high': 106.0,
                'low': 101.0,
                'close': 105.0,
                'adjusted_close': 105.0,
                'volume': 1100000
            }
        ]
        
        # Act
        downloader.save_to_dynamodb(task, price_data)
        
        # Assert
        mock_table = downloader.dynamodb.Table.return_value
        item = mock_table.put_item.call_args[1]['Item']
        
        prices = item['prices']
        assert prices[0]['date'] == '2024-01-01'
        assert prices[1]['date'] == '2024-01-02'
        assert prices[2]['date'] == '2024-01-03'
    
    def test_save_to_dynamodb_ema_calculation_integration(self, downloader):
        """Test that EMAs are calculated and saved correctly"""
        # Arrange
        task = {
            'symbol': 'AAPL',
            'marketCode': 'US',
            'date': '2024-01-15'
        }
        
        # Create dataset with enough data for EMA-7
        price_data = [
            {
                'date': f'2024-01-{i:02d}',
                'open': 100.0,
                'high': 105.0,
                'low': 99.0,
                'close': 100.0 + i,
                'adjusted_close': 100.0 + i,
                'volume': 1000000
            }
            for i in range(1, 11)
        ]
        
        # Act
        downloader.save_to_dynamodb(task, price_data)
        
        # Assert
        mock_table = downloader.dynamodb.Table.return_value
        item = mock_table.put_item.call_args[1]['Item']
        
        moving_averages = item['moving_averages']
        
        # First 6 EMAs should be None (insufficient data for EMA-7)
        for i in range(6):
            assert moving_averages[i]['ema_7'] is None
        
        # 7th EMA should exist
        assert moving_averages[6]['ema_7'] is not None
    
    def test_save_to_dynamodb_type_conversion(self, downloader):
        """Test that numeric values are properly converted to float/int"""
        # Arrange
        task = {
            'symbol': 'AAPL',
            'marketCode': 'US',
            'date': '2024-01-15'
        }
        
        price_data = [
            {
                'date': '2024-01-01',
                'open': '100.5',  # String
                'high': '105.5',
                'low': '99.5',
                'close': '103.5',
                'adjusted_close': '103.5',
                'volume': '1000000'
            }
        ]
        
        # Act
        downloader.save_to_dynamodb(task, price_data)
        
        # Assert
        mock_table = downloader.dynamodb.Table.return_value
        item = mock_table.put_item.call_args[1]['Item']
        
        prices = item['prices']
        assert isinstance(prices[0]['open'], float)
        assert isinstance(prices[0]['high'], float)
        assert isinstance(prices[0]['low'], float)
        assert isinstance(prices[0]['close'], float)
        assert isinstance(prices[0]['adjusted_close'], float)
        assert isinstance(prices[0]['volume'], int)
    
    def test_save_to_dynamodb_updated_at_timestamp(self, downloader):
        """Test that updated_at timestamp is included"""
        # Arrange
        task = {
            'symbol': 'AAPL',
            'marketCode': 'US',
            'date': '2024-01-15'
        }
        
        price_data = [
            {
                'date': '2024-01-01',
                'open': 100.0,
                'high': 105.0,
                'low': 99.0,
                'close': 103.0,
                'adjusted_close': 103.0,
                'volume': 1000000
            }
        ]
        
        # Act
        with patch('downloader.datetime') as mock_datetime:
            mock_now = Mock()
            mock_now.isoformat.return_value = '2024-01-15T10:30:00'
            mock_datetime.now.return_value = mock_now
            
            downloader.save_to_dynamodb(task, price_data)
        
        # Assert
        mock_table = downloader.dynamodb.Table.return_value
        item = mock_table.put_item.call_args[1]['Item']
        
        assert 'updated_at' in item
        assert item['updated_at'] == '2024-01-15T10:30:00'
