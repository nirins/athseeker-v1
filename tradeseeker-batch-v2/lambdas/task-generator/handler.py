# Task Generator Lambda Handler
# This Lambda is triggered by EventBridge Scheduler to generate download tasks

import json
import os
from datetime import datetime
from typing import Dict, Any
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    EventBridge triggered handler to generate download tasks
    
    Args:
        event: EventBridge event containing optional date parameter
        context: Lambda context object
        
    Returns:
        Response with status and message count
    """
    try:
        # Extract date from event or use current date
        date = event.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        # Extract optional test parameters
        market_filter = event.get('market')  # e.g., "US"
        limit = event.get('limit')  # e.g., 100
        mode = event.get('mode')   # e.g., "watchlist"
        
        logger.info(f"Starting task generation for date: {date}")
        logger.info(f"Request ID: {context.aws_request_id}")
        
        if market_filter:
            logger.info(f"Market filter: {market_filter}")
        if limit:
            logger.info(f"Symbol limit: {limit}")
        if mode:
            logger.info(f"Mode: {mode}")
        
        # Import dependencies here to avoid cold start issues
        from task_generator import TaskGenerator
        
        # Initialize task generator
        generator = TaskGenerator(
            environment=os.environ.get('ENVIRONMENT', 'dev'),
            sqs_queue_url=os.environ['SQS_QUEUE_URL']
        )

        if mode == 'watchlist':
            # Queue all unique watchlist symbols directly
            watchlist_table = os.environ.get('WATCHLIST_TABLE_NAME', '')
            total_tasks = generator.generate_watchlist_tasks(date, watchlist_table)
            logger.info(f"Successfully generated {total_tasks} watchlist tasks for date {date}")
        else:
            # Normal market-based task generation
            total_tasks = generator.generate_tasks(date, market_filter=market_filter, limit=limit)
            logger.info(f"Successfully generated {total_tasks} tasks for date {date}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Task generation completed',
                'date': date,
                'mode': mode or 'market',
                'market': market_filter,
                'limit': limit,
                'totalTasks': total_tasks
            })
        }
        
    except Exception as e:
        logger.error(f"Error generating tasks: {str(e)}", exc_info=True)
        raise
