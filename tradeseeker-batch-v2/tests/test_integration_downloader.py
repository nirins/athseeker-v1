"""Integration tests for SQS → Downloader → S3 + DynamoDB flow"""

import json
import gzip
import sys
import os
import pytest
from unittest.mock import patch, Mock
from decimal import Decimal

# Add lambdas to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambdas', 'downloader'))


class TestDownloaderIntegration:
    """End-to-end integration tests for Downloader Lambda"""
    
    def test_sqs_to_downloader_to_s3_and_dynamodb(self, full_aws_setup):
        """Test complete flow: SQS message → Downloader → S3 + DynamoDB"""
        # Arrange
        from handler import handler
        
        # Create SQS message
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
        
        # Receive message to create SQS event
        messages = sqs.receive_message(
            QueueUrl=full_aws_setup['main_queue_url'],
            MaxNumberOfMessages=1
        )
        
        # Create SQS event
        event = {
            'Records': [
                {
                    'messageId': messages['Messages'][0]['MessageId'],
                    'receiptHandle': messages['Messages'][0]['ReceiptHandle'],
                    'body': messages['Messages'][0]['Body'],
                    'attributes': {},
                    'messageAttributes': {},
                    'md5OfBody': '',
                    'eventSource': 'aws:sqs',
                    'eventSourceARN': 'arn:aws:sqs:ap-southeast-1:123456789:test-queue',
                    'awsRegion': 'ap-southeast-1'
                }
            ]
        }
        
        # Mock Lambda context
        context = Mock()
        context.aws_request_id = 'test-request-downloader-123'
        
        # Mock EODHD API response
        api_response = [
            {
                'date': '2024-01-10',
                'open': 180.0,
                'high': 182.0,
                'low': 179.0,
                'close': 181.0,
                'adjusted_close': 181.0,
                'volume': 50000000
            },
            {
                'date': '2024-01-11',
                'open': 181.0,
                'high': 183.0,
                'low': 180.0,
                'close': 182.0,
                'adjusted_close': 182.0,
                'volume': 51000000
            },
            {
                'date': '2024-01-12',
                'open': 182.0,
                'high': 184.0,
                'low': 181.0,
                'close': 183.0,
                'adjusted_close': 183.0,
                'volume': 52000000
            },
            {
                'date': '2024-01-13',
                'open': 183.0,
                'high': 185.0,
                'low': 182.0,
                'close': 184.0,
                'adjusted_close': 184.0,
                'volume': 53000000
            },
            {
                'date': '2024-01-14',
                'open': 184.0,
                'high': 186.0,
                'low': 183.0,
                'close': 185.0,
                'adjusted_close': 185.0,
                'volume': 54000000
            },
            {
                'date': '2024-01-15',
                'open': 185.0,
                'high': 187.0,
                'low': 184.0,
                'close': 186.0,
                'adjusted_close': 186.0,
                'volume': 55000000
            }
        ]
        
        # Set environment variables
        os.environ['ENVIRONMENT'] = 'dev'
        os.environ['S3_BUCKET_NAME'] = full_aws_setup['bucket_name']
        os.environ['DYNAMODB_TABLE_NAME'] = full_aws_setup['table_name']
        
        # Act
        with patch('downloader.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = api_response
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            response = handler(event, context)
        
        # Assert
        assert response['batchItemFailures'] == []
        
        # Verify S3 upload
        s3 = full_aws_setup['s3']
        expected_key = 'prices/market=US/dt=2024-01-15/symbol=AAPL/data.json.gz'
        
        s3_object = s3.get_object(
            Bucket=full_aws_setup['bucket_name'],
            Key=expected_key
        )
        
        # Decompress and verify content
        compressed_data = s3_object['Body'].read()
        decompressed_data = gzip.decompress(compressed_data).decode('utf-8')
        stored_data = json.loads(decompressed_data)
        
        assert stored_data == api_response
        assert s3_object['ContentEncoding'] == 'gzip'
        assert s3_object['ContentType'] == 'application/json'
        
        # Verify DynamoDB record
        table = full_aws_setup['table']
        item = table.get_item(Key={'symbol': 'AAPL.US'})
        
        assert 'Item' in item
        assert item['Item']['symbol'] == 'AAPL.US'
        assert item['Item']['market_code'] == 'US'
        assert 'prices' in item['Item']
        assert 'moving_averages' in item['Item']
        assert len(item['Item']['prices']) == 6
        assert len(item['Item']['moving_averages']) == 6
        
        # Verify EMA calculations exist
        ma = item['Item']['moving_averages'][-1]  # Last record
        assert 'ema_7' in ma
        assert 'ema_30' in ma
        assert 'ema_50' in ma
        assert 'ema_200' in ma
    
    def test_downloader_batch_processing(self, full_aws_setup):
        """Test Downloader processes multiple SQS messages in batch"""
        # Arrange
        from handler import handler
        
        tasks = [
            {'symbol': 'AAPL', 'marketCode': 'US', 'date': '2024-01-15', 'requestId': 'AAPL-US-2024-01-15'},
            {'symbol': 'MSFT', 'marketCode': 'US', 'date': '2024-01-15', 'requestId': 'MSFT-US-2024-01-15'},
            {'symbol': 'GOOGL', 'marketCode': 'US', 'date': '2024-01-15', 'requestId': 'GOOGL-US-2024-01-15'}
        ]
        
        # Send messages to SQS
        sqs = full_aws_setup['sqs']
        for task in tasks:
            sqs.send_message(
                QueueUrl=full_aws_setup['main_queue_url'],
                MessageBody=json.dumps(task)
            )
        
        # Receive messages
        messages = sqs.receive_message(
            QueueUrl=full_aws_setup['main_queue_url'],
            MaxNumberOfMessages=10
        )
        
        # Create SQS event with multiple records
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
        context.aws_request_id = 'test-batch-processing'
        
        # Mock API responses
        def mock_api_response(url, *args, **kwargs):
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            
            # Return different data based on symbol
            if 'AAPL' in url:
                data = [{'date': '2024-01-15', 'close': 180.0, 'open': 179.0, 'high': 181.0, 'low': 178.0, 'adjusted_close': 180.0, 'volume': 1000000}]
            elif 'MSFT' in url:
                data = [{'date': '2024-01-15', 'close': 370.0, 'open': 369.0, 'high': 371.0, 'low': 368.0, 'adjusted_close': 370.0, 'volume': 2000000}]
            else:  # GOOGL
                data = [{'date': '2024-01-15', 'close': 140.0, 'open': 139.0, 'high': 141.0, 'low': 138.0, 'adjusted_close': 140.0, 'volume': 3000000}]
            
            mock_response.json.return_value = data
            return mock_response
        
        os.environ['ENVIRONMENT'] = 'dev'
        os.environ['S3_BUCKET_NAME'] = full_aws_setup['bucket_name']
        os.environ['DYNAMODB_TABLE_NAME'] = full_aws_setup['table_name']
        
        # Act
        with patch('downloader.requests.get', side_effect=mock_api_response):
            response = handler(event, context)
        
        # Assert
        assert response['batchItemFailures'] == []
        
        # Verify all 3 symbols in S3
        s3 = full_aws_setup['s3']
        for symbol in ['AAPL', 'MSFT', 'GOOGL']:
            key = f'prices/market=US/dt=2024-01-15/symbol={symbol}/data.json.gz'
            s3_object = s3.get_object(
                Bucket=full_aws_setup['bucket_name'],
                Key=key
            )
            assert s3_object is not None
        
        # Verify all 3 symbols in DynamoDB
        table = full_aws_setup['table']
        for symbol in ['AAPL', 'MSFT', 'GOOGL']:
            item = table.get_item(Key={'symbol': f'{symbol}.US'})
            assert 'Item' in item
    
    def test_downloader_s3_key_structure(self, full_aws_setup):
        """Test S3 key follows correct partitioned structure"""
        # Arrange
        from handler import handler
        
        task = {
            'symbol': 'PTT',
            'marketCode': 'BK',
            'date': '2024-01-15',
            'requestId': 'PTT-BK-2024-01-15'
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
        context.aws_request_id = 'test-s3-key'
        
        api_response = [
            {'date': '2024-01-15', 'close': 35.0, 'open': 34.5, 'high': 35.5, 'low': 34.0, 'adjusted_close': 35.0, 'volume': 10000000}
        ]
        
        os.environ['ENVIRONMENT'] = 'dev'
        os.environ['S3_BUCKET_NAME'] = full_aws_setup['bucket_name']
        os.environ['DYNAMODB_TABLE_NAME'] = full_aws_setup['table_name']
        
        # Act
        with patch('downloader.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = api_response
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            handler(event, context)
        
        # Assert - Verify key structure
        s3 = full_aws_setup['s3']
        expected_key = 'prices/market=BK/dt=2024-01-15/symbol=PTT/data.json.gz'
        
        s3_object = s3.get_object(
            Bucket=full_aws_setup['bucket_name'],
            Key=expected_key
        )
        
        assert s3_object is not None
    
    def test_downloader_dynamodb_structure(self, full_aws_setup):
        """Test DynamoDB item has correct nested list structure"""
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
        context.aws_request_id = 'test-dynamodb-structure'
        
        # Create multi-day data for EMA calculation
        api_response = [
            {'date': f'2024-01-{i:02d}', 'close': 180.0 + i, 'open': 179.0 + i, 'high': 181.0 + i, 'low': 178.0 + i, 'adjusted_close': 180.0 + i, 'volume': 1000000 + i * 10000}
            for i in range(1, 16)
        ]
        
        os.environ['ENVIRONMENT'] = 'dev'
        os.environ['S3_BUCKET_NAME'] = full_aws_setup['bucket_name']
        os.environ['DYNAMODB_TABLE_NAME'] = full_aws_setup['table_name']
        
        # Act
        with patch('downloader.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = api_response
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            handler(event, context)
        
        # Assert
        table = full_aws_setup['table']
        item = table.get_item(Key={'symbol': 'AAPL.US'})
        
        assert 'Item' in item
        db_item = item['Item']
        
        # Verify structure
        assert 'symbol' in db_item
        assert 'market_code' in db_item
        assert 'prices' in db_item
        assert 'moving_averages' in db_item
        assert 'updated_at' in db_item
        
        # Verify prices list
        assert len(db_item['prices']) == 15
        first_price = db_item['prices'][0]
        assert 'date' in first_price
        assert 'open' in first_price
        assert 'high' in first_price
        assert 'low' in first_price
        assert 'close' in first_price
        assert 'adjusted_close' in first_price
        assert 'volume' in first_price
        
        # Verify moving averages list
        assert len(db_item['moving_averages']) == 15
        last_ma = db_item['moving_averages'][-1]
        assert 'date' in last_ma
        assert 'ema_7' in last_ma
        assert 'ema_30' in last_ma
        assert 'ema_50' in last_ma
        assert 'ema_200' in last_ma
        
        # Verify EMA 7 is calculated (need at least 7 data points)
        ma_with_ema7 = db_item['moving_averages'][6]  # 7th record (index 6)
        assert ma_with_ema7['ema_7'] is not None
