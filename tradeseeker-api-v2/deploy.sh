#!/bin/bash

# TradeSeekerAPI v2 Deployment Script
# This script packages the Lambda function and deploys infrastructure using Terraform

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-dev}
AWS_REGION=${AWS_REGION:-ap-southeast-1}
BUILD_DIR="build"
LAMBDA_PACKAGE="$BUILD_DIR/lambda_package.zip"

echo -e "${GREEN}=== TradeSeekerAPI v2 Deployment ===${NC}"
echo "Environment: $ENVIRONMENT"
echo "Region: $AWS_REGION"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
if [[ "$PYTHON_VERSION" != "3.12" ]]; then
    echo -e "${YELLOW}Warning: Python 3.12 is recommended, found $PYTHON_VERSION${NC}"
fi

if ! command -v terraform &> /dev/null; then
    echo -e "${RED}Error: Terraform is not installed${NC}"
    exit 1
fi

if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}Error: AWS credentials are not configured${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All prerequisites met${NC}"
echo ""

# Create build directory
echo -e "${YELLOW}Creating build directory...${NC}"
mkdir -p $BUILD_DIR
echo -e "${GREEN}✓ Build directory created${NC}"
echo ""

# Install dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip3 install -r requirements.txt -t $BUILD_DIR/package --quiet
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Package Lambda function
echo -e "${YELLOW}Packaging Lambda function...${NC}"
cd $BUILD_DIR/package
zip -r ../lambda_package.zip . -q
cd ../..

# Add source files maintaining the src/ structure
zip -g $LAMBDA_PACKAGE -r src/ -q

echo -e "${GREEN}✓ Lambda package created: $LAMBDA_PACKAGE${NC}"
echo ""

# Initialize Terraform
echo -e "${YELLOW}Initializing Terraform...${NC}"
cd terraform
terraform init
echo -e "${GREEN}✓ Terraform initialized${NC}"
echo ""

# Plan Terraform changes
echo -e "${YELLOW}Planning Terraform changes...${NC}"
terraform plan \
    -var="environment=$ENVIRONMENT" \
    -var="aws_region=$AWS_REGION" \
    -out=tfplan
echo ""

# Apply Terraform changes
echo -e "${YELLOW}Applying Terraform changes...${NC}"
terraform apply -auto-approve tfplan
echo -e "${GREEN}✓ Infrastructure deployed${NC}"
echo ""

# Get outputs
echo -e "${GREEN}=== Deployment Complete ===${NC}"
echo ""
echo "API Gateway URL:"
terraform output -raw api_gateway_url
echo ""
echo "Lambda Function ARN:"
terraform output -raw lambda_function_arn
echo ""

# Cleanup
cd ..
rm -rf $BUILD_DIR
rm -f terraform/tfplan

echo -e "${GREEN}✓ Cleanup complete${NC}"
echo ""
echo -e "${GREEN}Deployment successful!${NC}"
