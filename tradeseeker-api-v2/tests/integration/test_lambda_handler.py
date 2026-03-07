"""Integration tests for Lambda handler."""

import json
import pytest
from unittest.mock import patch, MagicMock

from src.lambda_handler import lambda_handler


class MockContext:
    """Mock Lambda context object."""
    def __init__(self):
        self.request_id = 'test-request-id'
        self.function_name = 'test-function'


class TestLambdaHandler:
    """Integration tests for lambda_handler function."""
    
    @patch('src.lambda_handler.route_request')
    def test_golden_crosses_request(self, mock_route):
        """Test complete golden crosses request flow."""
        mock_route.return_value = {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'data': []})
        }
        
        event = {
            'httpMethod': 'GET',
            'path': '/golden-crosses',
            'queryStringParameters': {'min_green': '80'},
            'pathParameters': None
        }
        context = MockContext()
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 200
        mock_route.assert_called_once_with('GET', '/golden-crosses', {'min_green': '80'}, {})
    
    @patch('src.lambda_handler.route_request')
    def test_stock_price_request(self, mock_route):
        """Test complete stock price request flow."""
        mock_route.return_value = {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'data': {'symbol': 'AAPL.US'}})
        }
        
        event = {
            'httpMethod': 'GET',
            'path': '/stocks/AAPL.US',
            'queryStringParameters': None,
            'pathParameters': {'symbol': 'AAPL.US'}
        }
        context = MockContext()
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 200
        mock_route.assert_called_once()
    
    def test_missing_http_method(self):
        """Test error when httpMethod is missing."""
        event = {
            'path': '/golden-crosses',
            'queryStringParameters': None
        }
        context = MockContext()
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
    
    def test_missing_path(self):
        """Test error when path is missing."""
        event = {
            'httpMethod': 'GET',
            'queryStringParameters': None
        }
        context = MockContext()
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
    
    @patch('src.lambda_handler.route_request')
    def test_null_query_parameters(self, mock_route):
        """Test handling of null queryStringParameters."""
        mock_route.return_value = {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'data': []})
        }
        
        event = {
            'httpMethod': 'GET',
            'path': '/golden-crosses',
            'queryStringParameters': None,
            'pathParameters': None
        }
        context = MockContext()
        
        response = lambda_handler(event, context)
        
        # Should convert None to empty dict
        mock_route.assert_called_once_with('GET', '/golden-crosses', {}, {})
        assert response['statusCode'] == 200
    
    @patch('src.lambda_handler.route_request')
    def test_unhandled_exception(self, mock_route):
        """Test unhandled exception returns 500."""
        mock_route.side_effect = Exception("Unexpected error")
        
        event = {
            'httpMethod': 'GET',
            'path': '/golden-crosses',
            'queryStringParameters': None,
            'pathParameters': None
        }
        context = MockContext()
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'error' in body
        assert body['error'] == "Internal server error"
