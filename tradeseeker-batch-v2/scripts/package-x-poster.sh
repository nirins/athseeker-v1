#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAMBDA_DIR="$SCRIPT_DIR/../lambdas/x-poster"

echo "📦 Packaging X Poster Lambda (linux/amd64)..."

cd "$LAMBDA_DIR"
rm -rf package x-poster.zip

docker run --rm \
  --entrypoint bash \
  --platform linux/amd64 \
  -v "$(pwd)":/out \
  public.ecr.aws/lambda/python:3.12 \
  -c "pip install -r /out/requirements.txt -t /out/package --quiet && echo DONE"

cp handler.py package/
cd package && zip -r ../x-poster.zip . --quiet && cd ..
rm -rf package

echo "✅ x-poster.zip created at $LAMBDA_DIR/x-poster.zip"
