# Batch Processing System - Stock Price Ingestion

A serverless batch ingestion pipeline that downloads ~100,000 stock prices daily from EODHD API, stores raw data in S3, calculates exponential moving averages, and saves analytics to DynamoDB.

## Architecture

### High-Level Overview

```
┌─────────────────────┐
│  EventBridge        │  Daily trigger (configurable schedule)
│  Scheduler          │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Task Generator     │  Fetches symbol lists from EODHD API
│  Lambda             │  Creates ~100k download tasks
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  SQS Main Queue     │  Buffers download tasks
│  (download-queue)   │  Batch size: 10, Visibility: 5min
└──────────┬──────────┘
           │
           ├─────────────────────┐
           │                     │ (after 3 failed attempts)
           ▼                     ▼
┌─────────────────────┐   ┌─────────────────────┐
│  Downloader Lambda  │   │  Dead Letter Queue  │
│  (8 concurrent)     │   │  (DLQ)              │
│  - Fetch prices     │   └──────────┬──────────┘
│  - Compress to gzip │              │
│  - Calculate EMAs   │              │ (manual replay)
│  - Save to S3+DDB   │              │
└──────────┬──────────┘              ▼
           │                  ┌─────────────────────┐
           ├─────────────────>│  DLQ Replay Lambda  │
           │                  └─────────────────────┘
           ▼
    ┌──────────┐
    │    S3    │  Raw data archive (gzip JSON)
    │  Bucket  │  Key: prices/market={CODE}/dt={DATE}/symbol={SYM}/data.json.gz
    └──────────┘
           │
           ▼
    ┌──────────┐
    │ DynamoDB │  Queryable analytics (OHLC + EMAs)
    │  Table   │  Partition key: symbol (e.g., "AAPL.US")
    └──────────┘
```

### Data Flow

1. **EventBridge Scheduler** triggers Task Generator Lambda daily
2. **Task Generator** fetches symbol lists from EODHD API for configured markets (US, Thailand, Crypto)
3. **Task Generator** creates ~100,000 SQS messages (one per symbol)
4. **SQS Queue** buffers messages and triggers Downloader Lambda in batches of 10
5. **Downloader Lambda** (8 concurrent instances):
   - Fetches full historical price data from EODHD API
   - Compresses response as gzip JSON
   - Uploads to S3 with partitioned key structure
   - Calculates exponential moving averages (EMA 7, 30, 50, 200)
   - Saves OHLC data and EMAs to DynamoDB
6. **Failed messages** (after 3 retries) go to DLQ for manual investigation and replay

### Rate Limiting Strategy

- **API Limits**: 1,000 requests/minute, 100,000 requests/day
- **Lambda Concurrency**: 8 (reserved)
- **SQS Batch Size**: 10 messages per invocation
- **Throughput**: ~960-1,600 req/min (within limits with safety margin)
- **Completion Time**: ~1.5-2.5 hours for 100k requests

## Features

- **Daily batch ingestion** of ~100,000 stock prices from EODHD API
- **Multi-market support**: US stocks, Thailand Exchange (BK), Cryptocurrencies (CC)
- **Automatic EMA calculation**: 7, 30, 50, 200 periods using exponential moving average formula
- **Dual storage**: S3 for raw data archive, DynamoDB for queryable analytics
- **Rate limiting**: Respects EODHD API limits (1000 req/min, 100k req/day)
- **Retry logic**: Exponential backoff with jitter for transient failures
- **Dead Letter Queue**: Captures failed messages for investigation and replay
- **Multi-environment**: Separate dev, uat, prod environments using Terraform workspaces
- **Monitoring**: CloudWatch metrics, logs, and alarms for operational visibility
- **Idempotent operations**: Safe to retry and replay without data duplication

## Project Structure

