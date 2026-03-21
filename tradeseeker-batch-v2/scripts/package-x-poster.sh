#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAMBDA_DIR="$SCRIPT_DIR/../lambdas/x-poster"

echo "📦 Packaging X Poster Lambda..."

cd "$LAMBDA_DIR"

# Install dependencies into package dir
rm -rf package
mkdir package
pip install -r requirements.txt -t package/ --quiet

# Copy handler
cp handler.py package/

# Zip it up
cd package
zip -r ../x-poster.zip . --quiet
cd ..
rm -rf package

echo "✅ x-poster.zip created at $LAMBDA_DIR/x-poster.zip"
