# Secrets Manager for EODHD API token

resource "aws_secretsmanager_secret" "eodhd_api_token" {
  name        = local.eodhd_secret_name
  description = "EODHD API token for ${local.environment} environment"

  tags = merge(
    local.common_tags,
    {
      Name = local.eodhd_secret_name
    }
  )
}

# Secret value - should be set manually or via separate process
# Uncomment and set the actual token value
# resource "aws_secretsmanager_secret_version" "eodhd_api_token" {
#   secret_id = aws_secretsmanager_secret.eodhd_api_token.id
#   secret_string = jsonencode({
#     api_token = "your_api_token_here"
#   })
# }

# Note: For security, it's recommended to set the secret value manually:
# aws secretsmanager put-secret-value \
#   --secret-id ${local.eodhd_secret_name} \
#   --secret-string '{"api_token":"69917262e3a876.40642506"}'
