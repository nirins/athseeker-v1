# TradeSeekerV2 - Stock Market Analysis Platform

A comprehensive stock market analysis platform built with a modern serverless architecture. TradeSeekerV2 provides real-time stock data, technical analysis, and AI-powered insights through a unified web interface.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │    │   API Backend   │    │ Batch Processing│
│   (Angular 18)  │◄──►│   (AWS Lambda)  │◄──►│  (ETL Pipeline) │
│                 │    │                 │    │                 │
│ • Landing Page  │    │ • Golden Cross  │    │ • Daily Ingestion│
│ • Dashboard     │    │ • Stock Prices  │    │ • EMA Calculation│
│ • Stock Details │    │ • AI Analysis   │    │ • Data Storage  │
│ • Authentication│    │ • CORS Support  │    │ • Error Handling│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CloudFront    │    │   API Gateway   │    │   EventBridge   │
│   S3 Bucket     │    │   DynamoDB      │    │   SQS Queues    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Node.js 18+** (for web frontend)
- **Python 3.12+** (for API and batch processing)
- **AWS CLI** (configured with credentials)
- **Terraform 1.0+** (for infrastructure)

### One-Command Deployment

```bash
# Deploy everything
make all

# Or deploy components individually
make web    # Deploy web frontend
make api    # Deploy API backend
make batch  # Deploy batch processing
```

## 📁 Project Structure

```
tradeseeker-v2/
├── tradeseeker-api-v2/          # API Backend (AWS Lambda)
│   ├── src/                     # Python source code
│   ├── terraform/               # Infrastructure as Code
│   ├── tests/                   # Unit & integration tests
│   └── deploy.sh               # Deployment script
├── tradeseeker-batch-v2/        # Batch Processing (ETL)
│   ├── lambdas/                # Lambda functions
│   ├── terraform/              # Infrastructure as Code
│   ├── tests/                  # Test suite
│   └── scripts/                # Deployment scripts
├── tradeseeker-web-v2/          # Web Frontend (Angular)
│   └── tradeseeker-web-v2/     # Angular application
│       ├── src/                # TypeScript source
│       ├── terraform/          # S3/CloudFront config
│       └── scripts/            # Build & deploy scripts
├── Makefile                     # Root orchestration
├── .gitignore                   # Git ignore patterns
└── README.md                    # This file
```

## 🌐 Components

### 1. Web Frontend (`tradeseeker-web-v2/`)

**Technology**: Angular 18 with Server-Side Rendering (SSR)

**Features**:
- 🎨 Modern light theme UI
- 📱 Responsive design
- 🔐 User authentication (Cognito ready)
- 📊 Interactive stock dashboard
- 🔍 Stock detail views with charts
- ⚡ Fast loading with CDN

**Deployment**: S3 + CloudFront + Custom Domain

**Live URLs**:
- Primary: https://athseeker.com
- Alternate: https://www.athseeker.com
- CloudFront: https://d310shk0w5mump.cloudfront.net

### 2. API Backend (`tradeseeker-api-v2/`)

**Technology**: Python 3.12 on AWS Lambda

**Endpoints**:
- `GET /golden-crosses` - Query golden cross signals with filters
- `GET /stocks/{symbol}` - Get stock price history and technical indicators
- `GET /openai-summary` - AI-powered stock analysis using ChatGPT

**Features**:
- 🔄 Real-time data from DynamoDB
- 🤖 OpenAI integration for intelligent analysis
- 🛡️ Input validation and error handling
- 📈 Technical indicators (EMA 7, 30, 50, 200)
- 🌍 CORS support for web integration

**Infrastructure**: API Gateway + Lambda + DynamoDB

### 3. Batch Processing (`tradeseeker-batch-v2/`)

**Technology**: Python 3.12 serverless ETL pipeline

**Components**:
- **Task Generator**: Creates download tasks for ~100k symbols daily
- **Downloader**: Fetches stock data from EODHD API with rate limiting
- **DLQ Replay**: Handles failed downloads for retry

**Features**:
- 📅 Daily automated execution via EventBridge
- 🔄 Processes ~100,000 stock prices daily
- 💾 Dual storage: S3 (raw data) + DynamoDB (analytics)
- 🧮 Automatic EMA calculation
- 🛡️ Error handling with Dead Letter Queue
- 📊 Multi-market support (US, Thailand, Crypto)

**Infrastructure**: Lambda + SQS + S3 + DynamoDB + EventBridge

## 🛠️ Development

### Available Commands

```bash
# Main deployment commands
make all          # Deploy all components
make web          # Deploy web frontend only
make api          # Deploy API backend only
make batch        # Deploy batch processing only

# Testing
make test         # Run all tests
make api-test     # Test API only
make batch-test   # Test batch only
make web-test     # Test web only

# Maintenance
make clean        # Clean all build artifacts
make status       # Show component status
make install      # Install all dependencies

# Quick deployments (for development)
make api-quick    # Quick API deployment
make batch-quick  # Quick batch deployment
make web-quick    # Quick web deployment

# Environment-specific
make deploy-dev   # Deploy to dev environment
make deploy-staging # Deploy to staging
make deploy-prod  # Deploy to production
```