```
.
├── lambdas/
│   ├── task-generator/          # Task Generator Lambda
│   │   ├── handler.py           # Lambda entry point
│   │   ├── task_generator.py    # Core logic
│   │   └── requirements.txt     # Dependencies
│   ├── downloader/              # Downloader Lambda
│   │   ├── handler.py           # Lambda entry point
│   │   ├── downloader.py        # Core logic (API, S3, DynamoDB, EMA)
│   │   └── requirements.txt     # Dependencies
│   ├── dlq-replay/              # DLQ Replay Lambda
│   │   ├── handler.py           # Lambda entry point
│   │   ├── dlq_replay.py        # Replay logic
│   │   └── requirements.txt     # Dependencies
│   └── common/                  # Shared utilities (future)
├── terraform/                   # Infrastructure as Code
│   ├── main.tf                  # Provider and backend config
│   ├── lambda.tf                # Lambda functions
│   ├── sqs.tf                   # SQS queues
│   ├── s3.tf                    # S3 bucket
│   ├── dynamodb.tf              # DynamoDB table
│   ├── eventbridge.tf           # EventBridge scheduler
│   ├── iam.tf                   # IAM roles and policies
│   ├── ssm.tf                   # Parameter Store
│   ├── secrets.tf               # Secrets Manager
│   ├── cloudwatch.tf            # CloudWatch alarms
│   ├── variables.tf             # Input variables
│   ├── outputs.tf               # Output values
│   └── locals.tf                # Local values
├── tests/                       # Unit and integration tests
│   ├── test_task_generator.py   # Task Generator tests
│   ├── test_downloader.py       # Downloader tests
│   ├── test_ema_calculation.py  # EMA calculation tests
│   ├── test_s3_key_formatting.py # S3 key tests
│   ├── test_dynamodb_save.py    # DynamoDB save tests
│   ├── test_integration_*.py    # Integration tests
│   └── conftest.py              # Pytest fixtures
├── scripts/                     # Deployment scripts
│   ├── deploy-dev.sh            # Automated deployment
│   ├── package-task-generator.sh
│   ├── package-downloader.sh
│   └── package-dlq-replay.sh
├── DEPLOYMENT.md                # Deployment guide
├── DEPLOYMENT_CHECKLIST.md      # Deployment checklist
├── MONITORING.md                # Monitoring and alerting guide
├── DLQ_REPLAY.md                # DLQ replay procedures
├── requirements.txt             # Python dependencies (dev)
├── pytest.ini                   # Pytest configuration
└── README.md                    # This file
```

## Prerequisites

