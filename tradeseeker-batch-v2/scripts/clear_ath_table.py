#!/usr/bin/env python3
"""
Script to clear ATH table and optionally recreate it
"""

import boto3
import sys
import time
from botocore.exceptions import ClientError

def clear_ath_table(recreate=False):
    """Clear all records from ATH table or recreate the table entirely"""
    
    # Initialize AWS clients
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-1')
    dynamodb_client = boto3.client('dynamodb', region_name='ap-southeast-1')
    
    table_name = 'ts-batch-v2-dev-ath'
    
    print(f"🗑️  ATH Table Management")
    print(f"Table: {table_name}")
    print("=" * 50)
    
    if recreate:
        print("⚠️  RECREATE MODE: This will delete and recreate the entire table!")
        confirm = input("Are you sure you want to recreate the table? (type 'RECREATE' to confirm): ")
        if confirm != 'RECREATE':
            print("❌ Operation cancelled.")
            return
        
        # Delete the table
        try:
            print("🗑️  Deleting existing table...")
            dynamodb_client.delete_table(TableName=table_name)
            
            # Wait for table to be deleted
            print("⏳ Waiting for table deletion...")
            waiter = dynamodb_client.get_waiter('table_not_exists')
            waiter.wait(TableName=table_name)
            print("✅ Table deleted successfully")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                print("ℹ️  Table doesn't exist, will create new one")
            else:
                print(f"❌ Error deleting table: {e}")
                return
        
        # Recreate the table
        try:
            print("🔨 Creating new ATH table...")
            table = dynamodb_client.create_table(
                TableName=table_name,
                KeySchema=[
                    {
                        'AttributeName': 'symbol',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'symbol',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'market_code',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'beauty_score',
                        'AttributeType': 'N'
                    }
                ],
                BillingMode='PAY_PER_REQUEST',
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'market_code-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'market_code',
                                'KeyType': 'HASH'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        }
                    },
                    {
                        'IndexName': 'beauty_score-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'market_code',
                                'KeyType': 'HASH'
                            },
                            {
                                'AttributeName': 'beauty_score',
                                'KeyType': 'RANGE'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        }
                    }
                ],
                SSESpecification={
                    'Enabled': True
                },
                Tags=[
                    {
                        'Key': 'Environment',
                        'Value': 'dev'
                    },
                    {
                        'Key': 'Project',
                        'Value': 'tradeseeker-batch-v2'
                    }
                ]
            )
            
            # Wait for table to be created
            print("⏳ Waiting for table creation...")
            waiter = dynamodb_client.get_waiter('table_exists')
            waiter.wait(TableName=table_name)
            
            # Enable point-in-time recovery after table creation
            print("🔒 Enabling point-in-time recovery...")
            dynamodb_client.update_continuous_backups(
                TableName=table_name,
                PointInTimeRecoverySpecification={
                    'PointInTimeRecoveryEnabled': True
                }
            )
            
            print("✅ Table created successfully")
            
        except ClientError as e:
            print(f"❌ Error creating table: {e}")
            return
    
    else:
        # Clear all records (scan and delete)
        print("🧹 CLEAR MODE: This will delete all records but keep the table structure")
        
        # Get record count first
        try:
            table = dynamodb.Table(table_name)
            response = table.scan(Select='COUNT')
            total_count = response['Count']
            
            # Continue scanning if there are more items
            while 'LastEvaluatedKey' in response:
                response = table.scan(
                    Select='COUNT',
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                total_count += response['Count']
            
            print(f"📊 Found {total_count} records to delete")
            
            if total_count == 0:
                print("ℹ️  Table is already empty")
                return
            
            confirm = input(f"Delete all {total_count} records? (y/N): ")
            if confirm.lower() != 'y':
                print("❌ Operation cancelled.")
                return
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                print("❌ Table doesn't exist")
                return
            else:
                print(f"❌ Error accessing table: {e}")
                return
        
        # Delete all records
        try:
            print("🗑️  Deleting all records...")
            deleted_count = 0
            
            # Scan and delete in batches
            response = table.scan()
            
            while True:
                items = response.get('Items', [])
                
                if not items:
                    break
                
                # Delete items in batches of 25 (DynamoDB limit)
                with table.batch_writer() as batch:
                    for item in items:
                        batch.delete_item(
                            Key={
                                'symbol': item['symbol']
                            }
                        )
                        deleted_count += 1
                
                print(f"🗑️  Deleted {deleted_count} records...")
                
                # Check if there are more items to scan
                if 'LastEvaluatedKey' not in response:
                    break
                
                response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            
            print(f"✅ Successfully deleted {deleted_count} records")
            
        except ClientError as e:
            print(f"❌ Error deleting records: {e}")
            return
    
    print("🎉 ATH table operation completed successfully!")

def show_table_info():
    """Show current table information"""
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-1')
    dynamodb_client = boto3.client('dynamodb', region_name='ap-southeast-1')
    
    table_name = 'ts-batch-v2-dev-ath'
    
    try:
        # Get table description
        response = dynamodb_client.describe_table(TableName=table_name)
        table_info = response['Table']
        
        print(f"📋 Table Information: {table_name}")
        print("=" * 50)
        print(f"Status: {table_info['TableStatus']}")
        print(f"Creation Date: {table_info['CreationDateTime']}")
        print(f"Billing Mode: {table_info['BillingModeSummary']['BillingMode']}")
        
        # Get item count
        table = dynamodb.Table(table_name)
        response = table.scan(Select='COUNT')
        total_count = response['Count']
        
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                Select='COUNT',
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            total_count += response['Count']
        
        print(f"Record Count: {total_count}")
        
        # Show indexes
        if 'GlobalSecondaryIndexes' in table_info:
            print("\nGlobal Secondary Indexes:")
            for gsi in table_info['GlobalSecondaryIndexes']:
                print(f"  - {gsi['IndexName']}")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"❌ Table '{table_name}' doesn't exist")
        else:
            print(f"❌ Error getting table info: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == 'recreate':
            clear_ath_table(recreate=True)
        elif sys.argv[1] == 'clear':
            clear_ath_table(recreate=False)
        elif sys.argv[1] == 'info':
            show_table_info()
        else:
            print("Usage:")
            print("  python clear_ath_table.py info      - Show table information")
            print("  python clear_ath_table.py clear     - Clear all records (keep table)")
            print("  python clear_ath_table.py recreate  - Delete and recreate table")
    else:
        print("ATH Table Management Script")
        print("=" * 30)
        print("Usage:")
        print("  python clear_ath_table.py info      - Show table information")
        print("  python clear_ath_table.py clear     - Clear all records (keep table)")
        print("  python clear_ath_table.py recreate  - Delete and recreate table")
        print("")
        print("Examples:")
        print("  python clear_ath_table.py info")
        print("  python clear_ath_table.py clear")
        print("  python clear_ath_table.py recreate")