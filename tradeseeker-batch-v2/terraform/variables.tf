variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "ap-southeast-1"
}

variable "lambda_reserved_concurrency" {
  description = "Reserved concurrency for Downloader Lambda"
  type        = number
  default     = 8
}

variable "sqs_batch_size" {
  description = "Number of messages per Lambda invocation"
  type        = number
  default     = 10
}

variable "sqs_visibility_timeout" {
  description = "SQS visibility timeout in seconds"
  type        = number
  default     = 300
}

variable "sqs_max_receives" {
  description = "Maximum receives before sending to DLQ"
  type        = number
  default     = 3
}

variable "rate_limit_per_minute" {
  description = "API rate limit per minute"
  type        = number
  default     = 1000
}

variable "rate_limit_per_day" {
  description = "API rate limit per day"
  type        = number
  default     = 100000
}

variable "schedule_expression" {
  description = "EventBridge schedule expression for daily trigger"
  type        = string
  default     = "cron(0 21 * * ? *)" # Daily at 4 AM Thailand time (9 PM UTC previous day, Thailand is UTC+7)
}

variable "schedule_enabled" {
  description = "Enable or disable the EventBridge schedule"
  type        = bool
  default     = false # Disabled by default
}
