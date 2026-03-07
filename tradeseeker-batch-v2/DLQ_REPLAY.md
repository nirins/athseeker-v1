# DLQ Replay Procedure

## Overview

The Dead Letter Queue (DLQ) captures messages that fail after maximum retry attempts. This guide covers how to investigate, fix, and replay failed messages.

## Understanding the DLQ

### When Messages Go to DLQ

Messages are sent to the DLQ when:
- Maximum receive count is reached (default: 3 attempts)
- Permanent errors occur (4xx errors, invalid data)
- Lambda function fails repeatedly

### DLQ Configuration

- **Queue Name**: `ts-batch-v2-{env}-download-dlq`
- **Message Retention**: 14 days
- **Alarm Threshold**: > 100 messages

## Investigating DLQ Messages

### Step 1: Check DLQ Depth

```bash
DLQ_URL=$(aws sqs get-queue-url \
  --queue-name ts-batch-v2-dev-download-dlq \
  --region ap-southeast-1 \
  --query 'QueueUrl' \
  --output text)

aws sqs get-queue-attributes \
  --queue-url "$DLQ_URL" \
  --attribute-names All \
  --region ap-southeast-1
```

**Key attributes:**
- `ApproximateNumberOfMessages`: Total messages in DLQ
- `ApproximateAgeOfOldestMessage`: Age of oldest message (seconds)

### Step 2: Sample Messages

Receive a few messages to understand failure patterns:

```bash
aws sqs receive-message \
  --queue-url "$DLQ_URL" \
  --max-number-of-messages 10 \
  --region ap-southeast-1 \
  --output json > dlq-sample.json
```

View the messages:
```bash
cat dlq-sample.json | jq '.Messages[].Body' | head -20
```

### Step 3: Analyze Message Content

Each message contains:
```json
{
  "symbol": "AAPL",
  "marketCode": "US",
  "date": "2024-02-15",
  "apiEndpoint": "https://eodhd.com/api/eod/AAPL.US",
  "requestId": "AAPL-US-2024-02-15"
}
```

### Step 4: Check CloudWatch Logs

Search for errors related to failed symbols:

```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/ts-batch-v2-dev-downloader \
  --filter-pattern "AAPL" \
  --region ap-southeast-1 \
  --max-items 20
```

Look for error patterns:
- `429`: Rate limiting (should be rare with proper concurrency)
- `401/403`: Authentication errors
- `404`: Symbol not found
- `500/502/503`: API server errors
- `Timeout`: Network or Lambda timeout

## Common Failure Scenarios

### Scenario 1: Rate Limiting (429 Errors)

**Cause:** Too many requests to EODHD API

**Investigation:**
```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/ts-batch-v2-dev-downloader \
  --filter-pattern "429" \
  --region ap-southeast-1 \
  --max-items 20
```

**Resolution:**
1. Verify Lambda reserved concurrency is set to 8
2. Check SQS batch size is set to 10
3. Wait 1 hour for rate limit to reset
4. Replay DLQ messages

### Scenario 2: Invalid API Token (401/403 Errors)

**Cause:** API token is invalid or expired

**Investigation:**
```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/ts-batch-v2-dev-downloader \
  --filter-pattern "401" \
  --region ap-southeast-1 \
  --max-items 10
```

**Resolution:**
1. Verify API token in Secrets Manager:
```bash
aws secretsmanager get-secret-value \
  --secret-id ts-batch-v2-dev-eodhd-api-token \
  --region ap-southeast-1 \
  --query 'SecretString' \
  --output text
```

2. Update token if needed:
```bash
aws secretsmanager update-secret \
  --secret-id ts-batch-v2-dev-eodhd-api-token \
  --secret-string '{"api_token":"NEW_TOKEN"}' \
  --region ap-southeast-1
```

3. Replay DLQ messages

### Scenario 3: Symbol Not Found (404 Errors)

**Cause:** Symbol doesn't exist or was delisted

**Investigation:**
```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/ts-batch-v2-dev-downloader \
  --filter-pattern "404" \
  --region ap-southeast-1 \
  --max-items 20
```

