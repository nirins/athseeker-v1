# DLQ Replay Lambda Handler
# This Lambda replays messages from the DLQ back to the main queue

import json
import os
from typing import Dict, Any, List
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Manually triggered handler to replay DLQ messages
    
    Args:
        event: Event containing optional parameters:
            - max_messages: Maximum number of messages to replay (default: 10)
            - filter_symbol: Optional symbol filter (e.g., "AAPL")
            - filter_market: Optional market code filter (e.g., "US")
        context: Lambda context object
        
    Returns:
        Response with replay statistics
    """
    try:
        # Extract parameters from event
        max_messages = event.get('max_messages', 10)
        filter_symbol = event.get('filter_symbol')
        filter_market = event.get('filter_market')
        
        logger.info(f"Starting DLQ replay with max_messages={max_messages}")
        logger.info(f"Filters: symbol={filter_symbol}, market={filter_market}")
        logger.info(f"Request ID: {context.aws_request_id}")
        
        # Import dependencies here to avoid cold start issues
        from dlq_replay import DLQReplay
        
        # Initialize DLQ replay handler
        replay = DLQReplay(
            dlq_url=os.environ['DLQ_URL'],
            main_queue_url=os.environ['MAIN_QUEUE_URL']
        )
        
        # Replay messages with optional filtering
        stats = replay.replay_messages(
            max_messages=max_messages,
            filter_symbol=filter_symbol,
            filter_market=filter_market
        )
        
        logger.info(f"Replay completed: {stats}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'DLQ replay completed',
                'statistics': stats
            })
        }
        
    except Exception as e:
        logger.error(f"Error replaying DLQ messages: {str(e)}", exc_info=True)
        raise
