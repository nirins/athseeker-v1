"""Unit tests for handler modules."""

import json
import pytest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError

from src.handlers.golden_crosses import handle_golden_crosses
from src.handlers.stock_price import handle_stock_price
from src.handlers.openai_summary import handle_openai_summary


class TestGoldenCrossesHandler:
    """Tests for golden crosses handler."""
    
    @patch('src.handlers.golden_crosses.DynamoDBClient')
    def test_default_filters_applied(self, mock_db_class):
        """Test default filters are applied when no parameters provided."""
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.scan_golden_crosses.return_value = [
            {'symbol': 'AAPL.US', 'green_days_30d_pct': 75, 'max_red_candle_30d_pct': -3},
            {'symbol': 'MSFT.US', 'green_days_30d_pct': 65, 'max_red_candle_30d_pct': -10}
        ]
        
        response = handle_golden_crosses({})
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        # Only AAPL.US should pass default filters (min_green=70, max_red_candle=-8)
        assert len(body['data']) == 1
        assert body['data'][0]['symbol'] == 'AAPL.US'
    
    @patch('src.handlers.golden_crosses.DynamoDBClient')
    def test_custom_filters(self, mock_db_class):
        """Test custom filters are applied correctly."""
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.scan_golden_crosses.return_value = [
            {'symbol': 'AAPL.US', 'green_days_30d_pct': 80, 'max_red_candle_30d_pct': -2},
            {'symbol': 'MSFT.US', 'green_days_30d_pct': 50, 'max_red_candle_30d_pct': -1}
        ]
        
        response = handle_golden_crosses({'min_green': '60', 'max_red_candle': '-3'})
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        # Only AAPL.US should pass (green_days >= 60 AND max_red_candle >= -3)
        assert len(body['data']) == 1
        assert body['data'][0]['symbol'] == 'AAPL.US'
    
    @patch('src.handlers.golden_crosses.DynamoDBClient')
    def test_date_query_strategy(self, mock_db_class):
        """Test date-based query strategy is used."""
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.query_golden_crosses_by_date.return_value = []
        
        response = handle_golden_crosses({'date': '2024-01-15'})
        
        mock_db.query_golden_crosses_by_date.assert_called_once_with('2024-01-15', None)
        assert response['statusCode'] == 200
    
    @patch('src.handlers.golden_crosses.DynamoDBClient')
    def test_validation_error(self, mock_db_class):
        """Test validation errors return 400."""
        response = handle_golden_crosses({'min_green': '150'})
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'details' in body
    
    @patch('src.handlers.golden_crosses.DynamoDBClient')
    def test_dynamodb_throttling_error(self, mock_db_class):
        """Test DynamoDB throttling returns 503."""
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.scan_golden_crosses.side_effect = ClientError(
            {'Error': {'Code': 'ProvisionedThroughputExceededException', 'Message': 'Throttled'}},
            'Scan'
        )
        
        response = handle_golden_crosses({})
        
        assert response['statusCode'] == 503
        body = json.loads(response['body'])
        assert 'error' in body


class TestStockPriceHandler:
    """Tests for stock price handler."""
    
    @patch('src.handlers.stock_price.DynamoDBClient')
    def test_symbol_found(self, mock_db_class):
        """Test successful stock price retrieval."""
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.get_stock_price.return_value = {
            'symbol': 'AAPL.US',
            'market_code': 'US',
            'prices': [
                {'date': '2024-01-15', 'close': 150.0}
            ]
        }
        
        response = handle_stock_price('AAPL.US', {})
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['data']['symbol'] == 'AAPL.US'
    
    @patch('src.handlers.stock_price.DynamoDBClient')
    def test_symbol_not_found(self, mock_db_class):
        """Test 404 when symbol not found."""
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.get_stock_price.return_value = None
        
        response = handle_stock_price('NONEXISTENT.US', {})
        
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert 'error' in body
    
    @patch('src.handlers.stock_price.DynamoDBClient')
    def test_date_range_filtering(self, mock_db_class):
        """Test date range filtering."""
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.get_stock_price.return_value = {
            'symbol': 'AAPL.US',
            'prices': [
                {'date': '2024-01-10', 'close': 145.0},
                {'date': '2024-01-15', 'close': 150.0},
                {'date': '2024-01-20', 'close': 155.0}
            ]
        }
        
        response = handle_stock_price('AAPL.US', {
            'start_date': '2024-01-12',
            'end_date': '2024-01-18'
        })
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        # Only 2024-01-15 should be in range
        assert len(body['data']['prices']) == 1
        assert body['data']['prices'][0]['date'] == '2024-01-15'
    
    @patch('src.handlers.stock_price.DynamoDBClient')
    def test_limit_applied(self, mock_db_class):
        """Test limit parameter."""
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.get_stock_price.return_value = {
            'symbol': 'AAPL.US',
            'prices': [
                {'date': '2024-01-10', 'close': 145.0},
                {'date': '2024-01-15', 'close': 150.0},
                {'date': '2024-01-20', 'close': 155.0}
            ]
        }
        
        response = handle_stock_price('AAPL.US', {'limit': '2'})
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        # Should return 2 most recent records
        assert len(body['data']['prices']) == 2
    
    def test_invalid_symbol(self):
        """Test invalid symbol returns 400."""
        response = handle_stock_price('AAPL', {})
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body


