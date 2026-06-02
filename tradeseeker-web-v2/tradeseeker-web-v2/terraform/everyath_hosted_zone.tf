# Create Route53 hosted zone for everyath.com
resource "aws_route53_zone" "everyath" {
  name = var.new_domain_name

  tags = {
    Name = "everyath-hosted-zone"
  }
}
