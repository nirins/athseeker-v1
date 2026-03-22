# DynamoDB table for storing OHLCV data and EMAs

resource "aws_dynamodb_table" "stock_prices" {
  name         = local.dynamodb_table_name
  billing_mode = local.current_config.dynamodb_billing_mode
  hash_key     = "symbol"

  attribute {
    name = "symbol"
    type = "S"
  }

  # Enable point-in-time recovery
  point_in_time_recovery {
    enabled = true
  }

  # Enable encryption at rest
  server_side_encryption {
    enabled = true
  }

  tags = merge(
    local.common_tags,
    {
      Name = local.dynamodb_table_name
    }
  )
}

# DynamoDB table for storing OHLCV data and EMAs (lite — 360 days, for dashboard batch API)
resource "aws_dynamodb_table" "stock_prices_lite" {
  name         = local.dynamodb_lite_table_name
  billing_mode = local.current_config.dynamodb_billing_mode
  hash_key     = "symbol"

  attribute {
    name = "symbol"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = merge(
    local.common_tags,
    {
      Name = local.dynamodb_lite_table_name
    }
  )
}

# DynamoDB table for golden cross signals (past 7 days)
resource "aws_dynamodb_table" "golden_crosses" {
  name         = "${local.name_prefix}-golden-crosses"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "symbol"
  range_key    = "cross_date"

  attribute {
    name = "symbol"
    type = "S"
  }

  attribute {
    name = "cross_date"
    type = "S"
  }

  attribute {
    name = "market_code"
    type = "S"
  }

  # GSI for querying by date (all symbols with golden cross on specific date)
  global_secondary_index {
    name            = "cross_date-index"
    hash_key        = "cross_date"
    projection_type = "ALL"
  }

  # GSI for querying by market (all golden crosses in specific market)
  global_secondary_index {
    name            = "market_code-cross_date-index"
    hash_key        = "market_code"
    range_key       = "cross_date"
    projection_type = "ALL"
  }

  # TTL to automatically delete old records after 30 days
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  # Enable point-in-time recovery
  point_in_time_recovery {
    enabled = true
  }

  # Enable encryption at rest
  server_side_encryption {
    enabled = true
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-golden-crosses"
    }
  )
}

# DynamoDB table for death cross signals (past 7 days)
resource "aws_dynamodb_table" "death_crosses" {
  name         = "${local.name_prefix}-death-crosses"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "symbol"
  range_key    = "cross_date"

  attribute {
    name = "symbol"
    type = "S"
  }

  attribute {
    name = "cross_date"
    type = "S"
  }

  attribute {
    name = "market_code"
    type = "S"
  }

  # GSI for querying by date (all symbols with death cross on specific date)
  global_secondary_index {
    name            = "cross_date-index"
    hash_key        = "cross_date"
    projection_type = "ALL"
  }

  # GSI for querying by market (all death crosses in specific market)
  global_secondary_index {
    name            = "market_code-cross_date-index"
    hash_key        = "market_code"
    range_key       = "cross_date"
    projection_type = "ALL"
  }

  # TTL to automatically delete old records after 30 days
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  # Enable point-in-time recovery
  point_in_time_recovery {
    enabled = true
  }

  # Enable encryption at rest
  server_side_encryption {
    enabled = true
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-death-crosses"
    }
  )
}

# DynamoDB table for ATH detection records (past 30 days) - RECREATED
resource "aws_dynamodb_table" "ath_detections" {
  name         = "${local.name_prefix}-ath"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "symbol"

  attribute {
    name = "symbol"
    type = "S"
  }

  attribute {
    name = "market_code"
    type = "S"
  }

  attribute {
    name = "beauty_score"
    type = "N"
  }

  # GSI for querying by market (all ATH detections in specific market)
  global_secondary_index {
    name            = "market_code-index"
    hash_key        = "market_code"
    projection_type = "ALL"
  }

  # GSI for querying by beauty score (ordered by beauty score descending)
  global_secondary_index {
    name            = "beauty_score-index"
    hash_key        = "market_code"
    range_key       = "beauty_score"
    projection_type = "ALL"
  }

  # TTL to automatically delete old records after 30 days
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  # Enable point-in-time recovery
  point_in_time_recovery {
    enabled = true
  }

  # Enable encryption at rest
  server_side_encryption {
    enabled = true
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-ath"
    }
  )
}

# DynamoDB table for Near ATH detection records (past 30 days)
resource "aws_dynamodb_table" "near_ath_detections" {
  name         = "${local.name_prefix}-near-ath"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "symbol"

  attribute {
    name = "symbol"
    type = "S"
  }

  attribute {
    name = "market_code"
    type = "S"
  }

  attribute {
    name = "beauty_score"
    type = "N"
  }

  global_secondary_index {
    name            = "market_code-index"
    hash_key        = "market_code"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "beauty_score-index"
    hash_key        = "market_code"
    range_key       = "beauty_score"
    projection_type = "ALL"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-near-ath"
    }
  )
}
