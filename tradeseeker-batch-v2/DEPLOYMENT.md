# Deployment Guide - Batch Processing System

## Prerequisites

Before deploying, ensure you have the following tools installed:

### 1. Install Terraform

**macOS (using Homebrew):**
```bash
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
```

**Verify installation:**
```bash
terraform --version
```

### 2. Install AWS CLI

**macOS (using Homebrew):**
```bash
brew install awscli
```

**Verify installation:**
```bash
aws --version
```

### 3. Configure AWS Credentials

Set up your AWS credentials for the dev account (894546098844):

```bash
aws configure
```

Enter:
- AWS Access Key ID: [Your access key]
- AWS Secret Access Key: [Your secret key]
- Default region: ap-southeast-1
- Default output format: json

**Verify credentials:**
```bash
aws sts get-caller-identity
```

This should return your account ID (894546098844).

## Pre-Deployment Steps

### 1. Package Lambda Functions

Before deploying, you need to create deployment packages for all Lambda functions:

```bash
# Make scripts executable
chmod +x scripts/package-task-generator.sh
chmod +x scripts/package-downloader.sh
chmod +x scripts/package-dlq-replay.sh

# Package all Lambda functions
./scripts/package-task-generator.sh
./scripts/package-downloader.sh
./scripts/package-dlq-replay.sh
```

This will create ZIP files in the `lambdas/` directories:
- `lambdas/task-generator/task-generator.zip`
- `lambdas/downloader/downloader.zip`
- `lambdas/dlq-replay/dlq-replay.zip`

### 2. Set Up EODHD API Token

You need to manually create the Secrets Manager secret with your EODHD API token:

```bash
aws secretsmanager create-secret \
  --name ts-batch-v2-dev-eodhd-api-token \
  --description "EODHD API token for dev environment" \
  --secret-string '{"api_token":"69917262e3a876.40642506"}' \
  --region ap-southeast-1
```

**Note:** Replace the API token with your actual token if different.

## Deployment Steps

### Task 9.1: Initialize Terraform Workspace for Dev

1. Navigate to the terraform directory:
```bash
cd terraform
```

2. Initialize Terraform (downloads providers and sets up backend):
```bash
terraform init
```

3. Create and select the dev workspace:
```bash
terraform workspace new dev
```

If the workspace already exists:
```bash
terraform workspace select dev
```

4. Verify you're on the correct workspace:
```bash
terraform workspace show
```

Expected output: `dev`

### Task 9.2: Apply Terraform Configuration to Dev

1. Review the planned changes:
```bash
terraform plan
```

This will show you all resources that will be created. Review carefully.

2. Apply the configuration:
```bash
terraform apply
```

Type `yes` when prompted to confirm.

This will create:
- S3 bucket for stock prices
- DynamoDB table for stock data
- SQS main queue and DLQ
- EventBridge Scheduler rule
- IAM roles and policies
- Lambda functions (Task Generator, Downloader, DLQ Replay)
- CloudWatch log groups
- SSM Parameter Store entries
- Lambda event source mappings

**Expected duration:** 2-5 minutes

### Task 9.3: Verify All Resources Created Successfully

1. Check Terraform outputs:
```bash
terraform output
```

2. Verify S3 bucket:
```bash
aws s3 ls | grep ts-batch-v2-dev-stock-prices
```

3. Verify DynamoDB table:
```bash
aws dynamodb describe-table \
  --table-name ts-batch-v2-dev-stock-prices \
  --region ap-southeast-1 \
  --query 'Table.TableStatus'
```

Expected output: `"ACTIVE"`

4. Verify Lambda functions:
```bash
aws lambda list-functions \
  --region ap-southeast-1 \
  --query 'Functions[?starts_with(FunctionName, `ts-batch-v2-dev`)].FunctionName'
```

Expected output:
```json
[
    "ts-batch-v2-dev-task-generator",
    "ts-batch-v2-dev-downloader",
    "ts-batch-v2-dev-dlq-replay"
]
```

5. Verify SQS queues:
```bash
aws sqs list-queues \
  --region ap-southeast-1 \
  --queue-name-prefix ts-batch-v2-dev
```

6. Verify SSM parameters:
```bash
aws ssm get-parameter \
  --name /ts-batch-v2/dev/markets \
  --region ap-southeast-1

aws ssm get-parameter \
  --name /ts-batch-v2/dev/api-endpoints \
  --region ap-southeast-1
```

