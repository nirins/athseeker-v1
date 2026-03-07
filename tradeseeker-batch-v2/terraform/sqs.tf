# SQS queues for download task management

# Dead Letter Queue
resource "aws_sqs_queue" "dlq" {
  name                      = local.sqs_dlq_name
  message_retention_seconds = 1209600 # 14 days

  tags = merge(
    local.common_tags,
    {
      Name = local.sqs_dlq_name
    }
  )
}

# Main Queue
resource "aws_sqs_queue" "main" {
  name                       = local.sqs_queue_name
  visibility_timeout_seconds = var.sqs_visibility_timeout
  message_retention_seconds  = 1209600 # 14 days
  receive_wait_time_seconds  = 20      # Long polling

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = var.sqs_max_receives
  })

  tags = merge(
    local.common_tags,
    {
      Name = local.sqs_queue_name
    }
  )
}

# CloudWatch alarm for DLQ depth
resource "aws_cloudwatch_metric_alarm" "dlq_depth" {
  count = local.current_config.enable_cloudwatch_alarms ? 1 : 0

  alarm_name          = "${local.name_prefix}-dlq-depth"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Average"
  threshold           = 100
  alarm_description   = "Alert when DLQ has more than 100 messages"
  treat_missing_data  = "notBreaching"

  dimensions = {
    QueueName = aws_sqs_queue.dlq.name
  }

  tags = local.common_tags
}

# CloudWatch alarm for queue age
resource "aws_cloudwatch_metric_alarm" "queue_age" {
  count = local.current_config.enable_cloudwatch_alarms ? 1 : 0

  alarm_name          = "${local.name_prefix}-queue-age"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateAgeOfOldestMessage"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Maximum"
  threshold           = 3600 # 1 hour
  alarm_description   = "Alert when oldest message is older than 1 hour"
  treat_missing_data  = "notBreaching"

  dimensions = {
    QueueName = aws_sqs_queue.main.name
  }

  tags = local.common_tags
}