- **Python 3.12+**: Lambda runtime
- **Terraform 1.0+**: Infrastructure provisioning
- **AWS CLI**: AWS resource management
- **AWS Account**: With appropriate permissions
- **EODHD API Token**: From [EODHD](https://eodhd.com/)

### AWS Account Configuration

- **Dev Account ID**: 894546098844
- **Region**: ap-southeast-1 (Singapore)
- **Required IAM Permissions**:
  - Lambda: Create, update, invoke functions
  - S3: Create buckets, put/get objects
  - DynamoDB: Create tables, put/get items
  - SQS: Create queues, send/receive messages
  - EventBridge: Create rules and targets
  - IAM: Create roles and policies
  - Secrets Manager: Create and read secrets
  - SSM Parameter Store: Create and read parameters
  - CloudWatch: Create log groups and alarms

## Quick Start

### 1. Install Dependencies

**macOS:**
```bash
# Install Terraform
brew tap hashicorp/tap
brew install hashicorp/tap/terraform

# Install AWS CLI
brew install awscli

# Install Python dependencies
pip install -r requirements.txt
```

**Verify installations:**
```bash
terraform --version  # Should be 1.0+
aws --version        # Should be 2.0+
python --version     # Should be 3.12+
```

### 2. Configure AWS Credentials

```bash
aws configure
```

Enter:
- **AWS Access Key ID**: [Your access key]
- **AWS Secret Access Key**: [Your secret key]
- **Default region**: ap-southeast-1
- **Default output format**: json

**Verify:**
```bash
aws sts get-caller-identity
# Should return account ID: 894546098844
```

### 3. Set Up Environment

```bash
# Clone repository
git clone <repository-url>
cd tradeseeker-batch-v2

# Copy environment template
cp .env.example .env

# Edit .env with your configuration (if needed)
# Most values are configured in Terraform
```

### 4. Deploy to Dev Environment

**Option A: Automated Deployment (Recommended)**

```bash
./scripts/deploy-dev.sh
```

This script will:
- Check prerequisites
- Package Lambda functions
- Create EODHD API secret
- Initialize Terraform
- Apply infrastructure
- Verify resources
- Optionally trigger a test run

**Option B: Manual Deployment**

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed step-by-step instructions.

**Quick manual steps:**

```bash
# 1. Package Lambda functions
./scripts/package-task-generator.sh
./scripts/package-downloader.sh
./scripts/package-dlq-replay.sh

# 2. Create API token secret
aws secretsmanager create-secret \
  --name ts-batch-v2-dev-eodhd-api-token \
  --secret-string '{"api_token":"YOUR_TOKEN"}' \
  --region ap-southeast-1

# 3. Deploy infrastructure
cd terraform
terraform init
terraform workspace new dev
terraform apply

# 4. Verify deployment
terraform output
```

### 5. Trigger a Test Run

```bash
aws lambda invoke \
  --function-name ts-batch-v2-dev-task-generator \
  --region ap-southeast-1 \
  --payload '{"date":"2024-02-15"}' \
  --cli-binary-format raw-in-base64-out \
  response.json

cat response.json
```

### 6. Monitor Execution

```bash
# Watch Downloader logs
aws logs tail /aws/lambda/ts-batch-v2-dev-downloader \
  --region ap-southeast-1 \
  --follow

# Check queue depth
aws sqs get-queue-attributes \
  --queue-url $(aws sqs get-queue-url --queue-name ts-batch-v2-dev-download-queue --region ap-southeast-1 --query 'QueueUrl' --output text) \
  --attribute-names ApproximateNumberOfMessages \
  --region ap-southeast-1

# Check S3 objects
aws s3 ls s3://ts-batch-v2-dev-stock-prices-894546098844/prices/ --recursive | head -20

# Check DynamoDB records
aws dynamodb scan \
  --table-name ts-batch-v2-dev-stock-prices \
  --region ap-southeast-1 \
  --max-items 5
```

## Usage

### Daily Automated Execution

The system runs automatically via EventBridge Scheduler:
- **Schedule**: Daily at configured time (default: 00:00 UTC)
- **Trigger**: EventBridge rule invokes Task Generator Lambda
- **Processing**: Automatically downloads all symbols from configured markets
- **Duration**: ~1.5-2.5 hours for 100,000 requests

**View schedule:**
```bash
aws events describe-rule \
  --name ts-batch-v2-dev-daily-trigger \
  --region ap-southeast-1
```

**Disable schedule (for maintenance):**
```bash
aws events disable-rule \
  --name ts-batch-v2-dev-daily-trigger \
  --region ap-southeast-1
```

**Re-enable schedule:**
```bash
aws events enable-rule \
  --name ts-batch-v2-dev-daily-trigger \
  --region ap-southeast-1
```

### Manual Execution

**Trigger for specific date:**
```bash
aws lambda invoke \
  --function-name ts-batch-v2-dev-task-generator \
  --region ap-southeast-1 \
  --payload '{"date":"2024-02-15"}' \
  --cli-binary-format raw-in-base64-out \
  response.json
```

**Trigger for today:**
```bash
aws lambda invoke \
  --function-name ts-batch-v2-dev-task-generator \
  --region ap-southeast-1 \
  --payload "{\"date\":\"$(date +%Y-%m-%d)\"}" \
  --cli-binary-format raw-in-base64-out \
  response.json
```

### Querying Data

**Query S3 for specific symbol:**
```bash
# List all dates for AAPL
aws s3 ls s3://ts-batch-v2-dev-stock-prices-894546098844/prices/market=US/ --recursive | grep AAPL

# Download specific file
aws s3 cp s3://ts-batch-v2-dev-stock-prices-894546098844/prices/market=US/dt=2024-02-15/symbol=AAPL/data.json.gz - | gunzip
```

**Query DynamoDB for specific symbol:**
```bash
# Get AAPL data
aws dynamodb get-item \
  --table-name ts-batch-v2-dev-stock-prices \
  --key '{"symbol":{"S":"AAPL.US"}}' \
  --region ap-southeast-1

# Query with projection (only get prices)
aws dynamodb get-item \
  --table-name ts-batch-v2-dev-stock-prices \
  --key '{"symbol":{"S":"AAPL.US"}}' \
  --projection-expression "prices" \
  --region ap-southeast-1
```

**Scan for all symbols in a market:**
```bash
aws dynamodb scan \
  --table-name ts-batch-v2-dev-stock-prices \
  --filter-expression "market_code = :market" \
  --expression-attribute-values '{":market":{"S":"US"}}' \
  --region ap-southeast-1
```

### Monitoring

**Check system health:**
```bash
# Lambda invocations (last hour)
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=ts-batch-v2-dev-downloader \
  --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum \
  --region ap-southeast-1

# Lambda errors (last hour)
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=ts-batch-v2-dev-downloader \
  --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum \
  --region ap-southeast-1

# DLQ depth
aws sqs get-queue-attributes \
  --queue-url $(aws sqs get-queue-url --queue-name ts-batch-v2-dev-download-dlq --region ap-southeast-1 --query 'QueueUrl' --output text) \
  --attribute-names ApproximateNumberOfMessages \
  --region ap-southeast-1
```

See [MONITORING.md](MONITORING.md) for comprehensive monitoring guide.

### Handling Failures

**Check DLQ for failed messages:**
```bash
DLQ_URL=$(aws sqs get-queue-url \
  --queue-name ts-batch-v2-dev-download-dlq \
  --region ap-southeast-1 \
  --query 'QueueUrl' \
  --output text)

aws sqs get-queue-attributes \
  --queue-url "$DLQ_URL" \
  --attribute-names All \
  --region ap-southeast-1
```

**Replay failed messages:**
```bash
aws lambda invoke \
  --function-name ts-batch-v2-dev-dlq-replay \
  --region ap-southeast-1 \
  --payload '{"maxMessages": 100}' \
  --cli-binary-format raw-in-base64-out \
  response.json
```

See [DLQ_REPLAY.md](DLQ_REPLAY.md) for detailed replay procedures.

## Testing

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/test_task_generator.py tests/test_downloader.py tests/test_ema_calculation.py

# Integration tests only
pytest tests/test_integration_*.py

# Specific test file
pytest tests/test_ema_calculation.py -v
```

### Run with Coverage

```bash
pytest --cov=lambdas --cov-report=html
open htmlcov/index.html
```

### Test Configuration

Tests use `moto` for AWS service mocking and `pytest` fixtures for setup/teardown.

**Key test files:**
- `test_task_generator.py`: Task generation and SQS batch creation
- `test_downloader.py`: API client, retry logic, compression
- `test_ema_calculation.py`: EMA calculation accuracy
- `test_s3_key_formatting.py`: S3 key structure validation
- `test_dynamodb_save.py`: DynamoDB save logic
- `test_integration_*.py`: End-to-end workflows

## Configuration

### Environments

The system supports multiple environments using Terraform workspaces:

- **dev**: Development environment (account: 894546098844)
- **uat**: User acceptance testing (to be configured)
- **prod**: Production environment (to be configured)

**Switch environments:**
```bash
cd terraform
terraform workspace select dev
terraform workspace select uat
terraform workspace select prod
```

### Naming Convention

All resources follow the pattern: `ts-batch-v2-{env}-{resource}-{account_id}`

**Examples:**
- Lambda: `ts-batch-v2-dev-task-generator`
- S3: `ts-batch-v2-dev-stock-prices-894546098844`
- DynamoDB: `ts-batch-v2-dev-stock-prices`
- SQS: `ts-batch-v2-dev-download-queue`

### Market Configuration

Markets are configured in SSM Parameter Store:

**Parameter**: `/ts-batch-v2/{env}/markets`

**Value:**
```json
[
  {"Name": "USA Stocks", "Code": "US"},
  {"Name": "Thailand Exchange", "Code": "BK"},
  {"Name": "Cryptocurrencies", "Code": "CC"}
]
```

**Update markets:**
```bash
aws ssm put-parameter \
  --name /ts-batch-v2/dev/markets \
  --value '[{"Name":"USA Stocks","Code":"US"},{"Name":"Thailand Exchange","Code":"BK"}]' \
  --type String \
  --overwrite \
  --region ap-southeast-1
```

### API Endpoints Configuration

API endpoints are configured in SSM Parameter Store:

**Parameter**: `/ts-batch-v2/{env}/api-endpoints`

**Value:**
```json
{
  "symbolListUrl": "https://eodhd.com/api/exchange-symbol-list/{MARKET_CODE}",
  "stockPriceUrl": "https://eodhd.com/api/eod/{SYMBOL}.{MARKET_CODE}"
}
```

### Rate Limiting Configuration

Rate limiting is controlled by Lambda configuration:

- **Reserved Concurrency**: 8 (set in Terraform)
- **SQS Batch Size**: 10 (set in Terraform)
- **Throughput**: ~960-1,600 req/min
- **API Limits**: 1,000 req/min, 100,000 req/day

**Adjust concurrency (if needed):**
```hcl
# terraform/lambda.tf
resource "aws_lambda_function" "downloader" {
  reserved_concurrent_executions = 8  # Adjust this value
}
```

### Environment Variables

Lambda functions use these environment variables (set by Terraform):

- `ENVIRONMENT`: Environment name (dev, uat, prod)
- `EODHD_SECRET_NAME`: Secrets Manager secret name
- `MARKETS_PARAMETER_NAME`: SSM parameter for markets
- `API_ENDPOINTS_PARAMETER_NAME`: SSM parameter for API endpoints
- `S3_BUCKET_NAME`: S3 bucket name
- `DYNAMODB_TABLE_NAME`: DynamoDB table name
- `SQS_QUEUE_URL`: Main queue URL
- `DLQ_URL`: Dead letter queue URL

## Data Schema

### S3 Object Structure

**Key Format:**
```
prices/market={MARKET_CODE}/dt={YYYY-MM-DD}/symbol={SYMBOL}/data.json.gz
```

**Examples:**
- `prices/market=US/dt=2024-02-15/symbol=AAPL/data.json.gz`
- `prices/market=BK/dt=2024-02-15/symbol=PTT/data.json.gz`
- `prices/market=CC/dt=2024-02-15/symbol=BTC-USD/data.json.gz`

**Content (gzip-compressed JSON):**
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
  ...
]
```

### DynamoDB Item Structure

**Table**: `ts-batch-v2-{env}-stock-prices`

**Partition Key**: `symbol` (e.g., "AAPL.US", "PTT.BK", "BTC-USD.CC")

**Item Structure:**
```json
{
  "symbol": "AAPL.US",
  "market_code": "US",
  "prices": [
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
  ],
  "moving_averages": [
    {
      "date": "2024-01-01",
      "ema_7": 100.5,
      "ema_30": 98.3,
      "ema_50": 97.1,
      "ema_200": 95.8
    },
    ...
  ],
  "updated_at": "2024-02-15T10:30:00Z"
}
```

**Note**: Each symbol has ONE item containing all historical data as nested lists.

### SQS Message Structure

**Queue**: `ts-batch-v2-{env}-download-queue`

**Message Body:**
```json
{
  "symbol": "AAPL",
  "marketCode": "US",
  "date": "2024-02-15",
  "apiEndpoint": "https://eodhd.com/api/eod/AAPL.US",
  "requestId": "AAPL-US-2024-02-15"
}
```

## Troubleshooting

### Common Issues

#### 1. Lambda Timeout Errors

**Symptoms**: Lambda execution exceeds 120 seconds

**Solutions:**
- Check CloudWatch logs for slow API responses
- Verify network connectivity to EODHD API
- Consider increasing Lambda timeout in Terraform
- Reduce SQS batch size if processing too many messages

#### 2. Rate Limit Errors (429)

**Symptoms**: HTTP 429 errors in logs

**Solutions:**
- Verify Lambda reserved concurrency is set to 8
- Check SQS batch size is set to 10
- Wait for rate limit to reset (1 minute)
- Review CloudWatch metrics for concurrent executions

#### 3. High DLQ Depth

**Symptoms**: Many messages in DLQ

**Solutions:**
- Check DLQ messages for error patterns
- Review CloudWatch logs for specific errors
- Fix root cause before replaying
- See [DLQ_REPLAY.md](DLQ_REPLAY.md) for replay procedures

#### 4. No Data in S3/DynamoDB

**Symptoms**: Empty or missing data

**Solutions:**
- Verify Task Generator ran successfully
- Check SQS queue has messages
- Review Downloader Lambda logs for errors
- Verify IAM permissions for S3/DynamoDB writes
- Check EODHD API token is valid

#### 5. Permission Errors

**Symptoms**: Access denied errors in logs

**Solutions:**
- Verify IAM roles have correct policies
- Check Lambda execution role permissions
- Ensure S3 bucket policy allows Lambda writes
- Verify Secrets Manager and SSM Parameter Store access

### Debug Commands

**View recent errors:**
```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/ts-batch-v2-dev-downloader \
  --filter-pattern "ERROR" \
  --region ap-southeast-1 \
  --max-items 20
```

**Check Lambda configuration:**
```bash
aws lambda get-function-configuration \
  --function-name ts-batch-v2-dev-downloader \
  --region ap-southeast-1
```

**Test API token:**
```bash
TOKEN=$(aws secretsmanager get-secret-value \
  --secret-id ts-batch-v2-dev-eodhd-api-token \
  --region ap-southeast-1 \
  --query 'SecretString' \
  --output text | jq -r '.api_token')

curl "https://eodhd.com/api/eod/AAPL.US?api_token=$TOKEN&fmt=json&limit=1"
```

## Documentation

- **[DEPLOYMENT.md](DEPLOYMENT.md)**: Detailed deployment guide with step-by-step instructions
- **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)**: Deployment checklist for tracking progress
- **[MONITORING.md](MONITORING.md)**: Monitoring, alerting, and observability guide
- **[DLQ_REPLAY.md](DLQ_REPLAY.md)**: DLQ investigation and replay procedures
- **[.kiro/specs/batch-processing/](.kiro/specs/batch-processing/)**: Feature specification documents
  - `requirements.md`: System requirements and acceptance criteria
  - `design.md`: Architecture and design decisions
  - `tasks.md`: Implementation task list

