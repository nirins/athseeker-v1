variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "ts-web-v2"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "ap-southeast-1"
}

variable "bucket_name" {
  description = "S3 bucket name for static website hosting"
  type        = string
}

variable "domain_name" {
  description = "Custom domain name for CloudFront (e.g. athseeker.com)"
  type        = string
  default     = ""
}

variable "new_domain_name" {
  description = "New domain name for CloudFront (e.g. everyath.com)"
  type        = string
  default     = "everyath.com"
}

variable "cloudfront_price_class" {
  description = "CloudFront price class"
  type        = string
  default     = "PriceClass_100" # US, Canada, Europe
}