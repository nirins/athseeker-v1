# Monitoring and Alerting Guide

## Overview

This guide covers monitoring, alerting, and observability for the batch processing system. The system uses CloudWatch for metrics, logs, and alarms to ensure reliable operation.

## CloudWatch Metrics

### Lambda Metrics

#### Task Generator Lambda
- **Invocations**: Number of times the function is invoked
- **Errors**: Number of failed invocations
- **Duration**: Execution time in milliseconds
- **Throttles**: Number of throttled invocations

**View metrics:**
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=ts-batch-v2-dev-task-generator \
  --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum \
  --region ap-southeast-1
```

#### Downloader Lambda
- **Invocations**: Should be high during processing (~10,000-12,500 invocations for 100k messages)
- **Errors**: Should be < 5% of invocations
- **Duration**: Average should be 3-5 seconds per batch
- **ConcurrentExecutions**: Should not exceed 8 (reserved concurrency)

**View concurrent executions:**
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name ConcurrentExecutions \
  --dimensions Name=FunctionName,Value=ts-batch-v2-dev-downloader \
  --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Maximum \
  --region ap-southeast-1
```

### SQS Metrics

#### Main Queue (download-queue)
- **ApproximateNumberOfMessagesVisible**: Messages available for processing
- **ApproximateAgeOfOldestMessage**: Age of oldest message in seconds
- **NumberOfMessagesSent**: Total messages sent to queue
- **NumberOfMessagesDeleted**: Total messages successfully processed

**View queue depth:**
```bash
QUEUE_URL=$(aws sqs get-queue-url \
  --queue-name ts-batch-v2-dev-download-queue \
  --region ap-southeast-1 \
  --query 'QueueUrl' \
  --output text)

aws sqs get-queue-attributes \
  --queue-url "$QUEUE_URL" \
  --attribute-names All \
  --region ap-southeast-1
```

**Key attributes to monitor:**
- `ApproximateNumberOfMessages`: Should decrease over time as messages are processed
- `ApproximateAgeOfOldestMessage`: Should be < 3600 seconds (1 hour)
- `ApproximateNumberOfMessagesNotVisible`: Messages currently being processed

#### Dead Letter Queue (download-dlq)
- **ApproximateNumberOfMessagesVisible**: Should be 0 or very low
- **NumberOfMessagesSent**: Total failed messages

**View DLQ depth:**
```bash
DLQ_URL=$(aws sqs get-queue-url \
  --queue-name ts-batch-v2-dev-download-dlq \
  --region ap-southeast-1 \
  --query 'QueueUrl' \
  --output text)

aws sqs get-queue-attributes \
  --queue-url "$DLQ_URL" \
  --attribute-names ApproximateNumberOfMessages \
  --region ap-southeast-1
```

### S3 Metrics

- **NumberOfObjects**: Total objects in bucket
- **BucketSizeBytes**: Total storage used

**Count S3 objects:**
```bash
aws s3 ls s3://ts-batch-v2-dev-stock-prices-894546098844/prices/ --recursive | wc -l
```

**Calculate bucket size:**
```bash
aws s3 ls s3://ts-batch-v2-dev-stock-prices-894546098844/prices/ --recursive --summarize | grep "Total Size"
```

### DynamoDB Metrics

- **ConsumedReadCapacityUnits**: Read capacity consumed
- **ConsumedWriteCapacityUnits**: Write capacity consumed
- **UserErrors**: Client-side errors (4xx)
- **SystemErrors**: Server-side errors (5xx)

**Count DynamoDB items:**
```bash
aws dynamodb scan \
  --table-name ts-batch-v2-dev-stock-prices \
  --region ap-southeast-1 \
  --select COUNT
```

## CloudWatch Alarms

### Configured Alarms

The Terraform configuration creates the following alarms:

#### 1. Lambda Error Rate Alarm
- **Metric**: Lambda Errors
- **Threshold**: > 5% error rate over 5 minutes
- **Action**: Send SNS notification (if configured)

**Check alarm status:**
```bash
aws cloudwatch describe-alarms \
  --alarm-names ts-batch-v2-dev-downloader-errors \
  --region ap-southeast-1
```

#### 2. DLQ Depth Alarm
- **Metric**: ApproximateNumberOfMessagesVisible
- **Threshold**: > 100 messages
- **Action**: Send SNS notification (if configured)

**Check alarm status:**
```bash
aws cloudwatch describe-alarms \
  --alarm-names ts-batch-v2-dev-dlq-depth \
  --region ap-southeast-1
```

#### 3. Queue Age Alarm
- **Metric**: ApproximateAgeOfOldestMessage
- **Threshold**: > 3600 seconds (1 hour)
- **Action**: Send SNS notification (if configured)

