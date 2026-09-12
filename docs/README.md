# EveryATH Documentation

Welcome to the EveryATH (formerly ATHSeeker) documentation.

## 📚 Documentation Files

### Architecture
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Complete system architecture with detailed diagrams
  - High-level architecture overview
  - Batch processing pipeline
  - API layer details
  - Frontend application structure
  - Data flows and sequences
  - Infrastructure details
  - Technology stack

- **[ARCHITECTURE_QUICK_REFERENCE.md](./ARCHITECTURE_QUICK_REFERENCE.md)** - One-page quick reference
  - Simplified architecture diagram
  - Key components table
  - API endpoints list
  - Deployment commands
  - Cost breakdown

## 🎯 Quick Start

### View Architecture
Start with the [Quick Reference](./ARCHITECTURE_QUICK_REFERENCE.md) for a high-level overview, then dive into the [full Architecture document](./ARCHITECTURE.md) for details.

### Deployment
```bash
# Deploy all components
make all  # in respective directories
```

### Monitoring
```bash
# Check API Gateway metrics
cd ../tradeseeker-api-v2
./scripts/check_api_gateway_metrics.sh
```

## 📖 Additional Documentation

Located in project root:
- `NEAR_ATH_FEATURE.md` - Near ATH detection feature documentation
- `TRAINING_WORKFLOW.md` - ML training data workflow
- `tradeseeker-api-v2/API_GATEWAY_COST_ANALYSIS.md` - API cost analysis
- `tradeseeker-api-v2/COST_OPTIMIZATION_COMPLETE.md` - Cost optimization results

## 🏗️ System Overview

EveryATH is a systematic AI platform that identifies stocks reaching all-time highs across multiple markets (US, Thailand, Crypto).

**Components:**
1. **Batch Processing** - Daily data ingestion (EventBridge + SQS + Lambda)
2. **REST API** - Stock data endpoints (API Gateway + Lambda + DynamoDB)
3. **Web Frontend** - Angular app (S3 + CloudFront)
4. **Mobile** - iOS app via Capacitor

**Key Features:**
- Daily ATH stock detection across US, BK, CC markets
- Golden/Death cross signal detection
- Beauty score calculation (EMA alignment)
- Interactive charts (TradingView Lightweight Charts)
- Training mode for ML dataset creation
- Multi-domain support (everyath.com, athseeker.com)

## 🔗 External Links

- **Website**: [everyath.com](https://everyath.com) | [athseeker.com](https://athseeker.com)
- **Data Provider**: [EODHD](https://eodhd.com)
- **Cloud**: AWS (ap-southeast-1 region)

## 📊 Architecture Diagrams

All diagrams in this documentation use Mermaid syntax and can be viewed on GitHub or any Mermaid-compatible viewer.

### Diagram Types Included:
- High-level system architecture
- Batch processing flow
- API request/response flow
- User interaction sequences
- Data flow diagrams
- Deployment architecture

## 🛠️ Technology Stack

- **Frontend**: Angular 19, TypeScript, Angular Material, TradingView Charts
- **Backend**: Python 3.12, AWS Lambda, API Gateway, DynamoDB
- **Infrastructure**: Terraform, CloudFront, Route53, S3, SQS, EventBridge
- **External**: EODHD API, OpenAI, X/Twitter

## 📈 Performance

- **API Response**: 100-500ms depending on endpoint
- **Batch Processing**: ~2 hours for US market (20k symbols)
- **Client Caching**: 5-minute TTL in browser
- **Availability**: 99.9% (AWS SLA)

## 💰 Cost

Monthly costs optimized to ~$16-31/month:
- API Gateway: $0.01 (cache disabled)
- Lambda: $5-10
- DynamoDB: $10-20
- CloudFront: Free tier
- S3: ~$1

**Recent optimization**: Saved $14.40/month by disabling API Gateway cache cluster (July 2026)

## 📝 Version History

- **v2.0** (July 2026) - Cost optimization, multi-domain support, Near ATH feature
- **v1.0** (February 2026) - Initial release with US market support

---

Last Updated: July 29, 2026
