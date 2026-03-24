# IAM roles and policies for Lambda functions

# Task Generator Lambda Role
resource "aws_iam_role" "task_generator" {
  name = "${local.task_generator_name}-role"

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

  tags = local.common_tags
}

# Task Generator Lambda Policy
resource "aws_iam_role_policy" "task_generator" {
  name = "${local.task_generator_name}-policy"
  role = aws_iam_role.task_generator.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${local.aws_account_id}:log-group:/aws/lambda/${local.task_generator_name}:*"
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:SendMessageBatch"
        ]
        Resource = aws_sqs_queue.main.arn
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters"
        ]
        Resource = [
          "arn:aws:ssm:${var.aws_region}:${local.aws_account_id}:parameter${local.markets_parameter_name}",
          "arn:aws:ssm:${var.aws_region}:${local.aws_account_id}:parameter${local.api_endpoints_parameter_name}"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = "arn:aws:secretsmanager:${var.aws_region}:${local.aws_account_id}:secret:${local.eodhd_secret_name}-*"
      }
    ]
  })
}

# Downloader Lambda Role
resource "aws_iam_role" "downloader" {
  name = "${local.downloader_name}-role"

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

  tags = local.common_tags
}

# Downloader Lambda Policy
resource "aws_iam_role_policy" "downloader" {
  name = "${local.downloader_name}-policy"
  role = aws_iam_role.downloader.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${local.aws_account_id}:log-group:/aws/lambda/${local.downloader_name}:*"
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:ChangeMessageVisibility"
        ]
        Resource = aws_sqs_queue.main.arn
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:PutObjectAcl"
        ]
        Resource = "${aws_s3_bucket.stock_prices.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:DeleteItem"
        ]
        Resource = [
          aws_dynamodb_table.stock_prices.arn,
          aws_dynamodb_table.stock_prices_lite.arn,
          aws_dynamodb_table.golden_crosses.arn,
          aws_dynamodb_table.death_crosses.arn,
          aws_dynamodb_table.ath_detections.arn,
          aws_dynamodb_table.near_ath_detections.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters"
        ]
        Resource = [
          "arn:aws:ssm:${var.aws_region}:${local.aws_account_id}:parameter${local.api_endpoints_parameter_name}"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = "arn:aws:secretsmanager:${var.aws_region}:${local.aws_account_id}:secret:${local.eodhd_secret_name}-*"
      }
    ]
  })
}

# DLQ Replay Lambda Role
resource "aws_iam_role" "dlq_replay" {
  name = "${local.dlq_replay_name}-role"

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

  tags = local.common_tags
}

# DLQ Replay Lambda Policy
resource "aws_iam_role_policy" "dlq_replay" {
  name = "${local.dlq_replay_name}-policy"
  role = aws_iam_role.dlq_replay.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${local.aws_account_id}:log-group:/aws/lambda/${local.dlq_replay_name}:*"
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = aws_sqs_queue.dlq.arn
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage"
        ]
        Resource = aws_sqs_queue.main.arn
      }
    ]
  })
}

# X Poster Lambda Role
resource "aws_iam_role" "x_poster" {
  name = "${local.x_poster_name}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action    = "sts:AssumeRole"
        Effect    = "Allow"
        Principal = { Service = "lambda.amazonaws.com" }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy" "x_poster" {
  name = "${local.x_poster_name}-policy"
  role = aws_iam_role.x_poster.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:${var.aws_region}:${local.aws_account_id}:log-group:/aws/lambda/${local.x_poster_name}:*"
      },
      {
        Effect   = "Allow"
        Action   = ["dynamodb:Query"]
        Resource = [
          aws_dynamodb_table.ath_detections.arn,
          "${aws_dynamodb_table.ath_detections.arn}/index/*"
        ]
      },
      {
        Effect   = "Allow"
        Action   = ["dynamodb:GetItem"]
        Resource = aws_dynamodb_table.stock_prices_lite.arn
      },
      {
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = "arn:aws:secretsmanager:${var.aws_region}:${local.aws_account_id}:secret:${local.x_secret_name}-*"
      }
    ]
  })
}
