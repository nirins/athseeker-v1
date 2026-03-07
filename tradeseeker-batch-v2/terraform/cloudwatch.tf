# CloudWatch log groups and alarms

# Task Generator Lambda log group
resource "aws_cloudwatch_log_group" "task_generator" {
  name              = "/aws/lambda/${local.task_generator_name}"
  retention_in_days = 14

  tags = merge(
    local.common_tags,
    {
      Name = "${local.task_generator_name}-logs"
    }
  )
}

# Downloader Lambda log group
resource "aws_cloudwatch_log_group" "downloader" {
  name              = "/aws/lambda/${local.downloader_name}"
  retention_in_days = 14

  tags = merge(
    local.common_tags,
    {
      Name = "${local.downloader_name}-logs"
    }
  )
}

# Task Generator Lambda error alarm
resource "aws_cloudwatch_metric_alarm" "task_generator_errors" {
  count = local.current_config.enable_cloudwatch_alarms ? 1 : 0

  alarm_name          = "${local.task_generator_name}-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Alert when Task Generator Lambda has more than 5 errors"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.task_generator.function_name
  }

  tags = local.common_tags
}

# Downloader Lambda error alarm
resource "aws_cloudwatch_metric_alarm" "downloader_errors" {
  count = local.current_config.enable_cloudwatch_alarms ? 1 : 0

  alarm_name          = "${local.downloader_name}-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 50
  alarm_description   = "Alert when Downloader Lambda has more than 50 errors in 10 minutes"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.downloader.function_name
  }

  tags = local.common_tags
}

# Downloader Lambda throttle alarm
resource "aws_cloudwatch_metric_alarm" "downloader_throttles" {
  count = local.current_config.enable_cloudwatch_alarms ? 1 : 0

  alarm_name          = "${local.downloader_name}-throttles"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Throttles"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "Alert when Downloader Lambda is throttled"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.downloader.function_name
  }

  tags = local.common_tags
}

# DLQ Replay Lambda Log Group
resource "aws_cloudwatch_log_group" "dlq_replay" {
  name              = "/aws/lambda/${local.dlq_replay_name}"
  retention_in_days = 7

  tags = local.common_tags
}
