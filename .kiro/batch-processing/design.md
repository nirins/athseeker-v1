# Design: Batch Processing

## 1. Architecture Overview

The system implements a serverless batch ingestion pipeline using AWS services:

```
EventBridge Scheduler → Task Generator Lambda → SQS Queue → Downloader Lambda → S3
                                                      ↓                              ↓
                                                    DLQ                         DynamoDB
                                                                            (OHLC + Moving Avg)
```

Key design principles:
- Event-driven architecture for scalability
- Decoupled components via SQS for failure isolation
- Idempotent operations to support retries
- Rate limiting via Lambda reserved concurrency and SQS batch size
- Dual storage: S3 for raw data archive, DynamoDB for queryable analytics

## 2. Components

### 2.1 Task Generator Lambda
- **Purpose**: Creates download tasks for all stock symbols from configured EODHD markets
- **Responsibilities**: 
  - Triggered daily by EventBridge Scheduler
  - Retrieves market list from SSM Parameter Store
  - Fetches symbol list from EODHD API for each market (`/exchange-symbol-list/{MARKET_CODE}`)
  - Generates ~100,000 SQS messages (one per symbol/date combination)
  - Implements idempotency checks to prevent duplicate task creation
- **Interfaces**: 
  - Input: EventBridge event with date parameter
  - Output: Batch writes to SQS queue
  - External: EODHD API for symbol list retrieval, SSM Parameter Store for market configuration

### 2.2 SQS Main Queue
- **Purpose**: Buffers download tasks and controls throughput
- **Configuration**:
  - Visibility timeout: 5 minutes (3x expected Lambda duration)
  - Message retention: 14 days
  - Max receives: 3 (before DLQ)
  - Batch size: 10 (process 10 messages per Lambda invocation)
  - Receive wait time: 20 seconds (long polling)
- **Interfaces**: Connects Task Generator to Downloader Lambda

### 2.3 Downloader Lambda
- **Purpose**: Fetches stock price data, stores in S3, calculates exponential moving averages, and saves to DynamoDB
- **Responsibilities**:
  - Consumes SQS messages in batches of 10
  - Calls external stock price API with retry logic for each symbol
  - Compresses response as gzip JSON and writes to S3
  - Calculates exponential moving averages (EMA 7, 30, 50, 200) from close prices
  - Stores OHLCV data and EMAs in DynamoDB
  - Reports partial batch failures back to SQS
- **Configuration**:
  - Reserved concurrency: 8 (to enforce 1000 req/min limit with safety margin)
  - Timeout: 120 seconds
  - Memory: 512 MB
  - SQS batch size: 10 (process 10 stocks per invocation)
- **Rate Limiting Strategy**:
  - 8 concurrent Lambdas × 10 req/Lambda = 80 requests per batch
  - Each batch takes ~3-5 seconds (including API calls, compression, S3 writes, DynamoDB writes)
  - Throughput: ~960-1,600 req/min (within 1000 req/min limit with safety margin)
  - Daily capacity: 100,000 requests completes in ~1.5-2.5 hours
- **Interfaces**:
  - Input: SQS batch of download tasks
  - Output: S3 objects, DynamoDB records, CloudWatch logs/metrics

### 2.4 SQS Dead Letter Queue (DLQ)
- **Purpose**: Captures messages that fail after max retries
- **Configuration**:
  - Message retention: 14 days
  - CloudWatch alarm on queue depth > 100
- **Interfaces**: Receives failed messages from main queue

### 2.5 DLQ Replay Lambda
- **Purpose**: Reprocesses failed messages from DLQ
- **Responsibilities**:
  - Manually triggered or scheduled
  - Reads messages from DLQ
  - Re-enqueues to main queue for retry
- **Interfaces**:
  - Input: Manual trigger or EventBridge schedule
  - Output: Messages moved from DLQ to main queue

### 2.7 DynamoDB Table
- **Purpose**: Queryable storage for OHLC data and calculated moving averages
- **Table Name**: `stock-prices`
- **Primary Key**:
  - Partition Key: `symbol` (String) - e.g., "AAPL.US", "PTT.BK"
