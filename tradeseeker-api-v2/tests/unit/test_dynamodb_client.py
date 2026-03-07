"""Unit tests for DynamoDB client."""

import pytest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError

from src.db.dynamodb_client import DynamoDBClient


class TestDynamoDBClient:
    """Tests for DynamoDBClient class."""
    
    @patch('src.db.dynamodb_client.boto3')
    def test_initialization(self, mock_boto3):
        """Test client initialization."""
        mock_resource = MagicMock()
        mock_boto3.resource.return_value = mock_resource
        
        client = DynamoDBClient(region='ap-southeast-1')
        
        mock_boto3.resource.assert_called_once_with('dynamodb', region_name='ap-southeast-1')
        assert client.region == 'ap-southeast-1'
    
    @patch('src.db.dynamodb_client.boto3')
    def test_query_by_date(self, mock_boto3):
        """Test query golden crosses by date."""
        mock_table = MagicMock()
        mock_table.query.return_value = {
            'Items': [{'symbol': 'AAPL.US', 'cross_date': '2024-01-15'}]
        }
        
        mock_resource = MagicMock()
        mock_resource.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_resource
        
        client = DynamoDBClient()
        results = client.query_golden_crosses_by_date('2024-01-15')
        
        assert len(results) == 1
        assert results[0]['symbol'] == 'AAPL.US'
        mock_table.query.assert_called_once()
    
    @patch('src.db.dynamodb_client.boto3')
    def test_query_by_date_and_market(self, mock_boto3):
        """Test query golden crosses by date and market."""
        mock_table = MagicMock()
        mock_table.query.return_value = {
            'Items': [{'symbol': 'AAPL.US', 'cross_date': '2024-01-15', 'market_code': 'US'}]
        }
        
        mock_resource = MagicMock()
        mock_resource.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_resource
        
        client = DynamoDBClient()
        results = client.query_golden_crosses_by_date('2024-01-15', 'US')
        
        assert len(results) == 1
        assert results[0]['market_code'] == 'US'
    
    @patch('src.db.dynamodb_client.boto3')
    def test_get_stock_price(self, mock_boto3):
        """Test get stock price by symbol."""
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            'Item': {'symbol': 'AAPL.US', 'prices': []}
        }
        
        mock_resource = MagicMock()
        mock_resource.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_resource
        
        client = DynamoDBClient()
        result = client.get_stock_price('AAPL.US')
        
        assert result is not None
        assert result['symbol'] == 'AAPL.US'
    
    @patch('src.db.dynamodb_client.boto3')
    def test_get_stock_price_not_found(self, mock_boto3):
        """Test get stock price when symbol not found."""
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}
        
        mock_resource = MagicMock()
        mock_resource.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_resource
        
        client = DynamoDBClient()
        result = client.get_stock_price('NONEXISTENT.US')
        
        assert result is None
    
    @patch('src.db.dynamodb_client.boto3')
    def test_scan_golden_crosses(self, mock_boto3):
        """Test scan golden crosses table."""
        mock_table = MagicMock()
        mock_table.scan.return_value = {
            'Items': [
                {'symbol': 'AAPL.US'},
                {'symbol': 'MSFT.US'}
            ]
        }
        
        mock_resource = MagicMock()
        mock_resource.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_resource
        
        client = DynamoDBClient()
        results = client.scan_golden_crosses()
        
        assert len(results) == 2
        mock_table.scan.assert_called_once()
