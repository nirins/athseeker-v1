# Requirements: Batch Processing

## 1. Overview
Build a daily ingestion pipeline that makes ~100,000 external stock-price API requests, stores each response as compressed JSON in S3, and provides controlled throughput, retries, and failure isolation using EventBridge Scheduler, SQS, and Lambda.

## 2. User Stories
- As a data engineer, I want to download stock price JSON data daily so that I can build analytics and reporting datasets.
- As an operator, I want failed downloads to retry automatically and land in a DLQ so that I can reprocess only failures.
- As a platform owner, I want to throttle request rate so that we stay within the upstream API’s rate limits.

## 3. Acceptance Criteria

### 3.1 Daily Job Trigger & Task Creation
- [ ] A scheduled EventBridge job runs daily and enqueues ~100,000 download tasks to SQS.
- [ ] Each SQS message includes symbol (or identifier), target date/interval, and request parameters.
- [ ]  Task creation is idempotent (re-running the scheduler does not create duplicate work without detection).

### 3.2 API Download & S3 Storage

- [ ] Lambda consumes SQS messages and calls the external stock price API.

- [ ] On success, the response is written to S3 as gzip-compressed JSON.

- [ ] S3 object key follows: prices/dt=YYYY-MM-DD/symbol=<SYMBOL>/data.json.gz.

### 3.3 Retry, DLQ, and Reprocessing

- [ ] Transient failures (e.g., 429/5xx/timeouts) are retried with exponential backoff and jitter.

- [ ] Messages exceeding max receives are sent to an SQS DLQ.

- [ ] DLQ messages can be replayed to the main queue for reprocessing.

### 3.4 Monitoring & Alerting

- [ ] CloudWatch metrics/alarms exist for Lambda errors, DLQ depth, and SQS age of oldest message.

- [ ] Logs include request id, symbol, date, status code, and error reason.

## 4. Non-Functional Requirements
- Performance: Support 100,000 requests/day within rate limits (1000 req/min, 100,000 req/day); completion window ~1.5-2.5 hours; enforce max concurrency of 8 Lambda instances with batch size of 10 to stay within rate limits.
- Security: API credentials stored in Secrets Manager; least-privilege IAM; S3 encryption enabled; S3 block public access enabled.
- Scalability: System scales via SQS-triggered Lambda concurrency; reserved concurrency set to 8 and SQS batch size of 10 to respect EODHD rate limits while optimizing for speed.

## 5. Out of Scope
- Real-time streaming prices or websocket ingestion.
- Data quality enrichment, deduplication beyond S3 key overwrite/idempotent writes.
