# REST API Gateway
resource "aws_api_gateway_rest_api" "tradeseeker_api" {
  name        = "${var.project_name}-${var.environment}"
  description = "TradeSeekerAPI v2 - Stock market data API"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}"
  }
}

# /golden-crosses resource
resource "aws_api_gateway_resource" "golden_crosses" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  parent_id   = aws_api_gateway_rest_api.tradeseeker_api.root_resource_id
  path_part   = "golden-crosses"
}

# GET method for /golden-crosses
resource "aws_api_gateway_method" "golden_crosses_get" {
  rest_api_id   = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id   = aws_api_gateway_resource.golden_crosses.id
  http_method   = "GET"
  authorization = "NONE"
}

# Lambda integration for /golden-crosses GET
resource "aws_api_gateway_integration" "golden_crosses_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id             = aws_api_gateway_resource.golden_crosses.id
  http_method             = aws_api_gateway_method.golden_crosses_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.tradeseeker_api.invoke_arn
}

# Method response for /golden-crosses GET
resource "aws_api_gateway_method_response" "golden_crosses_get" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.golden_crosses.id
  http_method = aws_api_gateway_method.golden_crosses_get.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

# /death-crosses resource
resource "aws_api_gateway_resource" "death_crosses" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  parent_id   = aws_api_gateway_rest_api.tradeseeker_api.root_resource_id
  path_part   = "death-crosses"
}

# GET method for /death-crosses
resource "aws_api_gateway_method" "death_crosses_get" {
  rest_api_id   = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id   = aws_api_gateway_resource.death_crosses.id
  http_method   = "GET"
  authorization = "NONE"
}

# Lambda integration for /death-crosses GET
resource "aws_api_gateway_integration" "death_crosses_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id             = aws_api_gateway_resource.death_crosses.id
  http_method             = aws_api_gateway_method.death_crosses_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.tradeseeker_api.invoke_arn
}

# Method response for /death-crosses GET
resource "aws_api_gateway_method_response" "death_crosses_get" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.death_crosses.id
  http_method = aws_api_gateway_method.death_crosses_get.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

# /ath resource (alias for ath-stocks)
resource "aws_api_gateway_resource" "ath" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  parent_id   = aws_api_gateway_rest_api.tradeseeker_api.root_resource_id
  path_part   = "ath"
}

# /near-ath resource
resource "aws_api_gateway_resource" "near_ath" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  parent_id   = aws_api_gateway_rest_api.tradeseeker_api.root_resource_id
  path_part   = "near-ath"
}

# GET method for /near-ath
resource "aws_api_gateway_method" "near_ath_get" {
  rest_api_id   = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id   = aws_api_gateway_resource.near_ath.id
  http_method   = "GET"
  authorization = "NONE"
}

# Lambda integration for /near-ath GET
resource "aws_api_gateway_integration" "near_ath_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id             = aws_api_gateway_resource.near_ath.id
  http_method             = aws_api_gateway_method.near_ath_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.tradeseeker_api.invoke_arn
}

# Method response for /near-ath GET
resource "aws_api_gateway_method_response" "near_ath_get" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.near_ath.id
  http_method = aws_api_gateway_method.near_ath_get.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

# CORS configuration for /near-ath
resource "aws_api_gateway_method" "near_ath_options" {
  rest_api_id   = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id   = aws_api_gateway_resource.near_ath.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "near_ath_options" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.near_ath.id
  http_method = aws_api_gateway_method.near_ath_options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "near_ath_options" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.near_ath.id
  http_method = aws_api_gateway_method.near_ath_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "near_ath_options" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.near_ath.id
  http_method = aws_api_gateway_method.near_ath_options.http_method
  status_code = aws_api_gateway_method_response.near_ath_options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# /openai-summary resource
resource "aws_api_gateway_resource" "openai_summary" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  parent_id   = aws_api_gateway_rest_api.tradeseeker_api.root_resource_id
  path_part   = "openai-summary"
}

# GET method for /ath
resource "aws_api_gateway_method" "ath_get" {
  rest_api_id   = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id   = aws_api_gateway_resource.ath.id
  http_method   = "GET"
  authorization = "NONE"
}

# Lambda integration for /ath GET
resource "aws_api_gateway_integration" "ath_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id             = aws_api_gateway_resource.ath.id
  http_method             = aws_api_gateway_method.ath_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.tradeseeker_api.invoke_arn
}

