# DLQ Replay Lambda

This Lambda function replays failed messages from the Dead Letter Queue (DLQ) back to the main processing queue.

## Purpose

When messages fail after maximum retry attempts, they are sent to the DLQ. This Lambda allows you to:
- Replay all DLQ messages back to the main queue
- Filter messages by symbol or market code before replaying
- Control the number of messages to replay in a single invocation

## Usage

### Manual Invocation

Invoke the Lambda manually through AWS Console or CLI with optional parameters:

```bash
aws lambda invoke \
  --function-name ts-batch-v2-dev-dlq-replay \
  --payload '{"max_messages": 50}' \
  response.json
```

### Event Parameters

- `max_messages` (optional, default: 10): Maximum number of messages to replay
- `filter_symbol` (optional): Only replay messages for a specific symbol (e.g., "AAPL")
- `filter_market` (optional): Only replay messages for a specific market (e.g., "US")

### Examples

Replay up to 100 messages:
```json
{
  "max_messages": 100
}
```

Replay only AAPL messages:
```json
{
  "max_messages": 50,
  "filter_symbol": "AAPL"
}
```

Replay only US market messages:
```json
{
  "max_messages": 50,
  "filter_market": "US"
}
```

Replay specific symbol in specific market:
```json
{
  "max_messages": 10,
  "filter_symbol": "PTT",
  "filter_market": "BK"
}
```

## Response

The Lambda returns statistics about the replay operation:

```json
{
  "statusCode": 200,
  "body": {
    "message": "DLQ replay completed",
    "statistics": {
      "received": 50,
      "filtered": 45,
      "replayed": 45,
      "deleted": 45,
      "failed": 0
    }
  }
}
```

Statistics:
- `received`: Total messages received from DLQ
- `filtered`: Messages that passed filters
- `replayed`: Messages successfully re-enqueued to main queue
- `deleted`: Messages successfully deleted from DLQ
- `failed`: Messages that failed to replay

## Deployment

Package the Lambda:
```bash
./scripts/package-dlq-replay.sh
```

Deploy with Terraform:
```bash
cd terraform
terraform apply
```

## Monitoring

CloudWatch logs are available at:
```
/aws/lambda/ts-batch-v2-{env}-dlq-replay
```

## IAM Permissions

The Lambda requires:
- `sqs:ReceiveMessage`, `sqs:DeleteMessage`, `sqs:GetQueueAttributes` on DLQ
- `sqs:SendMessage` on main queue
- CloudWatch Logs permissions