### Local Development Setup

1. **Clone and setup**:
```bash
git clone <repository-url>
cd tradeseeker-v2
make install
```

2. **Configure AWS credentials**:
```bash
aws configure
# Enter your AWS credentials and set region to ap-southeast-1
```

3. **Set up environment variables**:
```bash
# API requires OpenAI API key for /openai-summary endpoint
export OPENAI_API_KEY="your-openai-api-key"

# Batch requires EODHD API token
# This is stored in AWS Secrets Manager during deployment
```

4. **Deploy to development**:
```bash
make deploy-dev
```

### Component-Specific Development

**Web Frontend**:
```bash
cd tradeseeker-web-v2/tradeseeker-web-v2
npm install
npm start  # Development server
npm test   # Run tests
npm run build  # Production build
```

**API Backend**:
```bash
cd tradeseeker-api-v2
pip install -r requirements.txt -r requirements-dev.txt
pytest tests/  # Run tests
./deploy.sh dev  # Deploy to dev
```

**Batch Processing**:
```bash
cd tradeseeker-batch-v2
pip install -r requirements.txt
pytest  # Run tests
make deploy-all  # Deploy all lambdas
```

## 🔧 Configuration

### Environment Variables

**API Backend**:
- `OPENAI_API_KEY`: OpenAI API key for ChatGPT integration
- `DYNAMODB_REGION`: AWS region (ap-southeast-1)
- `GOLDEN_CROSSES_TABLE`: DynamoDB table for golden cross data
- `STOCK_PRICES_TABLE`: DynamoDB table for stock prices

**Batch Processing**:
- `EODHD_API_TOKEN`: EODHD API token (stored in Secrets Manager)
- `S3_BUCKET_NAME`: S3 bucket for raw data storage
- `SQS_QUEUE_URL`: Main processing queue URL

**Web Frontend**:
- `API_BASE_URL`: API Gateway endpoint URL
- `COGNITO_USER_POOL_ID`: Cognito User Pool (for authentication)

### AWS Resources

**Development Environment** (Account: 894546098844, Region: ap-southeast-1):

- **S3 Buckets**:
  - `ts-dev-web-v2-app`: Web frontend static files
  - `ts-batch-v2-dev-stock-prices-894546098844`: Raw stock data

- **DynamoDB Tables**:
  - `ts-batch-v2-dev-stock-prices`: Stock price analytics
  - `ts-batch-v2-dev-golden-crosses`: Golden cross signals
  - `ts-batch-v2-dev-death-crosses`: Death cross signals

- **Lambda Functions**:
  - `tradeseeker-api-v2-dev`: API backend
  - `ts-batch-v2-dev-task-generator`: ETL task generator
  - `ts-batch-v2-dev-downloader`: Stock data downloader
  - `ts-batch-v2-dev-dlq-replay`: Failed message replay

- **API Gateway**: REST API for frontend communication
- **CloudFront**: CDN for web frontend
- **SQS Queues**: Message queues for batch processing
- **EventBridge**: Daily scheduler for automated runs

## 📊 Data Flow

### Daily Batch Processing

1. **EventBridge** triggers Task Generator at scheduled time
2. **Task Generator** fetches symbol lists from EODHD API
3. **Task Generator** creates ~100k SQS messages (one per symbol)
4. **SQS** triggers Downloader Lambda in batches of 10
5. **Downloader** fetches historical data, calculates EMAs, stores in S3+DynamoDB
6. **Failed messages** go to DLQ for manual investigation and replay

### Real-Time API Access

1. **Web Frontend** makes API calls to API Gateway
2. **API Gateway** routes requests to appropriate Lambda functions
3. **Lambda** queries DynamoDB for real-time data
4. **Lambda** optionally calls OpenAI API for intelligent analysis
5. **Response** returned to frontend with formatted data

## 🔍 API Documentation

### Golden Cross Endpoint

```bash
GET /golden-crosses?min_green=70&market=US&days=7
```

**Parameters**:
- `min_green`: Minimum green days percentage (0-100)
- `max_red_candle`: Maximum red candle percentage (-100 to 0)
- `market`: Market code (US, BK, CC)
- `date`: Specific date (YYYY-MM-DD)
- `days`: Last N days

### Stock Price Endpoint

```bash
GET /stocks/AAPL.US?start_date=2024-01-01&limit=30
```

**Parameters**:
- `symbol`: Stock symbol with market code (e.g., AAPL.US)
- `start_date`: Start date for filtering
- `end_date`: End date for filtering
- `limit`: Number of records to return

### AI Analysis Endpoint

```bash
GET /openai-summary?symbol=AAPL.US&analysis_type=technical&model=gpt-4
```

**Parameters**:
- `symbol`: Stock symbol with market code
- `analysis_type`: news, technical, fundamental, all
- `model`: gpt-4, gpt-3.5-turbo, gpt-4-turbo

## 🧪 Testing

### Test Coverage

- **API Backend**: Unit tests, integration tests, property-based tests
- **Batch Processing**: Unit tests, integration tests, EMA calculation tests
- **Web Frontend**: Component tests, e2e tests

