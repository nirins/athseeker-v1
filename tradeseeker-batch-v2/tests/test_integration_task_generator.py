"""Integration tests for EventBridge → Task Generator → SQS flow"""

import json
import sys
import os
import pytest
from unittest.mock import patch, Mock

# Add lambdas to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambdas', 'task-generator'))


class TestTaskGeneratorIntegration:
    """End-to-end integration tests for Task Generator Lambda"""
    
    def test_eventbridge_to_task_generator_to_sqs(self, full_aws_setup):
        """Test complete flow: EventBridge event → Task Generator → SQS messages"""
        # Arrange
        from handler import handler
        
        # Mock EventBridge event
        event = {
            'date': '2024-01-15',
            'source': 'aws.scheduler',
            'detail-type': 'Scheduled Event'
        }
        
        # Mock Lambda context
        context = Mock()
        context.aws_request_id = 'test-request-123'
        context.function_name = 'test-task-generator'
        
        # Mock EODHD API responses
        us_symbols = [
            {'Code': 'AAPL', 'Name': 'Apple Inc'},
            {'Code': 'MSFT', 'Name': 'Microsoft Corp'},
            {'Code': 'GOOGL', 'Name': 'Alphabet Inc'}
        ]
        
        bk_symbols = [
            {'Code': 'PTT', 'Name': 'PTT Public Company Limited'},
            {'Code': 'AOT', 'Name': 'Airports of Thailand'}
        ]
        
        def mock_api_response(url, *args, **kwargs):
            """Mock EODHD API responses based on URL"""
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            
            if 'US' in url:
                mock_response.json.return_value = us_symbols
            elif 'BK' in url:
                mock_response.json.return_value = bk_symbols
            else:
                mock_response.json.return_value = []
            
            return mock_response
        
        # Set environment variables
        os.environ['ENVIRONMENT'] = 'dev'
        os.environ['SQS_QUEUE_URL'] = full_aws_setup['main_queue_url']
        
        # Act
        with patch('task_generator.requests.get', side_effect=mock_api_response):
            response = handler(event, context)
        
        # Assert
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['date'] == '2024-01-15'
        assert body['totalTasks'] == 5  # 3 US + 2 BK symbols
        
        # Verify messages in SQS
        sqs = full_aws_setup['sqs']
        messages = sqs.receive_message(
            QueueUrl=full_aws_setup['main_queue_url'],
            MaxNumberOfMessages=10
        )
        
        assert 'Messages' in messages
        assert len(messages['Messages']) == 5
        
        # Verify message structure
        first_message = json.loads(messages['Messages'][0]['Body'])
        assert 'symbol' in first_message
        assert 'marketCode' in first_message
        assert 'date' in first_message
        assert 'requestId' in first_message
        assert first_message['date'] == '2024-01-15'
    
    def test_task_generator_with_default_date(self, full_aws_setup):
        """Test Task Generator uses current date when not provided in event"""
        # Arrange
        from handler import handler
        from datetime import datetime
        
        event = {}  # No date provided
        context = Mock()
        context.aws_request_id = 'test-request-456'
        
        # Mock API to return empty list
        with patch('task_generator.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = []
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            os.environ['ENVIRONMENT'] = 'dev'
            os.environ['SQS_QUEUE_URL'] = full_aws_setup['main_queue_url']
            
            # Act
            response = handler(event, context)
        
        # Assert
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        
        # Should use current date
        expected_date = datetime.now().strftime('%Y-%m-%d')
        assert body['date'] == expected_date
    
    def test_task_generator_idempotency(self, full_aws_setup):
        """Test that running task generator twice produces consistent request IDs"""
        # Arrange
        from handler import handler
        
        event = {'date': '2024-01-15'}
        context = Mock()
        context.aws_request_id = 'test-request-789'
        
        symbols = [
            {'Code': 'AAPL', 'Name': 'Apple Inc'},
            {'Code': 'MSFT', 'Name': 'Microsoft Corp'}
        ]
        
        with patch('task_generator.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = symbols
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            os.environ['ENVIRONMENT'] = 'dev'
            os.environ['SQS_QUEUE_URL'] = full_aws_setup['main_queue_url']
            
            # Act - Run twice
            handler(event, context)
            handler(event, context)
        
        # Assert - Collect all messages
        sqs = full_aws_setup['sqs']
        all_messages = []
        
        while True:
            response = sqs.receive_message(
                QueueUrl=full_aws_setup['main_queue_url'],
                MaxNumberOfMessages=10
            )
            if 'Messages' not in response:
                break
            all_messages.extend(response['Messages'])
        
        # Should have 8 messages (2 symbols × 2 markets × 2 runs)
        assert len(all_messages) == 8
        
        # Verify request IDs are deterministic by grouping by requestId
        request_ids = [json.loads(msg['Body'])['requestId'] for msg in all_messages]
        unique_request_ids = set(request_ids)
        
        # Should have 4 unique request IDs (2 symbols × 2 markets)
        assert len(unique_request_ids) == 4
        
        # Each request ID should appear exactly twice (once per run)
        for req_id in unique_request_ids:
            assert request_ids.count(req_id) == 2
    
    def test_task_generator_handles_multiple_markets(self, full_aws_setup):
        """Test Task Generator processes multiple markets correctly"""
        # Arrange
        from handler import handler
        
        event = {'date': '2024-01-15'}
        context = Mock()
        context.aws_request_id = 'test-request-multi'
        
        us_symbols = [{'Code': 'AAPL'}, {'Code': 'MSFT'}]
        bk_symbols = [{'Code': 'PTT'}]
        
        def mock_api_response(url, *args, **kwargs):
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            
            if 'US' in url:
                mock_response.json.return_value = us_symbols
            elif 'BK' in url:
                mock_response.json.return_value = bk_symbols
            else:
                mock_response.json.return_value = []
            
            return mock_response
        
        os.environ['ENVIRONMENT'] = 'dev'
        os.environ['SQS_QUEUE_URL'] = full_aws_setup['main_queue_url']
        
        # Act
        with patch('task_generator.requests.get', side_effect=mock_api_response):
            response = handler(event, context)
        
        # Assert
        body = json.loads(response['body'])
        assert body['totalTasks'] == 3  # 2 US + 1 BK
        
        # Verify market codes in messages
        sqs = full_aws_setup['sqs']
        messages = sqs.receive_message(
            QueueUrl=full_aws_setup['main_queue_url'],
            MaxNumberOfMessages=10
        )
        
        market_codes = [json.loads(msg['Body'])['marketCode'] for msg in messages['Messages']]
        assert 'US' in market_codes
        assert 'BK' in market_codes
    
    def test_task_generator_handles_api_failure(self, full_aws_setup):
        """Test Task Generator handles EODHD API failures gracefully"""
        # Arrange
        from handler import handler
        import requests
        
        event = {'date': '2024-01-15'}
        context = Mock()
        context.aws_request_id = 'test-request-fail'
        
        os.environ['ENVIRONMENT'] = 'dev'
        os.environ['SQS_QUEUE_URL'] = full_aws_setup['main_queue_url']
        
        # Mock API to raise error
        with patch('task_generator.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.HTTPError("API Error")
            
            # Act - Task generator handles errors gracefully and continues
            response = handler(event, context)
        
        # Assert - Should complete with 0 tasks (all markets failed)
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['totalTasks'] == 0
