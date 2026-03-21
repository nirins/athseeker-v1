locals {
  # Environment-specific configurations
  env_config = {
    dev = {
      aws_account_id              = "894546098844"
      lambda_memory_size          = 512
      lambda_timeout              = 120
      lambda_reserved_concurrency = 8
      sqs_batch_size             = 10
      dynamodb_billing_mode      = "PAY_PER_REQUEST"
      enable_cloudwatch_alarms   = false
    }
    uat = {
      aws_account_id              = "" # To be configured
      lambda_memory_size          = 512
      lambda_timeout              = 120
      lambda_reserved_concurrency = 8
      sqs_batch_size             = 10
      dynamodb_billing_mode      = "PAY_PER_REQUEST"
      enable_cloudwatch_alarms   = true
    }
    prod = {
      aws_account_id              = "" # To be configured
      lambda_memory_size          = 1024
      lambda_timeout              = 120
      lambda_reserved_concurrency = 8
      sqs_batch_size             = 10
      dynamodb_billing_mode      = "PAY_PER_REQUEST"
      enable_cloudwatch_alarms   = true
    }
  }
  
  # Current environment configuration
  current_config = local.env_config[local.environment]
  
  # AWS Account ID (use from config or data source)
  aws_account_id = local.current_config.aws_account_id != "" ? local.current_config.aws_account_id : data.aws_caller_identity.current.account_id
  
  # Resource names
  s3_bucket_name       = "${local.name_prefix}-stock-prices-${local.aws_account_id}"
  dynamodb_table_name  = "${local.name_prefix}-stock-prices"
  sqs_queue_name       = "${local.name_prefix}-download-queue"
  sqs_dlq_name         = "${local.name_prefix}-download-dlq"
  
  # Lambda function names
  task_generator_name = "${local.name_prefix}-task-generator"
  downloader_name     = "${local.name_prefix}-downloader"
  dlq_replay_name     = "${local.name_prefix}-dlq-replay"
  x_poster_name       = "${local.name_prefix}-x-poster"
  
  # SSM Parameter paths
  markets_parameter_name      = "/ts-batch-v2/${local.environment}/markets"
  api_endpoints_parameter_name = "/ts-batch-v2/${local.environment}/api-endpoints"
  
  # Secrets Manager
  eodhd_secret_name = "ts-batch-v2-${local.environment}-eodhd-api-token"
  x_secret_name     = "ts-batch-v2-${local.environment}-x-credentials"
  
  # EventBridge
  schedule_name = "${local.name_prefix}-daily-trigger"
}