- **Attributes**:
  - `symbol`: Stock symbol with market code
  - `market_code`: Market code (e.g., "US", "BK", "CC")
  - `prices`: List of OHLC records (sorted by date)
    ```json
    [
      {
        "date": "2024-01-01",
        "open": 100.5,
        "high": 102.3,
        "low": 99.8,
        "close": 101.2,
        "adjusted_close": 101.2,
        "volume": 1000000
      },
      ...
    ]
    ```
  - `moving_averages`: List of exponential moving average records (sorted by date)
    ```json
    [
      {
        "date": "2024-01-01",
        "ema_7": 100.5,
        "ema_30": 98.3,
        "ema_50": 97.1,
        "ema_200": 95.8
      },
      ...
    ]
    ```
  - `updated_at`: Timestamp of last update
- **Configuration**:
  - Billing mode: On-demand (or provisioned with auto-scaling)
  - Point-in-time recovery: Enabled
  - Encryption: AWS managed key

Note: Each symbol has ONE item in DynamoDB containing all historical data as nested lists.

### 2.8 S3 Bucket
- **Purpose**: Persistent storage for stock price data
- **Configuration**:
  - Encryption: AES-256 (SSE-S3)
  - Block public access: Enabled
  - Lifecycle policy: Optional (e.g., transition to Glacier after 90 days)
- **Key Structure**: `prices/market={MARKET_CODE}/dt=YYYY-MM-DD/symbol=<SYMBOL>/data.json.gz`
  - Example US: `prices/market=US/dt=2024-01-15/symbol=AAPL/data.json.gz`
  - Example Thailand: `prices/market=BK/dt=2024-01-15/symbol=PTT/data.json.gz`
  - Example Crypto: `prices/market=CC/dt=2024-01-15/symbol=BTC-USD/data.json.gz`

## 3. Data Models

### 3.1 SQS Message Schema
```typescript
interface DownloadTask {
  symbol: string;           // Stock ticker symbol (e.g., "AAPL")
  marketCode: string;       // Market code (e.g., "US", "BK", "CC")
  date: string;             // ISO date (e.g., "2024-01-15")
  apiEndpoint: string;      // EODHD API URL template
  requestId: string;        // Unique identifier for idempotency
}
```

Example messages:
```json
{
  "symbol": "AAPL",
  "marketCode": "US",
  "date": "2024-01-15",
  "apiEndpoint": "https://eodhd.com/api/eod/AAPL.US",
  "requestId": "AAPL-US-2024-01-15"
}
```

```json
{
  "symbol": "PTT",
  "marketCode": "BK",
  "date": "2024-01-15",
  "apiEndpoint": "https://eodhd.com/api/eod/PTT.BK",
  "requestId": "PTT-BK-2024-01-15"
}
```

### 3.2 S3 Object Structure
```typescript
// EODHD API returns an array of daily price records
interface EODHDPriceRecord {
  date: string;              // ISO date (e.g., "1966-07-05")
  open: number;              // Opening price
  high: number;              // Highest price
  low: number;               // Lowest price
  close: number;             // Closing price
  adjusted_close: number;    // Adjusted closing price
  volume: number;            // Trading volume
}

type StockPriceResponse = EODHDPriceRecord[];
```

Example response:
```json
[
  {
    "date": "1966-07-05",
    "open": 32.5072,
    "high": 33.2592,
    "low": 32.5072,
    "close": 32.7496,
    "adjusted_close": 0.0042,
    "volume": 388800
  },
  {
    "date": "1966-07-06",
    "open": 32.7496,
    "high": 34.5064,
    "low": 32.5072,
    "close": 34.5064,
    "adjusted_close": 0.0045,
    "volume": 692550
  }
]
```

Note: The response is an array of historical records. When querying with `from` and `to` date parameters, it returns only records within that range.

### 3.3 CloudWatch Log Structure
```typescript
interface LogEntry {
  requestId: string;
  symbol: string;
  date: string;
  statusCode: number;
  duration: number;
  errorReason?: string;
  s3Key?: string;
}
```

## 4. API Design

