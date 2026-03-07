# TradeSeekerAPI v2

A serverless REST API built on AWS Lambda and API Gateway that provides read-only access to stock market data stored in DynamoDB. The API exposes endpoints for querying golden cross signals and retrieving detailed stock price history with technical indicators.

## Features

- **Golden Cross Queries**: Filter and discover golden cross signals with customizable criteria
- **Stock Price Data**: Retrieve detailed price history with technical indicators
- **AI-Powered Analysis**: Get intelligent stock analysis and news summaries using OpenAI's ChatGPT
- **Serverless Architecture**: Built on AWS Lambda for automatic scaling and cost efficiency
- **Read-Only Access**: Safe, non-destructive queries to DynamoDB tables
- **Comprehensive Validation**: Clear error messages for invalid inputs
- **CORS Support**: Ready for web application integration

## Architecture

```
Client → API Gateway → Lambda → DynamoDB (golden-crosses, stock-prices)
                                    ↓
                              CloudWatch Logs
```

**Technology Stack:**
- Runtime: Python 3.12
- Cloud Provider: AWS (ap-southeast-1 region)
- Compute: AWS Lambda
- API Layer: AWS API Gateway (REST API)
- Database: Amazon DynamoDB (read-only)
- Infrastructure as Code: Terraform

## Prerequisites

Before deploying the API, ensure you have the following installed:

1. **Python 3.12**
   ```bash
   python3 --version  # Should show 3.12.x
   ```

2. **Terraform** (v1.0 or later)
   ```bash
   terraform --version
   ```

3. **AWS CLI** (configured with credentials)
   ```bash
   aws configure
   # Enter your AWS Access Key ID, Secret Access Key, and default region
   ```

4. **AWS Credentials**
   - Ensure your AWS credentials have permissions for:
     - Lambda function creation and management
     - API Gateway creation and management
     - IAM role and policy creation
     - DynamoDB read access (GetItem, Query, Scan)
     - CloudWatch Logs access

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/tradeseeker-api-v2.git
   cd tradeseeker-api-v2
   ```

2. **Install Python dependencies**
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Install development dependencies** (for testing)
   ```bash
   pip3 install -r requirements-dev.txt
   ```

## Configuration

### Environment Variables

The API uses the following environment variables (configured automatically by Terraform):

| Variable | Description | Default |
|----------|-------------|---------|
| `DYNAMODB_REGION` | AWS region for DynamoDB | `ap-southeast-1` |
| `OPENAI_API_KEY` | OpenAI API key for ChatGPT integration | Required for /openai-summary |
| `GOLDEN_CROSSES_TABLE` | DynamoDB table name for golden crosses | `ts-batch-v2-dev-golden-crosses` |
| `STOCK_PRICES_TABLE` | DynamoDB table name for stock prices | `ts-batch-v2-dev-stock-prices` |
| `CROSS_DATE_INDEX` | GSI name for cross date queries | `cross_date-index` |
| `MARKET_CROSS_DATE_INDEX` | GSI name for market+date queries | `market_code-cross_date-index` |

### Terraform Variables

Configure deployment settings in `terraform/variables.tf` or pass via command line:

| Variable | Description | Default |
|----------|-------------|---------|
| `environment` | Deployment environment | `dev` |
| `aws_region` | AWS region | `ap-southeast-1` |
| `golden_crosses_table_name` | Golden crosses table name | `ts-batch-v2-dev-golden-crosses` |
| `stock_prices_table_name` | Stock prices table name | `ts-batch-v2-dev-stock-prices` |

## Deployment

### Prerequisites for OpenAI Integration

To use the `/openai-summary` endpoint, you'll need an OpenAI API key:

1. **Get OpenAI API Key**
   - Sign up at [OpenAI Platform](https://platform.openai.com/)
   - Navigate to API Keys section
   - Create a new API key

2. **Set Environment Variable**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key-here"
   ```

   Or add it to your Lambda environment variables in `terraform/lambda.tf`:
   ```hcl
   environment {
     variables = {
       OPENAI_API_KEY = var.openai_api_key
     }
   }
   ```

### Quick Deployment

Use the provided deployment script:

```bash
./deploy.sh [environment]
```

Example:
```bash
./deploy.sh dev
```

The script will:
1. Check prerequisites
2. Install Python dependencies
3. Package the Lambda function
4. Initialize Terraform
5. Plan infrastructure changes
6. Apply changes (with confirmation)
7. Output API Gateway URL and Lambda ARN

### Manual Deployment

If you prefer manual deployment:

1. **Package Lambda function**
   ```bash
   # Install dependencies
   pip3 install -r requirements.txt -t ./package
   
   # Create deployment package
   cd package
   zip -r ../lambda_package.zip .
   cd ../src
   zip -g ../lambda_package.zip *.py handlers/*.py db/*.py
   cd ..
   ```

