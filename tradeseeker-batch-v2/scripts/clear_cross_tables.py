#!/usr/bin/env python3
"""
Clear all items from golden-crosses and death-crosses tables
"""

import boto3
from concurrent.futures import ThreadPoolExecutor

def clear_table(table_name):
    """Clear all items from a DynamoDB table"""
    print(f"Clearing table: {table_name}")
    
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-1')
    table = dynamodb.Table(table_name)
    
    # Scan and delete all items
    scan_kwargs = {}
    deleted_count = 0
    
    while True:
        response = table.scan(**scan_kwargs)
        items = response.get('Items', [])
        
        if not items:
            break
        
        # Delete items in batches
        with table.batch_writer() as batch:
            for item in items:
                batch.delete_item(
                    Key={
                        'symbol': item['symbol'],
                        'cross_date': item['cross_date']
                    }
                )
                deleted_count += 1
        
        print(f"  Deleted {len(items)} items from {table_name}")
        
        # Handle pagination
        if 'LastEvaluatedKey' not in response:
            break
        scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
    
    print(f"✅ Cleared {table_name}: {deleted_count} items deleted")
    return deleted_count

def main():
    tables = [
        'ts-batch-v2-dev-golden-crosses',
        'ts-batch-v2-dev-death-crosses'
    ]
    
    print("Clearing cross signal tables...")
    
    # Clear tables in parallel
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(clear_table, table) for table in tables]
        total_deleted = sum(future.result() for future in futures)
    
    print(f"\n🎉 All done! Total items deleted: {total_deleted}")

if __name__ == '__main__':
    main()