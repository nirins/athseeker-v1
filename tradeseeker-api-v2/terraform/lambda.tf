# Lambda function
resource "aws_lambda_function" "tradeseeker_api" {
  filename         = "${path.module}/../build/lambda_package.zip"
  function_name    = "${var.project_name}-${var.environment}"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "src.lambda_handler.lambda_handler"
  source_code_hash = filebase64sha256("${path.module}/../build/lambda_package.zip")
  runtime         = "python3.12"
  timeout         = 30
  memory_size     = 1024

  environment {
    variables = {
      LAMBDA_REGION                = var.aws_region
      GOLDEN_CROSSES_TABLE         = var.golden_crosses_table
      DEATH_CROSSES_TABLE          = var.death_crosses_table
      STOCK_PRICES_TABLE           = var.stock_prices_table
      STOCK_PRICES_LITE_TABLE      = var.stock_prices_lite_table
      ATH_STOCKS_TABLE             = var.ath_stocks_table
      NEAR_ATH_STOCKS_TABLE        = var.near_ath_stocks_table
      CROSS_DATE_INDEX             = var.cross_date_index
      MARKET_CODE_CROSS_DATE_INDEX = var.market_code_cross_date_index
      EODHD_SECRET_NAME            = var.eodhd_secret_name
      OPENAI_SECRET_NAME           = aws_secretsmanager_secret.openai_api_key.name
      TRAINING_DATA_BUCKET         = aws_s3_bucket.training_data.bucket
      WATCHLIST_TABLE              = aws_dynamodb_table.watchlist.name
      ENVIRONMENT                  = var.environment
      DOWNLOAD_QUEUE_URL           = "https://sqs.${var.aws_region}.amazonaws.com/894546098844/ts-batch-v2-${var.environment}-download-queue"
    }
  }

  tags = {
    Name = "${var.project_name}-${var.environment}"
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${aws_lambda_function.tradeseeker_api.function_name}"
  retention_in_days = 14

  tags = {
    Name = "${var.project_name}-${var.environment}-logs"
  }
}
