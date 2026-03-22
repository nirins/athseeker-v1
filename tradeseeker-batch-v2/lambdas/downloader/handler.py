# Downloader Lambda Handler
# This Lambda is triggered by SQS to download stock prices and calculate EMAs

import json
import os
from typing import Dict, Any, List
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    SQS triggered handler to download stock prices
    
    Args:
        event: SQS event containing Records
        context: Lambda context object
        
    Returns:
        Response with batch item failures for retry
    """
    batch_item_failures = []
    
    logger.info(f"Processing {len(event['Records'])} messages")
    logger.info(f"Request ID: {context.aws_request_id}")
    
    # Import dependencies here to avoid cold start issues
    from downloader import StockDownloader
    
    # Initialize downloader
    downloader = StockDownloader(
        environment=os.environ.get('ENVIRONMENT', 'dev'),
        s3_bucket=os.environ['S3_BUCKET_NAME'],
        dynamodb_table=os.environ['DYNAMODB_TABLE_NAME'],
        dynamodb_lite_table=os.environ.get('DYNAMODB_LITE_TABLE_NAME', '')
    )
    
    # Process each message
    for record in event['Records']:
        message_id = record['messageId']
        
        try:
            logger.info(f"Processing message: {message_id}")
            
            # Process the download task
            downloader.process_task(record)
            
            logger.info(f"Successfully processed message: {message_id}")
            
        except Exception as e:
            logger.error(f"Error processing message {message_id}: {str(e)}", exc_info=True)
            
            # Add to batch item failures for retry
            batch_item_failures.append({
                'itemIdentifier': message_id
            })
    
    # Return batch item failures for SQS to retry
    response = {
        'batchItemFailures': batch_item_failures
    }
    
    logger.info(f"Completed processing. Failures: {len(batch_item_failures)}/{len(event['Records'])}")
    
    return response
