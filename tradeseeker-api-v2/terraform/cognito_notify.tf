# SNS topic for new user sign-up notifications
resource "aws_sns_topic" "user_signup_notifications" {
  name = "${var.project_name}-${var.environment}-user-signup"

  tags = {
    Name = "${var.project_name}-${var.environment}-user-signup"
  }
}

# Add email subscriptions manually in AWS Console:
# SNS → Topics → ts-api-v2-dev-user-signup → Create subscription → Protocol: Email

# Lambda function for Cognito PostConfirmation trigger
resource "aws_lambda_function" "cognito_signup_notify" {
  filename         = "${path.module}/../build/lambda_package.zip"
  function_name    = "${var.project_name}-${var.environment}-cognito-signup-notify"
  role             = aws_iam_role.cognito_notify_lambda_role.arn
  handler          = "src.handlers.cognito_signup_notify.lambda_handler"
  source_code_hash = filebase64sha256("${path.module}/../build/lambda_package.zip")
  runtime          = "python3.12"
  timeout          = 10
  memory_size      = 128

  environment {
    variables = {
      SNS_TOPIC_ARN = aws_sns_topic.user_signup_notifications.arn
    }
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-cognito-signup-notify"
  }
}

# CloudWatch log group for the notify Lambda
resource "aws_cloudwatch_log_group" "cognito_notify_logs" {
  name              = "/aws/lambda/${aws_lambda_function.cognito_signup_notify.function_name}"
  retention_in_days = 14
}

# IAM role for the notify Lambda
resource "aws_iam_role" "cognito_notify_lambda_role" {
  name = "${var.project_name}-${var.environment}-cognito-notify-role"

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
}

# Allow Lambda to write CloudWatch logs
resource "aws_iam_role_policy_attachment" "cognito_notify_basic_execution" {
  role       = aws_iam_role.cognito_notify_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Allow Lambda to publish to the SNS topic
resource "aws_iam_role_policy" "cognito_notify_sns_publish" {
  name = "${var.project_name}-${var.environment}-cognito-notify-sns"
  role = aws_iam_role.cognito_notify_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "sns:Publish"
        Resource = aws_sns_topic.user_signup_notifications.arn
      }
    ]
  })
}

# Allow Cognito to invoke this Lambda
resource "aws_lambda_permission" "cognito_invoke_notify" {
  statement_id  = "AllowCognitoInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cognito_signup_notify.function_name
  principal     = "cognito-idp.amazonaws.com"
  source_arn    = "arn:aws:cognito-idp:${var.aws_region}:${var.aws_account_id}:userpool/${var.cognito_user_pool_id}"
}

# Wire the PostConfirmation trigger to the existing Cognito User Pool via AWS CLI.
# Terraform cannot safely manage an existing unimported pool, so we use a null_resource.
resource "null_resource" "cognito_post_confirmation_trigger" {
  count = var.cognito_user_pool_id != "" ? 1 : 0

  triggers = {
    lambda_arn    = aws_lambda_function.cognito_signup_notify.arn
    user_pool_id  = var.cognito_user_pool_id
  }

  provisioner "local-exec" {
    command = <<-EOT
      aws cognito-idp update-user-pool \
        --user-pool-id ${var.cognito_user_pool_id} \
        --lambda-config PostConfirmation=${aws_lambda_function.cognito_signup_notify.arn} \
        --region ${var.aws_region}
    EOT
  }
}

# Outputs
output "signup_sns_topic_arn" {
  description = "SNS topic ARN for user signup notifications"
  value       = aws_sns_topic.user_signup_notifications.arn
}

output "cognito_notify_lambda_arn" {
  description = "ARN of the Cognito PostConfirmation notify Lambda"
  value       = aws_lambda_function.cognito_signup_notify.arn
}
