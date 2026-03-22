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
      ENVIRONMENT              = local.environment
      S3_BUCKET_NAME           = aws_s3_bucket.stock_prices.id
      DYNAMODB_TABLE_NAME      = aws_dynamodb_table.stock_prices.name
      DYNAMODB_LITE_TABLE_NAME = aws_dynamodb_table.stock_prices_lite.name
      MAX_DAILY_VOLATILITY     = var.max_daily_volatility
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

# X Poster Lambda
resource "aws_lambda_function" "x_poster" {
  filename         = "${path.module}/../lambdas/x-poster/x-poster.zip"
  function_name    = local.x_poster_name
  role             = aws_iam_role.x_poster.arn
  handler          = "handler.handler"
  source_code_hash = fileexists("${path.module}/../lambdas/x-poster/x-poster.zip") ? filebase64sha256("${path.module}/../lambdas/x-poster/x-poster.zip") : null
  runtime          = "python3.12"
  timeout          = 60
  memory_size      = 256

  environment {
    variables = {
      ENVIRONMENT    = local.environment
      ATH_TABLE_NAME = aws_dynamodb_table.ath_detections.name
      X_SECRET_NAME  = local.x_secret_name
      MARKET_CODE    = "US"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.x_poster
  ]

  tags = merge(
    local.common_tags,
    {
      Name = local.x_poster_name
    }
  )
}

resource "aws_cloudwatch_log_group" "x_poster" {
  name              = "/aws/lambda/${local.x_poster_name}"
  retention_in_days = 14
  tags              = local.common_tags
}

# EventBridge schedule to trigger X poster daily
resource "aws_cloudwatch_event_rule" "x_poster_schedule" {
  name                = "${local.x_poster_name}-schedule"
  description         = "Daily trigger for X poster Lambda"
  schedule_expression = "cron(0 22 * * ? *)"  # 5 AM Thailand time (UTC+7)
  state               = "ENABLED"
  tags                = local.common_tags
}

resource "aws_cloudwatch_event_target" "x_poster_schedule" {
  rule      = aws_cloudwatch_event_rule.x_poster_schedule.name
  target_id = "x-poster-lambda"
  arn       = aws_lambda_function.x_poster.arn
}

resource "aws_lambda_permission" "x_poster_eventbridge" {
  statement_id  = "AllowEventBridgeInvokeXPoster"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.x_poster.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.x_poster_schedule.arn
}