### 4.1 Task Generator Lambda Handler
```python
import json
import boto3
from typing import List, Dict
from datetime import datetime

ssm = boto3.client('ssm')
secretsmanager = boto3.client('secretsmanager')
sqs = boto3.client('sqs')

def handler(event, context):
    """EventBridge triggered handler to generate download tasks"""
    date = event.get('date', datetime.now().strftime('%Y-%m-%d'))
    api_token = get_secret_value('eodhd-api-token')
    
    # Fetch market list from SSM Parameter Store
    markets = get_markets()
    
    # Fetch symbols for each market
    for market in markets:
        symbols = fetch_symbol_list(market['Code'], api_token)
        
        # Send to SQS in batches of 10
        for i in range(0, len(symbols), 10):
            batch = symbols[i:i+10]
            send_batch_to_sqs(batch, market['Code'], date)

def get_markets() -> List[Dict]:
    """Retrieve market configuration from Parameter Store"""
    response = ssm.get_parameter(Name='/stock-ingestion/markets')
    return json.loads(response['Parameter']['Value'])

def fetch_symbol_list(market_code: str, api_token: str) -> List[Dict]:
    """Fetch symbol list from EODHD API"""
    import requests
    
    endpoints = get_api_endpoints()
    url = endpoints['symbolListUrl'].replace('{MARKET_CODE}', market_code)
    url += f'?api_token={api_token}&fmt=json'
    
    response = requests.get(url)
    response.raise_for_status()
    
    # Response is an array of symbol objects
    return response.json()

def get_api_endpoints() -> Dict:
    """Retrieve API endpoints from Parameter Store"""
    response = ssm.get_parameter(Name='/stock-ingestion/api-endpoints')
    return json.loads(response['Parameter']['Value'])

def get_secret_value(secret_name: str) -> str:
    """Retrieve API token from Secrets Manager"""
    response = secretsmanager.get_secret_value(SecretId=secret_name)
    secret = json.loads(response['SecretString'])
    return secret['api_token']
```

