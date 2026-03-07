#!/bin/bash

# Deployment script for dev environment
# This script automates the deployment process for the batch processing system

set -e  # Exit on error

echo "=========================================="
echo "Batch Processing System - Dev Deployment"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v terraform &> /dev/null; then
    echo -e "${RED}ERROR: Terraform is not installed${NC}"
    echo "Install with: brew install hashicorp/tap/terraform"
    exit 1
fi

if ! command -v aws &> /dev/null; then
    echo -e "${RED}ERROR: AWS CLI is not installed${NC}"
    echo "Install with: brew install awscli"
    exit 1
fi

echo -e "${GREEN}✓ Terraform installed${NC}"
echo -e "${GREEN}✓ AWS CLI installed${NC}"

# Verify AWS credentials
echo ""
echo "Verifying AWS credentials..."
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "")

if [ -z "$ACCOUNT_ID" ]; then
    echo -e "${RED}ERROR: AWS credentials not configured${NC}"
    echo "Run: aws configure"
    exit 1
fi

if [ "$ACCOUNT_ID" != "894546098844" ]; then
    echo -e "${YELLOW}WARNING: Expected account 894546098844, got $ACCOUNT_ID${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo -e "${GREEN}✓ AWS credentials configured (Account: $ACCOUNT_ID)${NC}"

# Package Lambda functions
echo ""
echo "Packaging Lambda functions..."

if [ ! -f "scripts/package-task-generator.sh" ]; then
    echo -e "${RED}ERROR: Package scripts not found${NC}"
    exit 1
fi

chmod +x scripts/package-task-generator.sh
chmod +x scripts/package-downloader.sh
chmod +x scripts/package-dlq-replay.sh

./scripts/package-task-generator.sh
./scripts/package-downloader.sh
./scripts/package-dlq-replay.sh

echo -e "${GREEN}✓ Lambda functions packaged${NC}"

# Check if secret exists
echo ""
echo "Checking EODHD API token secret..."
SECRET_EXISTS=$(aws secretsmanager describe-secret \
    --secret-id ts-batch-v2-dev-eodhd-api-token \
    --region ap-southeast-1 \
    --query 'Name' \
    --output text 2>/dev/null || echo "")

if [ -z "$SECRET_EXISTS" ]; then
    echo -e "${YELLOW}WARNING: EODHD API token secret not found${NC}"
    echo "Creating secret with default token..."
    aws secretsmanager create-secret \
        --name ts-batch-v2-dev-eodhd-api-token \
        --description "EODHD API token for dev environment" \
        --secret-string '{"api_token":"69917262e3a876.40642506"}' \
        --region ap-southeast-1
    echo -e "${GREEN}✓ Secret created${NC}"
else
    echo -e "${GREEN}✓ Secret already exists${NC}"
fi

# Initialize Terraform
echo ""
echo "=========================================="
echo "Task 9.1: Initialize Terraform workspace"
echo "=========================================="
cd terraform

echo "Initializing Terraform..."
terraform init

# Create or select dev workspace
echo ""
echo "Setting up dev workspace..."
if terraform workspace select dev 2>/dev/null; then
    echo -e "${GREEN}✓ Selected existing dev workspace${NC}"
else
    echo "Creating new dev workspace..."
    terraform workspace new dev
    echo -e "${GREEN}✓ Created dev workspace${NC}"
fi

CURRENT_WORKSPACE=$(terraform workspace show)
echo "Current workspace: $CURRENT_WORKSPACE"

if [ "$CURRENT_WORKSPACE" != "dev" ]; then
    echo -e "${RED}ERROR: Not on dev workspace${NC}"
    exit 1
fi

# Apply Terraform configuration
echo ""
echo "=========================================="
echo "Task 9.2: Apply Terraform configuration"
echo "=========================================="

echo "Planning Terraform changes..."
terraform plan -out=tfplan

echo ""
read -p "Apply these changes? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled"
    exit 1
fi

echo "Applying Terraform configuration..."
terraform apply tfplan
rm tfplan

echo -e "${GREEN}✓ Terraform applied successfully${NC}"

# Verify resources
echo ""
echo "=========================================="
echo "Task 9.3: Verify resources"
echo "=========================================="

cd ..

echo "Checking S3 bucket..."
S3_BUCKET=$(aws s3 ls | grep ts-batch-v2-dev-stock-prices || echo "")
if [ -n "$S3_BUCKET" ]; then
    echo -e "${GREEN}✓ S3 bucket exists${NC}"
else
    echo -e "${RED}✗ S3 bucket not found${NC}"
fi

