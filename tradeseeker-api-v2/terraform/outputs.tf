output "api_gateway_url" {
  description = "Base URL for API Gateway"
  value       = "${aws_api_gateway_stage.tradeseeker_api.invoke_url}"
}

output "api_gateway_id" {
  description = "API Gateway REST API ID"
  value       = aws_api_gateway_rest_api.tradeseeker_api.id
}

output "lambda_function_name" {
  description = "Lambda function name"
  value       = aws_lambda_function.tradeseeker_api.function_name
}

output "lambda_function_arn" {
  description = "Lambda function ARN"
  value       = aws_lambda_function.tradeseeker_api.arn
}

output "cloudwatch_log_group" {
  description = "CloudWatch Log Group name for Lambda"
  value       = aws_cloudwatch_log_group.lambda_logs.name
}

# Cognito outputs (uncomment when enabling Cognito)
# output "cognito_user_pool_id" {
#   description = "Cognito User Pool ID for Angular app configuration"
#   value       = aws_cognito_user_pool.tradeseeker_users.id
# }

# output "cognito_user_pool_arn" {
#   description = "Cognito User Pool ARN"
#   value       = aws_cognito_user_pool.tradeseeker_users.arn
# }

# output "cognito_client_id" {
#   description = "Cognito User Pool Client ID for Angular app configuration"
#   value       = aws_cognito_user_pool_client.angular_app.id
# }

# output "cognito_domain" {
#   description = "Cognito User Pool domain"
#   value       = aws_cognito_user_pool.tradeseeker_users.domain
# }

# API Endpoints
output "golden_crosses_endpoint" {
  description = "Full URL for golden crosses endpoint"
  value       = "${aws_api_gateway_stage.tradeseeker_api.invoke_url}/golden-crosses"
}

output "ath_endpoint" {
  description = "Full URL for all-time high stocks endpoint"
  value       = "${aws_api_gateway_stage.tradeseeker_api.invoke_url}/ath"
}

output "stocks_endpoint" {
  description = "Full URL for stocks endpoint (append /{symbol})"
  value       = "${aws_api_gateway_stage.tradeseeker_api.invoke_url}/stocks"
}

output "openai_summary_endpoint" {
  description = "Full URL for OpenAI summary endpoint"
  value       = "${aws_api_gateway_stage.tradeseeker_api.invoke_url}/openai-summary"
}

output "openai_secret_name" {
  description = "AWS Secrets Manager secret name for OpenAI API key"
  value       = aws_secretsmanager_secret.openai_api_key.name
}
