output "s3_bucket_name" {
  description = "Name of the S3 bucket for stock prices"
  value       = aws_s3_bucket.stock_prices.id
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  value       = aws_dynamodb_table.stock_prices.name
}

output "sqs_queue_url" {
  description = "URL of the main SQS queue"
  value       = aws_sqs_queue.main.url
}

output "sqs_dlq_url" {
  description = "URL of the DLQ"
  value       = aws_sqs_queue.dlq.url
}

output "task_generator_lambda_arn" {
  description = "ARN of the Task Generator Lambda"
  value       = aws_lambda_function.task_generator.arn
}

output "downloader_lambda_arn" {
  description = "ARN of the Downloader Lambda"
  value       = aws_lambda_function.downloader.arn
}

output "environment" {
  description = "Current environment"
  value       = local.environment
}