### Running Tests

```bash
# All tests
make test

# Component-specific tests
make api-test     # Python pytest
make batch-test   # Python pytest
make web-test     # Angular Jasmine/Karma

# With coverage
cd tradeseeker-api-v2 && pytest --cov=src --cov-report=html
cd tradeseeker-batch-v2 && pytest --cov=lambdas --cov-report=html
```

## 🚀 Deployment

### Environments

- **Development**: `dev` (current setup)
- **Staging**: `staging` (to be configured)
- **Production**: `prod` (to be configured)

### Deployment Process

1. **Automated** (recommended):
```bash
make all  # Deploys all components
```

2. **Manual** (for troubleshooting):
```bash
# Web
cd tradeseeker-web-v2/tradeseeker-web-v2
npm run build
./scripts/deploy.sh

# API
cd tradeseeker-api-v2
./deploy.sh dev

# Batch
cd tradeseeker-batch-v2
./scripts/package-*.sh  # Package all lambdas
cd terraform && terraform apply
```

### Rollback Strategy

- **Web**: Previous S3 objects are versioned
- **API**: Lambda versions are maintained
- **Batch**: Terraform state allows rollback
- **Infrastructure**: Terraform plan before apply

## 📈 Monitoring

### CloudWatch Metrics

- **Lambda**: Invocations, duration, errors, throttles
- **API Gateway**: Request count, latency, 4xx/5xx errors
- **DynamoDB**: Read/write capacity, throttling
- **S3**: Request metrics, data transfer

### Logs

```bash
# API logs
aws logs tail /aws/lambda/tradeseeker-api-v2-dev --follow

# Batch logs
aws logs tail /aws/lambda/ts-batch-v2-dev-downloader --follow

# Web logs (CloudFront)
# Available in AWS Console → CloudFront → Logs
```

### Alarms

- High error rates on Lambda functions
- DynamoDB throttling
- SQS DLQ depth
- CloudFront 5xx errors

## 💰 Cost Estimation

### Monthly Costs (Development Environment)

- **Lambda**: ~$10-15 (API + Batch processing)
- **S3**: ~$5-15 (Storage + requests)
- **DynamoDB**: ~$10-25 (On-demand pricing)
- **CloudFront**: ~$1-5 (CDN distribution)
- **API Gateway**: ~$3-10 (API requests)
- **Other**: ~$2-5 (SQS, Secrets Manager, etc.)

**Total**: ~$31-75/month for development environment

Production costs will scale with usage and data retention policies.

## 🔒 Security

### Best Practices Implemented

- **HTTPS Only**: All endpoints use TLS encryption
- **IAM Roles**: Principle of least privilege
- **API Keys**: Stored in AWS Secrets Manager
- **CORS**: Configured for specific origins
- **Input Validation**: All API inputs validated
- **Error Handling**: No sensitive data in error messages

### Authentication (Future)

- Cognito User Pools for user management
- JWT tokens for API authentication
- Role-based access control

## 🤝 Contributing

### Development Workflow

1. Create feature branch from `main`
2. Make changes in appropriate component directory
3. Run tests: `make test`
4. Deploy to dev: `make deploy-dev`
5. Test functionality
6. Submit pull request

### Code Standards

- **Python**: Follow PEP 8, use type hints
- **TypeScript**: Follow Angular style guide
- **Infrastructure**: Use Terraform best practices
- **Documentation**: Update README for new features

## 📚 Documentation

### Component Documentation

- **API**: `tradeseeker-api-v2/README.md`
- **Batch**: `tradeseeker-batch-v2/README.md`
- **Web**: `tradeseeker-web-v2/README.md`

### Additional Resources

- **Deployment Guide**: `tradeseeker-batch-v2/DEPLOYMENT.md`
- **Monitoring Guide**: `tradeseeker-batch-v2/MONITORING.md`
- **DLQ Procedures**: `tradeseeker-batch-v2/DLQ_REPLAY.md`

## 🐛 Troubleshooting

### Common Issues

1. **Deployment Failures**:
   - Check AWS credentials and permissions
   - Verify Terraform state is not locked
   - Ensure all prerequisites are installed

2. **API Errors**:
   - Check CloudWatch logs for detailed errors
   - Verify DynamoDB table names and regions
   - Confirm OpenAI API key is valid

3. **Batch Processing Issues**:
   - Check SQS DLQ for failed messages
   - Verify EODHD API token and rate limits
   - Monitor Lambda concurrency limits

4. **Web Frontend Issues**:
   - Clear CloudFront cache if changes not visible
   - Check browser console for JavaScript errors
   - Verify API endpoints are accessible

### Getting Help

1. Check component-specific README files
2. Review CloudWatch logs for errors
3. Consult AWS documentation
4. Open GitHub issue with detailed description

## 📄 License

MIT License - see individual component directories for specific license files.

## 🏆 Acknowledgments

- **EODHD**: Stock market data provider
- **OpenAI**: AI-powered analysis capabilities
- **AWS**: Cloud infrastructure platform
- **Angular**: Web frontend framework

---

**Built with ❤️ for traders and investors seeking data-driven insights.**