# EventBridge Scheduler for daily task generation

resource "aws_scheduler_schedule" "daily_trigger" {
  name        = local.schedule_name
  description = "Trigger Task Generator Lambda daily at 4 AM Thailand time"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = var.schedule_expression
  
  state = var.schedule_enabled ? "ENABLED" : "DISABLED"

  target {
    arn      = aws_lambda_function.task_generator.arn
    role_arn = aws_iam_role.scheduler_role.arn

    input = jsonencode({
      date = "{{execution-time:yyyy-MM-dd}}"
    })
  }
}

# EventBridge Scheduler for BK market at 7 PM Thailand time
resource "aws_scheduler_schedule" "bk_market_trigger" {
  name        = "${local.name_prefix}-bk-market-trigger"
  description = "Trigger Task Generator Lambda for BK market daily at 7 PM Thailand time"

  flexible_time_window {
    mode = "OFF"
  }

  # 7 PM Thailand time = 12 PM UTC (Thailand is UTC+7), Monday to Friday only
  schedule_expression = "cron(0 12 ? * MON-FRI *)"
  
  state = "ENABLED"

  target {
    arn      = aws_lambda_function.task_generator.arn
    role_arn = aws_iam_role.scheduler_role.arn

    input = jsonencode({
      date   = "{{execution-time:yyyy-MM-dd}}"
      market = "BK"
    })
  }
}

# EventBridge Scheduler for US market at 7 PM New York time
resource "aws_scheduler_schedule" "us_market_trigger" {
  name        = "${local.name_prefix}-us-market-trigger"
  description = "Trigger Task Generator Lambda for US market daily at 7 PM New York time"

  flexible_time_window {
    mode = "OFF"
  }

  # 7 PM New York time = 11 PM UTC (EST) or 12 AM UTC (EDT), Monday to Friday only
  # Using 11 PM UTC (23:00) for EST - adjust seasonally if needed
  schedule_expression = "cron(0 23 ? * MON-FRI *)"
  
  state = "ENABLED"

  target {
    arn      = aws_lambda_function.task_generator.arn
    role_arn = aws_iam_role.scheduler_role.arn

    input = jsonencode({
      date   = "{{execution-time:yyyy-MM-dd}}"
      market = "US"
    })
  }
}

# IAM role for EventBridge Scheduler
resource "aws_iam_role" "scheduler_role" {
  name = "${local.name_prefix}-scheduler-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "scheduler.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = local.common_tags
}

# IAM policy for Scheduler to invoke Lambda
resource "aws_iam_role_policy" "scheduler_invoke_lambda" {
  name = "InvokeLambda"
  role = aws_iam_role.scheduler_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = aws_lambda_function.task_generator.arn
      }
    ]
  })
}
