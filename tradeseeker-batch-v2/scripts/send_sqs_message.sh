#!/bin/bash

# Script to send SQS message for stock symbol processing
# Usage: ./scripts/send_sqs_message.sh SYMBOL MARKET_CODE [DATE]
# Example: ./scripts/send_sqs_message.sh AAPL US 2026-02-16

SYMBOL=${1:-AAPL}
MARKET_CODE=${2:-US}
DATE=${3:-$(date +%Y-%m-%d)}
REQUEST_ID="${SYMBOL}-${MARKET_CODE}-${DATE}"

QUEUE_URL="https://sqs.ap-southeast-1.amazonaws.com/894546098844/ts-batch-v2-dev-download-queue"
REGION="ap-southeast-1"

MESSAGE_BODY=$(cat <<EOF
{
  "symbol": "${SYMBOL}",
  "marketCode": "${MARKET_CODE}",
  "date": "${DATE}",
  "requestId": "${REQUEST_ID}"
}
EOF
)

echo "Sending message to SQS queue..."
echo "Symbol: ${SYMBOL}"
echo "Market: ${MARKET_CODE}"
echo "Date: ${DATE}"
echo "Request ID: ${REQUEST_ID}"
echo ""

aws sqs send-message \
  --queue-url "${QUEUE_URL}" \
  --message-body "${MESSAGE_BODY}" \
  --region "${REGION}"

if [ $? -eq 0 ]; then
  echo ""
  echo "✓ Message sent successfully!"
  echo ""
  echo "To check Lambda logs, run:"
  echo "aws logs tail /aws/lambda/ts-batch-v2-dev-downloader --follow --region ${REGION}"
else
  echo ""
  echo "✗ Failed to send message"
  exit 1
fi