### 4.2 Downloader Lambda Handler
```python
import json
import gzip
import boto3
import requests
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed

s3 = boto3.client('s3')
ssm = boto3.client('ssm')
secretsmanager = boto3.client('secretsmanager')

def handler(event, context):
    """SQS triggered handler to download stock prices"""
    batch_item_failures = []
    
    for record in event['Records']:
        try:
            process_download_task(record)
        except Exception as e:
            print(f"Error processing message {record['messageId']}: {str(e)}")
            batch_item_failures.append({'itemIdentifier': record['messageId']})
    
    return {'batchItemFailures': batch_item_failures}

def process_download_task(record: Dict):
    """Process a single download task"""
    task = json.loads(record['body'])
    
    # Fetch stock price data with retry
    response = fetch_with_retry(task)
    
    # Compress as gzip JSON and upload to S3
    compressed = gzip.compress(json.dumps(response).encode('utf-8'))
    upload_to_s3(task, compressed)
    
    # Calculate moving averages and save to DynamoDB
    save_to_dynamodb(task, response)

def fetch_with_retry(task: Dict, max_retries: int = 3) -> List[Dict]:
    """Fetch stock price with exponential backoff retry"""
    import time
    import random
    
    api_token = get_secret_value('eodhd-api-token')
    
    for attempt in range(max_retries + 1):
        try:
            return call_eodhd_api(task, api_token)
        except Exception as e:
            if not is_retriable(e) or attempt == max_retries:
                raise
            
            # Exponential backoff with jitter
            delay = (2 ** attempt) * 0.1 + random.uniform(0, 0.1)
            time.sleep(delay)

def call_eodhd_api(task: Dict, api_token: str) -> List[Dict]:
    """Call EODHD API to fetch full historical stock price data"""
    endpoints = get_api_endpoints()
    url = endpoints['stockPriceUrl'] \
        .replace('{SYMBOL}', task['symbol']) \
        .replace('{MARKET_CODE}', task['marketCode'])
    url += f'?api_token={api_token}&fmt=json'
    
    # No date params - get full historical data from inception to today
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    
    return response.json()

def upload_to_s3(task: Dict, compressed_data: bytes):
    """Upload compressed JSON to S3"""
    bucket = 'your-bucket-name'  # Should come from environment variable
    key = f"prices/market={task['marketCode']}/dt={task['date']}/symbol={task['symbol']}/data.json.gz"
    
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=compressed_data,
        ContentType='application/json',
        ContentEncoding='gzip'
    )

def get_api_endpoints() -> Dict:
    """Retrieve API endpoints from Parameter Store"""
    response = ssm.get_parameter(Name='/stock-ingestion/api-endpoints')
    return json.loads(response['Parameter']['Value'])

def get_secret_value(secret_name: str) -> str:
    """Retrieve API token from Secrets Manager"""
    response = secretsmanager.get_secret_value(SecretId=secret_name)
    secret = json.loads(response['SecretString'])
    return secret['api_token']

def is_retriable(error: Exception) -> bool:
    """Check if error is retriable"""
    if isinstance(error, requests.exceptions.HTTPError):
        return error.response.status_code in [429, 500, 502, 503, 504]
    return isinstance(error, (requests.exceptions.Timeout, requests.exceptions.ConnectionError))

def save_to_dynamodb(task: Dict, price_data: List[Dict]):
    """Save OHLCV data and exponential moving averages to DynamoDB as nested lists"""
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('stock-prices')
    
    symbol_with_market = f"{task['symbol']}.{task['marketCode']}"
    
    # Sort by date
    sorted_data = sorted(price_data, key=lambda x: x['date'])
    
    # Build prices list
    prices = []
    for record in sorted_data:
        prices.append({
            'date': record['date'],
            'open': record['open'],
            'high': record['high'],
            'low': record['low'],
            'close': record['close'],
            'adjusted_close': record['adjusted_close'],
            'volume': record['volume']
        })
    
    # Calculate EMAs for all periods
    ema_7 = calculate_ema_series(sorted_data, 7)
    ema_30 = calculate_ema_series(sorted_data, 30)
    ema_50 = calculate_ema_series(sorted_data, 50)
    ema_200 = calculate_ema_series(sorted_data, 200)
    
    # Build moving averages list
    moving_averages = []
    for i, record in enumerate(sorted_data):
        ma_record = {
            'date': record['date'],
            'ema_7': ema_7[i],
            'ema_30': ema_30[i],
            'ema_50': ema_50[i],
            'ema_200': ema_200[i]
        }
        moving_averages.append(ma_record)
    
    # Save single item with nested lists
    table.put_item(Item={
        'symbol': symbol_with_market,
        'market_code': task['marketCode'],
        'prices': prices,
        'moving_averages': moving_averages,
        'updated_at': datetime.now().isoformat()
    })

def calculate_ema_series(data: List[Dict], period: int) -> List[float]:
    """Calculate EMA series for all data points
    
    EMA formula:
    - EMA(today) = (Price(today) × k) + (EMA(yesterday) × (1 - k))
    - k = 2 / (period + 1)
    - First EMA = SMA of first 'period' prices
    """
    if len(data) < period:
        return [None] * len(data)
    
    k = 2 / (period + 1)
    ema_values = []
    
    # Calculate initial SMA for first EMA value
    initial_prices = [data[i]['close'] for i in range(period)]
    ema = sum(initial_prices) / period
    
    # Fill None for insufficient data points
    for i in range(period - 1):
        ema_values.append(None)
    
    # First EMA value
    ema_values.append(ema)
    
    # Calculate EMA for remaining data points
    for i in range(period, len(data)):
        price = data[i]['close']
        ema = (price * k) + (ema * (1 - k))
        ema_values.append(ema)
    
    return ema_values
```

Note: Each Lambda invocation processes up to 10 SQS messages (10 stocks) sequentially. For parallel processing within a single invocation, use `ThreadPoolExecutor`.

