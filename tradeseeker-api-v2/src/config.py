"""
Environment configuration for TradeSeekerAPI v2.

This module manages environment variables for DynamoDB table names,
region, and GSI names. Provides sensible defaults for local development.
"""

import os
import boto3
import json
import logging

logger = logging.getLogger(__name__)

# AWS Region
AWS_REGION = os.environ.get('LAMBDA_REGION', 'ap-southeast-1')

# OpenAI Configuration - retrieved from AWS Secrets Manager
OPENAI_SECRET_NAME = os.environ.get('OPENAI_SECRET_NAME')

# DynamoDB Table Names
GOLDEN_CROSSES_TABLE = os.environ.get(
    'GOLDEN_CROSSES_TABLE',
    'ts-batch-v2-dev-golden-crosses'
)

STOCK_PRICES_TABLE = os.environ.get(
    'STOCK_PRICES_TABLE',
    'ts-batch-v2-dev-stock-prices'
)

# DynamoDB GSI Names
CROSS_DATE_INDEX = os.environ.get(
    'CROSS_DATE_INDEX',
    'cross_date-index'
)

MARKET_CODE_CROSS_DATE_INDEX = os.environ.get(
    'MARKET_CODE_CROSS_DATE_INDEX',
    'market_code-cross_date-index'
)


def get_openai_api_key() -> str:
    """
    Retrieve OpenAI API key from AWS Secrets Manager.
    
    Returns:
        OpenAI API key string
        
    Raises:
        ValueError: If secret name not configured or secret not found
        Exception: If unable to retrieve secret
    """
    if not OPENAI_SECRET_NAME:
        raise ValueError("OPENAI_SECRET_NAME environment variable not set")
    
    try:
        # Create Secrets Manager client
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=AWS_REGION
        )
        
        # Retrieve secret
        response = client.get_secret_value(SecretId=OPENAI_SECRET_NAME)
        secret_data = json.loads(response['SecretString'])
        
        # Extract API key from secret
        api_key = secret_data.get('api_key')
        if not api_key:
            raise ValueError(f"'api_key' key not found in secret '{OPENAI_SECRET_NAME}'")
        
        logger.info(f"Successfully retrieved OpenAI API key from secret '{OPENAI_SECRET_NAME}'")
        return api_key
        
    except Exception as e:
        logger.error(f"Failed to retrieve OpenAI API key from secret '{OPENAI_SECRET_NAME}': {e}")
        raise