7. Verify EventBridge rule:
```bash
aws events list-rules \
  --region ap-southeast-1 \
  --name-prefix ts-batch-v2-dev
```

### Task 9.4: Manually Trigger Task Generator Lambda and Verify Execution

1. Invoke the Task Generator Lambda manually:
```bash
aws lambda invoke \
  --function-name ts-batch-v2-dev-task-generator \
  --region ap-southeast-1 \
  --payload '{"date":"2024-02-15"}' \
  --cli-binary-format raw-in-base64-out \
  response.json
```

2. Check the response:
```bash
cat response.json
```

Expected: `{"statusCode": 200, ...}`

3. Verify SQS messages were created:
```bash
aws sqs get-queue-attributes \
  --queue-url $(aws sqs get-queue-url --queue-name ts-batch-v2-dev-download-queue --region ap-southeast-1 --query 'QueueUrl' --output text) \
  --attribute-names ApproximateNumberOfMessages \
  --region ap-southeast-1
```

Expected: Should show a large number of messages (close to 100,000).

4. Monitor Downloader Lambda invocations:
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=ts-batch-v2-dev-downloader \
  --start-time $(date -u -v-10M +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Sum \
  --region ap-southeast-1
```

### Task 9.5: Monitor CloudWatch Logs for Errors

1. View Task Generator logs:
```bash
aws logs tail /aws/lambda/ts-batch-v2-dev-task-generator \
  --region ap-southeast-1 \
  --follow
```

Press Ctrl+C to stop following.

2. View Downloader logs:
```bash
aws logs tail /aws/lambda/ts-batch-v2-dev-downloader \
  --region ap-southeast-1 \
  --follow
```

3. Check for errors in Task Generator:
```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/ts-batch-v2-dev-task-generator \
  --filter-pattern "ERROR" \
  --region ap-southeast-1 \
  --max-items 20
```

4. Check for errors in Downloader:
```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/ts-batch-v2-dev-downloader \
  --filter-pattern "ERROR" \
  --region ap-southeast-1 \
  --max-items 20
```

5. Monitor DLQ depth:
```bash
aws sqs get-queue-attributes \
  --queue-url $(aws sqs get-queue-url --queue-name ts-batch-v2-dev-download-dlq --region ap-southeast-1 --query 'QueueUrl' --output text) \
  --attribute-names ApproximateNumberOfMessages \
  --region ap-southeast-1
```

Expected: Should be 0 or very low if everything is working correctly.

6. Check S3 for uploaded files:
```bash
aws s3 ls s3://ts-batch-v2-dev-stock-prices-894546098844/prices/ --recursive | head -20
```

7. Check DynamoDB for saved records:
```bash
aws dynamodb scan \
  --table-name ts-batch-v2-dev-stock-prices \
  --region ap-southeast-1 \
  --max-items 5
```

## Post-Deployment Verification

### Success Criteria

✅ All Terraform resources created without errors
✅ Task Generator Lambda executes successfully
✅ SQS queue receives ~100,000 messages
✅ Downloader Lambda processes messages
✅ S3 bucket contains compressed JSON files
✅ DynamoDB table contains stock price records
✅ No errors in CloudWatch logs (or minimal transient errors)
✅ DLQ depth is 0 or very low

### Troubleshooting

**Issue: Lambda timeout errors**
- Check CloudWatch logs for specific errors
- Verify API token is correct in Secrets Manager
- Check network connectivity to EODHD API

**Issue: High DLQ depth**
- Check DLQ messages for error patterns
- Review Downloader Lambda logs
- May need to replay DLQ messages after fixing issues

**Issue: Rate limit errors (429)**
- Verify Lambda reserved concurrency is set to 8
- Check SQS batch size is set to 10
- Review rate limiting configuration

**Issue: Permission errors**
- Verify IAM roles have correct policies
- Check Lambda execution role permissions
- Ensure S3 bucket policy allows Lambda writes

## Cleanup (Optional)

To destroy all resources in dev environment:

```bash
cd terraform
terraform workspace select dev
terraform destroy
```

Type `yes` when prompted.

**Warning:** This will delete all data in S3 and DynamoDB!

## Next Steps

After successful deployment:

1. Monitor the system for 24-48 hours
2. Review CloudWatch metrics and alarms
3. Verify data quality in S3 and DynamoDB
4. Test DLQ replay functionality if needed
5. Prepare for UAT deployment
