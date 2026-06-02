# Output the bucket name
output "bucket_name" {
  description = "S3 bucket name for static website"
  value       = aws_s3_bucket.website.bucket
}

# Output CloudFront distribution info
output "cloudfront_domain" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.website.domain_name
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = aws_cloudfront_distribution.website.id
}

# Output nameservers for everyath.com
output "everyath_nameservers" {
  description = "Nameservers for everyath.com - Configure these at your domain registrar"
  value       = aws_route53_zone.everyath.name_servers
}

# Output the new multi-domain certificate ARN
output "multi_domain_certificate_arn" {
  description = "ARN of the new certificate covering both domains"
  value       = aws_acm_certificate.multi_domain.arn
}

output "multi_domain_certificate_status" {
  description = "Status of the new certificate"
  value       = aws_acm_certificate.multi_domain.status
}
