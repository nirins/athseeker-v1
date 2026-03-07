# SSM Parameter Store for configuration

# Markets configuration
resource "aws_ssm_parameter" "markets" {
  name        = local.markets_parameter_name
  description = "List of markets to fetch stock prices from"
  type        = "String"
  value = jsonencode([
    {
      Name = "USA Stocks"
      Code = "US"
    },
    {
      Name = "Thailand Exchange"
      Code = "BK"
    },
    {
      Name = "Cryptocurrencies"
      Code = "CC"
    }
  ])

  tags = merge(
    local.common_tags,
    {
      Name = local.markets_parameter_name
    }
  )
}

# API endpoints configuration
resource "aws_ssm_parameter" "api_endpoints" {
  name        = local.api_endpoints_parameter_name
  description = "EODHD API endpoint templates"
  type        = "String"
  value = jsonencode({
    symbolListUrl  = "https://eodhd.com/api/exchange-symbol-list/{MARKET_CODE}"
    stockPriceUrl = "https://eodhd.com/api/eod/{SYMBOL}.{MARKET_CODE}"
  })

  tags = merge(
    local.common_tags,
    {
      Name = local.api_endpoints_parameter_name
    }
  )
}
