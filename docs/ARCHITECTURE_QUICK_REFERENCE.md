# EveryATH Architecture - Quick Reference

## System Overview (One-Page)

```mermaid
graph TB
    subgraph "Users"
        U1[Web Browser]
        U2[iOS App]
    end
    
    subgraph "Frontend Layer"
        DNS[Route53<br/>everyath.com]
        CDN[CloudFront CDN]
        S3[S3 Static Site<br/>Angular App]
    end
    
    subgraph "API Layer"
        API[API Gateway]
        LambdaAPI[Lambda API<br/>Python]
    end
    
    subgraph "Batch Processing - Daily Jobs"
        EB1[EventBridge<br/>US: 7PM NY]
        EB2[EventBridge<br/>BK: 7PM Bangkok]
        EB3[EventBridge<br/>CC: 8AM Bangkok]
        TG[Task Generator]
        Q[SQS Queue<br/>~20k tasks]
        DL[Downloader x10<br/>Parallel]
    end
    
    subgraph "Data Storage"
        DDB1[DynamoDB<br/>Stock Prices<br/>3 years]
        DDB2[DynamoDB<br/>ATH Stocks<br/>30 days TTL]
        DDB3[DynamoDB<br/>Golden/Death<br/>30 days TTL]
    end
    
    subgraph "External"
        EODHD[EODHD API<br/>Market Data]
    end
    
    U1 --> DNS
    U2 --> DNS
    DNS --> CDN
    CDN --> S3
    S3 --> API
    API --> LambdaAPI
    LambdaAPI --> DDB1
    LambdaAPI --> DDB2
    LambdaAPI --> DDB3
    
    EB1 --> TG
    EB2 --> TG
    EB3 --> TG
    TG --> Q
    Q --> DL
    DL --> EODHD
    DL --> DDB1
    DL --> DDB2
    DL --> DDB3
    
    style CDN fill:#ff9900
    style API fill:#ff9900
    style LambdaAPI fill:#ff9900
    style TG fill:#ff9900
    style DL fill:#ff9900
    style DDB1 fill:#4053d6
    style DDB2 fill:#4053d6
    style DDB3 fill:#4053d6
    style S3 fill:#569a31
```

## Key Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Frontend** | Angular 19 + S3 + CloudFront | User interface, charts, stock browsing |
| **API** | API Gateway + Lambda (Python) | REST endpoints for stock data |
| **Batch** | EventBridge + SQS + Lambda | Daily data ingestion from EODHD |
| **Database** | DynamoDB (7 tables) | Stock prices, ATH, signals |
| **External** | EODHD API | Market data provider |

## Data Flow

1. **Daily**: EventBridge triggers batch job → Download 20k stocks → Store in DynamoDB
2. **User Request**: Browser → CloudFront → S3 → API Gateway → Lambda → DynamoDB → Response
3. **Caching**: Client-side 5min TTL (API Gateway cache disabled to save $14.40/month)


## API Endpoints

- `GET /ath?market=US` - Get ATH stocks
- `GET /near-ath?market=US` - Get near-ATH stocks
- `GET /golden-crosses?market=US` - Get golden cross signals
- `GET /death-crosses?market=US` - Get death cross signals
- `GET /stocks/batch?symbols=AAPL,MSFT` - Batch stock data
- `GET /stocks/:symbol` - Single stock detail

## Deployment Commands

```bash
# Frontend
cd tradeseeker-web-v2/tradeseeker-web-v2
make all

# API
cd tradeseeker-api-v2
make deploy

# Batch
cd tradeseeker-batch-v2
make deploy

# iOS
cd tradeseeker-web-v2/tradeseeker-web-v2
make ios
```

## Costs (Optimized)

- API Gateway: $0.01/month (cache disabled)
- Lambda: $5-10/month
- DynamoDB: $10-20/month
- **Total: ~$16-31/month**

## Monitoring

```bash
# Check API metrics
cd tradeseeker-api-v2
./scripts/check_api_gateway_metrics.sh
```

---

**For detailed architecture, see [ARCHITECTURE.md](./ARCHITECTURE.md)**