# Method response for /ath GET
resource "aws_api_gateway_method_response" "ath_get" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.ath.id
  http_method = aws_api_gateway_method.ath_get.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

# GET method for /openai-summary
resource "aws_api_gateway_method" "openai_summary_get" {
  rest_api_id   = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id   = aws_api_gateway_resource.openai_summary.id
  http_method   = "GET"
  authorization = "NONE"
}

# Lambda integration for /openai-summary GET
resource "aws_api_gateway_integration" "openai_summary_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id             = aws_api_gateway_resource.openai_summary.id
  http_method             = aws_api_gateway_method.openai_summary_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.tradeseeker_api.invoke_arn
}

# Method response for /openai-summary GET
resource "aws_api_gateway_method_response" "openai_summary_get" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.openai_summary.id
  http_method = aws_api_gateway_method.openai_summary_get.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

# CORS configuration for /death-crosses
resource "aws_api_gateway_method" "death_crosses_options" {
  rest_api_id   = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id   = aws_api_gateway_resource.death_crosses.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "death_crosses_options" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.death_crosses.id
  http_method = aws_api_gateway_method.death_crosses_options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "death_crosses_options" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.death_crosses.id
  http_method = aws_api_gateway_method.death_crosses_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "death_crosses_options" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.death_crosses.id
  http_method = aws_api_gateway_method.death_crosses_options.http_method
  status_code = aws_api_gateway_method_response.death_crosses_options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# CORS configuration for /ath
resource "aws_api_gateway_method" "ath_options" {
  rest_api_id   = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id   = aws_api_gateway_resource.ath.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "ath_options" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.ath.id
  http_method = aws_api_gateway_method.ath_options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "ath_options" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.ath.id
  http_method = aws_api_gateway_method.ath_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "ath_options" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.ath.id
  http_method = aws_api_gateway_method.ath_options.http_method
  status_code = aws_api_gateway_method_response.ath_options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# CORS configuration for /openai-summary
resource "aws_api_gateway_method" "openai_summary_options" {
  rest_api_id   = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id   = aws_api_gateway_resource.openai_summary.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "openai_summary_options" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.openai_summary.id
  http_method = aws_api_gateway_method.openai_summary_options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "openai_summary_options" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.openai_summary.id
  http_method = aws_api_gateway_method.openai_summary_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "openai_summary_options" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.openai_summary.id
  http_method = aws_api_gateway_method.openai_summary_options.http_method
  status_code = aws_api_gateway_method_response.openai_summary_options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# /stocks resource
resource "aws_api_gateway_resource" "stocks" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  parent_id   = aws_api_gateway_rest_api.tradeseeker_api.root_resource_id
  path_part   = "stocks"
}

# /stocks/batch resource
resource "aws_api_gateway_resource" "stock_batch" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  parent_id   = aws_api_gateway_resource.stocks.id
  path_part   = "batch"
}

# GET method for /stocks/batch
resource "aws_api_gateway_method" "stock_batch_get" {
  rest_api_id   = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id   = aws_api_gateway_resource.stock_batch.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "stock_batch_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id             = aws_api_gateway_resource.stock_batch.id
  http_method             = aws_api_gateway_method.stock_batch_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.tradeseeker_api.invoke_arn
}

resource "aws_api_gateway_method_response" "stock_batch_get" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.stock_batch.id
  http_method = aws_api_gateway_method.stock_batch_get.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

# CORS for /stocks/batch
resource "aws_api_gateway_method" "stock_batch_options" {
  rest_api_id   = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id   = aws_api_gateway_resource.stock_batch.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "stock_batch_options" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.stock_batch.id
  http_method = aws_api_gateway_method.stock_batch_options.http_method
  type        = "MOCK"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "stock_batch_options" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.stock_batch.id
  http_method = aws_api_gateway_method.stock_batch_options.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "stock_batch_options" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.stock_batch.id
  http_method = aws_api_gateway_method.stock_batch_options.http_method
  status_code = aws_api_gateway_method_response.stock_batch_options.status_code
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# /stocks/{symbol} resource
resource "aws_api_gateway_resource" "stock_symbol" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  parent_id   = aws_api_gateway_resource.stocks.id
  path_part   = "{symbol}"
}

# GET method for /stocks/{symbol}
resource "aws_api_gateway_method" "stock_symbol_get" {
  rest_api_id   = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id   = aws_api_gateway_resource.stock_symbol.id
  http_method   = "GET"
  authorization = "NONE"

  request_parameters = {
    "method.request.path.symbol" = true
  }
}

# Lambda integration for /stocks/{symbol} GET
resource "aws_api_gateway_integration" "stock_symbol_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id             = aws_api_gateway_resource.stock_symbol.id
  http_method             = aws_api_gateway_method.stock_symbol_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.tradeseeker_api.invoke_arn
}

