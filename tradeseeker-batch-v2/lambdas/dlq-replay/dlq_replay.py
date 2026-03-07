# DLQ Replay Logic
# Handles reading messages from DLQ, filtering, and re-enqueueing to main queue

import json
import boto3
from typing import Dict, List, Optional
import logging

logger = logging.getLogger()


class DLQReplay:
    """Handles DLQ message replay operations"""
    
    def __init__(self, dlq_url: str, main_queue_url: str):
        """
        Initialize DLQ replay handler
        
        Args:
            dlq_url: URL of the dead letter queue
            main_queue_url: URL of the main processing queue
        """
        self.dlq_url = dlq_url
        self.main_queue_url = main_queue_url
        self.sqs = boto3.client('sqs')
    
    def replay_messages(
        self,
        max_messages: int = 10,
        filter_symbol: Optional[str] = None,
        filter_market: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Replay messages from DLQ to main queue with optional filtering
        
        Args:
            max_messages: Maximum number of messages to replay
            filter_symbol: Optional symbol filter (e.g., "AAPL")
            filter_market: Optional market code filter (e.g., "US")
            
        Returns:
            Dictionary with replay statistics:
                - received: Total messages received from DLQ
                - filtered: Messages that passed filters
                - replayed: Messages successfully re-enqueued
                - deleted: Messages successfully deleted from DLQ
                - failed: Messages that failed to replay
        """
        stats = {
            'received': 0,
            'filtered': 0,
            'replayed': 0,
            'deleted': 0,
            'failed': 0
        }
        
        messages_to_process = max_messages
        
        while messages_to_process > 0:
            # Receive messages from DLQ (up to 10 at a time)
            batch_size = min(10, messages_to_process)
            
            response = self.sqs.receive_message(
                QueueUrl=self.dlq_url,
                MaxNumberOfMessages=batch_size,
                WaitTimeSeconds=5,  # Short poll
                AttributeNames=['All'],
                MessageAttributeNames=['All']
            )
            
            messages = response.get('Messages', [])
            
            if not messages:
                logger.info("No more messages in DLQ")
                break
            
            stats['received'] += len(messages)
            logger.info(f"Received {len(messages)} messages from DLQ")
            
            # Process each message
            for message in messages:
                try:
                    # Parse message body
                    body = json.loads(message['Body'])
                    
                    # Apply filters
                    if self._should_replay(body, filter_symbol, filter_market):
                        stats['filtered'] += 1
                        
                        # Re-enqueue to main queue
                        self._send_to_main_queue(message)
                        stats['replayed'] += 1
                        
                        # Delete from DLQ
                        self._delete_from_dlq(message)
                        stats['deleted'] += 1
                        
                        logger.info(f"Replayed message: {body.get('symbol', 'unknown')}")
                    else:
                        logger.info(f"Skipped message (filtered): {body.get('symbol', 'unknown')}")
                
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}", exc_info=True)
                    stats['failed'] += 1
            
            messages_to_process -= len(messages)
        
        return stats
    
    def _should_replay(
        self,
        message_body: Dict,
        filter_symbol: Optional[str],
        filter_market: Optional[str]
    ) -> bool:
        """
        Check if message should be replayed based on filters
        
        Args:
            message_body: Parsed message body
            filter_symbol: Optional symbol filter
            filter_market: Optional market code filter
            
        Returns:
            True if message should be replayed, False otherwise
        """
        # If no filters, replay all messages
        if not filter_symbol and not filter_market:
            return True
        
        # Check symbol filter
        if filter_symbol:
            symbol = message_body.get('symbol', '')
            if symbol != filter_symbol:
                return False
        
        # Check market filter
        if filter_market:
            market_code = message_body.get('marketCode', '')
            if market_code != filter_market:
                return False
        
        return True
    
    def _send_to_main_queue(self, message: Dict) -> None:
        """
        Send message to main queue
        
        Args:
            message: SQS message to re-enqueue
        """
        # Preserve original message body and attributes
        send_params = {
            'QueueUrl': self.main_queue_url,
            'MessageBody': message['Body']
        }
        
        # Preserve message attributes if present
        if 'MessageAttributes' in message:
            send_params['MessageAttributes'] = message['MessageAttributes']
        
        self.sqs.send_message(**send_params)
        logger.debug(f"Sent message to main queue: {message['MessageId']}")
    
    def _delete_from_dlq(self, message: Dict) -> None:
        """
        Delete message from DLQ
        
        Args:
            message: SQS message to delete
        """
        self.sqs.delete_message(
            QueueUrl=self.dlq_url,
            ReceiptHandle=message['ReceiptHandle']
        )
        logger.debug(f"Deleted message from DLQ: {message['MessageId']}")
