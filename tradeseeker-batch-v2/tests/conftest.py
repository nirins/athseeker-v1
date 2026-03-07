"""Pytest configuration and shared fixtures for integration tests"""

import os
import json
import pytest
import boto3
from moto import mock_aws


@pytest.fixture(scope='function')
def aws_credentials():
    """Mock AWS credentials for moto"""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'ap-southeast-1'


@pytest.fixture(scope='function')
def mock_aws_services(aws_credentials):
    """Setup mocked AWS services for integration tests"""
    with mock_aws():
        yield


@pytest.fixture
def sqs_setup(mock_aws_services):
    """Create SQS queues for testing"""
    sqs = boto3.client('sqs', region_name='ap-southeast-1')
    
    # Create main queue
    main_queue = sqs.create_queue(
        QueueName='test-stock-ingestion-queue',
        Attributes={
            'VisibilityTimeout': '300',
            'MessageRetentionPeriod': '1209600',
            'ReceiveMessageWaitTimeSeconds': '20'
        }
    )
    main_queue_url = main_queue['QueueUrl']
    
    # Create DLQ
    dlq = sqs.create_queue(
        QueueName='test-stock-ingestion-dlq',
        Attributes={
            'MessageRetentionPeriod': '1209600'
        }
    )
    dlq_url = dlq['QueueUrl']
    
    # Get DLQ ARN
    dlq_attrs = sqs.get_queue_attributes(
        QueueUrl=dlq_url,
        AttributeNames=['QueueArn']
    )
    dlq_arn = dlq_attrs['Attributes']['QueueArn']
    
    # Configure DLQ on main queue
    sqs.set_queue_attributes(
        QueueUrl=main_queue_url,
        Attributes={
            'RedrivePolicy': json.dumps({
                'deadLetterTargetArn': dlq_arn,
                'maxReceiveCount': '3'
            })
        }
    )
    
    return {
        'sqs': sqs,
        'main_queue_url': main_queue_url,
        'dlq_url': dlq_url,
        'dlq_arn': dlq_arn
    }


@pytest.fixture
def s3_setup(mock_aws_services):
    """Create S3 bucket for testing"""
    s3 = boto3.client('s3', region_name='ap-southeast-1')
    bucket_name = 'test-stock-prices-bucket'
    
    s3.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={'LocationConstraint': 'ap-southeast-1'}
    )
    
    return {
        's3': s3,
        'bucket_name': bucket_name
    }


@pytest.fixture
def dynamodb_setup(mock_aws_services):
    """Create DynamoDB table for testing"""
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-1')
    
    table = dynamodb.create_table(
        TableName='test-stock-prices',
        KeySchema=[
            {'AttributeName': 'symbol', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'symbol', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    
    # Wait for table to be created
    table.meta.client.get_waiter('table_exists').wait(TableName='test-stock-prices')
    
    return {
        'dynamodb': dynamodb,
        'table': table,
        'table_name': 'test-stock-prices'
    }


@pytest.fixture
def ssm_setup(mock_aws_services):
    """Create SSM parameters for testing"""
    ssm = boto3.client('ssm', region_name='ap-southeast-1')
    
    # Create markets parameter
    markets = [
        {'Name': 'USA Stocks', 'Code': 'US'},
        {'Name': 'Thailand Exchange', 'Code': 'BK'}
    ]
    ssm.put_parameter(
        Name='/ts-batch-v2/dev/markets',
        Value=json.dumps(markets),
        Type='String'
    )
    
    # Create API endpoints parameter
    endpoints = {
        'symbolListUrl': 'https://eodhd.com/api/exchange-symbol-list/{MARKET_CODE}',
        'stockPriceUrl': 'https://eodhd.com/api/eod/{SYMBOL}.{MARKET_CODE}'
    }
    ssm.put_parameter(
        Name='/ts-batch-v2/dev/api-endpoints',
        Value=json.dumps(endpoints),
        Type='String'
    )
    
    return {
        'ssm': ssm,
        'markets': markets,
        'endpoints': endpoints
    }


@pytest.fixture
def secrets_manager_setup(mock_aws_services):
    """Create Secrets Manager secret for testing"""
    secretsmanager = boto3.client('secretsmanager', region_name='ap-southeast-1')
    
    secret_value = {'api_token': 'test-api-token-12345'}
    
    secretsmanager.create_secret(
        Name='ts-batch-v2-dev-eodhd-api-token',
        SecretString=json.dumps(secret_value)
    )
    
    return {
        'secretsmanager': secretsmanager,
        'secret_name': 'ts-batch-v2-dev-eodhd-api-token',
        'api_token': secret_value['api_token']
    }


@pytest.fixture
def full_aws_setup(sqs_setup, s3_setup, dynamodb_setup, ssm_setup, secrets_manager_setup):
    """Combined fixture with all AWS services configured"""
    return {
        **sqs_setup,
        **s3_setup,
        **dynamodb_setup,
        **ssm_setup,
        **secrets_manager_setup
    }
