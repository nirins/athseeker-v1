# EveryATH (ATHSeeker) System Architecture

This document provides a comprehensive overview of the EveryATH platform architecture, including all components, data flows, and AWS services.

## System Overview

EveryATH is a systematic AI platform that identifies stocks reaching all-time highs across multiple markets (US, Thailand/BK, Crypto). The system consists of three main components:

1. **Batch Processing Pipeline** - Daily data ingestion and analysis
2. **REST API** - Serves processed data to clients
3. **Web Frontend** - Angular-based user interface

## Table of Contents

- [High-Level Architecture](#high-level-architecture)
- [Batch Processing Pipeline](#batch-processing-pipeline)
- [API Layer](#api-layer)
- [Frontend Application](#frontend-application)
- [Data Flow](#data-flow)
- [Infrastructure Details](#infrastructure-details)

---

## High-Level Architecture

```mermaid
graph TB
    subgraph "Users"
        User[Web Browser]
        Mobile[iOS App]
    end
    
    subgraph "DNS & CDN"
        Route53[Route53<br/>everyath.com<br/>athseeker.com]
        CF_Web[CloudFront<br/>Web CDN]
    end
    
    subgraph "Frontend - S3"
        S3_Web[S3 Bucket<br/>Static Website]
    end
    
    subgraph "API Layer"
        APIGW[API Gateway<br/>REST API]
        Lambda_API[Lambda<br/>API Handler]
    end
    
    subgraph "Batch Processing"
        EventBridge[EventBridge<br/>Schedulers]
        TaskGen[Task Generator<br/>Lambda]
        SQS[SQS Queue<br/>Download Tasks]
        DLQ[Dead Letter<br/>Queue]
        Downloader[Downloader<br/>Lambda]
        XPoster[X Poster<br/>Lambda]
    end
    
    subgraph "Data Storage"
        DDB_Prices[DynamoDB<br/>Stock Prices]
        DDB_Lite[DynamoDB<br/>Prices Lite]
        DDB_ATH[DynamoDB<br/>ATH Stocks]
        DDB_NearATH[DynamoDB<br/>Near ATH]
        DDB_Golden[DynamoDB<br/>Golden Crosses]
        DDB_Death[DynamoDB<br/>Death Crosses]
        DDB_Watch[DynamoDB<br/>Watchlist]
        S3_Training[S3<br/>Training Data]
    end
    
    subgraph "External Services"
        EODHD[EODHD API<br/>Market Data]
        Twitter[X/Twitter API]
        OpenAI[OpenAI API]
    end
    
    subgraph "Auth & Monitoring"
        Cognito[Cognito<br/>User Pool]
        SNS[SNS Topics]
        CloudWatch[CloudWatch<br/>Logs & Alarms]
        Secrets[Secrets Manager]
    end
    
    User --> Route53
    Mobile --> Route53
    Route53 --> CF_Web
    CF_Web --> S3_Web
    S3_Web --> APIGW
    APIGW --> Lambda_API
    Lambda_API --> DDB_Prices
    Lambda_API --> DDB_Lite
    Lambda_API --> DDB_ATH
    Lambda_API --> DDB_NearATH
    Lambda_API --> DDB_Golden
    Lambda_API --> DDB_Death
    Lambda_API --> DDB_Watch
    Lambda_API --> S3_Training
    Lambda_API --> OpenAI
    Lambda_API --> Secrets
    
    EventBridge --> TaskGen
    EventBridge --> XPoster
    TaskGen --> SQS
    SQS --> Downloader
    SQS --> DLQ
    Downloader --> EODHD
    Downloader --> DDB_Prices
    Downloader --> DDB_Lite
    Downloader --> DDB_ATH
    Downloader --> DDB_NearATH
    Downloader --> DDB_Golden
    Downloader --> DDB_Death
    XPoster --> Twitter
    XPoster --> DDB_ATH
    
    Cognito --> SNS
    Lambda_API --> CloudWatch
    TaskGen --> CloudWatch
    Downloader --> CloudWatch
    
    style User fill:#e1f5ff
    style Mobile fill:#e1f5ff
    style CF_Web fill:#ff9900
    style APIGW fill:#ff9900
    style Lambda_API fill:#ff9900
    style TaskGen fill:#ff9900
    style Downloader fill:#ff9900
    style XPoster fill:#ff9900
    style DDB_Prices fill:#4053d6
    style DDB_ATH fill:#4053d6
    style S3_Web fill:#569a31
    style S3_Training fill:#569a31
```

---

## Batch Processing Pipeline

The batch processing pipeline runs daily to fetch market data, calculate technical indicators, and detect trading signals.

### Batch Processing Flow

```mermaid
flowchart TD
    Start([Daily Trigger]) --> EB_US[EventBridge<br/>US: 7PM NY]
    Start --> EB_BK[EventBridge<br/>BK: 7PM Bangkok]
    Start --> EB_CC[EventBridge<br/>CC: 8AM Bangkok]
    Start --> EB_X[EventBridge<br/>X Post: 9PM NY]
    
    EB_US --> TG[Task Generator Lambda]
    EB_BK --> TG
    EB_CC --> TG
    
    TG --> |Fetch Symbol List| EODHD_API[EODHD API<br/>Exchange Symbols]
    EODHD_API --> TG
    TG --> |Filter Symbols| Filter{Filter:<br/>Common Stock<br/>NASDAQ/NYSE/etc}
    Filter --> |Create Tasks| SQS_Main[SQS Main Queue<br/>~20k messages]
    
    SQS_Main --> |Batch: 100| DL[Downloader Lambda<br/>Concurrent: 10]
    
    DL --> |Fetch OHLCV| EODHD_Data[EODHD API<br/>Historical Data]
    EODHD_Data --> DL
    
    DL --> |Calculate EMAs| Process[Process:<br/>- EMA 7,30,50,200<br/>- Golden/Death Cross<br/>- ATH Detection<br/>- Beauty Score]
    
    Process --> Save{Save Results}
    Save --> |Full Data<br/>3 years| DDB_Full[DynamoDB<br/>Stock Prices]
    Save --> |Lite Data<br/>360 days| DDB_Lite_Save[DynamoDB<br/>Stock Prices Lite]
    Save --> |ATH Records| DDB_ATH_Save[DynamoDB<br/>ATH Table]
    Save --> |Near ATH| DDB_Near[DynamoDB<br/>Near ATH Table]
    Save --> |Golden Cross| DDB_GC[DynamoDB<br/>Golden Crosses]
    Save --> |Death Cross| DDB_DC[DynamoDB<br/>Death Crosses]
    
    DL --> |Failed| Retry{Retry Count<br/>< 3?}
    Retry --> |Yes| SQS_Main
    Retry --> |No| DLQ_Final[Dead Letter Queue]
    
    EB_X --> XPost[X Poster Lambda]
    XPost --> |Read Top ATH| DDB_ATH_Read[DynamoDB ATH]
    DDB_ATH_Read --> XPost
    XPost --> |Post Tweet| Twitter[X/Twitter API]
    
    style Start fill:#90EE90
    style EB_US fill:#FFD700
    style EB_BK fill:#FFD700
    style EB_CC fill:#FFD700
    style DDB_Full fill:#4053d6
    style DDB_ATH_Save fill:#4053d6
    style SQS_Main fill:#FF6347
    style DLQ_Final fill:#8B0000
```

### Batch Schedule

| Market | Trigger Time | EventBridge Schedule | Frequency |
|--------|-------------|---------------------|-----------|
| **US** | 7 PM New York | `cron(0 23 ? * MON-FRI *)` | Mon-Fri |
| **BK** (Thailand) | 7 PM Bangkok | `cron(0 12 ? * MON-FRI *)` | Mon-Fri |
| **CC** (Crypto) | 8 AM Bangkok | `cron(0 1 * * ? *)` | Daily |
| **X Poster** | 9 PM New York | `cron(0 2 ? * TUE-SAT *)` | Mon-Fri |


### Processing Details

**Task Generator Lambda:**
- Fetches exchange symbol list from EODHD API
- Filters to Common Stock, ETF on major exchanges (NASDAQ, NYSE, AMEX for US)
- Generates ~20,000 download tasks for US market
- Sends tasks to SQS queue in batches

**Downloader Lambda:**
- Triggered by SQS messages (batch size: 100)
- Concurrent executions: 10
- Fetches 3 years of historical OHLCV data
- Calculates EMAs (7, 30, 50, 200 periods)
- Detects Golden Cross (EMA7 > EMA30) and Death Cross (EMA7 < EMA30)
- Identifies ATH (new all-time high) and Near ATH (within 5% of ATH)
- Calculates "Beauty Score" based on EMA alignment
- Stores full data (3 years) and lite data (360 days)


---

## API Layer

The API layer provides REST endpoints for the frontend to query processed stock data.

### API Architecture

```mermaid
flowchart LR
    Client[Web/Mobile<br/>Client] --> |HTTPS| APIGW[API Gateway<br/>REST API]
    
    APIGW --> |Invoke| Lambda[Lambda Function<br/>Python Router]
    
    Lambda --> Router{Route Handler}
    
    Router --> |/ath| ATH_Handler[ATH Stocks<br/>Handler]
    Router --> |/near-ath| NearATH_Handler[Near ATH<br/>Handler]
    Router --> |/golden-crosses| GC_Handler[Golden Cross<br/>Handler]
    Router --> |/death-crosses| DC_Handler[Death Cross<br/>Handler]
    Router --> |/stocks/batch| Batch_Handler[Batch Stock<br/>Handler]
    Router --> |/stocks/:symbol| Stock_Handler[Stock Detail<br/>Handler]
    Router --> |/watchlist| Watchlist_Handler[Watchlist<br/>Handler]
    Router --> |/training-data| Training_Handler[Training Data<br/>Handler]
    Router --> |/openai-summary| OpenAI_Handler[OpenAI Summary<br/>Handler]
    
    ATH_Handler --> DDB_ATH[DynamoDB<br/>ATH Table]
    NearATH_Handler --> DDB_Near[DynamoDB<br/>Near ATH]
    GC_Handler --> DDB_GC[DynamoDB<br/>Golden Crosses]
    DC_Handler --> DDB_DC[DynamoDB<br/>Death Crosses]
    Batch_Handler --> DDB_Lite[DynamoDB<br/>Prices Lite]
    Stock_Handler --> DDB_Full[DynamoDB<br/>Prices Full]
    Watchlist_Handler --> DDB_Watch[DynamoDB<br/>Watchlist]
    Training_Handler --> S3[S3<br/>Training Data]
    OpenAI_Handler --> OpenAI[OpenAI API]
    OpenAI_Handler --> Secrets[Secrets Manager<br/>API Keys]
    
    DDB_ATH --> ATH_Handler
    DDB_Near --> NearATH_Handler
    DDB_GC --> GC_Handler
    DDB_DC --> DC_Handler
    DDB_Lite --> Batch_Handler
    DDB_Full --> Stock_Handler
    DDB_Watch --> Watchlist_Handler
    OpenAI --> OpenAI_Handler
    
    ATH_Handler --> Lambda
    NearATH_Handler --> Lambda
    GC_Handler --> Lambda
    DC_Handler --> Lambda
    Batch_Handler --> Lambda
    Stock_Handler --> Lambda
    Watchlist_Handler --> Lambda
    Training_Handler --> Lambda
    OpenAI_Handler --> Lambda
    
    Lambda --> APIGW
    APIGW --> Client
    
    style APIGW fill:#ff9900
    style Lambda fill:#ff9900
    style DDB_ATH fill:#4053d6
    style DDB_Lite fill:#4053d6
    style S3 fill:#569a31
```

### API Endpoints

| Endpoint | Method | Purpose | DynamoDB Table |
|----------|--------|---------|----------------|
| `/ath` | GET | Get ATH stocks by market | `ath` |
| `/near-ath` | GET | Get near-ATH stocks | `near-ath` |
| `/golden-crosses` | GET | Get golden cross signals | `golden-crosses` |
| `/death-crosses` | GET | Get death cross signals | `death-crosses` |
| `/stocks/batch` | GET | Get multiple stocks (lite data) | `stock-prices-lite` |
| `/stocks/:symbol` | GET | Get single stock (full data) | `stock-prices` |
| `/stocks/:symbol/history` | GET | Get historical data | `stock-prices` |
| `/watchlist` | GET/POST/DELETE | User watchlist management | `watchlist` |
| `/training-data/save-by-grade` | POST | Save training data to S3 | S3 bucket |
| `/openai-summary` | GET | Get AI-generated summary | OpenAI API |

### Authentication

- **Public Endpoints**: ATH, Near-ATH, Golden/Death Crosses, Stocks (no auth required)
- **Private Endpoints**: Watchlist (Cognito auth - planned but not implemented yet)
- **API Keys**: None currently (consider adding for rate limiting)


---

## Frontend Application

### Frontend Architecture

```mermaid
flowchart TD
    User[User Browser<br/>iOS App] --> DNS[Route53<br/>everyath.com<br/>athseeker.com]
    
    DNS --> CF[CloudFront CDN<br/>Global Edge Locations]
    
    CF --> S3[S3 Bucket<br/>Static Website<br/>Angular Build]
    
    S3 --> App[Angular Application]
    
    App --> Components{Components}
    
    Components --> Landing[Landing Page<br/>Marketing]
    Components --> Dashboard[Dashboard<br/>Stock Lists]
    Components --> StockDetail[Stock Detail<br/>Charts & Analysis]
    Components --> Training[Training Mode<br/>Grade Stocks]
    
    App --> Services{Angular Services}
    
    Services --> API_Service[API Service<br/>HTTP Client]
    Services --> Auth_Service[Auth Service<br/>Cognito]
    Services --> Cache_Service[Cache Service<br/>Local Storage]
    
    API_Service --> |HTTPS REST| APIGW[API Gateway<br/>https://56qpa0i92h...]
    
    Cache_Service --> LocalCache[Browser Storage<br/>5min TTL]
    
    Auth_Service --> Cognito[AWS Cognito<br/>User Pool]
    
    style CF fill:#ff9900
    style S3 fill:#569a31
    style App fill:#dd0031
    style APIGW fill:#ff9900
```


### Frontend Technology Stack

- **Framework**: Angular 19
- **UI Library**: Angular Material
- **Charts**: Lightweight Charts (TradingView)
- **State Management**: RxJS Observables
- **Build Tool**: Angular CLI / esbuild
- **Deployment**: S3 + CloudFront
- **Mobile**: Capacitor (iOS)

### Key Features

1. **Landing Page**: Marketing content, call-to-action
2. **Dashboard**: Browse ATH stocks, filter by market, sort by beauty score
3. **Stock Detail**: Interactive charts, technical indicators, price history
4. **Training Mode**: Label stocks with grades (A-F) for ML training data
5. **Watchlist**: Save favorite stocks (authenticated users)
6. **Multi-Market**: Support for US, Thailand (BK), Crypto (CC)


---

## Data Flow

### User Request Flow

```mermaid
sequenceDiagram
    actor User
    participant Browser
    participant CloudFront
    participant S3
    participant APIGW as API Gateway
    participant Lambda
    participant DynamoDB
    participant Cache as Browser Cache
    
    User->>Browser: Visit everyath.com
    Browser->>CloudFront: Request index.html
    CloudFront->>S3: Fetch static files
    S3-->>CloudFront: HTML, JS, CSS
    CloudFront-->>Browser: Cached response
    Browser->>User: Render Landing Page
    
    User->>Browser: Click "View Stocks"
    Browser->>Cache: Check cache (5min TTL)
    
    alt Cache Miss
        Browser->>APIGW: GET /ath?market=US&limit=50
        APIGW->>Lambda: Invoke with request
        Lambda->>DynamoDB: Query ATH table<br/>Filter: market=US<br/>Sort: beauty_score DESC
        DynamoDB-->>Lambda: Return top 50 stocks
        Lambda->>Lambda: Format response
        Lambda-->>APIGW: JSON response
        APIGW-->>Browser: Stock list
        Browser->>Cache: Store in cache (5min)
    else Cache Hit
        Cache-->>Browser: Return cached data
    end
    
    Browser->>User: Display stock list
    
    User->>Browser: Click stock symbol
    Browser->>APIGW: GET /stocks/batch?symbols=AAPL,MSFT...
    APIGW->>Lambda: Invoke batch request
    Lambda->>DynamoDB: BatchGetItem (Lite table)<br/>360 days of data
    DynamoDB-->>Lambda: Price history + EMAs
    Lambda-->>APIGW: Batch response
    APIGW-->>Browser: Stock data
    Browser->>User: Render charts
```

### Daily Batch Processing Flow

```mermaid
sequenceDiagram
    participant EB as EventBridge
    participant TG as Task Generator
    participant EODHD as EODHD API
    participant SQS
    participant DL as Downloader
    participant DDB as DynamoDB
    
    Note over EB: 7 PM NY Time (US Market)
    EB->>TG: Trigger with market=US
    TG->>EODHD: GET /exchange-symbol-list/US
    EODHD-->>TG: 51,505 symbols
    TG->>TG: Filter to Common Stock<br/>NASDAQ, NYSE, AMEX<br/>Result: ~20,000 symbols
    
    loop For each symbol
        TG->>SQS: Send download task
    end
    
    TG-->>EB: Complete (5 minutes)
    
    Note over SQS,DL: Parallel Processing (10 concurrent)
    
    loop Process Queue
        SQS->>DL: Batch of 100 tasks
        DL->>EODHD: GET /eod/:symbol<br/>3 years historical
        EODHD-->>DL: OHLCV data
        
        DL->>DL: Calculate EMAs<br/>Detect patterns<br/>Calculate beauty score
        
        alt New ATH Detected
            DL->>DDB: Write to ATH table<br/>TTL: 30 days
        end
        
        alt Golden Cross Detected
            DL->>DDB: Write to Golden Cross table<br/>TTL: 30 days
        end
        
        DL->>DDB: Write to Prices table (full)
        DL->>DDB: Write to Prices Lite table (360d)
        DL-->>SQS: ACK message
    end
    
    Note over SQS,DL: Processing completes in ~2 hours
```

---

## Infrastructure Details

### AWS Services Used

| Service | Purpose | Configuration |
|---------|---------|---------------|
| **Route53** | DNS management | Hosted zones for everyath.com, athseeker.com |
| **CloudFront** | CDN for web app | Price class 100, HTTPS only |
| **S3** | Static website hosting, training data | Versioning enabled, encrypted |
| **API Gateway** | REST API endpoints | Regional, CORS enabled, **cache disabled** |
| **Lambda** | Serverless compute | Python 3.12, 512MB-3GB memory |
| **DynamoDB** | NoSQL database | Pay-per-request, TTL enabled, PITR enabled |
| **SQS** | Message queue | Visibility timeout: 900s, DLQ enabled |
| **EventBridge** | Scheduled triggers | Multiple schedules for different markets |
| **Cognito** | User authentication | User pool with email verification |
| **Secrets Manager** | API key storage | EODHD, OpenAI, X API keys |
| **CloudWatch** | Logging & monitoring | Lambda logs, alarms for DLQ depth |
| **SNS** | Notifications | User signup notifications |
| **ACM** | SSL certificates | Multi-domain cert (*.everyath.com, *.athseeker.com) |


### DynamoDB Tables

| Table Name | Hash Key | Range Key | GSI | TTL | Purpose |
|------------|----------|-----------|-----|-----|---------|
| `stock-prices` | symbol | - | - | No | Full stock data (3 years) |
| `stock-prices-lite` | symbol | - | - | No | Lite data (360 days) for batch API |
| `ath` | symbol | - | market_code, beauty_score | 30d | ATH detection records |
| `near-ath` | symbol | - | market_code, beauty_score | 30d | Near-ATH records |
| `golden-crosses` | symbol | cross_date | market_code-cross_date | 30d | Golden cross signals |
| `death-crosses` | symbol | cross_date | market_code-cross_date | 30d | Death cross signals |
| `watchlist` | user_id | symbol | - | No | User watchlists |


### Lambda Functions

| Function | Trigger | Memory | Timeout | Concurrency | Purpose |
|----------|---------|--------|---------|-------------|---------|
| **task-generator** | EventBridge | 512 MB | 15 min | 1 | Generate download tasks |
| **downloader** | SQS | 3 GB | 15 min | 10 | Fetch & process stock data |
| **dlq-replay** | Manual | 512 MB | 5 min | 1 | Replay failed tasks |
| **x-poster** | EventBridge | 512 MB | 1 min | 1 | Post to X/Twitter |
| **tradeseeker-api** | API Gateway | 512 MB | 30 sec | 100 | Handle API requests |
| **cognito-signup-notify** | Cognito | 256 MB | 10 sec | 5 | Send signup notifications |


### Cost Optimization

**Recent Changes (July 2026):**
- ✅ **Disabled API Gateway cache cluster**: Saved $14.40/month (99% cost reduction)
  - Cache had 0% hit rate
  - Base cost eliminated
  - Client-side caching (5min TTL) provides adequate performance
- 🔄 **Proposed: CloudFront for API caching**: Free tier eligible
  - Better performance with edge locations
  - No base cost (pay per use)
  - Can implement if performance degrades

**Current Monthly Costs (estimated):**
- API Gateway: ~$0.01/month (~3,000 requests)
- Lambda: ~$5-10/month (batch processing)
- DynamoDB: ~$10-20/month (pay-per-request)
- CloudFront: Free tier (< 1TB transfer)
- S3: ~$1/month (storage + requests)
- **Total: ~$16-31/month**


### Security Features

1. **Encryption at Rest**
   - DynamoDB: Server-side encryption enabled
   - S3: Default encryption enabled
   - Secrets Manager: Encrypted storage for API keys

2. **Encryption in Transit**
   - HTTPS only (CloudFront, API Gateway)
   - TLS 1.2+ enforced

3. **IAM Roles & Policies**
   - Least privilege access
   - Lambda execution roles with scoped permissions
   - No hardcoded credentials

4. **API Security**
   - CORS enabled for specific origins
   - Rate limiting: Planned (not yet implemented)
   - Authentication: Cognito ready (not enforced on public endpoints)


5. **Monitoring & Alerts**
   - CloudWatch Logs for all Lambda functions
   - DLQ depth alarms
   - Queue age alarms

---

## Deployment Architecture

### Multi-Environment Setup

```mermaid
graph LR
    subgraph "Development"
        Dev_Code[Local Code] --> Dev_Build[Build Process]
        Dev_Build --> Dev_Deploy[Deploy Script]
        Dev_Deploy --> Dev_AWS[AWS Dev Env]
    end
    
    subgraph "Production"
        Prod_Code[Git Repository] --> Prod_Build[CI/CD Pipeline]
        Prod_Build --> Prod_Deploy[Terraform Apply]
        Prod_Deploy --> Prod_AWS[AWS Prod Env]
    end
    
    style Dev_AWS fill:#FFE5B4
    style Prod_AWS fill:#90EE90
```


### Deployment Process

#### Frontend (Web App)
```bash
cd tradeseeker-web-v2/tradeseeker-web-v2
make all
# Steps:
# 1. npm run build (Angular production build)
# 2. aws s3 sync dist/ to S3 bucket
# 3. aws cloudfront create-invalidation
```

#### API Layer
```bash
cd tradeseeker-api-v2
make deploy
# Steps:
# 1. Install Python dependencies
# 2. Package Lambda function (zip)
# 3. terraform init
# 4. terraform plan
# 5. terraform apply (updates Lambda + API Gateway)
```

#### Batch Processing
```bash
cd tradeseeker-batch-v2
make deploy
# Steps:
# 1. Package Lambda functions
# 2. terraform apply (updates all batch Lambdas)
```


#### iOS App
```bash
cd tradeseeker-web-v2/tradeseeker-web-v2
make ios
# Steps:
# 1. npm run build
# 2. npx cap sync ios
# 3. open ios/App/App.xcworkspace (Xcode)
# 4. Manual build & deploy via Xcode
```

---

## Performance Characteristics

### API Response Times

| Endpoint | Response Time | Data Size | Caching |
|----------|---------------|-----------|---------|
| `/ath` | 100-200ms | ~50 stocks | Client: 5min |
| `/stocks/batch` | 200-500ms | ~10 stocks | Client: 5min |
| `/stocks/:symbol` | 150-300ms | 1 stock (3yr) | Client: 5min |

### Batch Processing Times

| Market | Symbols | Processing Time | Concurrency |
|--------|---------|-----------------|-------------|
| **US** | ~20,000 | ~2 hours | 10 Lambdas |
| **BK** | ~800 | ~10 minutes | 10 Lambdas |
| **CC** | ~500 | ~5 minutes | 10 Lambdas |


### Scalability

**Current Capacity:**
- API Gateway: 10,000 requests/second (AWS default)
- Lambda API: 100 concurrent executions
- Lambda Downloader: 10 concurrent executions
- DynamoDB: Pay-per-request (unlimited throughput)
- SQS: Unlimited messages

**Bottlenecks:**
- EODHD API rate limits (main constraint for batch processing)
- Lambda concurrency (can be increased)
- Frontend CloudFront edge cache (already optimized)

---

## Future Enhancements

### Planned Features

1. **API Caching with CloudFront**
   - Status: Infrastructure ready (cloudfront_api.tf created)
   - Benefit: Faster response times, lower Lambda invocations
   - Cost: Free tier eligible


2. **API Authentication & Rate Limiting**
   - Add API keys for frontend apps
   - Implement Cognito authorizer for private endpoints
   - Usage plans with throttling (100 req/sec, 10k/day)

3. **Real-time Updates**
   - WebSocket API for live stock updates
   - Server-Sent Events for notifications

4. **Advanced Analytics**
   - More technical indicators (RSI, MACD, Bollinger Bands)
   - Pattern recognition (head & shoulders, double top/bottom)
   - Backtesting framework

5. **Machine Learning**
   - Use training data to build predictive models
   - Beauty score ML model (currently rule-based)
   - Stock price prediction

6. **Mobile Apps**
   - iOS App Store deployment (Capacitor ready)
   - Android version


7. **Social Features**
   - User profiles
   - Share watchlists
   - Community discussions

---

## Technology Stack Summary

### Frontend
- **Framework**: Angular 19
- **Language**: TypeScript 5.7
- **UI**: Angular Material
- **Charts**: Lightweight Charts (TradingView)
- **State**: RxJS
- **Mobile**: Capacitor
- **Hosting**: S3 + CloudFront

### Backend
- **Runtime**: Python 3.12
- **Framework**: AWS Lambda (serverless)
- **API**: AWS API Gateway (REST)
- **Database**: AWS DynamoDB (NoSQL)
- **Queue**: AWS SQS
- **Scheduler**: AWS EventBridge
- **Auth**: AWS Cognito
- **Secrets**: AWS Secrets Manager


### Infrastructure
- **IaC**: Terraform
- **CI/CD**: Manual deployment scripts (Makefile)
- **Monitoring**: CloudWatch
- **DNS**: Route53
- **CDN**: CloudFront
- **Region**: ap-southeast-1 (Singapore)

### External APIs
- **Market Data**: EODHD (https://eodhd.com)
- **AI**: OpenAI GPT
- **Social**: X/Twitter API

---

## Repository Structure

```
athseeker-v1/
├── docs/
│   └── ARCHITECTURE.md              # This file
├── tradeseeker-api-v2/              # REST API
│   ├── src/                         # Lambda source code
│   │   ├── handlers/               # API route handlers
│   │   ├── db/                     # DynamoDB client
│   │   └── lambda_handler.py       # Main entry point
│   ├── terraform/                   # Infrastructure as Code
│   │   ├── api_gateway.tf
│   │   ├── lambda.tf
│   │   ├── dynamodb.tf
│   │   └── ...
│   ├── Makefile                     # Deployment commands
│   └── deploy.sh                    # Deployment script
├── tradeseeker-batch-v2/            # Batch processing
│   ├── lambdas/
│   │   ├── task-generator/
│   │   ├── downloader/
│   │   ├── dlq-replay/
│   │   └── x-poster/
│   ├── terraform/
│   │   ├── lambda.tf
│   │   ├── sqs.tf
│   │   ├── eventbridge.tf
│   │   └── ...
│   └── Makefile
└── tradeseeker-web-v2/
    └── tradeseeker-web-v2/          # Angular frontend
        ├── src/
        │   ├── app/
        │   │   ├── core/           # Services, guards, interceptors
        │   │   ├── features/       # Feature modules
        │   │   └── shared/         # Shared components
        │   └── environments/
        ├── terraform/               # Frontend infrastructure
        │   ├── cloudfront.tf
        │   ├── s3.tf
        │   └── route53.tf
        ├── ios/                     # Capacitor iOS app
        └── Makefile
```

---

## Contact & Maintenance

**Last Updated**: July 29, 2026
**Maintained By**: Development Team
**Architecture Version**: 2.0

For questions or updates, refer to:
- API Cost Analysis: `tradeseeker-api-v2/API_GATEWAY_COST_ANALYSIS.md`
- Cost Optimization: `tradeseeker-api-v2/COST_OPTIMIZATION_COMPLETE.md`
- Near ATH Feature: `NEAR_ATH_FEATURE.md`
- Training Workflow: `TRAINING_WORKFLOW.md`
