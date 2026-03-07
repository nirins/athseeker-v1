#!/bin/bash

# Cache invalidation script for TradeSeekerWeb v2
# This script invalidates CloudFront cache for all paths

set -e  # Exit on error

# Check arguments
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <cloudfront-distribution-id>"
    echo "Example: $0 E1234567890ABC"
    exit 1
fi

DISTRIBUTION_ID=$1

echo "🔄 Invalidating CloudFront cache..."
echo "☁️  Distribution: $DISTRIBUTION_ID"

# Create cache invalidation
INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id "$DISTRIBUTION_ID" \
    --paths "/*" \
    --query 'Invalidation.Id' \
    --output text)

echo "✅ Cache invalidation created!"
echo "📋 Invalidation ID: $INVALIDATION_ID"
echo "⏳ Cache will be cleared shortly"
