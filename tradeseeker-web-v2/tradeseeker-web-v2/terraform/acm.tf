# ACM certificate must be in us-east-1 for CloudFront
# Original certificate for athseeker.com only
resource "aws_acm_certificate" "website" {
  provider          = aws.us_east_1
  domain_name       = var.domain_name
  subject_alternative_names = ["www.${var.domain_name}"]
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_acm_certificate_validation" "website" {
  provider                = aws.us_east_1
  certificate_arn         = aws_acm_certificate.website.arn
  validation_record_fqdns = [
    for record in aws_route53_record.acm_validation : record.fqdn
  ]
}

# NEW certificate covering BOTH domains
resource "aws_acm_certificate" "multi_domain" {
  provider          = aws.us_east_1
  domain_name       = var.domain_name
  subject_alternative_names = [
    "www.${var.domain_name}",
    var.new_domain_name,
    "www.${var.new_domain_name}"
  ]
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "multi-domain-certificate"
  }
}

# Validation records for the new certificate
resource "aws_route53_record" "multi_domain_acm_validation" {
  for_each = {
    for dvo in aws_acm_certificate.multi_domain.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      type   = dvo.resource_record_type
      record = dvo.resource_record_value
      zone_id = length(regexall(".*everyath\\.com", dvo.domain_name)) > 0 ? aws_route53_zone.everyath.zone_id : data.aws_route53_zone.website.zone_id
    }
  }

  allow_overwrite = true
  zone_id = each.value.zone_id
  name    = each.value.name
  type    = each.value.type
  records = [each.value.record]
  ttl     = 60
}

# Validation for new certificate
resource "aws_acm_certificate_validation" "multi_domain" {
  provider                = aws.us_east_1
  certificate_arn         = aws_acm_certificate.multi_domain.arn
  validation_record_fqdns = [
    for record in aws_route53_record.multi_domain_acm_validation : record.fqdn
  ]
}
