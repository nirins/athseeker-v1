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
    },
    {
      Name = "Hong Kong Exchange"
      Code = "HK"
    },
    {
      Name = "Shanghai Stock Exchange"
      Code = "SHG"
    },
    {
      Name = "Shenzhen Stock Exchange"
      Code = "SHE"
    }
    # Note: India (NSE/BSE) is not available on the current EODHD plan —
    # exchange-symbol-list returns 404 for NSE, BSE, IN, BOM, NSI. Add it
    # here once the EODHD subscription includes Indian exchanges.
  ])

  tags = merge(
    local.common_tags,
    {
      Name = local.markets_parameter_name
    }
  )
}

# Extra symbols to include per market, on top of what EODHD's exchange
# symbol list returns filtered to Common Stock. Used for instruments EODHD
# tags as a non-stock Type (e.g. ETF) that we still want tracked — such as
# BK's gold and oil tracker ETFs, which don't otherwise show up in the
# Common Stock filter task_generator.py applies.
resource "aws_ssm_parameter" "extra_symbols" {
  name        = local.extra_symbols_parameter_name
  description = "Extra symbols to queue per market, beyond the EODHD Common Stock filter"
  type        = "String"
  value = jsonencode({
    BK = ["GLD", "OIL24"] # KTAM Gold ETF Tracker, Global X Crude Oil Futures ETF
  })

  tags = merge(
    local.common_tags,
    {
      Name = local.extra_symbols_parameter_name
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
