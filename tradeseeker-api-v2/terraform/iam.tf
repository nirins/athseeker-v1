# Lambda execution role
resource "aws_iam_role" "lambda_execution" {
  name = "${var.project_name}-${var.environment}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-${var.environment}-lambda-role"
  }
}

# DynamoDB read policy
resource "aws_iam_policy" "dynamodb_read" {
  name        = "${var.project_name}-${var.environment}-dynamodb-read"
  description = "Allow Lambda to read from DynamoDB tables"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          "arn:aws:dynamodb:${var.aws_region}:*:table/${var.golden_crosses_table}",
          "arn:aws:dynamodb:${var.aws_region}:*:table/${var.golden_crosses_table}/index/*",
          "arn:aws:dynamodb:${var.aws_region}:*:table/${var.death_crosses_table}",
          "arn:aws:dynamodb:${var.aws_region}:*:table/${var.death_crosses_table}/index/*",
          "arn:aws:dynamodb:${var.aws_region}:*:table/${var.stock_prices_table}",
          "arn:aws:dynamodb:${var.aws_region}:*:table/${var.ath_stocks_table}",
          "arn:aws:dynamodb:${var.aws_region}:*:table/${var.ath_stocks_table}/index/*",
          "arn:aws:dynamodb:${var.aws_region}:*:table/${var.near_ath_stocks_table}",
          "arn:aws:dynamodb:${var.aws_region}:*:table/${var.near_ath_stocks_table}/index/*"
        ]
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-${var.environment}-dynamodb-read"
  }
}

# Secrets Manager read policy
resource "aws_iam_policy" "secrets_manager_read" {
  name        = "${var.project_name}-${var.environment}-secrets-read"
  description = "Allow Lambda to read from Secrets Manager"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          "arn:aws:secretsmanager:${var.aws_region}:*:secret:${var.eodhd_secret_name}*",
          "arn:aws:secretsmanager:${var.aws_region}:*:secret:${aws_secretsmanager_secret.openai_api_key.name}*"
        ]
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-${var.environment}-secrets-read"
  }
}

# Attach Secrets Manager read policy to Lambda role
resource "aws_iam_role_policy_attachment" "lambda_secrets_manager" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = aws_iam_policy.secrets_manager_read.arn
}

# Attach DynamoDB read policy to Lambda role
resource "aws_iam_role_policy_attachment" "lambda_dynamodb" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = aws_iam_policy.dynamodb_read.arn
}

# Attach AWS managed policy for Lambda basic execution (CloudWatch Logs)
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
# S3 write policy for training data
resource "aws_iam_policy" "s3_training_data_write" {
  name        = "${var.project_name}-${var.environment}-s3-training-data-write"
  description = "Allow Lambda to write training data to S3"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:PutObjectAcl"
        ]
        Resource = [
          "${aws_s3_bucket.training_data.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.training_data.arn
        ]
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-${var.environment}-s3-training-data-write"
  }
}

# Attach S3 training data write policy to Lambda role
resource "aws_iam_role_policy_attachment" "lambda_s3_training_data" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = aws_iam_policy.s3_training_data_write.arn
}