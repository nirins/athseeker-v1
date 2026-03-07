# S3 bucket for ML training data
resource "aws_s3_bucket" "training_data" {
  bucket = "tradeseeker-training-data"

  tags = {
    Name        = "TradeSeekerV2 Training Data"
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "ML Training Dataset Storage"
  }
}

# S3 bucket versioning
resource "aws_s3_bucket_versioning" "training_data_versioning" {
  bucket = aws_s3_bucket.training_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 bucket server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "training_data_encryption" {
  bucket = aws_s3_bucket.training_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 bucket public access block (keep private)
resource "aws_s3_bucket_public_access_block" "training_data_pab" {
  bucket = aws_s3_bucket.training_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 bucket lifecycle configuration for cost optimization
resource "aws_s3_bucket_lifecycle_configuration" "training_data_lifecycle" {
  bucket = aws_s3_bucket.training_data.id

  rule {
    id     = "training_data_lifecycle"
    status = "Enabled"

    filter {
      prefix = "training-data/"
    }

    # Move to IA after 30 days
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    # Move to Glacier after 90 days
    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    # Delete old versions after 365 days
    noncurrent_version_expiration {
      noncurrent_days = 365
    }
  }
}