### 4.3 External API Client
```typescript
async function fetchWithRetry(
  task: DownloadTask,
  maxRetries: number = 3
): Promise<StockPriceResponse> {
  const backoff = exponentialBackoffWithJitter();
  const apiToken = await getSecretValue('eodhd-api-token');
  
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await callEODHDAPI(task, apiToken);
    } catch (error) {
      if (!isRetriable(error) || attempt === maxRetries) {
        throw error;
      }
      await sleep(backoff.next());
    }
  }
}

async function callEODHDAPI(
  task: DownloadTask,
  apiToken: string
): Promise<StockPriceResponse> {
  const endpoints = await getApiEndpoints();
  const url = endpoints.stockPriceUrl
    .replace('{SYMBOL}', task.symbol)
    .replace('{MARKET_CODE}', task.marketCode) +
    `?api_token=${apiToken}&fmt=json`;
  
  const response = await axios.get(url, {
    timeout: 30000,
    params: {
      from: task.date,
      to: task.date
    }
  });
  
  return response.data;
}

async function getApiEndpoints(): Promise<{symbolListUrl: string, stockPriceUrl: string}> {
  const ssm = new SSMClient({});
  const response = await ssm.send(new GetParameterCommand({
    Name: '/stock-ingestion/api-endpoints'
  }));
  
  return JSON.parse(response.Parameter.Value);
}
```

## 5. Correctness Properties

### 5.1 Idempotent Task Creation
- **Description**: Running the task generator multiple times for the same date does not create duplicate work
- **Implementation**: Use requestId derived from (symbol, marketCode, date) as deduplication key
- **Testing**: Unit tests verify requestId generation is deterministic
- **Validates**: Requirements 3.1

### 5.2 At-Least-Once Delivery
- **Description**: Every symbol/date combination is processed at least once, even with failures
- **Implementation**: SQS message retention + DLQ ensures no message loss
- **Testing**: Integration tests verify DLQ captures failed messages
- **Validates**: Requirements 3.1, 3.3

### 5.3 Idempotent S3 Writes
- **Description**: Writing the same symbol/date multiple times produces identical S3 state
- **Implementation**: Fixed S3 key structure overwrites previous data; compressed JSON is deterministic
- **Testing**: Unit tests verify S3 key generation is consistent
- **Validates**: Requirements 3.2

### 5.4 Rate Limit Compliance
- **Description**: System never exceeds EODHD API rate limits (1000 req/min, 100,000 req/day)
- **Implementation**: 
  - Lambda reserved concurrency set to 8
  - SQS batch size set to 10
  - Each Lambda processes 10 stocks in parallel per invocation
  - Math: 8 concurrent Lambdas × 10 req/Lambda = 80 requests per batch cycle (~3-5 seconds)
  - Throughput: ~960-1,600 req/min (close to 1000 req/min limit, optimized for speed)
  - Daily: 100,000 requests complete in ~1.5-2.5 hours
- **Testing**: Load tests verify throughput stays within limits
- **Validates**: Requirements 4 (Performance)

### 5.5 Failure Isolation
- **Description**: One failed download does not block other downloads
- **Implementation**: SQS partial batch failure reporting; each message processed independently
- **Testing**: Integration tests verify partial batch failures are handled correctly
- **Validates**: Requirements 3.3

## 6. Testing Strategy

### 6.1 Unit Tests
- Task generator: Symbol list parsing, SQS batch creation, idempotency key generation
- Downloader: API client retry logic, gzip compression, S3 key formatting
- DLQ replay: Message filtering, re-enqueue logic
- Mock external dependencies (EODHD API, AWS services) using `moto` and `pytest` fixtures

### 6.2 Integration Tests
- End-to-end: EventBridge → Task Generator → SQS → Downloader → S3 (using LocalStack or moto)
- DLQ flow: Force failures, verify DLQ delivery, test replay
- API mocking: Mock external API with rate limits, verify retry behavior
- Test with sample data from multiple markets (US, BK, CC)

## 7. Dependencies

### 7.1 AWS Services
- EventBridge Scheduler
- Lambda (Python 3.12 runtime)
- SQS (Standard queues)
- S3
- DynamoDB
- Secrets Manager (API credentials)
- CloudWatch (Logs, Metrics, Alarms)
- IAM (Roles and policies)

### 7.2 External Libraries
- `boto3`: AWS SDK for Python
- `requests`: HTTP client for external API
- `pytest`: Unit testing framework
- `moto`: AWS service mocking for tests

