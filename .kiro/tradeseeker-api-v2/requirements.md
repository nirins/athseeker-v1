# Requirements Document

## Introduction

The TradeSeekerAPI v2 is a REST API service that provides query access to stock market data stored in DynamoDB tables. The API enables users to discover golden cross signals and retrieve detailed stock price information with technical indicators. This service will be implemented in a separate GitHub repository (tradeseeker-api-v2) and deployed as an independent AWS Lambda-based service.

## Glossary

- **API**: The TradeSeekerAPI v2 REST API service
- **Golden_Cross**: A technical analysis pattern where the 50-day EMA crosses above the 200-day EMA
- **Symbol**: A stock ticker symbol with market code suffix (e.g., AAPL.US, PTT.BK)
- **Market_Code**: The market identifier (US, BK, CC)
- **EMA**: Exponential Moving Average
- **Green_Days_Percentage**: Percentage of days with positive price movement over a 30-day period
- **Max_Red_Candle**: The largest single-day percentage decline over a 30-day period
- **DynamoDB_Client**: AWS SDK client for accessing DynamoDB tables
- **Lambda_Handler**: AWS Lambda function entry point
- **API_Gateway**: AWS service that routes HTTP requests to Lambda functions

## Requirements

### Requirement 1: Golden Cross Query Endpoint

**User Story:** As a trader, I want to query golden cross signals with filters, so that I can identify stocks meeting my technical criteria.

#### Acceptance Criteria

1. WHEN a GET request is made to /golden-crosses, THE API SHALL query the ts-batch-v2-dev-golden-crosses DynamoDB table
2. WHEN no query parameters are provided, THE API SHALL apply default filters of min_green_days >= 70% and max_red_candle >= -5%
3. WHEN the min_green query parameter is provided, THE API SHALL filter results where green_days_30d_pct >= min_green
4. WHEN the max_red_candle query parameter is provided, THE API SHALL filter results where max_red_candle_30d_pct >= max_red_candle
5. WHEN the market query parameter is provided, THE API SHALL filter results to the specified market code (US, BK, or CC)
6. WHEN the date query parameter is provided in YYYY-MM-DD format, THE API SHALL filter results to crosses detected on that specific date
7. WHEN the days query parameter is provided, THE API SHALL filter results to crosses detected within the last N days
8. THE API SHALL return a JSON response containing an array of golden cross records with symbol, cross_date, market_code, signal, ema_50, ema_200, crossover_strength, green_days_30d_pct, max_red_candle_30d_pct, and detected_at fields

### Requirement 2: Stock Price Query Endpoint

**User Story:** As a trader, I want to retrieve price history and technical indicators for a specific symbol, so that I can analyze stock performance.

#### Acceptance Criteria

1. WHEN a GET request is made to /stocks/{symbol}, THE API SHALL query the ts-batch-v2-dev-stock-prices DynamoDB table using the symbol as the partition key
2. WHEN the symbol path parameter is provided, THE API SHALL validate it contains a market code suffix (e.g., .US, .BK, .CC)
3. WHEN the start_date query parameter is provided in YYYY-MM-DD format, THE API SHALL filter prices array to dates >= start_date
4. WHEN the end_date query parameter is provided in YYYY-MM-DD format, THE API SHALL filter prices array to dates <= end_date
5. WHEN the limit query parameter is provided, THE API SHALL return only the N most recent price records
6. WHEN a symbol is not found in the database, THE API SHALL return a 404 status code with an error message
7. THE API SHALL return a JSON response containing symbol, market_code, prices array, moving_averages array, golden_cross boolean, golden_cross_date, death_cross_date, green_days_30d_pct, and max_red_candle_30d_pct fields

### Requirement 3: All-Time High Query Endpoint

**User Story:** As a trader, I want to query all-time high signals with filters, so that I can identify stocks reaching new price peaks.

#### Acceptance Criteria

1. WHEN a GET request is made to /ath, THE API SHALL query the ts-batch-v2-dev-ath DynamoDB table
2. WHEN the market query parameter is provided, THE API SHALL filter results to the specified market code (US, BK, or CC)
3. WHEN the date query parameter is provided in YYYY-MM-DD format, THE API SHALL filter results to ATH signals detected on that specific date
4. WHEN the days query parameter is provided, THE API SHALL filter results to ATH signals detected within the last N days
5. WHEN the limit query parameter is provided, THE API SHALL return only the N most recent ATH records
6. THE API SHALL return a JSON response containing an array of ATH records with symbol, detection_date, ath_price, ath_percentage_gain, market_code, and detected_at fields
7. WHEN no ATH records are found for the given filters, THE API SHALL return a 200 status code with an empty data array

### Requirement 4: Input Validation

**User Story:** As an API consumer, I want clear error messages for invalid inputs, so that I can correct my requests.

#### Acceptance Criteria

