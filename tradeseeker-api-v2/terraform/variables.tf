variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "ts-api-v2"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "ap-southeast-1"
}

variable "golden_crosses_table" {
  description = "DynamoDB table name for golden crosses"
  type        = string
  default     = "ts-batch-v2-dev-golden-crosses"
}

variable "death_crosses_table" {
  description = "DynamoDB table name for death crosses"
  type        = string
  default     = "ts-batch-v2-dev-death-crosses"
}

variable "stock_prices_table" {
  description = "DynamoDB table name for stock prices"
  type        = string
  default     = "ts-batch-v2-dev-stock-prices"
}

variable "ath_stocks_table" {
  description = "DynamoDB table name for ATH stocks"
  type        = string
  default     = "ts-batch-v2-dev-ath"
}

variable "near_ath_stocks_table" {
  description = "DynamoDB table name for Near ATH stocks"
  type        = string
  default     = "ts-batch-v2-dev-near-ath"
}

variable "cross_date_index" {
  description = "GSI name for cross_date index"
  type        = string
  default     = "cross_date-index"
}

variable "market_code_cross_date_index" {
  description = "GSI name for market_code-cross_date index"
  type        = string
  default     = "market_code-cross_date-index"
}

variable "eodhd_secret_name" {
  description = "AWS Secrets Manager secret name for EODHD API token"
  type        = string
  default     = "ts-batch-v2-dev-eodhd-api-token"
}

variable "openai_api_key" {
  description = "OpenAI API key for ChatGPT integration (optional, can be set manually in AWS Secrets Manager)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "aws_account_id" {
  description = "AWS account ID"
  type        = string
}

variable "cognito_user_pool_id" {
  description = "Existing Cognito User Pool ID to attach the PostConfirmation trigger to"
  type        = string
  default     = "ap-southeast-1_ZB2oGErmf"
}

# Optional Cognito variables (uncomment when enabling Cognito)
# variable "cognito_callback_urls" {
#   description = "Callback URLs for Cognito (Angular app URLs)"
#   type        = list(string)
#   default     = ["http://localhost:4200", "https://your-angular-app.com"]
# }

# variable "cognito_logout_urls" {
#   description = "Logout URLs for Cognito (Angular app URLs)"
#   type        = list(string)
#   default     = ["http://localhost:4200", "https://your-angular-app.com"]
# }
