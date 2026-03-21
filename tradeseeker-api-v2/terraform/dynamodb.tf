# DynamoDB table for user watchlists
resource "aws_dynamodb_table" "watchlist" {
  name         = "${var.project_name}-${var.environment}-watchlist"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"
  range_key    = "symbol"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "symbol"
    type = "S"
  }

  server_side_encryption {
    enabled = true
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-watchlist"
  }
}