**Resolution:**
1. Identify invalid symbols from DLQ messages
2. Remove invalid symbols from source data
3. Purge these messages from DLQ (don't replay)

### Scenario 4: Lambda Timeout

**Cause:** Lambda execution exceeds timeout (120 seconds)

**Investigation:**
```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/ts-batch-v2-dev-downloader \
  --filter-pattern "Task timed out" \
  --region ap-southeast-1 \
  --max-items 10
```

**Resolution:**
1. Check Lambda duration metrics:
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=ts-batch-v2-dev-downloader \
  --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum \
  --region ap-southeast-1
```

2. If needed, increase Lambda timeout in Terraform:
```hcl
resource "aws_lambda_function" "downloader" {
  timeout = 180  # Increase from 120 to 180 seconds
}
```

3. Apply Terraform changes and replay DLQ

### Scenario 5: API Server Errors (500/502/503)

**Cause:** EODHD API is experiencing issues

**Investigation:**
- Check EODHD API status page
- Look for patterns in error timing

**Resolution:**
1. Wait for API to recover
2. Replay DLQ messages after recovery

## Replaying DLQ Messages

### Method 1: Using DLQ Replay Lambda (Recommended)

The system includes a dedicated Lambda function for replaying DLQ messages.

**Invoke the replay Lambda:**
```bash
aws lambda invoke \
  --function-name ts-batch-v2-dev-dlq-replay \
  --region ap-southeast-1 \
  --payload '{"maxMessages": 100}' \
  --cli-binary-format raw-in-base64-out \
  response.json

cat response.json
```

**Parameters:**
- `maxMessages`: Number of messages to replay (default: 100)

**What it does:**
1. Receives messages from DLQ
2. Validates message format
3. Sends messages back to main queue
4. Deletes messages from DLQ

**Monitor replay progress:**
```bash
# Check DLQ depth (should decrease)
aws sqs get-queue-attributes \
  --queue-url "$DLQ_URL" \
  --attribute-names ApproximateNumberOfMessages \
  --region ap-southeast-1

# Check main queue depth (should increase)
QUEUE_URL=$(aws sqs get-queue-url \
  --queue-name ts-batch-v2-dev-download-queue \
  --region ap-southeast-1 \
  --query 'QueueUrl' \
  --output text)

aws sqs get-queue-attributes \
  --queue-url "$QUEUE_URL" \
  --attribute-names ApproximateNumberOfMessages \
  --region ap-southeast-1
```

### Method 2: Manual Replay (For Small Batches)

For a small number of messages, you can manually move them:

**Step 1: Receive messages from DLQ:**
```bash
aws sqs receive-message \
  --queue-url "$DLQ_URL" \
  --max-number-of-messages 10 \
  --region ap-southeast-1 \
  --output json > messages.json
```

**Step 2: Send messages to main queue:**
```bash
QUEUE_URL=$(aws sqs get-queue-url \
  --queue-name ts-batch-v2-dev-download-queue \
  --region ap-southeast-1 \
  --query 'QueueUrl' \
  --output text)

# Extract and send each message
cat messages.json | jq -r '.Messages[] | .Body' | while read -r body; do
  aws sqs send-message \
    --queue-url "$QUEUE_URL" \
    --message-body "$body" \
    --region ap-southeast-1
done
```

**Step 3: Delete messages from DLQ:**
```bash
cat messages.json | jq -r '.Messages[] | "\(.MessageId) \(.ReceiptHandle)"' | while read -r id handle; do
  aws sqs delete-message \
    --queue-url "$DLQ_URL" \
    --receipt-handle "$handle" \
    --region ap-southeast-1
done
```

### Method 3: Bulk Replay Script

For large-scale replay, use this script:

```bash
#!/bin/bash
# replay-dlq.sh

set -e

DLQ_URL=$(aws sqs get-queue-url \
  --queue-name ts-batch-v2-dev-download-dlq \
  --region ap-southeast-1 \
  --query 'QueueUrl' \
  --output text)

QUEUE_URL=$(aws sqs get-queue-url \
  --queue-name ts-batch-v2-dev-download-queue \
  --region ap-southeast-1 \
  --query 'QueueUrl' \
  --output text)

BATCH_SIZE=10
MAX_BATCHES=${1:-100}  # Default: 100 batches (1000 messages)

echo "Replaying up to $((MAX_BATCHES * BATCH_SIZE)) messages from DLQ..."

for i in $(seq 1 $MAX_BATCHES); do
  echo "Processing batch $i..."
  
  # Receive messages
  MESSAGES=$(aws sqs receive-message \
    --queue-url "$DLQ_URL" \
    --max-number-of-messages $BATCH_SIZE \
    --region ap-southeast-1 \
    --output json)
  
  # Check if we got any messages
  MSG_COUNT=$(echo "$MESSAGES" | jq '.Messages | length')
  
  if [ "$MSG_COUNT" -eq 0 ]; then
    echo "No more messages in DLQ"
    break
  fi
  
  echo "Found $MSG_COUNT messages"
  
  # Send to main queue and delete from DLQ
  echo "$MESSAGES" | jq -r '.Messages[] | "\(.Body)|\(.ReceiptHandle)"' | while IFS='|' read -r body handle; do
    # Send to main queue
    aws sqs send-message \
      --queue-url "$QUEUE_URL" \
      --message-body "$body" \
      --region ap-southeast-1 > /dev/null
    
    # Delete from DLQ
    aws sqs delete-message \
      --queue-url "$DLQ_URL" \
      --receipt-handle "$handle" \
      --region ap-southeast-1
  done
  
  echo "Batch $i complete"
  sleep 1  # Rate limiting
done

echo "Replay complete!"
```

Make it executable and run:
```bash
chmod +x replay-dlq.sh
./replay-dlq.sh 50  # Replay 50 batches (500 messages)
```

## Purging Invalid Messages

If messages are permanently invalid (e.g., invalid symbols), purge them instead of replaying:

**Purge entire DLQ (use with caution!):**
```bash
aws sqs purge-queue \
  --queue-url "$DLQ_URL" \
  --region ap-southeast-1
```

**Selective purge (filter by pattern):**
```bash
# Receive and filter messages
aws sqs receive-message \
  --queue-url "$DLQ_URL" \
  --max-number-of-messages 10 \
  --region ap-southeast-1 \
  --output json | \
  jq -r '.Messages[] | select(.Body | contains("INVALID_SYMBOL")) | .ReceiptHandle' | \
  while read -r handle; do
    aws sqs delete-message \
      --queue-url "$DLQ_URL" \
      --receipt-handle "$handle" \
      --region ap-southeast-1
  done
```

## Monitoring Replay

### During Replay

**Watch DLQ depth decrease:**
```bash
watch -n 5 'aws sqs get-queue-attributes \
  --queue-url $(aws sqs get-queue-url --queue-name ts-batch-v2-dev-download-dlq --region ap-southeast-1 --query QueueUrl --output text) \
  --attribute-names ApproximateNumberOfMessages \
  --region ap-southeast-1 \
  --query "Attributes.ApproximateNumberOfMessages"'
```

**Watch main queue processing:**
```bash
watch -n 5 'aws sqs get-queue-attributes \
  --queue-url $(aws sqs get-queue-url --queue-name ts-batch-v2-dev-download-queue --region ap-southeast-1 --query QueueUrl --output text) \
  --attribute-names ApproximateNumberOfMessages \
  --region ap-southeast-1 \
  --query "Attributes.ApproximateNumberOfMessages"'
```

**Monitor Lambda invocations:**
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

### After Replay

**Verify success:**
1. DLQ depth should be 0 or significantly reduced
2. No new errors in CloudWatch logs
3. S3 objects created for replayed symbols
4. DynamoDB records updated

**Check for new failures:**
```bash
# Wait 10 minutes, then check DLQ again
sleep 600

aws sqs get-queue-attributes \
  --queue-url "$DLQ_URL" \
  --attribute-names ApproximateNumberOfMessages \
  --region ap-southeast-1
```

If messages return to DLQ, investigate further.

## Best Practices

### Before Replaying

1. **Identify root cause**: Don't replay until you understand why messages failed
2. **Fix the issue**: Resolve the underlying problem first
3. **Test with small batch**: Replay 10-100 messages first to verify fix
4. **Monitor closely**: Watch logs and metrics during replay

### During Replay

1. **Rate limiting**: Don't replay too fast (respect API limits)
2. **Batch processing**: Replay in batches of 100-1000 messages
3. **Monitor errors**: Watch for new failures
4. **Document actions**: Keep notes on what was done and why

### After Replay

1. **Verify data**: Check S3 and DynamoDB for expected data
2. **Monitor for 24 hours**: Ensure no recurring issues
3. **Update runbooks**: Document lessons learned
4. **Review alarms**: Adjust thresholds if needed

## Troubleshooting Replay Issues

### Messages Return to DLQ Immediately

**Cause:** Root cause not fixed

**Resolution:**
1. Stop replay
2. Re-investigate error logs
3. Fix underlying issue
4. Wait before retrying

### Replay Lambda Times Out

**Cause:** Too many messages or slow processing

**Resolution:**
1. Reduce `maxMessages` parameter
2. Increase Lambda timeout
3. Run replay multiple times with smaller batches

### Messages Disappear from DLQ but Don't Process

**Cause:** Messages deleted but not sent to main queue

**Resolution:**
1. Check replay Lambda logs for errors
2. Verify IAM permissions for SQS send
3. May need to regenerate tasks from Task Generator

## Emergency Procedures

### Complete System Failure

If the entire system is failing:

1. **Stop processing**: Disable EventBridge rule
```bash
aws events disable-rule \
  --name ts-batch-v2-dev-daily-trigger \
  --region ap-southeast-1
```

2. **Investigate**: Review all logs and metrics
3. **Fix issues**: Apply necessary fixes
4. **Test**: Manually trigger with small dataset
5. **Resume**: Re-enable EventBridge rule
```bash
aws events enable-rule \
  --name ts-batch-v2-dev-daily-trigger \
  --region ap-southeast-1
```

### Data Loss Prevention

If you suspect data loss:

1. **Check S3**: Verify expected objects exist
2. **Check DynamoDB**: Verify expected records exist
3. **Compare counts**: Task Generator messages vs S3 objects
4. **Regenerate if needed**: Run Task Generator again for missing dates

## Additional Resources

- [AWS SQS Dead Letter Queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html)
- [Lambda Error Handling](https://docs.aws.amazon.com/lambda/latest/dg/invocation-retries.html)
- [SQS Message Visibility](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html)