**Check alarm status:**
```bash
aws cloudwatch describe-alarms \
  --alarm-names ts-batch-v2-dev-queue-age \
  --region ap-southeast-1
```

### View All Alarms

```bash
aws cloudwatch describe-alarms \
  --alarm-name-prefix ts-batch-v2-dev \
  --region ap-southeast-1 \
  --query 'MetricAlarms[*].[AlarmName,StateValue,StateReason]' \
  --output table
```

### Alarm States

- **OK**: Metric is within threshold
- **ALARM**: Metric has breached threshold
- **INSUFFICIENT_DATA**: Not enough data to evaluate

## CloudWatch Logs

### Log Groups

Each Lambda function has its own log group:
- `/aws/lambda/ts-batch-v2-dev-task-generator`
- `/aws/lambda/ts-batch-v2-dev-downloader`
- `/aws/lambda/ts-batch-v2-dev-dlq-replay`

### Viewing Logs

**Tail logs in real-time:**
```bash
aws logs tail /aws/lambda/ts-batch-v2-dev-downloader \
  --region ap-southeast-1 \
  --follow
```

**View recent logs:**
```bash
aws logs tail /aws/lambda/ts-batch-v2-dev-downloader \
  --region ap-southeast-1 \
  --since 1h \
  --format short
```

**View logs for specific time range:**
```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/ts-batch-v2-dev-downloader \
  --start-time $(date -u -v-1H +%s)000 \
  --end-time $(date -u +%s)000 \
  --region ap-southeast-1 \
  --max-items 50
```

### Searching Logs

**Search for errors:**
```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/ts-batch-v2-dev-downloader \
  --filter-pattern "ERROR" \
  --region ap-southeast-1 \
  --max-items 20
```

**Search for specific symbol:**
```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/ts-batch-v2-dev-downloader \
  --filter-pattern "AAPL" \
  --region ap-southeast-1 \
  --max-items 10
```

**Search for rate limit errors:**
```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/ts-batch-v2-dev-downloader \
  --filter-pattern "429" \
  --region ap-southeast-1 \
  --max-items 20
```

**Search for timeout errors:**
```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/ts-batch-v2-dev-downloader \
  --filter-pattern "timeout" \
  --region ap-southeast-1 \
  --max-items 20
```

### Log Insights Queries

CloudWatch Logs Insights provides powerful querying capabilities.

**Query error rate by hour:**
```
fields @timestamp, @message
| filter @message like /ERROR/
| stats count() as error_count by bin(1h)
```

**Query average duration:**
```
fields @timestamp, @duration
| stats avg(@duration) as avg_duration, max(@duration) as max_duration, min(@duration) as min_duration
```

**Query top error messages:**
```
fields @timestamp, @message
| filter @message like /ERROR/
| stats count() as error_count by @message
| sort error_count desc
| limit 10
```

**Run query via CLI:**
```bash
aws logs start-query \
  --log-group-name /aws/lambda/ts-batch-v2-dev-downloader \
  --start-time $(date -u -v-1H +%s) \
  --end-time $(date -u +%s) \
  --query-string 'fields @timestamp, @message | filter @message like /ERROR/ | limit 20' \
  --region ap-southeast-1
```

## Monitoring Dashboard

### Create Custom Dashboard

You can create a CloudWatch dashboard to visualize key metrics:

```bash
aws cloudwatch put-dashboard \
  --dashboard-name ts-batch-v2-dev-monitoring \
  --dashboard-body file://dashboard.json \
  --region ap-southeast-1
```

**Example dashboard.json:**
```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/Lambda", "Invocations", {"stat": "Sum", "label": "Task Generator"}],
          [".", ".", {"stat": "Sum", "label": "Downloader"}]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "ap-southeast-1",
        "title": "Lambda Invocations"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/SQS", "ApproximateNumberOfMessagesVisible", {"stat": "Average"}]
        ],
        "period": 60,
        "stat": "Average",
        "region": "ap-southeast-1",
        "title": "Queue Depth"
      }
    }
  ]
}
```

### View Dashboard

```bash
aws cloudwatch get-dashboard \
  --dashboard-name ts-batch-v2-dev-monitoring \
  --region ap-southeast-1
```

Or view in AWS Console:
https://console.aws.amazon.com/cloudwatch/home?region=ap-southeast-1#dashboards:

## Health Checks

### Daily Health Check Script

Create a script to check system health:

