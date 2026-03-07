# Tasks: Batch Processing

## Implementation Tasks

- [x] 1. Setup project structure and configuration
  - [x] 1.1 Initialize Terraform project with workspace configuration
  - [x] 1.2 Create directory structure for Lambda functions (task-generator, downloader)
  - [x] 1.3 Setup Python project with requirements.txt (boto3, requests, pytest, moto)
  - [x] 1.4 Configure environment variables and locals for multi-environment deployment

- [x] 2. Implement Terraform infrastructure
  - [x] 2.1 Create S3 bucket with encryption and lifecycle policies
  - [x] 2.2 Create DynamoDB table with partition key (symbol)
  - [x] 2.3 Create SQS main queue and DLQ with appropriate configurations
  - [x] 2.4 Create EventBridge Scheduler rule for daily trigger
  - [x] 2.5 Create IAM roles and policies for Lambda functions
  - [x] 2.6 Create SSM Parameter Store entries for markets and API endpoints
  - [x] 2.7 Create Secrets Manager secret for EODHD API token
  - [x] 2.8 Create CloudWatch log groups and alarms

- [x] 3. Implement Task Generator Lambda
  - [x] 3.1 Create Lambda handler function
  - [x] 3.2 Implement SSM Parameter Store client to fetch markets
  - [x] 3.3 Implement Secrets Manager client to fetch API token
  - [x] 3.4 Implement EODHD API client to fetch symbol list
  - [x] 3.5 Implement SQS batch message creation and sending
  - [x] 3.6 Add error handling and logging
  - [x] 3.7 Package Lambda deployment artifact

- [x] 4. Implement Downloader Lambda
  - [x] 4.1 Create Lambda handler function with SQS event processing
  - [x] 4.2 Implement EODHD API client to fetch full historical stock prices
  - [x] 4.3 Implement retry logic with exponential backoff
  - [x] 4.4 Implement gzip compression for JSON data
  - [x] 4.5 Implement S3 upload with partitioned key structure
  - [x] 4.6 Implement EMA calculation functions (EMA 7, 30, 50, 200)
  - [x] 4.7 Implement DynamoDB save function with nested list structure
  - [x] 4.8 Implement partial batch failure handling
  - [x] 4.9 Add error handling and structured logging
  - [x] 4.10 Package Lambda deployment artifact

- [x] 5. Deploy Terraform infrastructure for Lambda functions
  - [x] 5.1 Create Terraform resources for Task Generator Lambda
  - [x] 5.2 Create Terraform resources for Downloader Lambda with reserved concurrency
  - [x] 5.3 Create Lambda-SQS event source mapping
  - [x] 5.4 Create EventBridge-Lambda trigger for Task Generator

- [x] 6. Implement DLQ Replay Lambda (optional)
  - [x] 6.1 Create Lambda handler to replay DLQ messages
  - [x] 6.2 Implement message filtering and re-enqueue logic
  - [x] 6.3 Package and deploy Lambda

- [x] 7. Write unit tests
  - [x] 7.1 Write tests for Task Generator (symbol list parsing, SQS batch creation)
  - [x] 7.2 Write tests for Downloader (API client, retry logic, gzip compression)
  - [x] 7.3 Write tests for EMA calculation functions
  - [x] 7.4 Write tests for S3 key formatting
  - [x] 7.5 Write tests for DynamoDB save logic

- [x] 8. Write integration tests
  - [x] 8.1 Setup moto for AWS service mocking
  - [x] 8.2 Write end-to-end test: EventBridge → Task Generator → SQS
  - [x] 8.3 Write end-to-end test: SQS → Downloader → S3 + DynamoDB
  - [x] 8.4 Write DLQ flow test with forced failures
  - [x] 8.5 Write test for API retry behavior with mocked rate limits

- [x] 9. Deploy to dev environment
  - [x] 9.1 Initialize Terraform workspace for dev
  - [x] 9.2 Apply Terraform configuration to dev
  - [x] 9.3 Verify all resources created successfully
  - [x] 9.4 Manually trigger Task Generator Lambda and verify execution
  - [x] 9.5 Monitor CloudWatch logs for errors

- [x] 10. Documentation
  - [x] 10.1 Document deployment process
  - [x] 10.2 Document monitoring and alerting setup
  - [x] 10.3 Document DLQ replay procedure
  - [x] 10.4 Update README with architecture diagram and usage instructions
