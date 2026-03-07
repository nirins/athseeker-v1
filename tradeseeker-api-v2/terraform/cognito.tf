# Cognito User Pool for Angular Web App Authentication
# Uncomment these resources to enable Cognito authentication

# Cognito User Pool
# resource "aws_cognito_user_pool" "tradeseeker_users" {
#   name = "${var.project_name}-${var.environment}-users"
#
#   # Password policy
#   password_policy {
#     minimum_length    = 8
#     require_lowercase = true
#     require_uppercase = true
#     require_numbers   = true
#     require_symbols   = true
#   }
#
#   # Auto-verified attributes
#   auto_verified_attributes = ["email"]
#
#   # User attributes
#   schema {
#     name                = "email"
#     attribute_data_type = "String"
#     required            = true
#     mutable             = false
#   }
#
#   # Account recovery
#   account_recovery_setting {
#     recovery_mechanism {
#       name     = "verified_email"
#       priority = 1
#     }
#   }
#
#   # MFA configuration (optional)
#   mfa_configuration = "OPTIONAL"
#
#   tags = {
#     Name = "${var.project_name}-${var.environment}-users"
#   }
# }

# Cognito User Pool Client for Angular App
# resource "aws_cognito_user_pool_client" "angular_app" {
#   name         = "${var.project_name}-${var.environment}-angular-client"
#   user_pool_id = aws_cognito_user_pool.tradeseeker_users.id
#
#   # OAuth settings
#   allowed_oauth_flows_user_pool_client = true
#   allowed_oauth_flows                  = ["implicit", "code"]
#   allowed_oauth_scopes                 = ["email", "openid", "profile"]
#   callback_urls                        = var.cognito_callback_urls
#   logout_urls                          = var.cognito_logout_urls
#
#   # Token validity
#   id_token_validity      = 60  # 1 hour
#   access_token_validity  = 60  # 1 hour
#   refresh_token_validity = 30  # 30 days
#
#   token_validity_units {
#     id_token      = "minutes"
#     access_token  = "minutes"
#     refresh_token = "days"
#   }
#
#   # Prevent secret generation (not needed for public clients like Angular)
#   generate_secret = false
#
#   # Explicit auth flows
#   explicit_auth_flows = [
#     "ALLOW_USER_SRP_AUTH",
#     "ALLOW_REFRESH_TOKEN_AUTH"
#   ]
# }

# API Gateway Cognito Authorizer
# resource "aws_api_gateway_authorizer" "cognito" {
#   name          = "${var.project_name}-${var.environment}-cognito-authorizer"
#   rest_api_id   = aws_api_gateway_rest_api.tradeseeker_api.id
#   type          = "COGNITO_USER_POOLS"
#   provider_arns = [aws_cognito_user_pool.tradeseeker_users.arn]
# }

# To enable Cognito authentication:
# 1. Uncomment all resources above
# 2. Add cognito_callback_urls and cognito_logout_urls to variables.tf
# 3. Update API Gateway methods to use the authorizer:
#    - Set authorization = aws_api_gateway_authorizer.cognito.id
#    - Set authorization_type = "COGNITO_USER_POOLS"
# 4. Configure Angular app with the User Pool ID and Client ID from outputs

# Angular Configuration Example:
# ================================
# import { Amplify } from 'aws-amplify';
# import { Auth } from '@aws-amplify/auth';
#
# Amplify.configure({
#   Auth: {
#     region: 'ap-southeast-1',
#     userPoolId: '<USER_POOL_ID_FROM_OUTPUT>',
#     userPoolWebClientId: '<CLIENT_ID_FROM_OUTPUT>'
#   }
# });
#
# // Login
# await Auth.signIn(username, password);
#
# // Get token for API calls
# const session = await Auth.currentSession();
# const token = session.getIdToken().getJwtToken();
#
# // Make API request with token
# fetch('https://api-url/golden-crosses', {
#   headers: {
#     'Authorization': `Bearer ${token}`,
#     'Content-Type': 'application/json'
#   }
# });
