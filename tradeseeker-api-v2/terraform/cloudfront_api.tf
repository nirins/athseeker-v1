# CloudFront distribution for API Gateway caching
# This provides free caching (no base cost) to improve performance after removing API Gateway cache cluster

resource "aws_cloudfront_distribution" "api" {
  enabled             = true
  comment             = "TradeSeekerAPI v2 - CloudFront cache for better performance"
  price_class         = "PriceClass_100" # Use only North America and Europe edge locations (cheapest)

  # Origin: API Gateway
  origin {
    domain_name = replace(aws_api_gateway_deployment.tradeseeker_api.invoke_url, "/^https?://([^/]*).*/", "$1")
    origin_id   = "api-gateway"
    origin_path = "/${var.environment}"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  # Default cache behavior for all endpoints
  default_cache_behavior {
    target_origin_id       = "api-gateway"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    allowed_methods = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods  = ["GET", "HEAD", "OPTIONS"]

    # Cache based on query strings and headers
    forwarded_values {
      query_string = true
      headers      = ["Authorization", "Origin", "Access-Control-Request-Headers", "Access-Control-Request-Method"]

      cookies {
        forward = "none"
      }
    }

    # Default TTL: 5 minutes for most endpoints
    min_ttl     = 0
    default_ttl = 300   # 5 minutes
    max_ttl     = 3600  # 1 hour
  }

  # Specific behavior for /stocks/batch - aggressive caching
  ordered_cache_behavior {
    path_pattern           = "/stocks/batch*"
    target_origin_id       = "api-gateway"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    allowed_methods = ["GET", "HEAD", "OPTIONS"]
    cached_methods  = ["GET", "HEAD", "OPTIONS"]

    forwarded_values {
      query_string = true
      headers      = []

      cookies {
        forward = "none"
      }
    }

    # Cache for 5 minutes (stock data doesn't change often during market hours)
    min_ttl     = 0
    default_ttl = 300   # 5 minutes
    max_ttl     = 900   # 15 minutes
  }

  # Behavior for /ath - cache for longer since data updates daily
  ordered_cache_behavior {
    path_pattern           = "/ath*"
    target_origin_id       = "api-gateway"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    allowed_methods = ["GET", "HEAD", "OPTIONS"]
    cached_methods  = ["GET", "HEAD", "OPTIONS"]

    forwarded_values {
      query_string = true
      headers      = []

      cookies {
        forward = "none"
      }
    }

    # Cache for 1 hour (ATH data updates once per day)
    min_ttl     = 0
    default_ttl = 3600  # 1 hour
    max_ttl     = 7200  # 2 hours
  }

  # Behavior for /near-ath
  ordered_cache_behavior {
    path_pattern           = "/near-ath*"
    target_origin_id       = "api-gateway"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    allowed_methods = ["GET", "HEAD", "OPTIONS"]
    cached_methods  = ["GET", "HEAD", "OPTIONS"]

    forwarded_values {
      query_string = true
      headers      = []

      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 3600  # 1 hour
    max_ttl     = 7200  # 2 hours
  }

  # Behavior for /golden-crosses
  ordered_cache_behavior {
    path_pattern           = "/golden-crosses*"
    target_origin_id       = "api-gateway"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    allowed_methods = ["GET", "HEAD", "OPTIONS"]
    cached_methods  = ["GET", "HEAD", "OPTIONS"]

    forwarded_values {
      query_string = true
      headers      = []

      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 3600  # 1 hour
    max_ttl     = 7200  # 2 hours
  }

  # Behavior for /death-crosses
  ordered_cache_behavior {
    path_pattern           = "/death-crosses*"
    target_origin_id       = "api-gateway"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    allowed_methods = ["GET", "HEAD", "OPTIONS"]
    cached_methods  = ["GET", "HEAD", "OPTIONS"]

    forwarded_values {
      query_string = true
      headers      = []

      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 3600  # 1 hour
    max_ttl     = 7200  # 2 hours
  }

  # Don't cache POST/DELETE endpoints (watchlist, training-data)
  ordered_cache_behavior {
    path_pattern           = "/watchlist*"
    target_origin_id       = "api-gateway"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    allowed_methods = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods  = ["GET", "HEAD", "OPTIONS"]

    forwarded_values {
      query_string = true
      headers      = ["Authorization", "Content-Type"]

      cookies {
        forward = "all"
      }
    }

    # No caching for user-specific data
    min_ttl     = 0
    default_ttl = 0
    max_ttl     = 0
  }

  # No caching for training data endpoints
  ordered_cache_behavior {
    path_pattern           = "/training-data*"
    target_origin_id       = "api-gateway"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    allowed_methods = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods  = ["GET", "HEAD", "OPTIONS"]

    forwarded_values {
      query_string = true
      headers      = ["Authorization", "Content-Type"]

      cookies {
        forward = "all"
      }
    }

    min_ttl     = 0
    default_ttl = 0
    max_ttl     = 0
  }

  # Restrictions
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # SSL certificate - use default CloudFront certificate for now
  # Can be upgraded to custom domain later
  viewer_certificate {
    cloudfront_default_certificate = true
    minimum_protocol_version       = "TLSv1.2_2021"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-api-cdn"
    Environment = var.environment
  }
}

# Output the CloudFront API URL
output "api_cloudfront_url" {
  value       = "https://${aws_cloudfront_distribution.api.domain_name}"
  description = "CloudFront URL for cached API access (use this instead of direct API Gateway URL)"
}

output "api_cloudfront_id" {
  value       = aws_cloudfront_distribution.api.id
  description = "CloudFront distribution ID for the API"
}

</content>
