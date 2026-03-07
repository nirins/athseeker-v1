# Lambda functions

# Task Generator Lambda
resource "aws_lambda_function" "task_generator" {
  filename         = "${path.module}/../lambdas/task-generator/task-generator.zip"
  function_name    = local.task_generator_name
  role            = aws_iam_role.task_generator.arn
  handler         = "handler.handler"
  source_code_hash = fileexists("${path.module}/../lambdas/task-generator/task-generator.zip") ? filebase64sha256("${path.module}/../lambdas/task-generator/task-generator.zip") : null
  runtime         = "python3.12"
  timeout         = local.current_config.lambda_timeout
  memory_size     = local.current_config.lambda_memory_size

  environment {
    variables = {
      ENVIRONMENT   = local.environment
      SQS_QUEUE_URL = aws_sqs_queue.main.url
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.task_generator
  ]

  tags = merge(
    local.common_tags,
    {
      Name = local.task_generator_name
    }
  )
}

# Downloader Lambda
resource "aws_lambda_function" "downloader" {
  filename         = "${path.module}/../lambdas/downloader/downloader.zip"
  function_name    = local.downloader_name
  role            = aws_iam_role.downloader.arn
  handler         = "handler.handler"
  source_code_hash = fileexists("${path.module}/../lambdas/downloader/downloader.zip") ? filebase64sha256("${path.module}/../lambdas/downloader/downloader.zip") : null
  runtime         = "python3.12"
  timeout         = local.current_config.lambda_timeout
  memory_size     = local.current_config.lambda_memory_size
  
  reserved_concurrent_executions = local.current_config.lambda_reserved_concurrency

  environment {
    variables = {
      ENVIRONMENT         = local.environment
      S3_BUCKET_NAME      = aws_s3_bucket.stock_prices.id
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.stock_prices.name
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.downloader
  ]

  tags = merge(
    local.common_tags,
    {
      Name = local.downloader_name
    }
  )
}

# Lambda-SQS event source mapping
resource "aws_lambda_event_source_mapping" "downloader_sqs" {
  event_source_arn = aws_sqs_queue.main.arn
  function_name    = aws_lambda_function.downloader.arn
  batch_size       = local.current_config.sqs_batch_size
  
  # Enable partial batch failure reporting
  function_response_types = ["ReportBatchItemFailures"]
  
  # Scaling configuration
  scaling_config {
    maximum_concurrency = local.current_config.lambda_reserved_concurrency
  }
}

# DLQ Replay Lambda
resource "aws_lambda_function" "dlq_replay" {
  filename         = "${path.module}/../lambdas/dlq-replay/dlq-replay.zip"
  function_name    = local.dlq_replay_name
  role            = aws_iam_role.dlq_replay.arn
  handler         = "handler.handler"
  source_code_hash = fileexists("${path.module}/../lambdas/dlq-replay/dlq-replay.zip") ? filebase64sha256("${path.module}/../lambdas/dlq-replay/dlq-replay.zip") : null
  runtime         = "python3.12"
  timeout         = 300  # 5 minutes for batch processing
  memory_size     = 256

  environment {
    variables = {
      DLQ_URL         = aws_sqs_queue.dlq.url
      MAIN_QUEUE_URL  = aws_sqs_queue.main.url
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.dlq_replay
  ]

  tags = merge(
    local.common_tags,
    {
      Name = local.dlq_replay_name
    }
  )
}
