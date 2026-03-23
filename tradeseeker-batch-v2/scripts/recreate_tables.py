#!/usr/bin/env python3
"""
Recreate DynamoDB tables for tradeseeker-batch-v2.
Deletes and recreates all tables with correct schemas.
"""

import boto3
import time
import sys

REGION = 'ap-southeast-1'
PREFIX = 'ts-batch-v2-dev'

TABLES = {
    f'{PREFIX}-stock-prices': {
        'BillingMode': 'PAY_PER_REQUEST',
        'KeySchema': [{'AttributeName': 'symbol', 'KeyType': 'HASH'}],
        'AttributeDefinitions': [{'AttributeName': 'symbol', 'AttributeType': 'S'}],
        'PointInTimeRecoveryEnabled': True,
    },
    f'{PREFIX}-stock-prices-lite': {
        'BillingMode': 'PAY_PER_REQUEST',
        'KeySchema': [{'AttributeName': 'symbol', 'KeyType': 'HASH'}],
        'AttributeDefinitions': [{'AttributeName': 'symbol', 'AttributeType': 'S'}],
        'PointInTimeRecoveryEnabled': True,
    },
    f'{PREFIX}-ath': {
        'BillingMode': 'PAY_PER_REQUEST',
        'KeySchema': [{'AttributeName': 'symbol', 'KeyType': 'HASH'}],
        'AttributeDefinitions': [
            {'AttributeName': 'symbol', 'AttributeType': 'S'},
            {'AttributeName': 'market_code', 'AttributeType': 'S'},
            {'AttributeName': 'beauty_score', 'AttributeType': 'N'},
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'market_code-index',
                'KeySchema': [{'AttributeName': 'market_code', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'},
            },
            {
                'IndexName': 'beauty_score-index',
                'KeySchema': [
                    {'AttributeName': 'market_code', 'KeyType': 'HASH'},
                    {'AttributeName': 'beauty_score', 'KeyType': 'RANGE'},
                ],
                'Projection': {'ProjectionType': 'ALL'},
            },
        ],
        'TTLAttribute': 'ttl',
        'PointInTimeRecoveryEnabled': True,
    },
    f'{PREFIX}-near-ath': {
        'BillingMode': 'PAY_PER_REQUEST',
        'KeySchema': [{'AttributeName': 'symbol', 'KeyType': 'HASH'}],
        'AttributeDefinitions': [
            {'AttributeName': 'symbol', 'AttributeType': 'S'},
            {'AttributeName': 'market_code', 'AttributeType': 'S'},
            {'AttributeName': 'beauty_score', 'AttributeType': 'N'},
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'market_code-index',
                'KeySchema': [{'AttributeName': 'market_code', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'},
            },
            {
                'IndexName': 'beauty_score-index',
                'KeySchema': [
                    {'AttributeName': 'market_code', 'KeyType': 'HASH'},
                    {'AttributeName': 'beauty_score', 'KeyType': 'RANGE'},
                ],
                'Projection': {'ProjectionType': 'ALL'},
            },
        ],
        'TTLAttribute': 'ttl',
        'PointInTimeRecoveryEnabled': True,
    },
    f'{PREFIX}-golden-crosses': {
        'BillingMode': 'PAY_PER_REQUEST',
        'KeySchema': [
            {'AttributeName': 'symbol', 'KeyType': 'HASH'},
            {'AttributeName': 'cross_date', 'KeyType': 'RANGE'},
        ],
        'AttributeDefinitions': [
            {'AttributeName': 'symbol', 'AttributeType': 'S'},
            {'AttributeName': 'cross_date', 'AttributeType': 'S'},
            {'AttributeName': 'market_code', 'AttributeType': 'S'},
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'cross_date-index',
                'KeySchema': [{'AttributeName': 'cross_date', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'},
            },
            {
                'IndexName': 'market_code-cross_date-index',
                'KeySchema': [
                    {'AttributeName': 'market_code', 'KeyType': 'HASH'},
                    {'AttributeName': 'cross_date', 'KeyType': 'RANGE'},
                ],
                'Projection': {'ProjectionType': 'ALL'},
            },
        ],
        'TTLAttribute': 'ttl',
        'PointInTimeRecoveryEnabled': True,
    },
    f'{PREFIX}-death-crosses': {
        'BillingMode': 'PAY_PER_REQUEST',
        'KeySchema': [
            {'AttributeName': 'symbol', 'KeyType': 'HASH'},
            {'AttributeName': 'cross_date', 'KeyType': 'RANGE'},
        ],
        'AttributeDefinitions': [
            {'AttributeName': 'symbol', 'AttributeType': 'S'},
            {'AttributeName': 'cross_date', 'AttributeType': 'S'},
            {'AttributeName': 'market_code', 'AttributeType': 'S'},
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'cross_date-index',
                'KeySchema': [{'AttributeName': 'cross_date', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'},
            },
            {
                'IndexName': 'market_code-cross_date-index',
                'KeySchema': [
                    {'AttributeName': 'market_code', 'KeyType': 'HASH'},
                    {'AttributeName': 'cross_date', 'KeyType': 'RANGE'},
                ],
                'Projection': {'ProjectionType': 'ALL'},
            },
        ],
        'TTLAttribute': 'ttl',
        'PointInTimeRecoveryEnabled': True,
    },
}


def delete_table(client, name):
    try:
        client.delete_table(TableName=name)
        print(f'  Deleting {name}...')
        waiter = client.get_waiter('table_not_exists')
        waiter.wait(TableName=name, WaiterConfig={'Delay': 5, 'MaxAttempts': 24})
        print(f'  ✅ Deleted {name}')
    except client.exceptions.ResourceNotFoundException:
        print(f'  ⚠️  {name} does not exist, skipping delete')


def create_table(client, name, schema):
    params = {
        'TableName': name,
        'BillingMode': schema['BillingMode'],
        'KeySchema': schema['KeySchema'],
        'AttributeDefinitions': schema['AttributeDefinitions'],
        'SSESpecification': {'Enabled': True},
    }
    if 'GlobalSecondaryIndexes' in schema:
        params['GlobalSecondaryIndexes'] = schema['GlobalSecondaryIndexes']

    print(f'  Creating {name}...')
    client.create_table(**params)

    waiter = client.get_waiter('table_exists')
    waiter.wait(TableName=name, WaiterConfig={'Delay': 5, 'MaxAttempts': 24})
    print(f'  ✅ Created {name}')

    if schema.get('PointInTimeRecoveryEnabled'):
        for attempt in range(10):
            try:
                client.update_continuous_backups(
                    TableName=name,
                    PointInTimeRecoverySpecification={'PointInTimeRecoveryEnabled': True}
                )
                break
            except client.exceptions.ContinuousBackupsUnavailableException:
                print(f'  ⏳ Waiting for PITR to be available (attempt {attempt + 1}/10)...')
                time.sleep(5)

    if 'TTLAttribute' in schema:
        client.update_time_to_live(
            TableName=name,
            TimeToLiveSpecification={'Enabled': True, 'AttributeName': schema['TTLAttribute']}
        )


def main():
    confirm = input(f'⚠️  This will DELETE and RECREATE {len(TABLES)} tables. Type "yes" to confirm: ')
    if confirm.strip().lower() != 'yes':
        print('Aborted.')
        sys.exit(0)

    client = boto3.client('dynamodb', region_name=REGION)

    for name, schema in TABLES.items():
        print(f'\n📋 Processing {name}')
        delete_table(client, name)
        create_table(client, name, schema)

    print('\n✅ All tables recreated successfully.')


if __name__ == '__main__':
    main()
