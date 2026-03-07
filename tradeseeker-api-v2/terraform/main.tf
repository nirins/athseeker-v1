terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket = "ts-api-v2-terraform-state"
    key    = "terraform.tfstate"
    region = "ap-southeast-1"
    
    # Enable state locking with DynamoDB (optional but recommended)
    # dynamodb_table = "ts-api-v2-terraform-locks"
    
    # Enable encryption at rest
    encrypt = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "TradeSeekerAPI"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}