# Method response for /stocks/{symbol} GET
resource "aws_api_gateway_method_response" "stock_symbol_get" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.stock_symbol.id
  http_method = aws_api_gateway_method.stock_symbol_get.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

# CORS configuration for /golden-crosses
resource "aws_api_gateway_method" "golden_crosses_options" {
  rest_api_id   = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id   = aws_api_gateway_resource.golden_crosses.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "golden_crosses_options" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.golden_crosses.id
  http_method = aws_api_gateway_method.golden_crosses_options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "golden_crosses_options" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.golden_crosses.id
  http_method = aws_api_gateway_method.golden_crosses_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "golden_crosses_options" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.golden_crosses.id
  http_method = aws_api_gateway_method.golden_crosses_options.http_method
  status_code = aws_api_gateway_method_response.golden_crosses_options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# CORS configuration for /stocks/{symbol}
resource "aws_api_gateway_method" "stock_symbol_options" {
  rest_api_id   = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id   = aws_api_gateway_resource.stock_symbol.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "stock_symbol_options" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.stock_symbol.id
  http_method = aws_api_gateway_method.stock_symbol_options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "stock_symbol_options" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.stock_symbol.id
  http_method = aws_api_gateway_method.stock_symbol_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "stock_symbol_options" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.stock_symbol.id
  http_method = aws_api_gateway_method.stock_symbol_options.http_method
  status_code = aws_api_gateway_method_response.stock_symbol_options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}


# /stocks/{symbol}/history resource
resource "aws_api_gateway_resource" "stock_history" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  parent_id   = aws_api_gateway_resource.stock_symbol.id
  path_part   = "history"
}

# GET method for /stocks/{symbol}/history
resource "aws_api_gateway_method" "stock_history_get" {
  rest_api_id   = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id   = aws_api_gateway_resource.stock_history.id
  http_method   = "GET"
  authorization = "NONE"
}

# Lambda integration for /stocks/{symbol}/history GET
resource "aws_api_gateway_integration" "stock_history_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id             = aws_api_gateway_resource.stock_history.id
  http_method             = aws_api_gateway_method.stock_history_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.tradeseeker_api.invoke_arn
}

# Method response for /stocks/{symbol}/history GET
resource "aws_api_gateway_method_response" "stock_history_get" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.stock_history.id
  http_method = aws_api_gateway_method.stock_history_get.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