## Contributing

### Development Workflow

1. Create a feature branch
2. Make changes
3. Run tests: `pytest`
4. Update documentation if needed
5. Submit pull request

### Code Style

- Follow PEP 8 for Python code
- Use type hints where appropriate
- Add docstrings to functions and classes
- Keep functions small and focused

### Testing Requirements

- Write unit tests for new functionality
- Ensure integration tests pass
- Maintain >80% code coverage
- Test with mocked AWS services using `moto`

## Cost Estimation

### Monthly Costs (Dev Environment)

Assuming daily execution with 100,000 requests:

- **Lambda**: ~$5-10/month
  - Task Generator: ~$0.50 (1 invocation/day)
  - Downloader: ~$4-8 (10,000-12,500 invocations/day)
  - DLQ Replay: ~$0.10 (occasional use)
- **S3**: ~$5-15/month
  - Storage: ~$1-3 (depends on data retention)
  - Requests: ~$4-12 (100k PUT requests/day)
- **DynamoDB**: ~$5-20/month
  - On-demand pricing (depends on read/write patterns)
- **SQS**: ~$0.50/month
  - 100k messages/day = 3M messages/month
- **CloudWatch**: ~$2-5/month
  - Logs and metrics
- **Secrets Manager**: ~$0.40/month
  - 1 secret
- **EventBridge**: ~$0.01/month
  - 1 rule, 30 invocations/month

**Total**: ~$18-51/month (dev environment)

**Note**: Production costs will be higher with more data retention and higher read patterns.

## License

MIT

## Support

For issues or questions:
1. Check documentation in this repository
2. Review CloudWatch logs for errors
3. Consult [MONITORING.md](MONITORING.md) and [DLQ_REPLAY.md](DLQ_REPLAY.md)
4. Contact the development team
