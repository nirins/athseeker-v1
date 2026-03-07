"""Unit tests for Task Generator"""

import json
import sys
import os
import pytest
from unittest.mock import Mock, patch, MagicMock

# Add lambdas/task-generator to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambdas', 'task-generator'))
from task_generator import TaskGenerator


@pytest.fixture
def task_generator():
    """Create TaskGenerator instance with mocked AWS clients"""
    with patch('task_generator.boto3'):
        generator = TaskGenerator(
            environment='dev',
            sqs_queue_url='https://sqs.us-east-1.amazonaws.com/123456789/test-queue'
        )
        
        # Mock AWS clients
        generator.ssm = Mock()
        generator.secretsmanager = Mock()
        generator.sqs = Mock()
        
        return generator


class TestSymbolListParsing:
    """Tests for symbol list parsing and API interaction"""
    
    def test_fetch_symbol_list_success(self, task_generator):
        """Test successful symbol list fetch from EODHD API"""
        # Arrange
        market_code = 'US'
        api_token = 'test-token'
        endpoints = {
            'symbolListUrl': 'https://eodhd.com/api/exchange-symbol-list/{MARKET_CODE}',
            'stockPriceUrl': 'https://eodhd.com/api/eod/{SYMBOL}.{MARKET_CODE}'
        }
        
        expected_symbols = [
            {'Code': 'AAPL', 'Name': 'Apple Inc'},
            {'Code': 'MSFT', 'Name': 'Microsoft Corp'},
            {'Code': 'GOOGL', 'Name': 'Alphabet Inc'}
        ]
        
        with patch('task_generator.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = expected_symbols
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            # Act
            result = task_generator.fetch_symbol_list(market_code, api_token, endpoints)
            
            # Assert
            assert result == expected_symbols
            mock_get.assert_called_once()
            call_url = mock_get.call_args[0][0]
            assert market_code in call_url
            assert api_token in call_url
    
    def test_fetch_symbol_list_empty_response(self, task_generator):
        """Test handling of empty symbol list"""
        # Arrange
        market_code = 'XX'
        api_token = 'test-token'
        endpoints = {
            'symbolListUrl': 'https://eodhd.com/api/exchange-symbol-list/{MARKET_CODE}'
        }
        
        with patch('task_generator.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = []
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            # Act
            result = task_generator.fetch_symbol_list(market_code, api_token, endpoints)
            
            # Assert
            assert result == []


class TestSQSBatchCreation:
    """Tests for SQS batch message creation and sending"""
    
    def test_send_tasks_to_sqs_single_batch(self, task_generator):
        """Test sending tasks to SQS with single batch (< 10 symbols)"""
        # Arrange
        symbols = [
            {'Code': 'AAPL'},
            {'Code': 'MSFT'},
            {'Code': 'GOOGL'}
        ]
        market_code = 'US'
        date = '2024-01-15'
        
        task_generator.sqs.send_message_batch.return_value = {
            'Successful': [{'Id': f'{s["Code"]}-{market_code}-{date}'} for s in symbols],
            'Failed': []
        }
        
        # Act
        result = task_generator.send_tasks_to_sqs(symbols, market_code, date)
        
        # Assert
        assert result == 3
        assert task_generator.sqs.send_message_batch.call_count == 1
        
        # Verify message structure
        call_args = task_generator.sqs.send_message_batch.call_args
        entries = call_args[1]['Entries']
        assert len(entries) == 3
        
        # Check first entry structure
        first_entry = entries[0]
        assert 'Id' in first_entry
        assert 'MessageBody' in first_entry
        
        message = json.loads(first_entry['MessageBody'])
        assert message['symbol'] == 'AAPL'
        assert message['marketCode'] == 'US'
        assert message['date'] == '2024-01-15'
        assert message['requestId'] == 'AAPL-US-2024-01-15'
    
    def test_send_tasks_to_sqs_multiple_batches(self, task_generator):
        """Test sending tasks to SQS with multiple batches (> 10 symbols)"""
        # Arrange
        symbols = [{'Code': f'SYM{i:03d}'} for i in range(25)]
        market_code = 'US'
        date = '2024-01-15'
        
        task_generator.sqs.send_message_batch.return_value = {
            'Successful': [{'Id': 'test'}] * 10,
            'Failed': []
        }
        
        # Act
        result = task_generator.send_tasks_to_sqs(symbols, market_code, date)
        
        # Assert
        assert result == 25
        assert task_generator.sqs.send_message_batch.call_count == 3  # 10 + 10 + 5
    
    def test_send_tasks_to_sqs_with_failures(self, task_generator):
        """Test handling of partial batch failures"""
        # Arrange
        symbols = [
            {'Code': 'AAPL'},
            {'Code': 'MSFT'},
            {'Code': 'GOOGL'}
        ]
        market_code = 'US'
        date = '2024-01-15'
        
        task_generator.sqs.send_message_batch.return_value = {
            'Successful': [
                {'Id': 'AAPL-US-2024-01-15'},
                {'Id': 'GOOGL-US-2024-01-15'}
            ],
            'Failed': [
                {'Id': 'MSFT-US-2024-01-15', 'Code': 'ServiceUnavailable'}
            ]
        }
        
        # Act
        result = task_generator.send_tasks_to_sqs(symbols, market_code, date)
        
        # Assert
        assert result == 2  # Only successful messages counted
    
    def test_request_id_generation(self, task_generator):
        """Test that request IDs are deterministic and follow expected format"""
        # Arrange
        symbols = [{'Code': 'AAPL'}]
        market_code = 'US'
        date = '2024-01-15'
        
        task_generator.sqs.send_message_batch.return_value = {
            'Successful': [{'Id': 'AAPL-US-2024-01-15'}],
            'Failed': []
        }
        
        # Act
        task_generator.send_tasks_to_sqs(symbols, market_code, date)
        
        # Assert
        call_args = task_generator.sqs.send_message_batch.call_args
        entries = call_args[1]['Entries']
        
        entry = entries[0]
        assert entry['Id'] == 'AAPL-US-2024-01-15'
        
        message = json.loads(entry['MessageBody'])
        assert message['requestId'] == 'AAPL-US-2024-01-15'
