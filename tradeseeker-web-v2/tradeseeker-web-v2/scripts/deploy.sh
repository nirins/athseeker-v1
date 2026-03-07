#!/bin/bash

# Deployment script for TradeSeekerWeb v2
# This script uploads built files to S3 and invalidates CloudFront cache

set -e  # Exit on error

# Check arguments
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <s3-bucket-name> <cloudfront-distribution-id>"
    echo "Example: $0 my-bucket-name E1234567890ABC"
    exit 1
fi

BUCKET_NAME=$1
DISTRIBUTION_ID=$2
BUILD_DIR="dist/tradeseeker-web-v2/browser"

echo "🚀 Deploying TradeSeekerWeb v2..."
echo "📦 Bucket: $BUCKET_NAME"
echo "☁️  Distribution: $DISTRIBUTION_ID"

# Check if build directory exists
if [ ! -d "$BUILD_DIR" ]; then
    echo "❌ Build directory not found: $BUILD_DIR"
    echo "Run ./scripts/build.sh first"
    exit 1
fi

# Sync static assets with long cache headers (1 year)
echo "📤 Uploading static assets..."
aws s3 sync "$BUILD_DIR" "s3://$BUCKET_NAME/" \
    --exclude "index.html" \
    --cache-control "public, max-age=31536000, immutable" \
    --delete

# Upload index.html separately with no-cache headers
echo "📤 Uploading index.html..."
aws s3 cp "$BUILD_DIR/index.html" "s3://$BUCKET_NAME/index.html" \
    --cache-control "no-cache, no-store, must-revalidate" \
    --metadata-directive REPLACE

# Create CloudFront cache invalidation
echo "🔄 Invalidating CloudFront cache..."
INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id "$DISTRIBUTION_ID" \
    --paths "/*" \
    --query 'Invalidation.Id' \
    --output text)

echo "✅ Deployment complete!"
echo "📋 Invalidation ID: $INVALIDATION_ID"
echo "🌐 Your site will be updated shortly"
