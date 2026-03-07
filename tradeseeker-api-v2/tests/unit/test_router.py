"""Unit tests for router module."""

import json
import pytest
from unittest.mock import patch, MagicMock
from src.router import route_request


class TestRouteRequest:
    """Tests for route_request function."""
    
    @patch('src.router.handle_golden_crosses')
    def test_route_golden_crosses(self, mock_handler):
        """Test routing to golden crosses handler."""
        mock_handler.return_value = {'statusCode': 200, 'body': '{"data": []}'}
        
        response = route_request('GET', '/golden-crosses', {}, {})
        
        mock_handler.assert_called_once_with({})
        assert response['statusCode'] == 200
    
    @patch('src.router.handle_stock_price')
    def test_route_stock_price(self, mock_handler):
        """Test routing to stock price handler."""
        mock_handler.return_value = {'statusCode': 200, 'body': '{"data": {}}'}
        
        response = route_request('GET', '/stocks/AAPL.US', {}, {})
        
        mock_handler.assert_called_once_with('AAPL.US', {})
        assert response['statusCode'] == 200
    
    @patch('src.router.handle_openai_summary')
    def test_route_openai_summary(self, mock_handler):
        """Test routing to OpenAI summary handler."""
        mock_handler.return_value = {'statusCode': 200, 'body': '{"data": {}}'}
        
        response = route_request('GET', '/openai-summary', {'symbol': 'AAPL.US'}, {})
        
        mock_handler.assert_called_once_with({'symbol': 'AAPL.US'})
        assert response['statusCode'] == 200
    
    def test_route_unknown_path(self):
        """Test routing unknown path returns 404."""
        response = route_request('GET', '/unknown', {}, {})
        
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert 'error' in body
    
    def test_route_unsupported_method(self):
        """Test unsupported HTTP method returns 405."""
        response = route_request('POST', '/golden-crosses', {}, {})
        
        assert response['statusCode'] == 405
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'POST' in body['error']
    
    def test_route_with_trailing_slash(self):
        """Test path normalization with trailing slash."""
        with patch('src.router.handle_golden_crosses') as mock_handler:
            mock_handler.return_value = {'statusCode': 200, 'body': '{"data": []}'}
            
            response = route_request('GET', '/golden-crosses/', {}, {})
            
            mock_handler.assert_called_once()
            assert response['statusCode'] == 200