class TestOpenAISummaryHandler:
    """Tests for OpenAI summary handler."""
    
    @patch('src.handlers.openai_summary.get_openai_api_key')
    @patch('src.handlers.openai_summary.openai.ChatCompletion.create')
    def test_successful_summary_generation(self, mock_chat_completion, mock_get_api_key):
        """Test successful OpenAI summary generation."""
        mock_get_api_key.return_value = 'test-api-key'
        
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Apple Inc. (AAPL) analysis..."
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 200
        mock_response.usage.total_tokens = 300
        mock_chat_completion.return_value = mock_response
        
        response = handle_openai_summary({'symbol': 'AAPL.US'})
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['data']['symbol'] == 'AAPL.US'
        assert body['data']['analysis_type'] == 'news'
        assert body['data']['model'] == 'gpt-3.5-turbo'
        assert 'analysis' in body['data']
        assert 'usage' in body['data']
    
    @patch('src.handlers.openai_summary.get_openai_api_key')
    def test_missing_api_key(self, mock_get_api_key):
        """Test error when OpenAI API key is not configured."""
        mock_get_api_key.side_effect = ValueError("OPENAI_SECRET_NAME environment variable not set")
        
        response = handle_openai_summary({'symbol': 'AAPL.US'})
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'OpenAI service not configured' in body['error']
    
    def test_missing_symbol(self):
        """Test validation error when symbol is missing."""
        response = handle_openai_summary({})
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'details' in body
    
    def test_invalid_symbol(self):
        """Test validation error for invalid symbol format."""
        response = handle_openai_summary({'symbol': 'AAPL'})
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
    
    def test_invalid_analysis_type(self):
        """Test validation error for invalid analysis type."""
        response = handle_openai_summary({
            'symbol': 'AAPL.US',
            'analysis_type': 'invalid'
        })
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
    
    @patch('src.handlers.openai_summary.get_openai_api_key')
    @patch('src.handlers.openai_summary.openai.ChatCompletion.create')
    def test_custom_parameters(self, mock_chat_completion, mock_get_api_key):
        """Test custom analysis type and model parameters."""
        mock_get_api_key.return_value = 'test-api-key'
        
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Technical analysis..."
        mock_response.usage.prompt_tokens = 150
        mock_response.usage.completion_tokens = 250
        mock_response.usage.total_tokens = 400
        mock_chat_completion.return_value = mock_response
        
        response = handle_openai_summary({
            'symbol': 'AAPL.US',
            'analysis_type': 'technical',
            'model': 'gpt-4'
        })
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['data']['analysis_type'] == 'technical'
        assert body['data']['model'] == 'gpt-4'
    
    @patch('src.handlers.openai_summary.get_openai_api_key')
    @patch('src.handlers.openai_summary.openai.ChatCompletion.create')
    def test_openai_api_error(self, mock_chat_completion, mock_get_api_key):
        """Test error handling when OpenAI API fails."""
        mock_get_api_key.return_value = 'test-api-key'
        mock_chat_completion.side_effect = Exception("API Error")
        
        response = handle_openai_summary({'symbol': 'AAPL.US'})
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'Failed to generate AI analysis' in body['error']