### 7.3 External API
- **Provider**: EODHD (EOD Historical Data)
- **Symbol List Endpoint**: `https://eodhd.com/api/exchange-symbol-list/{MARKET_CODE}?api_token={TOKEN}&fmt=json`
  - Supported markets configured in SSM Parameter Store
- **Stock Price Endpoint**: `https://eodhd.com/api/eod/{SYMBOL}.{MARKET_CODE}?api_token={TOKEN}&fmt=json`
  - Example US: `https://eodhd.com/api/eod/AAPL.US?api_token={TOKEN}&fmt=json`
  - Example Thailand: `https://eodhd.com/api/eod/PTT.BK?api_token={TOKEN}&fmt=json`
  - Example Crypto: `https://eodhd.com/api/eod/BTC-USD.CC?api_token={TOKEN}&fmt=json`
  - Query params: `from` and `to` for date range (optional, defaults to latest)
- **Rate Limits**: 
  - 1,000 requests per minute
  - 100,000 requests per day
  - Target throughput: ~16.6 requests/second (with safety margin: 15 req/sec)
- **Authentication**: API token stored in AWS Secrets Manager
  - Secret name: `eodhd-api-token`
  - Secret value: `{"api_token": "69917262e3a876.40642506"}`
- **Response Format**: JSON array with daily OHLCV data

## 8. Error Handling

### 8.1 Transient Errors (Retriable)
- HTTP 429 (Rate Limit), 500, 502, 503, 504
- Network timeouts, connection errors
- **Strategy**: Exponential backoff with jitter (100ms, 200ms, 400ms, 800ms)

### 8.2 Permanent Errors (Non-Retriable)
- HTTP 400, 401, 403, 404
- Invalid symbol or date format
- **Strategy**: Log error, send to DLQ immediately (skip retries)

### 8.3 Lambda Errors
- Out of memory: Increase Lambda memory allocation
- Timeout: Reduce SQS batch size or increase timeout
- **Monitoring**: CloudWatch alarm on error rate > 5%

### 8.4 DLQ Handling
- **Alarm**: DLQ depth > 100 messages
- **Response**: Manual investigation, fix root cause, replay via DLQ Replay Lambda
- **Logging**: All DLQ messages logged with full context for debugging

## 9. Configuration

### 9.1 Environment Variables
```typescript
interface Config {
  ENVIRONMENT: string;                    // Environment name (dev, uat, prod)
  EODHD_SECRET_NAME: string;              // Secrets Manager secret name (default: "ts-batch-v2-{env}-eodhd-api-token")
  MARKETS_PARAMETER_NAME: string;         // SSM Parameter Store name (default: "/ts-batch-v2/{env}/markets")
  API_ENDPOINTS_PARAMETER_NAME: string;   // SSM Parameter Store name (default: "/ts-batch-v2/{env}/api-endpoints")
  S3_BUCKET_NAME: string;                 // S3 bucket name (default: "ts-batch-v2-{env}-stock-prices")
  DYNAMODB_TABLE_NAME: string;            // DynamoDB table name (default: "ts-batch-v2-{env}-stock-prices")
  MAX_CONCURRENCY: number;                // Lambda reserved concurrency (default: 8)
  SQS_BATCH_SIZE: number;                 // Messages per Lambda invocation (default: 10)
  RETRY_MAX_ATTEMPTS: number;             // Max retries per message (default: 3)
  RATE_LIMIT_PER_MINUTE: number;          // API rate limit per minute (1000)
  RATE_LIMIT_PER_DAY: number;             // API rate limit per day (100000)
}
```

### 9.5 Secrets Manager Configuration
```json
{
  "secretName": "ts-batch-v2-{env}-eodhd-api-token",
  "secretValue": {
    "api_token": "69917262e3a876.40642506"
  }
}
```

Note: Each environment (dev, uat, prod) has its own secret. In practice, you may use the same API token across environments or separate tokens per environment.