```bash
#!/bin/bash
# health-check.sh

echo "=== Batch Processing System Health Check ==="
echo ""

# Check Lambda errors
echo "Lambda Errors (last hour):"
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=ts-batch-v2-dev-downloader \
  --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum \
  --region ap-southeast-1 \
  --query 'Datapoints[0].Sum'

# Check DLQ depth
echo ""
echo "DLQ Depth:"
DLQ_URL=$(aws sqs get-queue-url \
  --queue-name ts-batch-v2-dev-download-dlq \
  --region ap-southeast-1 \
  --query 'QueueUrl' \
  --output text)

aws sqs get-queue-attributes \
  --queue-url "$DLQ_URL" \
  --attribute-names ApproximateNumberOfMessages \
  --region ap-southeast-1 \
  --query 'Attributes.ApproximateNumberOfMessages'

# Check queue age
echo ""
echo "Queue Age (seconds):"
QUEUE_URL=$(aws sqs get-queue-url \
  --queue-name ts-batch-v2-dev-download-queue \
  --region ap-southeast-1 \
  --query 'QueueUrl' \
  --output text)

aws sqs get-queue-attributes \
  --queue-url "$QUEUE_URL" \
  --attribute-names ApproximateAgeOfOldestMessage \
  --region ap-southeast-1 \
  --query 'Attributes.ApproximateAgeOfOldestMessage'

# Check S3 object count
echo ""
echo "S3 Objects (today):"
aws s3 ls s3://ts-batch-v2-dev-stock-prices-894546098844/prices/market=US/dt=$(date +%Y-%m-%d)/ --recursive | wc -l

# Check DynamoDB item count
echo ""
echo "DynamoDB Items:"
aws dynamodb scan \
  --table-name ts-batch-v2-dev-stock-prices \
  --region ap-southeast-1 \
  --select COUNT \
  --query 'Count'

echo ""
echo "=== Health Check Complete ==="
```

Make it executable:
```bash
chmod +x health-check.sh
./health-check.sh
```

## Troubleshooting Guide

### High Error Rate

**Symptoms:**
- Lambda error rate > 5%
- CloudWatch alarm triggered

**Investigation:**
1. Check CloudWatch logs for error patterns
2. Look for specific error messages (rate limits, timeouts, API errors)
3. Check DLQ for failed messages

**Common causes:**
- API rate limiting (429 errors)
- Network timeouts
- Invalid API token
- Malformed data

**Resolution:**
- For rate limits: Verify Lambda concurrency is set to 8
- For timeouts: Increase Lambda timeout or reduce batch size
- For API errors: Check EODHD API status
- For data errors: Review and fix data validation

### High DLQ Depth

**Symptoms:**
- DLQ has > 100 messages
- CloudWatch alarm triggered

**Investigation:**
1. Sample messages from DLQ to identify patterns
2. Check error reasons in CloudWatch logs
3. Determine if errors are transient or permanent

**Resolution:**
- Fix root cause (see error rate troubleshooting)
- Replay DLQ messages (see DLQ_REPLAY.md)
- If messages are invalid, purge DLQ

### Queue Processing Slow

**Symptoms:**
- Queue age > 1 hour
- Messages not being processed quickly

**Investigation:**
1. Check Lambda concurrent executions
2. Check for Lambda throttling
3. Review Lambda duration metrics

**Resolution:**
- Verify reserved concurrency is set correctly
- Check for Lambda errors causing retries
- Consider increasing batch size (if within rate limits)

### No Data in S3/DynamoDB

**Symptoms:**
- S3 bucket is empty or has few objects
- DynamoDB table has no items

**Investigation:**
1. Check if Task Generator ran successfully
2. Check if SQS queue has messages
3. Check Downloader Lambda logs for errors

**Resolution:**
- Manually trigger Task Generator
- Check IAM permissions for S3/DynamoDB writes
- Verify API token is valid

## Best Practices

### Regular Monitoring

- Check CloudWatch dashboard daily
- Review error logs weekly
- Monitor DLQ depth continuously
- Track S3 storage costs monthly

### Alerting

- Configure SNS topics for alarm notifications
- Set up email/SMS alerts for critical alarms
- Create runbooks for common issues
- Document escalation procedures

### Log Retention

- Default: 7 days (configurable in Terraform)
- Consider longer retention for production
- Archive important logs to S3 for compliance

### Cost Optimization

- Monitor Lambda invocations and duration
- Review S3 storage and implement lifecycle policies
- Use DynamoDB on-demand billing for variable workloads
- Set up AWS Budgets for cost alerts

## Additional Resources

- [AWS Lambda Monitoring](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-functions.html)
- [CloudWatch Logs Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AnalyzingLogData.html)
- [SQS Monitoring](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-monitoring-using-cloudwatch.html)
- [DynamoDB Monitoring](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/monitoring-cloudwatch.html)
