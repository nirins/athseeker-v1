"""
Handler for saving stock data by grade to S3 for ML training dataset
"""
import json
import boto3
from datetime import datetime
from typing import Dict, Any
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Save stock data with grade label to S3 for training dataset
    
    Expected payload:
    {
        "symbol": "AAPL",
        "grade": "A+",
        "stockData": {...},
        "timestamp": "2024-01-01T00:00:00Z"
    }
    """
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        # Validate required fields
        required_fields = ['symbol', 'grade', 'stockData']
        for field in required_fields:
            if field not in body:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                        'Access-Control-Allow-Methods': 'POST,OPTIONS'
                    },
                    'body': json.dumps({
                        'error': f'Missing required field: {field}'
                    })
                }
        
        symbol = body['symbol']
        grade = body['grade']
        stock_data = body['stockData']
        timestamp = body.get('timestamp', datetime.utcnow().isoformat())
        
        # Validate grade
        valid_grades = ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D', 'F']
        if grade not in valid_grades:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Methods': 'POST,OPTIONS'
                },
                'body': json.dumps({
                    'error': f'Invalid grade: {grade}. Must be one of: {", ".join(valid_grades)}'
                })
            }
        
        # Save to S3
        result = save_to_s3(symbol, grade, stock_data, timestamp)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'POST,OPTIONS'
            },
            'body': json.dumps({
                'message': 'Training data saved successfully',
                'symbol': symbol,
                'grade': grade,
                's3_key': result['s3_key'],
                'timestamp': timestamp
            })
        }
        
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'POST,OPTIONS'
            },
            'body': json.dumps({
                'error': 'Invalid JSON in request body'
            })
        }
    except Exception as e:
        logger.error(f"Error saving training data: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'POST,OPTIONS'
            },
            'body': json.dumps({
                'error': 'Internal server error'
            })
        }

def save_to_s3(symbol: str, grade: str, stock_data: Dict[str, Any], timestamp: str) -> Dict[str, Any]:
    """
    Save stock data to S3 organized by grade for ML training
    
    S3 structure: training-data/{grade}/{symbol}-{timestamp}.json
    """
    try:
        # Initialize S3 client
        s3_client = boto3.client('s3')
        
        # Get bucket name from environment or use default
        import os
        bucket_name = os.environ.get('TRAINING_DATA_BUCKET', 'tradeseeker-training-data')
        
        # Create S3 key with grade folder structure
        # Format: training-data/{grade}/{symbol}-{timestamp}.json
        timestamp_clean = timestamp.replace(':', '-').replace('.', '-')
        s3_key = f"training-data/{grade}/{symbol}-{timestamp_clean}.json"
        
        # Prepare data for storage
        training_data = {
            'symbol': symbol,
            'grade': grade,
            'timestamp': timestamp,
            'stockData': stock_data,
            'metadata': {
                'created_at': datetime.utcnow().isoformat(),
                'data_points': len(stock_data.get('prices', [])),
                'has_emas': bool(stock_data.get('emas')),
                'last_price_date': stock_data.get('prices', [{}])[-1].get('date') if stock_data.get('prices') else None
            }
        }
        
        # Upload to S3
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=json.dumps(training_data, indent=2),
            ContentType='application/json',
            Metadata={
                'symbol': symbol,
                'grade': grade,
                'timestamp': timestamp
            }
        )
        
        logger.info(f"Successfully saved training data to S3: {s3_key}")
        
        return {
            's3_key': s3_key,
            'bucket': bucket_name,
            'size_bytes': len(json.dumps(training_data))
        }
        
    except ClientError as e:
        logger.error(f"S3 error saving training data: {str(e)}")
        raise Exception(f"Failed to save to S3: {str(e)}")
    except Exception as e:
        logger.error(f"Error saving training data to S3: {str(e)}")
        raise Exception(f"Failed to save training data: {str(e)}")