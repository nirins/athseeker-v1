# AWS Secrets Manager secret for OpenAI API key
resource "aws_secretsmanager_secret" "openai_api_key" {
  name        = "${var.project_name}-${var.environment}-openai-api-key"
  description = "OpenAI API key for ChatGPT integration"

  tags = {
    Name        = "${var.project_name}-${var.environment}-openai-api-key"
    Environment = var.environment
    Purpose     = "OpenAI API Integration"
  }
}

# Secret version (placeholder - you'll need to set the actual value manually or via CLI)
resource "aws_secretsmanager_secret_version" "openai_api_key" {
  secret_id     = aws_secretsmanager_secret.openai_api_key.id
  secret_string = jsonencode({
    api_key = var.openai_api_key != "" ? var.openai_api_key : "PLACEHOLDER_SET_MANUALLY"
  })

  lifecycle {
    ignore_changes = [secret_string]
  }
}