# CORS configuration for /stocks/{symbol}/history
resource "aws_api_gateway_method" "stock_history_options" {
  rest_api_id   = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id   = aws_api_gateway_resource.stock_history.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "stock_history_options" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.stock_history.id
  http_method = aws_api_gateway_method.stock_history_options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "stock_history_options" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.stock_history.id
  http_method = aws_api_gateway_method.stock_history_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "stock_history_options" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.stock_history.id
  http_method = aws_api_gateway_method.stock_history_options.http_method
  status_code = aws_api_gateway_method_response.stock_history_options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# API Gateway deployment
resource "aws_api_gateway_deployment" "tradeseeker_api" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id

  depends_on = [
    aws_api_gateway_integration.golden_crosses_lambda,
    aws_api_gateway_integration.death_crosses_lambda,
    aws_api_gateway_integration.ath_lambda,
    aws_api_gateway_integration.near_ath_lambda,
    aws_api_gateway_integration.openai_summary_lambda,
    aws_api_gateway_integration.stock_symbol_lambda,
    aws_api_gateway_integration.stock_batch_lambda,
    aws_api_gateway_integration.stock_history_lambda,
    aws_api_gateway_integration.training_data_save_by_grade_lambda,
    aws_api_gateway_integration.watchlist_get_lambda,
    aws_api_gateway_integration.watchlist_post_lambda,
    aws_api_gateway_integration.watchlist_delete_lambda,
    aws_api_gateway_integration.stock_refresh_lambda,
    aws_api_gateway_integration.golden_crosses_options,
    aws_api_gateway_integration.death_crosses_options,
    aws_api_gateway_integration.ath_options,
    aws_api_gateway_integration.near_ath_options,
    aws_api_gateway_integration.openai_summary_options,
    aws_api_gateway_integration.stock_symbol_options,
    aws_api_gateway_integration.stock_batch_options,
    aws_api_gateway_integration.stock_history_options,
    aws_api_gateway_integration.training_data_save_by_grade_options,
    aws_api_gateway_integration.watchlist_options,
    aws_api_gateway_method_response.golden_crosses_get,
    aws_api_gateway_method_response.death_crosses_get,
    aws_api_gateway_method_response.ath_get,
    aws_api_gateway_method_response.near_ath_get,
    aws_api_gateway_method_response.openai_summary_get,
    aws_api_gateway_method_response.stock_symbol_get,
    aws_api_gateway_method_response.stock_batch_get,
    aws_api_gateway_method_response.stock_history_get,
    aws_api_gateway_method_response.training_data_save_by_grade_post,
    aws_api_gateway_method_response.watchlist_get,
    aws_api_gateway_method_response.watchlist_post,
    aws_api_gateway_method_response.watchlist_delete,
  ]

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.golden_crosses.id,
      aws_api_gateway_resource.death_crosses.id,
      aws_api_gateway_resource.ath.id,
      aws_api_gateway_resource.near_ath.id,
      aws_api_gateway_resource.openai_summary.id,
      aws_api_gateway_resource.stocks.id,
      aws_api_gateway_resource.stock_symbol.id,
      aws_api_gateway_resource.stock_batch.id,
      aws_api_gateway_resource.stock_history.id,
      aws_api_gateway_resource.training_data.id,
      aws_api_gateway_resource.training_data_save_by_grade.id,
      aws_api_gateway_resource.watchlist.id,
      aws_api_gateway_resource.stock_refresh.id,
      aws_api_gateway_method.golden_crosses_get.id,
      aws_api_gateway_method.death_crosses_get.id,
      aws_api_gateway_method.ath_get.id,
      aws_api_gateway_method.near_ath_get.id,
      aws_api_gateway_method.openai_summary_get.id,
      aws_api_gateway_method.stock_symbol_get.id,
      aws_api_gateway_method.stock_batch_get.id,
      aws_api_gateway_method.stock_history_get.id,
      aws_api_gateway_method.training_data_save_by_grade_post.id,
      aws_api_gateway_method.watchlist_get.id,
      aws_api_gateway_method.watchlist_post.id,
      aws_api_gateway_method.watchlist_delete.id,
      aws_api_gateway_method.watchlist_options.id,
      aws_api_gateway_method.stock_refresh_post.id,
      aws_api_gateway_method.stock_refresh_options.id,
      aws_api_gateway_method.golden_crosses_options.id,
      aws_api_gateway_method.death_crosses_options.id,
      aws_api_gateway_method.ath_options.id,
      aws_api_gateway_method.near_ath_options.id,
      aws_api_gateway_method.openai_summary_options.id,
      aws_api_gateway_method.stock_symbol_options.id,
      aws_api_gateway_method.stock_batch_options.id,
      aws_api_gateway_method.stock_history_options.id,
      aws_api_gateway_method.training_data_save_by_grade_options.id,
      aws_api_gateway_integration.golden_crosses_lambda.id,
      aws_api_gateway_integration.death_crosses_lambda.id,
      aws_api_gateway_integration.ath_lambda.id,
      aws_api_gateway_integration.near_ath_lambda.id,
      aws_api_gateway_integration.openai_summary_lambda.id,
      aws_api_gateway_integration.stock_symbol_lambda.id,
      aws_api_gateway_integration.stock_batch_lambda.id,
      aws_api_gateway_integration.stock_history_lambda.id,
      aws_api_gateway_integration.training_data_save_by_grade_lambda.id,
      aws_api_gateway_integration.watchlist_get_lambda.id,
      aws_api_gateway_integration.watchlist_post_lambda.id,
      aws_api_gateway_integration.watchlist_delete_lambda.id,
      aws_api_gateway_integration.stock_refresh_lambda.id,
      aws_api_gateway_integration.stock_refresh_options.id,
      aws_api_gateway_integration.golden_crosses_options.id,
      aws_api_gateway_integration.death_crosses_options.id,
      aws_api_gateway_integration.ath_options.id,
      aws_api_gateway_integration.near_ath_options.id,
      aws_api_gateway_integration.openai_summary_options.id,
      aws_api_gateway_integration.stock_symbol_options.id,
      aws_api_gateway_integration.stock_batch_options.id,
      aws_api_gateway_integration.stock_history_options.id,
      aws_api_gateway_integration.training_data_save_by_grade_options.id,
      aws_api_gateway_integration.watchlist_options.id,
      aws_api_gateway_method_response.golden_crosses_get.id,
      aws_api_gateway_method_response.death_crosses_get.id,
      aws_api_gateway_method_response.ath_get.id,
      aws_api_gateway_method_response.near_ath_get.id,
      aws_api_gateway_method_response.openai_summary_get.id,
      aws_api_gateway_method_response.stock_symbol_get.id,
      aws_api_gateway_method_response.stock_batch_get.id,
      aws_api_gateway_method_response.stock_history_get.id,
      aws_api_gateway_method_response.training_data_save_by_grade_post.id,
      aws_api_gateway_method_response.watchlist_get.id,
      aws_api_gateway_method_response.watchlist_post.id,
      aws_api_gateway_method_response.watchlist_delete.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

# API Gateway stage
resource "aws_api_gateway_stage" "tradeseeker_api" {
  deployment_id = aws_api_gateway_deployment.tradeseeker_api.id
  rest_api_id   = aws_api_gateway_rest_api.tradeseeker_api.id
  stage_name    = var.environment

  # DISABLED: Cache cluster provides no benefit at current scale (0% hit rate)
  # Savings: $14.40/month
  cache_cluster_enabled = false
  # cache_cluster_size    = "0.5"  # Not needed when cache is disabled

  tags = {
    Name = "${var.project_name}-${var.environment}"
  }
}

# Cache settings disabled - no longer needed without cache cluster
# Commented out to save $14.40/month
# resource "aws_api_gateway_method_settings" "stock_batch_cache" {
#   rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
#   stage_name  = aws_api_gateway_stage.tradeseeker_api.stage_name
#   method_path = "${aws_api_gateway_resource.stock_batch.path_part}/GET"
#
#   settings {
#     caching_enabled      = true
#     cache_ttl_in_seconds = 300 # 5 minutes
#     cache_data_encrypted = false
#     require_authorization_for_cache_control = false
#   }
# }

# Lambda permission for API Gateway to invoke Lambda
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.tradeseeker_api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.tradeseeker_api.execution_arn}/*/*"
}

# POST /stocks/{symbol}/refresh resource
resource "aws_api_gateway_resource" "stock_refresh" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  parent_id   = aws_api_gateway_resource.stock_symbol.id
  path_part   = "refresh"
}

# POST method for /stocks/{symbol}/refresh
resource "aws_api_gateway_method" "stock_refresh_post" {
  rest_api_id   = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id   = aws_api_gateway_resource.stock_refresh.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "stock_refresh_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id             = aws_api_gateway_resource.stock_refresh.id
  http_method             = aws_api_gateway_method.stock_refresh_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.tradeseeker_api.invoke_arn
}

resource "aws_api_gateway_method_response" "stock_refresh_post" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.stock_refresh.id
  http_method = aws_api_gateway_method.stock_refresh_post.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

# CORS for /stocks/{symbol}/refresh
resource "aws_api_gateway_method" "stock_refresh_options" {
  rest_api_id   = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id   = aws_api_gateway_resource.stock_refresh.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "stock_refresh_options" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.stock_refresh.id
  http_method = aws_api_gateway_method.stock_refresh_options.http_method
  type        = "MOCK"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "stock_refresh_options" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.stock_refresh.id
  http_method = aws_api_gateway_method.stock_refresh_options.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "stock_refresh_options" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.stock_refresh.id
  http_method = aws_api_gateway_method.stock_refresh_options.http_method
  status_code = aws_api_gateway_method_response.stock_refresh_options.status_code
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'POST,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}
# /training-data resource
resource "aws_api_gateway_resource" "training_data" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  parent_id   = aws_api_gateway_rest_api.tradeseeker_api.root_resource_id
  path_part   = "training-data"
}

# /training-data/save-by-grade resource
resource "aws_api_gateway_resource" "training_data_save_by_grade" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  parent_id   = aws_api_gateway_resource.training_data.id
  path_part   = "save-by-grade"
}

# POST method for /training-data/save-by-grade
resource "aws_api_gateway_method" "training_data_save_by_grade_post" {
  rest_api_id   = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id   = aws_api_gateway_resource.training_data_save_by_grade.id
  http_method   = "POST"
  authorization = "NONE"
}

# Lambda integration for /training-data/save-by-grade POST
resource "aws_api_gateway_integration" "training_data_save_by_grade_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id             = aws_api_gateway_resource.training_data_save_by_grade.id
  http_method             = aws_api_gateway_method.training_data_save_by_grade_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.tradeseeker_api.invoke_arn
}

# Method response for /training-data/save-by-grade POST
resource "aws_api_gateway_method_response" "training_data_save_by_grade_post" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.training_data_save_by_grade.id
  http_method = aws_api_gateway_method.training_data_save_by_grade_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

# CORS configuration for /training-data/save-by-grade
resource "aws_api_gateway_method" "training_data_save_by_grade_options" {
  rest_api_id   = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id   = aws_api_gateway_resource.training_data_save_by_grade.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "training_data_save_by_grade_options" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.training_data_save_by_grade.id
  http_method = aws_api_gateway_method.training_data_save_by_grade_options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "training_data_save_by_grade_options" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.training_data_save_by_grade.id
  http_method = aws_api_gateway_method.training_data_save_by_grade_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "training_data_save_by_grade_options" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.training_data_save_by_grade.id
  http_method = aws_api_gateway_method.training_data_save_by_grade_options.http_method
  status_code = aws_api_gateway_method_response.training_data_save_by_grade_options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'POST,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# /watchlist resource
resource "aws_api_gateway_resource" "watchlist" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  parent_id   = aws_api_gateway_rest_api.tradeseeker_api.root_resource_id
  path_part   = "watchlist"
}

# GET /watchlist
resource "aws_api_gateway_method" "watchlist_get" {
  rest_api_id   = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id   = aws_api_gateway_resource.watchlist.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "watchlist_get_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id             = aws_api_gateway_resource.watchlist.id
  http_method             = aws_api_gateway_method.watchlist_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.tradeseeker_api.invoke_arn
}

resource "aws_api_gateway_method_response" "watchlist_get" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.watchlist.id
  http_method = aws_api_gateway_method.watchlist_get.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

# POST /watchlist
resource "aws_api_gateway_method" "watchlist_post" {
  rest_api_id   = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id   = aws_api_gateway_resource.watchlist.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "watchlist_post_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id             = aws_api_gateway_resource.watchlist.id
  http_method             = aws_api_gateway_method.watchlist_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.tradeseeker_api.invoke_arn
}

resource "aws_api_gateway_method_response" "watchlist_post" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.watchlist.id
  http_method = aws_api_gateway_method.watchlist_post.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

# DELETE /watchlist
resource "aws_api_gateway_method" "watchlist_delete" {
  rest_api_id   = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id   = aws_api_gateway_resource.watchlist.id
  http_method   = "DELETE"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "watchlist_delete_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id             = aws_api_gateway_resource.watchlist.id
  http_method             = aws_api_gateway_method.watchlist_delete.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.tradeseeker_api.invoke_arn
}

resource "aws_api_gateway_method_response" "watchlist_delete" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.watchlist.id
  http_method = aws_api_gateway_method.watchlist_delete.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

# OPTIONS /watchlist (CORS)
resource "aws_api_gateway_method" "watchlist_options" {
  rest_api_id   = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id   = aws_api_gateway_resource.watchlist.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "watchlist_options" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.watchlist.id
  http_method = aws_api_gateway_method.watchlist_options.http_method
  type        = "MOCK"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "watchlist_options" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.watchlist.id
  http_method = aws_api_gateway_method.watchlist_options.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "watchlist_options" {
  rest_api_id = aws_api_gateway_rest_api.tradeseeker_api.id
  resource_id = aws_api_gateway_resource.watchlist.id
  http_method = aws_api_gateway_method.watchlist_options.http_method
  status_code = aws_api_gateway_method_response.watchlist_options.status_code
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,DELETE,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}