### 9.3 Terraform Workspace Strategy
```hcl
# Use Terraform workspaces for environment separation
# Workspaces: dev, uat, prod

locals {
  prefix      = "ts"
  project     = "batch-v2"
  environment = terraform.workspace
  name_prefix = "${local.prefix}-${local.project}-${local.environment}"
  
  common_tags = {
    Project     = local.project
    Environment = local.environment
    ManagedBy   = "Terraform"
  }
}

# Example resource naming
resource "aws_lambda_function" "task_generator" {
  function_name = "${local.name_prefix}-task-generator"
  # ...
}

resource "aws_s3_bucket" "stock_prices" {
  bucket = "${local.name_prefix}-stock-prices"
  # ...
}

resource "aws_dynamodb_table" "stock_prices" {
  name = "${local.name_prefix}-stock-prices"
  # ...
}
```

### 9.4 SSM Parameter Store Configuration
```json
{
  "parameterName": "/ts-batch-v2/{env}/markets",
  "parameterType": "String",
  "parameterValue": [
    {
      "Name": "USA Stocks",
      "Code": "US"
    },
    {
      "Name": "Thailand Exchange",
      "Code": "BK"
    },
    {
      "Name": "Cryptocurrencies",
      "Code": "CC"
    }
  ]
}
```

```json
{
  "parameterName": "/ts-batch-v2/{env}/api-endpoints",
  "parameterType": "String",
  "parameterValue": {
    "symbolListUrl": "https://eodhd.com/api/exchange-symbol-list/{MARKET_CODE}",
    "stockPriceUrl": "https://eodhd.com/api/eod/{SYMBOL}.{MARKET_CODE}"
  }
}
```

Note: The parameter values should be stored as JSON strings in SSM Parameter Store. URL templates use placeholders that will be replaced at runtime. Parameter names include environment (e.g., `/ts-batch-v2/dev/markets`, `/ts-batch-v2/prod/markets`).

### 9.2 Deployment Parameters
- Project prefix: `ts`
- Project name: `batch-v2`
- Environments: `dev`, `uat`, `prod`
- AWS Account IDs:
  - Dev: `894546098844`
  - UAT: To be configured
  - Prod: To be configured
- Naming convention: `<prefix>-<project>-<env>-<resource>-<account_id>` (S3 only)
  - Example Lambda: `ts-batch-v2-dev-task-generator`
  - Example S3: `ts-batch-v2-dev-stock-prices-894546098844`
  - Example DynamoDB: `ts-batch-v2-dev-stock-prices`
- Region: `ap-southeast-1` (Singapore)
- IaC tool: Terraform

### 9.3 Terraform Workspace Strategy
```hcl
# Use Terraform workspaces for environment separation
# Workspaces: dev, uat, prod

locals {
  prefix      = "ts"
  project     = "batch-v2"
  environment = terraform.workspace
  name_prefix = "${local.prefix}-${local.project}-${local.environment}"
  
  common_tags = {
    Project     = local.project
    Environment = local.environment
    ManagedBy   = "Terraform"
  }
}

# Example resource naming
resource "aws_lambda_function" "task_generator" {
  function_name = "${local.name_prefix}-task-generator"
  # ...
}

resource "aws_s3_bucket" "stock_prices" {
  bucket = "${local.name_prefix}-stock-prices"
  # ...
}

resource "aws_dynamodb_table" "stock_prices" {
  name = "${local.name_prefix}-stock-prices"
  # ...
}
```

## 10. Monitoring & Observability

### 10.1 CloudWatch Metrics
- `DownloaderLambda/Invocations`: Total invocations
- `DownloaderLambda/Errors`: Error count
- `DownloaderLambda/Duration`: Execution time
- `MainQueue/ApproximateAgeOfOldestMessage`: Queue lag
- `DLQ/ApproximateNumberOfMessagesVisible`: Failed message count

### 10.2 CloudWatch Alarms
- Lambda error rate > 5% (5-minute period)
- DLQ depth > 100 messages
- Queue age > 1 hour (indicates processing bottleneck)

### 10.3 Structured Logging
All logs include:
- `requestId`: Unique identifier
- `symbol`: Stock ticker
- `date`: Target date
- `statusCode`: HTTP response code
- `duration`: Processing time (ms)
- `errorReason`: Error message (if failed)
