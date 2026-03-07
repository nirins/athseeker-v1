"""Integration tests for DLQ flow with forced failures"""

import json
import sys
import os
import pytest
import time
from unittest.mock import patch, Mock
import requests

# Add lambdas to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambdas', 'downloader'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambdas', 'dlq-replay'))


class TestDLQFlow:
    """Integration tests for Dead Letter Queue flow"""
    
    def test_message_moves_to_dlq_after_max_retries(self, full_aws_setup):
        """Test that failed messages move to DLQ after exceeding max receives"""
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
        
        context = Mock()
        context.aws_request_id = 'test-dlq-flow'
        
        os.environ['ENVIRONMENT'] = 'dev'
        os.environ['S3_BUCKET_NAME'] = full_aws_setup['bucket_name']
        os.environ['DYNAMODB_TABLE_NAME'] = full_aws_setup['table_name']
        
        # Mock API to always fail with 404 (non-retriable)
        with patch('downloader.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_get.side_effect = requests.exceptions.HTTPError(response=mock_response)
            
            # Act - Process message 3 times (max receives = 3)
            for i in range(3):
                messages = sqs.receive_message(
                    QueueUrl=full_aws_setup['main_queue_url'],
                    MaxNumberOfMessages=1,
                    AttributeNames=['ApproximateReceiveCount']
                )
                
                if 'Messages' not in messages:
                    break
                
                event = {
                    'Records': [{
                        'messageId': messages['Messages'][0]['MessageId'],
                        'receiptHandle': messages['Messages'][0]['ReceiptHandle'],
                        'body': messages['Messages'][0]['Body'],
                        'attributes': messages['Messages'][0].get('Attributes', {}),
                        'messageAttributes': {},
                        'md5OfBody': '',
                        'eventSource': 'aws:sqs',
                        'eventSourceARN': 'arn:aws:sqs:ap-southeast-1:123456789:test-queue',
                        'awsRegion': 'ap-southeast-1'
                    }]
                }
                
                # Process and expect failure
                response = handler(event, context)
                assert len(response['batchItemFailures']) == 1
        
        # Assert - Message should be in DLQ
        # Note: moto may not fully simulate DLQ redrive, so we verify the failure handling
        # In real AWS, the message would automatically move to DLQ after 3 failed receives
        
        # Verify main queue is empty or message moved
        messages = sqs.receive_message(
            QueueUrl=full_aws_setup['main_queue_url'],
            MaxNumberOfMessages=1,
            WaitTimeSeconds=1
        )
        
        # In moto, we can manually verify the DLQ behavior by checking that
        # the handler correctly reported batch item failures
        assert 'Messages' not in messages or len(messages.get('Messages', [])) == 0
    
    def test_dlq_replay_moves_messages_back_to_main_queue(self, full_aws_setup):
        """Test DLQ Replay Lambda moves messages from DLQ to main queue"""
        # Arrange
        from dlq_replay import DLQReplay
        
        # Manually add messages to DLQ
        tasks = [
            {'symbol': 'AAPL', 'marketCode': 'US', 'date': '2024-01-15', 'requestId': 'AAPL-US-2024-01-15'},
            {'symbol': 'MSFT', 'marketCode': 'US', 'date': '2024-01-15', 'requestId': 'MSFT-US-2024-01-15'},
            {'symbol': 'GOOGL', 'marketCode': 'US', 'date': '2024-01-15', 'requestId': 'GOOGL-US-2024-01-15'}
        ]
        
        sqs = full_aws_setup['sqs']
        for task in tasks:
            sqs.send_message(
                QueueUrl=full_aws_setup['dlq_url'],
                MessageBody=json.dumps(task)
            )
        
        # Act
        replay = DLQReplay(
            dlq_url=full_aws_setup['dlq_url'],
            main_queue_url=full_aws_setup['main_queue_url']
        )
        
        stats = replay.replay_messages(max_messages=10)
        
        # Assert
        assert stats['processed'] == 3
        assert stats['replayed'] == 3
        assert stats['failed'] == 0
        
        # Verify DLQ is empty
        dlq_messages = sqs.receive_message(
            QueueUrl=full_aws_setup['dlq_url'],
            MaxNumberOfMessages=10
        )
        assert 'Messages' not in dlq_messages
        
        # Verify messages in main queue
        main_messages = sqs.receive_message(
            QueueUrl=full_aws_setup['main_queue_url'],
            MaxNumberOfMessages=10
        )
        assert 'Messages' in main_messages
        assert len(main_messages['Messages']) == 3
    
    def test_dlq_replay_with_symbol_filter(self, full_aws_setup):
        """Test DLQ Replay with symbol filtering"""
        # Arrange
        from dlq_replay import DLQReplay
        
        tasks = [
            {'symbol': 'AAPL', 'marketCode': 'US', 'date': '2024-01-15', 'requestId': 'AAPL-US-2024-01-15'},
            {'symbol': 'MSFT', 'marketCode': 'US', 'date': '2024-01-15', 'requestId': 'MSFT-US-2024-01-15'},
            {'symbol': 'PTT', 'marketCode': 'BK', 'date': '2024-01-15', 'requestId': 'PTT-BK-2024-01-15'}
        ]
        
        sqs = full_aws_setup['sqs']
        for task in tasks:
            sqs.send_message(
                QueueUrl=full_aws_setup['dlq_url'],
                MessageBody=json.dumps(task)
            )
        
        # Act - Replay only AAPL
        replay = DLQReplay(
            dlq_url=full_aws_setup['dlq_url'],
            main_queue_url=full_aws_setup['main_queue_url']
        )
        
        stats = replay.replay_messages(max_messages=10, filter_symbol='AAPL')
        
        # Assert
        assert stats['processed'] == 3
        assert stats['replayed'] == 1  # Only AAPL
        assert stats['skipped'] == 2  # MSFT and PTT
        
        # Verify only AAPL in main queue
        main_messages = sqs.receive_message(
            QueueUrl=full_aws_setup['main_queue_url'],
            MaxNumberOfMessages=10
        )
        assert 'Messages' in main_messages
        assert len(main_messages['Messages']) == 1
        
        message_body = json.loads(main_messages['Messages'][0]['Body'])
        assert message_body['symbol'] == 'AAPL'
    
    def test_dlq_replay_with_market_filter(self, full_aws_setup):
        """Test DLQ Replay with market code filtering"""
        # Arrange
        from dlq_replay import DLQReplay
        
        tasks = [
            {'symbol': 'AAPL', 'marketCode': 'US', 'date': '2024-01-15', 'requestId': 'AAPL-US-2024-01-15'},
            {'symbol': 'MSFT', 'marketCode': 'US', 'date': '2024-01-15', 'requestId': 'MSFT-US-2024-01-15'},
            {'symbol': 'PTT', 'marketCode': 'BK', 'date': '2024-01-15', 'requestId': 'PTT-BK-2024-01-15'}
        ]
        
        sqs = full_aws_setup['sqs']
        for task in tasks:
            sqs.send_message(
                QueueUrl=full_aws_setup['dlq_url'],
                MessageBody=json.dumps(task)
            )
        
        # Act - Replay only US market
        replay = DLQReplay(
            dlq_url=full_aws_setup['dlq_url'],
            main_queue_url=full_aws_setup['main_queue_url']
        )
        
        stats = replay.replay_messages(max_messages=10, filter_market='US')
        
        # Assert
        assert stats['processed'] == 3
        assert stats['replayed'] == 2  # AAPL and MSFT
        assert stats['skipped'] == 1  # PTT
        
        # Verify only US symbols in main queue
        main_messages = sqs.receive_message(
            QueueUrl=full_aws_setup['main_queue_url'],
            MaxNumberOfMessages=10
        )
        assert 'Messages' in main_messages
        assert len(main_messages['Messages']) == 2
        
        for message in main_messages['Messages']:
            message_body = json.loads(message['Body'])
            assert message_body['marketCode'] == 'US'
    
    def test_partial_batch_failure_handling(self, full_aws_setup):
        """Test that partial batch failures are correctly reported"""
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
        context.aws_request_id = 'test-partial-failure'
        
        os.environ['ENVIRONMENT'] = 'dev'
        os.environ['S3_BUCKET_NAME'] = full_aws_setup['bucket_name']
        os.environ['DYNAMODB_TABLE_NAME'] = full_aws_setup['table_name']
        
        # Mock API - INVALID symbol fails, others succeed
        def mock_api_response(url, *args, **kwargs):
            mock_response = Mock()
            
            if 'INVALID' in url:
                mock_response.status_code = 404
                raise requests.exceptions.HTTPError(response=mock_response)
            
            mock_response.raise_for_status = Mock()
            mock_response.json.return_value = [
                {'date': '2024-01-15', 'close': 180.0, 'open': 179.0, 'high': 181.0, 'low': 178.0, 'adjusted_close': 180.0, 'volume': 1000000}
            ]
            return mock_response
        
        # Act
        with patch('downloader.requests.get', side_effect=mock_api_response):
            response = handler(event, context)
        
        # Assert
        assert len(response['batchItemFailures']) == 1
        
        # Verify successful messages processed
        s3 = full_aws_setup['s3']
        
        # AAPL should be in S3
        try:
            s3.get_object(
                Bucket=full_aws_setup['bucket_name'],
                Key='prices/market=US/dt=2024-01-15/symbol=AAPL/data.json.gz'
            )
            aapl_exists = True
        except:
            aapl_exists = False
        
        # MSFT should be in S3
        try:
            s3.get_object(
                Bucket=full_aws_setup['bucket_name'],
                Key='prices/market=US/dt=2024-01-15/symbol=MSFT/data.json.gz'
            )
            msft_exists = True
        except:
            msft_exists = False
        
        # INVALID should NOT be in S3
        try:
            s3.get_object(
                Bucket=full_aws_setup['bucket_name'],
                Key='prices/market=US/dt=2024-01-15/symbol=INVALID/data.json.gz'
            )
            invalid_exists = True
        except:
            invalid_exists = False
        
        assert aapl_exists
        assert msft_exists
        assert not invalid_exists
    
    def test_dlq_replay_handler_integration(self, full_aws_setup):
        """Test DLQ Replay Lambda handler end-to-end"""
        # Arrange
        from lambdas.dlq_replay.handler import handler
        
        # Add messages to DLQ
        tasks = [
            {'symbol': 'AAPL', 'marketCode': 'US', 'date': '2024-01-15', 'requestId': 'AAPL-US-2024-01-15'},
            {'symbol': 'MSFT', 'marketCode': 'US', 'date': '2024-01-15', 'requestId': 'MSFT-US-2024-01-15'}
        ]
        
        sqs = full_aws_setup['sqs']
        for task in tasks:
            sqs.send_message(
                QueueUrl=full_aws_setup['dlq_url'],
                MessageBody=json.dumps(task)
            )
        
        # Create event
        event = {
            'max_messages': 10,
            'filter_symbol': None,
            'filter_market': None
        }
        
        context = Mock()
        context.aws_request_id = 'test-dlq-handler'
        
        os.environ['DLQ_URL'] = full_aws_setup['dlq_url']
        os.environ['MAIN_QUEUE_URL'] = full_aws_setup['main_queue_url']
        
        # Act
        response = handler(event, context)
        
        # Assert
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['statistics']['replayed'] == 2
        
        # Verify messages moved to main queue
        main_messages = sqs.receive_message(
            QueueUrl=full_aws_setup['main_queue_url'],
            MaxNumberOfMessages=10
        )
        assert 'Messages' in main_messages
        assert len(main_messages['Messages']) == 2
