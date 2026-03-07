"""Unit tests for formatters module."""

import json
import pytest
from src.formatters import success_response, error_response


class TestSuccessResponse:
    """Tests for success_response function."""
    
    def test_basic_success_response(self):
        """Test basic success response structure."""
        data = [{"symbol": "AAPL.US", "cross_date": "2024-01-15"}]
        response = success_response(data)
        
        assert response['statusCode'] == 200
        assert response['headers']['Content-Type'] == 'application/json'
        assert response['headers']['Access-Control-Allow-Origin'] == '*'
        
        body = json.loads(response['body'])
        assert 'data' in body
        assert body['data'] == data
    
    def test_custom_status_code(self):
        """Test success response with custom status code."""
        response = success_response({"result": "created"}, status_code=201)
        assert response['statusCode'] == 201
    
    def test_cors_headers(self):
        """Test CORS headers are present."""
        response = success_response([])
        headers = response['headers']
        
        assert 'Access-Control-Allow-Origin' in headers
        assert 'Access-Control-Allow-Methods' in headers
        assert 'Access-Control-Allow-Headers' in headers


class TestErrorResponse:
    """Tests for error_response function."""
    
    def test_basic_error_response(self):
        """Test basic error response structure."""
        response = error_response("Invalid parameters", 400)
        
        assert response['statusCode'] == 400
        assert response['headers']['Content-Type'] == 'application/json'
        
        body = json.loads(response['body'])
        assert 'error' in body
        assert body['error'] == "Invalid parameters"
    
    def test_error_with_details(self):
        """Test error response with details array."""
        errors = ["min_green must be between 0 and 100", "market must be one of: US, BK, CC"]
        response = error_response("Invalid parameters", 400, errors)
        
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'details' in body
        assert body['details'] == errors
    
    def test_default_status_code(self):
        """Test error response with default status code."""
        response = error_response("Bad request")
        assert response['statusCode'] == 400
    
    def test_500_error(self):
        """Test 500 error response."""
        response = error_response("Internal server error", 500)
        assert response['statusCode'] == 500
        
        body = json.loads(response['body'])
        assert body['error'] == "Internal server error"
