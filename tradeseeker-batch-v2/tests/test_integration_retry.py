"""Integration tests for API retry behavior with mocked rate limits"""

import json
import sys
import os
import pytest
from unittest.mock import patch, Mock, call
import requests
import time

# Add lambdas to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambdas', 'downloader'))


class TestAPIRetryBehavior:
    """Integration tests for API retry logic with rate limiting"""
    
    def test_retry_on_429_rate_limit(self, full_aws_setup):
        """Test that 429 rate limit errors trigger retry with backoff"""
        # Arrange
        from handler import handler
        
        task = {
            'symbol': 'AAPL',
            'marketCode': 'US',
            'date': '2024-01-15',
            'requestId': 'AAPL-US-2024-01-15'
        }
        
        sqs = full_aws_setup['sqs']
        sqs.send_message(
            QueueUrl=full_aws_setup['main_queue_url'],
            MessageBody=json.dumps(task)
        )
        
        messages = sqs.receive_message(
            QueueUrl=full_aws_setup['main_queue_url'],
            MaxNumberOfMessages=1
        )
        
        event = {
            'Records': [{
                'messageId': messages['Messages'][0]['MessageId'],
                'receiptHandle': messages['Messages'][0]['ReceiptHandle'],
                'body': messages['Messages'][0]['Body'],
                'attributes': {},
                'messageAttributes': {},
                'md5OfBody': '',
                'eventSource': 'aws:sqs',
                'eventSourceARN': 'arn:aws:sqs:ap-southeast-1:123456789:test-queue',
                'awsRegion': 'ap-southeast-1'
            }]
        }
        
        context = Mock()
        context.aws_request_id = 'test-retry-429'
        
        os.environ['ENVIRONMENT'] = 'dev'
        os.environ['S3_BUCKET_NAME'] = full_aws_setup['bucket_name']
        os.environ['DYNAMODB_TABLE_NAME'] = full_aws_setup['table_name']
        
        # Mock API - First 2 calls return 429, third succeeds
        call_count = 0
        
        def mock_api_with_rate_limit(url, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            mock_response = Mock()
            
            if call_count <= 2:
                # Rate limit error
                mock_response.status_code = 429
                raise requests.exceptions.HTTPError(response=mock_response)
            else:
                # Success
                mock_response.raise_for_status = Mock()
                mock_response.json.return_value = [
                    {'date': '2024-01-15', 'close': 180.0, 'open': 179.0, 'high': 181.0, 'low': 178.0, 'adjusted_close': 180.0, 'volume': 1000000}
                ]
                return mock_response
        
        # Act
        with patch('downloader.requests.get', side_effect=mock_api_with_rate_limit), \
             patch('downloader.time.sleep') as mock_sleep:
            response = handler(event, context)
        
        # Assert
        assert response['batchItemFailures'] == []
        assert call_count == 3  # 2 failures + 1 success
        assert mock_sleep.call_count == 2  # Sleep after each failure
        
        # Verify exponential backoff (sleep times should increase)
        sleep_calls = [call_args[0][0] for call_args in mock_sleep.call_args_list]
        assert sleep_calls[0] < sleep_calls[1]  # Second sleep should be longer
    
    def test_retry_on_500_server_error(self, full_aws_setup):
        """Test that 500 server errors trigger retry"""
        # Arrange
        from handler import handler
        
        task = {
            'symbol': 'MSFT',
            'marketCode': 'US',
            'date': '2024-01-15',
            'requestId': 'MSFT-US-2024-01-15'
        }
        
        sqs = full_aws_setup['sqs']
        sqs.send_message(
            QueueUrl=full_aws_setup['main_queue_url'],
            MessageBody=json.dumps(task)
        )
        
        messages = sqs.receive_message(
            QueueUrl=full_aws_setup['main_queue_url'],
            MaxNumberOfMessages=1
        )
        
        event = {
            'Records': [{
                'messageId': messages['Messages'][0]['MessageId'],
                'receiptHandle': messages['Messages'][0]['ReceiptHandle'],
                'body': messages['Messages'][0]['Body'],
                'attributes': {},
                'messageAttributes': {},
                'md5OfBody': '',
                'eventSource': 'aws:sqs',
                'eventSourceARN': 'arn:aws:sqs:ap-southeast-1:123456789:test-queue',
                'awsRegion': 'ap-southeast-1'
            }]
        }
        
        context = Mock()
        context.aws_request_id = 'test-retry-500'
        
        os.environ['ENVIRONMENT'] = 'dev'
        os.environ['S3_BUCKET_NAME'] = full_aws_setup['bucket_name']
        os.environ['DYNAMODB_TABLE_NAME'] = full_aws_setup['table_name']
        
        # Mock API - First call returns 500, second succeeds
        call_count = 0
        
        def mock_api_with_server_error(url, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            mock_response = Mock()
            
            if call_count == 1:
                mock_response.status_code = 500
                raise requests.exceptions.HTTPError(response=mock_response)
            else:
                mock_response.raise_for_status = Mock()
                mock_response.json.return_value = [
                    {'date': '2024-01-15', 'close': 370.0, 'open': 369.0, 'high': 371.0, 'low': 368.0, 'adjusted_close': 370.0, 'volume': 2000000}
                ]
                return mock_response
        
        # Act
        with patch('downloader.requests.get', side_effect=mock_api_with_server_error), \
             patch('downloader.time.sleep'):
            response = handler(event, context)
        
        # Assert
        assert response['batchItemFailures'] == []
        assert call_count == 2
    
    def test_retry_on_timeout(self, full_aws_setup):
        """Test that timeout errors trigger retry"""
        # Arrange
        from handler import handler
        
        task = {
            'symbol': 'GOOGL',
            'marketCode': 'US',
            'date': '2024-01-15',
            'requestId': 'GOOGL-US-2024-01-15'
        }
        
        sqs = full_aws_setup['sqs']
        sqs.send_message(
            QueueUrl=full_aws_setup['main_queue_url'],
            MessageBody=json.dumps(task)
        )
        
        messages = sqs.receive_message(
            QueueUrl=full_aws_setup['main_queue_url'],
            MaxNumberOfMessages=1
        )
        
        event = {
            'Records': [{
                'messageId': messages['Messages'][0]['MessageId'],
                'receiptHandle': messages['Messages'][0]['ReceiptHandle'],
                'body': messages['Messages'][0]['Body'],
                'attributes': {},
                'messageAttributes': {},
                'md5OfBody': '',
                'eventSource': 'aws:sqs',
                'eventSourceARN': 'arn:aws:sqs:ap-southeast-1:123456789:test-queue',
                'awsRegion': 'ap-southeast-1'
            }]
        }
        
        context = Mock()
        context.aws_request_id = 'test-retry-timeout'
        
        os.environ['ENVIRONMENT'] = 'dev'
        os.environ['S3_BUCKET_NAME'] = full_aws_setup['bucket_name']
        os.environ['DYNAMODB_TABLE_NAME'] = full_aws_setup['table_name']
        
        # Mock API - First call times out, second succeeds
        call_count = 0
        
        def mock_api_with_timeout(url, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if call_count == 1:
                raise requests.exceptions.Timeout()
            else:
                mock_response = Mock()
                mock_response.raise_for_status = Mock()
                mock_response.json.return_value = [
                    {'date': '2024-01-15', 'close': 140.0, 'open': 139.0, 'high': 141.0, 'low': 138.0, 'adjusted_close': 140.0, 'volume': 3000000}
                ]
                return mock_response
        
        # Act
        with patch('downloader.requests.get', side_effect=mock_api_with_timeout), \
             patch('downloader.time.sleep'):
            response = handler(event, context)
        
        # Assert
        assert response['batchItemFailures'] == []
        assert call_count == 2
    
    def test_no_retry_on_404_not_found(self, full_aws_setup):
        """Test that 404 errors do NOT trigger retry (non-retriable)"""
        # Arrange
        from handler import handler
        
        task = {
            'symbol': 'INVALID',
            'marketCode': 'US',
            'date': '2024-01-15',
            'requestId': 'INVALID-US-2024-01-15'
        }
        
        sqs = full_aws_setup['sqs']
        sqs.send_message(
            QueueUrl=full_aws_setup['main_queue_url'],
            MessageBody=json.dumps(task)
        )
        
        messages = sqs.receive_message(
            QueueUrl=full_aws_setup['main_queue_url'],
            MaxNumberOfMessages=1
        )
        
        event = {
            'Records': [{
                'messageId': messages['Messages'][0]['MessageId'],
                'receiptHandle': messages['Messages'][0]['ReceiptHandle'],
                'body': messages['Messages'][0]['Body'],
                'attributes': {},
                'messageAttributes': {},
                'md5OfBody': '',
                'eventSource': 'aws:sqs',
                'eventSourceARN': 'arn:aws:sqs:ap-southeast-1:123456789:test-queue',
                'awsRegion': 'ap-southeast-1'
            }]
        }
        
        context = Mock()
        context.aws_request_id = 'test-no-retry-404'
        
        os.environ['ENVIRONMENT'] = 'dev'
        os.environ['S3_BUCKET_NAME'] = full_aws_setup['bucket_name']
        os.environ['DYNAMODB_TABLE_NAME'] = full_aws_setup['table_name']
        
        # Mock API - Always return 404
        call_count = 0
        
        def mock_api_with_404(url, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            mock_response = Mock()
            mock_response.status_code = 404
            raise requests.exceptions.HTTPError(response=mock_response)
        
        # Act
        with patch('downloader.requests.get', side_effect=mock_api_with_404), \
             patch('downloader.time.sleep') as mock_sleep:
            response = handler(event, context)
        
        # Assert
        assert len(response['batchItemFailures']) == 1
        assert call_count == 1  # No retries for 404
        assert mock_sleep.call_count == 0  # No sleep/backoff
    
    def test_max_retries_exceeded(self, full_aws_setup):
        """Test that retries stop after max attempts"""
        # Arrange
        from handler import handler
        
        task = {
            'symbol': 'AAPL',
            'marketCode': 'US',
            'date': '2024-01-15',
            'requestId': 'AAPL-US-2024-01-15'
        }
        
        sqs = full_aws_setup['sqs']
        sqs.send_message(
            QueueUrl=full_aws_setup['main_queue_url'],
            MessageBody=json.dumps(task)
        )
        
        messages = sqs.receive_message(
            QueueUrl=full_aws_setup['main_queue_url'],
            MaxNumberOfMessages=1
        )
        
        event = {
            'Records': [{
                'messageId': messages['Messages'][0]['MessageId'],
                'receiptHandle': messages['Messages'][0]['ReceiptHandle'],
                'body': messages['Messages'][0]['Body'],
                'attributes': {},
                'messageAttributes': {},
                'md5OfBody': '',
                'eventSource': 'aws:sqs',
                'eventSourceARN': 'arn:aws:sqs:ap-southeast-1:123456789:test-queue',
                'awsRegion': 'ap-southeast-1'
            }]
        }
        
        context = Mock()
        context.aws_request_id = 'test-max-retries'
        
        os.environ['ENVIRONMENT'] = 'dev'
        os.environ['S3_BUCKET_NAME'] = full_aws_setup['bucket_name']
        os.environ['DYNAMODB_TABLE_NAME'] = full_aws_setup['table_name']
        
        # Mock API - Always return 429
        call_count = 0
        
        def mock_api_always_rate_limit(url, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            mock_response = Mock()
            mock_response.status_code = 429
            raise requests.exceptions.HTTPError(response=mock_response)
        
        # Act
        with patch('downloader.requests.get', side_effect=mock_api_always_rate_limit), \
             patch('downloader.time.sleep'):
            response = handler(event, context)
        
        # Assert
        assert len(response['batchItemFailures']) == 1
        # Default max_retries is 3, so total calls = 1 initial + 3 retries = 4
        assert call_count == 4
    
    def test_exponential_backoff_with_jitter(self, full_aws_setup):
        """Test that retry delays follow exponential backoff pattern"""
        # Arrange
        from handler import handler
        
        task = {
            'symbol': 'AAPL',
            'marketCode': 'US',
            'date': '2024-01-15',
            'requestId': 'AAPL-US-2024-01-15'
        }
        
        sqs = full_aws_setup['sqs']
        sqs.send_message(
            QueueUrl=full_aws_setup['main_queue_url'],
            MessageBody=json.dumps(task)
        )
        
        messages = sqs.receive_message(
            QueueUrl=full_aws_setup['main_queue_url'],
            MaxNumberOfMessages=1
        )
        
        event = {
            'Records': [{
                'messageId': messages['Messages'][0]['MessageId'],
                'receiptHandle': messages['Messages'][0]['ReceiptHandle'],
                'body': messages['Messages'][0]['Body'],
                'attributes': {},
                'messageAttributes': {},
                'md5OfBody': '',
                'eventSource': 'aws:sqs',
                'eventSourceARN': 'arn:aws:sqs:ap-southeast-1:123456789:test-queue',
                'awsRegion': 'ap-southeast-1'
            }]
        }
        
        context = Mock()
        context.aws_request_id = 'test-backoff'
        
        os.environ['ENVIRONMENT'] = 'dev'
        os.environ['S3_BUCKET_NAME'] = full_aws_setup['bucket_name']
        os.environ['DYNAMODB_TABLE_NAME'] = full_aws_setup['table_name']
        
        # Mock API - Fail 3 times, then succeed
        call_count = 0
        
        def mock_api_with_retries(url, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            mock_response = Mock()
            
            if call_count <= 3:
                mock_response.status_code = 429
                raise requests.exceptions.HTTPError(response=mock_response)
            else:
                mock_response.raise_for_status = Mock()
                mock_response.json.return_value = [
                    {'date': '2024-01-15', 'close': 180.0, 'open': 179.0, 'high': 181.0, 'low': 178.0, 'adjusted_close': 180.0, 'volume': 1000000}
                ]
                return mock_response
        
        # Act
        with patch('downloader.requests.get', side_effect=mock_api_with_retries), \
             patch('downloader.time.sleep') as mock_sleep:
            response = handler(event, context)
        
        # Assert
        assert response['batchItemFailures'] == []
        assert call_count == 4
        assert mock_sleep.call_count == 3
        
        # Verify exponential backoff pattern
        sleep_times = [call_args[0][0] for call_args in mock_sleep.call_args_list]
        
        # Each delay should be roughly double the previous (with jitter)
        # First retry: ~0.1s, Second: ~0.2s, Third: ~0.4s
        assert sleep_times[0] < sleep_times[1]
        assert sleep_times[1] < sleep_times[2]
        
        # Verify delays are in expected range (accounting for jitter)
        assert 0.05 <= sleep_times[0] <= 0.3  # ~0.1s ± jitter
        assert 0.15 <= sleep_times[1] <= 0.5  # ~0.2s ± jitter
        assert 0.3 <= sleep_times[2] <= 1.0   # ~0.4s ± jitter
    
    def test_mixed_retriable_and_non_retriable_errors(self, full_aws_setup):
        """Test handling of both retriable and non-retriable errors in batch"""
        # Arrange
        from handler import handler
        
        tasks = [
            {'symbol': 'AAPL', 'marketCode': 'US', 'date': '2024-01-15', 'requestId': 'AAPL-US-2024-01-15'},
            {'symbol': 'INVALID', 'marketCode': 'US', 'date': '2024-01-15', 'requestId': 'INVALID-US-2024-01-15'},
            {'symbol': 'MSFT', 'marketCode': 'US', 'date': '2024-01-15', 'requestId': 'MSFT-US-2024-01-15'}
        ]
        
        sqs = full_aws_setup['sqs']
        for task in tasks:
            sqs.send_message(
                QueueUrl=full_aws_setup['main_queue_url'],
                MessageBody=json.dumps(task)
            )
        
        messages = sqs.receive_message(
            QueueUrl=full_aws_setup['main_queue_url'],
            MaxNumberOfMessages=10
        )
        
        event = {
            'Records': [
                {
                    'messageId': msg['MessageId'],
                    'receiptHandle': msg['ReceiptHandle'],
                    'body': msg['Body'],
                    'attributes': {},
                    'messageAttributes': {},
                    'md5OfBody': '',
                    'eventSource': 'aws:sqs',
                    'eventSourceARN': 'arn:aws:sqs:ap-southeast-1:123456789:test-queue',
                    'awsRegion': 'ap-southeast-1'
                }
                for msg in messages['Messages']
            ]
        }
        
        context = Mock()
        context.aws_request_id = 'test-mixed-errors'
        
        os.environ['ENVIRONMENT'] = 'dev'
        os.environ['S3_BUCKET_NAME'] = full_aws_setup['bucket_name']
        os.environ['DYNAMODB_TABLE_NAME'] = full_aws_setup['table_name']
        
        # Mock API responses
        call_counts = {'AAPL': 0, 'INVALID': 0, 'MSFT': 0}
        
        def mock_api_mixed_errors(url, *args, **kwargs):
            mock_response = Mock()
            
            if 'AAPL' in url:
                call_counts['AAPL'] += 1
                if call_counts['AAPL'] == 1:
                    # First call: rate limit (retriable)
                    mock_response.status_code = 429
                    raise requests.exceptions.HTTPError(response=mock_response)
                else:
                    # Second call: success
                    mock_response.raise_for_status = Mock()
                    mock_response.json.return_value = [
                        {'date': '2024-01-15', 'close': 180.0, 'open': 179.0, 'high': 181.0, 'low': 178.0, 'adjusted_close': 180.0, 'volume': 1000000}
                    ]
                    return mock_response
            
            elif 'INVALID' in url:
                call_counts['INVALID'] += 1
                # Always 404 (non-retriable)
                mock_response.status_code = 404
                raise requests.exceptions.HTTPError(response=mock_response)
            
            else:  # MSFT
                call_counts['MSFT'] += 1
                # Success on first try
                mock_response.raise_for_status = Mock()
                mock_response.json.return_value = [
                    {'date': '2024-01-15', 'close': 370.0, 'open': 369.0, 'high': 371.0, 'low': 368.0, 'adjusted_close': 370.0, 'volume': 2000000}
                ]
                return mock_response
        
        # Act
        with patch('downloader.requests.get', side_effect=mock_api_mixed_errors), \
             patch('downloader.time.sleep'):
            response = handler(event, context)
        
        # Assert
        assert len(response['batchItemFailures']) == 1  # Only INVALID failed
        
        # Verify retry behavior
        assert call_counts['AAPL'] == 2  # Retried once
        assert call_counts['INVALID'] == 1  # No retry for 404
        assert call_counts['MSFT'] == 1  # Success on first try