1. WHEN the min_green parameter is provided and is not a valid number between 0 and 100, THE API SHALL return a 400 status code with a descriptive error message
2. WHEN the max_red_candle parameter is provided and is not a valid number between -100 and 0, THE API SHALL return a 400 status code with a descriptive error message
3. WHEN the market parameter is provided and is not one of US, BK, or CC, THE API SHALL return a 400 status code with a descriptive error message
4. WHEN a date parameter is provided and is not in YYYY-MM-DD format, THE API SHALL return a 400 status code with a descriptive error message
5. WHEN the days parameter is provided and is not a positive integer, THE API SHALL return a 400 status code with a descriptive error message
6. WHEN the limit parameter is provided and is not a positive integer, THE API SHALL return a 400 status code with a descriptive error message
7. WHEN the symbol path parameter contains invalid characters, THE API SHALL return a 400 status code with a descriptive error message

### Requirement 5: DynamoDB Integration

**User Story:** As a system operator, I want the API to efficiently access DynamoDB tables, so that queries are fast and cost-effective.

#### Acceptance Criteria

1. THE API SHALL use the AWS SDK for Python (boto3) to access DynamoDB tables
2. THE API SHALL connect to DynamoDB in the ap-southeast-1 region
3. WHEN querying golden-crosses with a date filter, THE API SHALL use the cross_date-index GSI for efficient queries
4. WHEN querying golden-crosses with a market and date filter, THE API SHALL use the market_code-cross_date-index GSI for efficient queries
5. WHEN querying ath with a date filter, THE API SHALL use the detection_date-index GSI for efficient queries
6. WHEN querying ath with a market and date filter, THE API SHALL use the market_code-detection_date-index GSI for efficient queries
7. WHEN querying stock prices by symbol, THE API SHALL use the GetItem operation with the symbol partition key
8. THE API SHALL implement read-only access to DynamoDB tables with no write operations
9. WHEN a DynamoDB operation fails, THE API SHALL return a 500 status code with an error message

### Requirement 6: AWS Lambda Deployment

**User Story:** As a developer, I want the API deployed as AWS Lambda functions, so that it scales automatically and minimizes costs.

#### Acceptance Criteria

1. THE API SHALL be implemented as Python 3.12 Lambda functions
2. THE API SHALL be deployed in the ap-southeast-1 AWS region
3. THE API SHALL use environment variables for configuration (table names, region)
4. WHEN a Lambda function is invoked, THE Lambda_Handler SHALL parse the API Gateway event and route to the appropriate handler function
5. THE API SHALL return responses in the format expected by API Gateway (statusCode, headers, body)
6. THE API SHALL complete requests within the Lambda timeout limit
7. THE API SHALL log errors and warnings to CloudWatch Logs

### Requirement 7: API Gateway Configuration

**User Story:** As an API consumer, I want to access the API through standard HTTP endpoints, so that I can integrate it with any HTTP client.

#### Acceptance Criteria

1. THE API SHALL be exposed through AWS API Gateway as a REST API
2. THE API SHALL support CORS with appropriate headers for cross-origin requests
3. THE API SHALL return Content-Type: application/json headers for all responses
4. WHEN an endpoint is not found, THE API_Gateway SHALL return a 404 status code
5. WHEN an HTTP method is not supported, THE API_Gateway SHALL return a 405 status code
6. THE API SHALL support GET requests for all defined endpoints
7. THE API SHALL be accessible via HTTPS only

### Requirement 8: Response Format

**User Story:** As an API consumer, I want consistent JSON response formats, so that I can reliably parse API responses.

#### Acceptance Criteria

1. THE API SHALL return all successful responses with a 200 status code and a JSON body
2. WHEN returning golden cross results, THE API SHALL include a data array containing the filtered records
3. WHEN returning stock price results, THE API SHALL include a data object containing the stock information
4. WHEN an error occurs, THE API SHALL return a JSON body with an error field containing a descriptive message
5. THE API SHALL format all date fields as ISO 8601 strings (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ)
6. THE API SHALL format all numeric fields as numbers (not strings)
7. THE API SHALL omit null or undefined fields from response objects

### Requirement 9: Error Handling

**User Story:** As a developer, I want comprehensive error handling, so that failures are logged and communicated clearly.

#### Acceptance Criteria

1. WHEN an unhandled exception occurs, THE API SHALL catch it and return a 500 status code with a generic error message
2. WHEN a DynamoDB throttling error occurs, THE API SHALL return a 503 status code with a retry-after suggestion
3. WHEN a DynamoDB table is not found, THE API SHALL return a 500 status code and log the configuration error
4. WHEN request parsing fails, THE API SHALL return a 400 status code with details about the parsing error
5. THE API SHALL log all errors with sufficient context for debugging (request ID, parameters, stack trace)
6. THE API SHALL not expose sensitive information (credentials, internal paths) in error messages
7. WHEN multiple validation errors occur, THE API SHALL return all validation errors in a single response

### Requirement 10: Deployment Configuration

**User Story:** As a DevOps engineer, I want clear deployment configuration, so that I can deploy the API to different environments.

#### Acceptance Criteria

1. THE API SHALL support environment-specific configuration through environment variables
2. THE API SHALL use the dev environment configuration initially (ts-batch-v2-dev-* tables)
3. THE API SHALL be deployable to the tradeseeker-api-v2 GitHub repository as a separate service
4. THE API SHALL include Terraform configuration for Lambda and API Gateway resources
5. THE API SHALL document required IAM permissions for DynamoDB read access
6. THE API SHALL support deployment to multiple AWS accounts and regions through Terraform variables
7. THE API SHALL include deployment scripts or CI/CD pipeline configuration
