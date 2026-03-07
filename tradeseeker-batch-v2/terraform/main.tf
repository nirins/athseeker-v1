terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    # Configure backend in backend.tf or via CLI
    bucket = "ts-batch-terraform-state"
    key    = "batch-processing/terraform.tfstate"
    region = "ap-southeast-1"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = local.common_tags
  }
}

# Get current AWS account ID
data "aws_caller_identity" "current" {}

locals {
  prefix      = "ts"
  project     = "batch-v2"
  environment = terraform.workspace
  name_prefix = "${local.prefix}-${local.project}-${local.environment}"
  
  common_tags = {
    Project     = local.project
    Environment = local.environment
    ManagedBy   = "Terraform"
  }
}