echo "Checking DynamoDB table..."
DYNAMODB_STATUS=$(aws dynamodb describe-table \
    --table-name ts-batch-v2-dev-stock-prices \
    --region ap-southeast-1 \
    --query 'Table.TableStatus' \
    --output text 2>/dev/null || echo "")
if [ "$DYNAMODB_STATUS" = "ACTIVE" ]; then
    echo -e "${GREEN}✓ DynamoDB table is ACTIVE${NC}"
else
    echo -e "${RED}✗ DynamoDB table not found or not active${NC}"
fi

echo "Checking Lambda functions..."
LAMBDA_COUNT=$(aws lambda list-functions \
    --region ap-southeast-1 \
    --query 'Functions[?starts_with(FunctionName, `ts-batch-v2-dev`)].FunctionName' \
    --output text | wc -w)
if [ "$LAMBDA_COUNT" -ge 3 ]; then
    echo -e "${GREEN}✓ Lambda functions created ($LAMBDA_COUNT)${NC}"
else
    echo -e "${RED}✗ Expected 3 Lambda functions, found $LAMBDA_COUNT${NC}"
fi

echo "Checking SQS queues..."
SQS_COUNT=$(aws sqs list-queues \
    --region ap-southeast-1 \
    --queue-name-prefix ts-batch-v2-dev \
    --query 'QueueUrls' \
    --output text | wc -w)
if [ "$SQS_COUNT" -ge 2 ]; then
    echo -e "${GREEN}✓ SQS queues created ($SQS_COUNT)${NC}"
else
    echo -e "${RED}✗ Expected 2 SQS queues, found $SQS_COUNT${NC}"
fi

# Manual trigger
echo ""
echo "=========================================="
echo "Task 9.4: Trigger Task Generator Lambda"
echo "=========================================="

read -p "Manually trigger Task Generator Lambda? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Invoking Task Generator Lambda..."
    aws lambda invoke \
        --function-name ts-batch-v2-dev-task-generator \
        --region ap-southeast-1 \
        --payload '{"date":"2024-02-15"}' \
        --cli-binary-format raw-in-base64-out \
        response.json
    
    echo ""
    echo "Response:"
    cat response.json
    echo ""
    rm response.json
    
    echo ""
    echo "Waiting 10 seconds for messages to be created..."
    sleep 10
    
    echo "Checking SQS queue depth..."
    QUEUE_URL=$(aws sqs get-queue-url \
        --queue-name ts-batch-v2-dev-download-queue \
        --region ap-southeast-1 \
        --query 'QueueUrl' \
        --output text)
    
    MSG_COUNT=$(aws sqs get-queue-attributes \
        --queue-url "$QUEUE_URL" \
        --attribute-names ApproximateNumberOfMessages \
        --region ap-southeast-1 \
        --query 'Attributes.ApproximateNumberOfMessages' \
        --output text)
    
    echo -e "${GREEN}✓ SQS queue has $MSG_COUNT messages${NC}"
fi

# Monitor logs
echo ""
echo "=========================================="
echo "Task 9.5: Monitor CloudWatch logs"
echo "=========================================="

echo "Recent Task Generator logs:"
aws logs tail /aws/lambda/ts-batch-v2-dev-task-generator \
    --region ap-southeast-1 \
    --since 10m \
    --format short || echo "No logs yet"

echo ""
echo "Recent Downloader logs:"
aws logs tail /aws/lambda/ts-batch-v2-dev-downloader \
    --region ap-southeast-1 \
    --since 10m \
    --format short || echo "No logs yet"

echo ""
echo "Checking for errors..."
ERROR_COUNT=$(aws logs filter-log-events \
    --log-group-name /aws/lambda/ts-batch-v2-dev-task-generator \
    --filter-pattern "ERROR" \
    --region ap-southeast-1 \
    --max-items 5 \
    --query 'events' \
    --output text | wc -l)

if [ "$ERROR_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}WARNING: Found $ERROR_COUNT errors in Task Generator logs${NC}"
else
    echo -e "${GREEN}✓ No errors in Task Generator logs${NC}"
fi

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Monitor CloudWatch logs: aws logs tail /aws/lambda/ts-batch-v2-dev-downloader --region ap-southeast-1 --follow"
echo "2. Check S3 for data: aws s3 ls s3://ts-batch-v2-dev-stock-prices-$ACCOUNT_ID/prices/ --recursive"
echo "3. Check DynamoDB: aws dynamodb scan --table-name ts-batch-v2-dev-stock-prices --region ap-southeast-1 --max-items 5"
echo "4. Monitor DLQ: aws sqs get-queue-attributes --queue-url <DLQ_URL> --attribute-names ApproximateNumberOfMessages"
echo ""
echo "For detailed instructions, see DEPLOYMENT.md"