2. **Deploy with Terraform**
   ```bash
   cd terraform
   terraform init
   terraform plan -var="environment=dev"
   terraform apply -var="environment=dev"
   ```

3. **Get API endpoint**
   ```bash
   terraform output api_gateway_url
   ```

## API Documentation

### Base URL

After deployment, your API will be available at:
```
https://{api-id}.execute-api.ap-southeast-1.amazonaws.com/dev
```

### Endpoints

#### 1. Query Golden Crosses

**Endpoint:** `GET /golden-crosses`

**Description:** Query golden cross signals with optional filters.

**Query Parameters:**

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `min_green` | integer | No | Minimum green days percentage (0-100) | 70 |
| `max_red_candle` | integer | No | Maximum red candle percentage (-100 to 0) | -5 |
| `market` | string | No | Market code (US, BK, CC) | All markets |
| `date` | string | No | Specific date (YYYY-MM-DD) | All dates |
| `days` | integer | No | Last N days | All dates |

**Example Requests:**

```bash
# Get all golden crosses with default filters
curl https://your-api-url/golden-crosses

# Filter by market and minimum green days
curl "https://your-api-url/golden-crosses?market=US&min_green=80"

# Get golden crosses from specific date
curl "https://your-api-url/golden-crosses?date=2024-01-15"

# Get golden crosses from last 7 days
curl "https://your-api-url/golden-crosses?days=7"
```

**Response:**

```json
{
  "data": [
    {
      "symbol": "AAPL.US",
      "cross_date": "2024-01-15",
      "market_code": "US",
      "signal": "GOLDEN_CROSS",
      "ema_50": 185.42,
      "ema_200": 182.15,
      "crossover_strength": 1.8,
      "green_days_30d_pct": 75.5,
      "max_red_candle_30d_pct": -3.2,
      "detected_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### 2. Get Stock Price Data

**Endpoint:** `GET /stocks/{symbol}`

**Description:** Retrieve price history and technical indicators for a specific symbol.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `symbol` | string | Yes | Stock symbol with market code (e.g., AAPL.US) |

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | string | No | Start date for price filter (YYYY-MM-DD) |
| `end_date` | string | No | End date for price filter (YYYY-MM-DD) |
| `limit` | integer | No | Number of most recent records to return |

**Example Requests:**

```bash
# Get all price data for a symbol
curl https://your-api-url/stocks/AAPL.US

# Get price data for date range
curl "https://your-api-url/stocks/AAPL.US?start_date=2024-01-01&end_date=2024-01-31"

# Get last 30 price records
curl "https://your-api-url/stocks/AAPL.US?limit=30"
```

**Response:**

```json
{
  "data": {
    "symbol": "AAPL.US",
    "market_code": "US",
    "prices": [
      {
        "date": "2024-01-15",
        "open": 185.50,
        "high": 187.20,
        "low": 184.80,
        "close": 186.90,
        "volume": 52000000
      }
    ],
    "moving_averages": [
      {
        "date": "2024-01-15",
        "ema_7": 186.20,
        "ema_30": 183.50,
        "ema_50": 185.42,
        "ema_200": 182.15
      }
    ],
    "golden_cross": true,
    "golden_cross_date": "2024-01-15",
    "death_cross_date": null,
    "green_days_30d_pct": 75.5,
    "max_red_candle_30d_pct": -3.2
  }
}
```

#### 3. Get AI-Powered Stock Analysis

**Endpoint:** `GET /openai-summary`

**Description:** Generate intelligent stock analysis and news summaries using OpenAI's ChatGPT API.

**Query Parameters:**

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `symbol` | string | Yes | Stock symbol with market code (e.g., AAPL.US) | - |
| `analysis_type` | string | No | Type of analysis (news, technical, fundamental, all) | news |
| `model` | string | No | OpenAI model (gpt-4, gpt-3.5-turbo, gpt-4-turbo) | gpt-3.5-turbo |

**Analysis Types:**

- `news`: Latest news, market sentiment, and recent developments
- `technical`: Technical analysis with chart patterns and indicators
- `fundamental`: Financial performance and business fundamentals
- `all`: Comprehensive analysis covering all aspects

**Example Requests:**

```bash
# Get latest news analysis for Apple
curl "https://your-api-url/openai-summary?symbol=AAPL.US"

# Get technical analysis using GPT-4
curl "https://your-api-url/openai-summary?symbol=AAPL.US&analysis_type=technical&model=gpt-4"

