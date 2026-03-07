# Deployment Checklist - Dev Environment

Use this checklist to track your deployment progress.

## Pre-Deployment

- [ ] Install Terraform: `brew install hashicorp/tap/terraform`
- [ ] Install AWS CLI: `brew install awscli`
- [ ] Configure AWS credentials: `aws configure`
- [ ] Verify account ID is 894546098844: `aws sts get-caller-identity`
- [ ] Package Lambda functions: `./scripts/package-task-generator.sh && ./scripts/package-downloader.sh && ./scripts/package-dlq-replay.sh`
- [ ] Create EODHD API secret (see DEPLOYMENT.md)

## Task 9.1: Initialize Terraform Workspace

- [ ] Navigate to terraform directory: `cd terraform`
- [ ] Initialize Terraform: `terraform init`
- [ ] Create dev workspace: `terraform workspace new dev` (or select if exists: `terraform workspace select dev`)
- [ ] Verify workspace: `terraform workspace show` (should output "dev")

## Task 9.2: Apply Terraform Configuration

- [ ] Review plan: `terraform plan`
- [ ] Apply configuration: `terraform apply`
- [ ] Confirm with "yes" when prompted
- [ ] Wait for completion (2-5 minutes)
- [ ] Note any errors or warnings

## Task 9.3: Verify Resources

- [ ] Check Terraform outputs: `terraform output`
- [ ] Verify S3 bucket: `aws s3 ls | grep ts-batch-v2-dev-stock-prices`
- [ ] Verify DynamoDB table: `aws dynamodb describe-table --table-name ts-batch-v2-dev-stock-prices --region ap-southeast-1`
- [ ] Verify Lambda functions: `aws lambda list-functions --region ap-southeast-1 --query 'Functions[?starts_with(FunctionName, \`ts-batch-v2-dev\`)].FunctionName'`
- [ ] Verify SQS queues: `aws sqs list-queues --region ap-southeast-1 --queue-name-prefix ts-batch-v2-dev`
- [ ] Verify SSM parameters: `aws ssm get-parameter --name /ts-batch-v2/dev/markets --region ap-southeast-1`
- [ ] Verify EventBridge rule: `aws events list-rules --region ap-southeast-1 --name-prefix ts-batch-v2-dev`

## Task 9.4: Manual Trigger

- [ ] Invoke Task Generator: `aws lambda invoke --function-name ts-batch-v2-dev-task-generator --region ap-southeast-1 --payload '{"date":"2024-02-15"}' --cli-binary-format raw-in-base64-out response.json`
- [ ] Check response: `cat response.json`
- [ ] Wait 10 seconds for processing
- [ ] Check SQS message count (should be ~100,000)
- [ ] Monitor Downloader invocations (wait a few minutes)

## Task 9.5: Monitor Logs

- [ ] View Task Generator logs: `aws logs tail /aws/lambda/ts-batch-v2-dev-task-generator --region ap-southeast-1 --since 10m`
- [ ] View Downloader logs: `aws logs tail /aws/lambda/ts-batch-v2-dev-downloader --region ap-southeast-1 --since 10m`
- [ ] Check for errors in Task Generator: `aws logs filter-log-events --log-group-name /aws/lambda/ts-batch-v2-dev-task-generator --filter-pattern "ERROR" --region ap-southeast-1`
- [ ] Check for errors in Downloader: `aws logs filter-log-events --log-group-name /aws/lambda/ts-batch-v2-dev-downloader --filter-pattern "ERROR" --region ap-southeast-1`
- [ ] Check DLQ depth (should be 0 or very low)
- [ ] Verify S3 files: `aws s3 ls s3://ts-batch-v2-dev-stock-prices-894546098844/prices/ --recursive | head -20`
- [ ] Verify DynamoDB records: `aws dynamodb scan --table-name ts-batch-v2-dev-stock-prices --region ap-southeast-1 --max-items 5`

## Post-Deployment

- [ ] Document any issues encountered
- [ ] Monitor system for 24-48 hours
- [ ] Review CloudWatch metrics
- [ ] Verify data quality
- [ ] Test DLQ replay if needed

## Quick Commands Reference

**Follow Downloader logs in real-time:**
```bash
aws logs tail /aws/lambda/ts-batch-v2-dev-downloader --region ap-southeast-1 --follow
```

**Check queue depth:**
```bash
aws sqs get-queue-attributes \
  --queue-url $(aws sqs get-queue-url --queue-name ts-batch-v2-dev-download-queue --region ap-southeast-1 --query 'QueueUrl' --output text) \
  --attribute-names ApproximateNumberOfMessages \
  --region ap-southeast-1
```

**Check DLQ depth:**
```bash
aws sqs get-queue-attributes \
  --queue-url $(aws sqs get-queue-url --queue-name ts-batch-v2-dev-download-dlq --region ap-southeast-1 --query 'QueueUrl' --output text) \
  --attribute-names ApproximateNumberOfMessages \
  --region ap-southeast-1
```

**Count S3 objects:**
```bash
aws s3 ls s3://ts-batch-v2-dev-stock-prices-894546098844/prices/ --recursive | wc -l
```

**Count DynamoDB items:**
```bash
aws dynamodb scan \
  --table-name ts-batch-v2-dev-stock-prices \
  --region ap-southeast-1 \
  --select COUNT
```

## Automated Deployment

Alternatively, use the automated deployment script:

```bash
./scripts/deploy-dev.sh
```

This script will guide you through all steps interactively.
