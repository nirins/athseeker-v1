# S3 bucket for storing raw stock price data

resource "aws_s3_bucket" "stock_prices" {
  bucket = local.s3_bucket_name

  tags = merge(
    local.common_tags,
    {
      Name = local.s3_bucket_name
    }
  )
}

# Enable versioning
resource "aws_s3_bucket_versioning" "stock_prices" {
  bucket = aws_s3_bucket.stock_prices.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Enable server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "stock_prices" {
  bucket = aws_s3_bucket.stock_prices.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access
resource "aws_s3_bucket_public_access_block" "stock_prices" {
  bucket = aws_s3_bucket.stock_prices.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle policy - transition to Glacier after 90 days
resource "aws_s3_bucket_lifecycle_configuration" "stock_prices" {
  bucket = aws_s3_bucket.stock_prices.id

  rule {
    id     = "archive-old-data"
    status = "Enabled"

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    expiration {
      days = 365
    }
  }
}
