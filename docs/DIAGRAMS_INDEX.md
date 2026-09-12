# Architecture Diagrams Index

This document provides an index of all architecture diagrams in the EveryATH documentation.

## 📊 Available Diagrams

### 1. High-Level System Architecture
**File**: [ARCHITECTURE.md - High-Level Architecture](./ARCHITECTURE.md#high-level-architecture)

Shows the complete system overview including:
- User interfaces (Web, iOS)
- DNS and CDN layer
- Frontend (S3 + CloudFront)
- API layer (API Gateway + Lambda)
- Batch processing components
- All DynamoDB tables
- External services (EODHD, OpenAI, X/Twitter)
- Auth and monitoring services

**Use Case**: Understanding the entire system at a glance

---

### 2. Batch Processing Pipeline
**File**: [ARCHITECTURE.md - Batch Processing Flow](./ARCHITECTURE.md#batch-processing-flow)

Detailed flow showing:
- EventBridge schedulers for different markets (US, BK, CC)
- Task Generator Lambda
- SQS queue management
- Downloader Lambda (10 concurrent)
- Data processing steps (EMA calculation, signal detection)
- Storage to multiple DynamoDB tables
- Dead Letter Queue handling
- X Poster Lambda for social media

**Use Case**: Understanding daily data ingestion process

---

### 3. API Layer Architecture
**File**: [ARCHITECTURE.md - API Architecture](./ARCHITECTURE.md#api-architecture)

Shows:
- API Gateway entry point
- Lambda function routing
- All route handlers (/ath, /near-ath, /stocks, etc.)
- DynamoDB table access patterns
- External API integrations (OpenAI)
- Request/response flow

**Use Case**: Understanding API endpoints and data access

---

### 4. Frontend Application Architecture
**File**: [ARCHITECTURE.md - Frontend Architecture](./ARCHITECTURE.md#frontend-architecture)

Illustrates:
- Route53 DNS resolution
- CloudFront CDN distribution
- S3 static website hosting
- Angular application structure
- Component hierarchy
- Service layer (API, Auth, Cache)
- Browser caching strategy
- Cognito authentication

**Use Case**: Understanding frontend structure and data flow

---

### 5. User Request Sequence
**File**: [ARCHITECTURE.md - User Request Flow](./ARCHITECTURE.md#user-request-flow)

Sequence diagram showing:
- User visiting website
- CloudFront serving static files
- User clicking to view stocks
- API request with caching
- DynamoDB query
- Response rendering
- Client-side cache management

**Use Case**: Understanding end-to-end user interaction

---

### 6. Daily Batch Processing Sequence
**File**: [ARCHITECTURE.md - Daily Batch Processing Flow](./ARCHITECTURE.md#daily-batch-processing-flow)

Sequence diagram showing:
- EventBridge trigger at specific times
- Task Generator fetching symbol list from EODHD
- Filtering and task creation
- SQS queue processing
- Downloader fetching historical data
- EMA calculation and signal detection
- Storage to multiple DynamoDB tables

**Use Case**: Understanding batch job execution flow

---

### 7. Deployment Architecture
**File**: [ARCHITECTURE.md - Multi-Environment Setup](./ARCHITECTURE.md#multi-environment-setup)

Shows:
- Development environment workflow
- Production deployment pipeline
- Build and deployment processes
- Environment separation

**Use Case**: Understanding deployment strategies

---

### 8. Quick Reference System Overview
**File**: [ARCHITECTURE_QUICK_REFERENCE.md](./ARCHITECTURE_QUICK_REFERENCE.md)

Simplified one-page diagram showing:
- Core components only
- Main data flows
- Key integrations
- Basic architecture

**Use Case**: Quick overview for presentations or onboarding

---

## 🎨 Diagram Types

All diagrams are created using **Mermaid** syntax, which means they:
- ✅ Render automatically on GitHub
- ✅ Can be viewed in VS Code with Mermaid extensions
- ✅ Are version-controlled as text
- ✅ Can be easily updated
- ✅ Work in most modern markdown viewers

### Diagram Formats Used:

1. **Graph TB/LR** - Flowcharts and system architecture
   - Shows components and connections
   - Used for high-level architecture

2. **Flowchart TD** - Detailed process flows
   - Shows decision points and branching
   - Used for batch processing pipeline

3. **Sequence Diagram** - Time-based interactions
   - Shows component communication over time
   - Used for user requests and batch processing

## 🔧 Viewing Diagrams

### On GitHub
Just open any markdown file - diagrams render automatically!

### In VS Code
1. Install "Markdown Preview Mermaid Support" extension
2. Open markdown file
3. Click "Preview" button

### Online
Copy diagram code to [Mermaid Live Editor](https://mermaid.live)

## 📝 Diagram Conventions

**Color Coding:**
- 🟠 Orange: AWS Lambda functions
- 🔵 Blue: DynamoDB tables
- 🟢 Green: S3 buckets
- 🟡 Yellow: EventBridge/Schedulers
- 🔴 Red: SQS queues, error queues
- 🔷 Light Blue: User interfaces

**Component Labels:**
- Service name on first line
- Key details on subsequent lines (memory, concurrency, etc.)

## 🆕 Creating New Diagrams

When adding new diagrams:
1. Use Mermaid syntax
2. Follow existing color conventions
3. Add entry to this index
4. Include brief description of what it shows
5. Specify use case

## 📚 Related Documentation

- [README.md](./README.md) - Documentation overview
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Complete architecture documentation
- [ARCHITECTURE_QUICK_REFERENCE.md](./ARCHITECTURE_QUICK_REFERENCE.md) - One-page reference

---

**Total Diagrams**: 8
**Last Updated**: August 1, 2026
