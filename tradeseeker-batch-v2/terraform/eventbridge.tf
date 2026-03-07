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