# Get comprehensive analysis
curl "https://your-api-url/openai-summary?symbol=AAPL.US&analysis_type=all"
```

**Response:**

```json
{
  "data": {
    "symbol": "AAPL.US",
    "analysis_type": "news",
    "model": "gpt-3.5-turbo",
    "analysis": "Apple Inc. (AAPL) has shown strong performance in recent weeks...\n\n**Recent Developments:**\n- Q4 earnings beat expectations with revenue of $119.6B\n- iPhone 15 sales exceeding projections\n- Services revenue growing at 16% YoY\n\n**Market Sentiment:**\nAnalysts remain bullish with average price target of $200...\n\n**Disclaimer:** This analysis is for informational purposes only and should not be considered as investment advice.",
    "usage": {
      "prompt_tokens": 150,
      "completion_tokens": 300,
      "total_tokens": 450
    }
  }
}
```

### Error Responses

All errors return a consistent JSON structure:

```json
{
  "error": "Brief error description",
  "details": ["Specific error 1", "Specific error 2"]
}
```

**Common Error Codes:**

| Status Code | Description |
|-------------|-------------|
| 400 | Bad Request - Invalid parameters |
| 404 | Not Found - Symbol or endpoint not found |
| 405 | Method Not Allowed - Unsupported HTTP method |
| 500 | Internal Server Error - Server-side error |
| 503 | Service Unavailable - DynamoDB throttling |

**Example Error Response:**

```json
{
  "error": "Invalid parameters",
  "details": [
    "min_green must be between 0 and 100",
    "date must be in YYYY-MM-DD format"
  ]
}
```

## Testing

### Run Unit Tests

```bash
pytest tests/unit/ -v
```

### Run Property-Based Tests

```bash
pytest tests/property/ -v
```

### Run All Tests with Coverage

```bash
pytest tests/ --cov=src --cov-report=html
```

### Run Integration Tests

```bash
pytest tests/integration/ -v
```

## Development

### Project Structure

```
tradeseeker-api-v2/
├── src/
│   ├── lambda_handler.py          # Lambda entry point
│   ├── router.py                  # Request routing
│   ├── config.py                  # Environment configuration
│   ├── formatters.py              # Response formatting
│   ├── validators.py              # Input validation
│   ├── handlers/
│   │   ├── golden_crosses.py      # Golden cross endpoint
│   │   ├── stock_price.py         # Stock price endpoint
│   │   └── openai_summary.py      # OpenAI analysis endpoint
│   └── db/
│       └── dynamodb_client.py     # DynamoDB operations
├── tests/                         # Test suite
├── terraform/                     # Infrastructure as Code
├── requirements.txt               # Production dependencies
├── requirements-dev.txt           # Development dependencies
├── deploy.sh                      # Deployment script
└── README.md                      # This file
```

### Local Development

For local testing with mocked DynamoDB:

```python
# Use moto for DynamoDB mocking
import boto3
from moto import mock_dynamodb

@mock_dynamodb
def test_local():
    # Your test code here
    pass
```

## Monitoring

### CloudWatch Logs

Lambda function logs are automatically sent to CloudWatch Logs:

```bash
# View logs
aws logs tail /aws/lambda/tradeseeker-api-v2-dev --follow
```

### CloudWatch Metrics

Monitor Lambda performance:
- Invocations
- Duration
- Errors
- Throttles

Access metrics in AWS Console → CloudWatch → Metrics → Lambda

## Troubleshooting

### Common Issues

**1. Deployment fails with "Access Denied"**
- Ensure AWS credentials have necessary permissions
- Check IAM policies for Lambda, API Gateway, and DynamoDB access

**2. API returns 500 errors**
- Check CloudWatch Logs for detailed error messages
- Verify DynamoDB table names in environment variables
- Ensure Lambda has IAM permissions for DynamoDB

**3. API returns 503 (Service Unavailable)**
- DynamoDB is being throttled
- Consider increasing DynamoDB capacity or implementing exponential backoff

**4. Symbol not found (404)**
- Verify symbol format includes market code suffix (e.g., .US, .BK, .CC)
- Check if symbol exists in DynamoDB table

### Debug Mode

Enable detailed logging by setting log level in Lambda environment:

```bash
# In terraform/lambda.tf
environment {
  variables = {
    LOG_LEVEL = "DEBUG"
  }
}
```

## Security

### Best Practices

- API uses HTTPS only (enforced by API Gateway)
- Read-only DynamoDB access (no write operations)
- IAM roles follow principle of least privilege
- No sensitive data in error messages or logs
- CORS configured for specific origins (update in production)

### Future: Authentication with Cognito

For production deployment with user authentication:

1. Uncomment Cognito resources in `terraform/cognito.tf`
2. Deploy infrastructure
3. Configure Angular app with Cognito User Pool ID and Client ID
4. Users authenticate and receive JWT tokens
5. API Gateway validates tokens automatically

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Open an issue on GitHub
- Contact the development team

## Changelog

### v2.0.0 (Initial Release)
- Golden cross query endpoint with filtering
- Stock price query endpoint with date range filtering
- Serverless deployment on AWS Lambda
- Terraform infrastructure configuration
- Comprehensive test suite with property-based testing
