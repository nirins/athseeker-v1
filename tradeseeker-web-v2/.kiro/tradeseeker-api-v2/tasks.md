# Implementation Plan: TradeSeekerAPI v2

## Overview

This implementation plan breaks down the TradeSeekerAPI v2 into discrete coding tasks. The API is a serverless REST service built on AWS Lambda and API Gateway that provides read-only access to stock market data in DynamoDB. The implementation follows a layered architecture with clear separation between routing, validation, business logic, and data access.

The tasks are organized to build incrementally: first establishing the core infrastructure and utilities, then implementing the data access layer, followed by business logic handlers, and finally wiring everything together with the Lambda entry point and deployment configuration.

## Tasks

- [x] 1. Set up project structure and core utilities
  - Create Python 3.12 project structure with src/ directory
  - Create formatters.py module for response formatting (success_response, error_response functions)
  - Add CORS headers and Content-Type headers to all responses
  - Create requirements.txt with boto3 dependency
  - Create requirements-dev.txt with pytest, hypothesis, moto, pytest-cov
  - _Requirements: 5.5, 6.2, 6.3, 7.1, 7.4_

- [x] 2. Implement input validation module
  - Create validators.py with validation functions
  - Implement validate_golden_cross_params function (min_green, max_red_candle, market, date, days)
  - Implement validate_stock_price_params function (symbol, start_date, end_date, limit)
  - Implement validate_ath_params function (market, date, days, limit)
  - Implement date format validation (YYYY-MM-DD) and numeric range validation
  - Return tuple of (validated_params, errors) for accumulating multiple validation errors
  - _Requirements: 2.2, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 4.2, 4.3, 4.4, 4.5_

- [x] 3. Implement DynamoDB client
  - Create db/dynamodb_client.py with DynamoDBClient class
  - Initialize boto3 DynamoDB resource with region from environment variable
  - Implement query_golden_crosses_by_date method with optional market_code parameter (uses cross_date-index or market_code-cross_date-index GSI)
  - Implement query_golden_crosses_by_date_range method with optional market_code parameter
  - Implement scan_golden_crosses method with optional market filter
  - Implement query_ath_by_date method with optional market_code parameter (uses detection_date-index or market_code-detection_date-index GSI)
  - Implement query_ath_by_date_range method with optional market_code parameter
  - Implement scan_ath method with optional market filter
  - Implement get_stock_price method using GetItem with symbol partition key
  - Add error handling for DynamoDB exceptions (throttling, resource not found)
  - Add logging for all queries with execution time
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9_

- [x] 4. Implement golden cross handler
  - Create handlers/golden_crosses.py with handle_golden_crosses function
  - Parse and validate query parameters using validators
  - Apply default filters (min_green=70, max_red_candle=-5) when not provided
  - Determine optimal DynamoDB query strategy based on parameters (date+market, date only, days, or scan)
  - Execute DynamoDB query using appropriate method from DynamoDBClient
  - Apply in-memory filtering for green_days_30d_pct and max_red_candle_30d_pct
  - Format response using success_response or error_response
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8_

- [x] 5. Implement stock price handler
  - Create handlers/stock_price.py with handle_stock_price function
  - Validate symbol format (must contain market code suffix)
  - Validate query parameters using validators
  - Execute DynamoDB GetItem using DynamoDBClient
  - Return 404 if symbol not found
  - Filter prices array based on start_date and end_date
  - Apply limit to return N most recent records
  - Format response using success_response or error_response
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

- [ ] 6. Implement all-time high handler
  - Create handlers/ath.py with handle_ath function
  - Parse and validate query parameters using validators
  - Determine optimal DynamoDB query strategy based on parameters (date+market, date only, days, or scan)
  - Execute DynamoDB query using appropriate method from DynamoDBClient
  - Apply market filter if specified
  - Apply limit to return N most recent records
  - Format response using success_response or error_response
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [x] 7. Implement request router
  - Create router.py with route_request function
  - Parse HTTP method and path
  - Route GET /golden-crosses to golden_crosses_handler
  - Route GET /stocks/{symbol} to stock_price_handler
  - Route GET /ath to ath_handler
  - Return 404 for unknown paths
  - Return 405 for unsupported HTTP methods
  - Extract path parameters (symbol) and query parameters
  - _Requirements: 7.4, 7.5, 7.6_

- [x] 8. Implement Lambda handler entry point
  - Create lambda_handler.py with lambda_handler function
  - Parse API Gateway proxy integration event
  - Extract HTTP method, path, query parameters, path parameters
  - Call route_request with extracted parameters
  - Catch all unhandled exceptions and return 500 error response
  - Log errors to CloudWatch with request context
  - Format response for API Gateway (statusCode, headers, body)
  - _Requirements: 6.1, 6.4, 6.5, 6.7, 9.1, 9.5_

- [x] 9. Add environment configuration
  - Create config.py for environment variable management
  - Define constants for DynamoDB table names (from env vars)
  - Define constants for DynamoDB region (from env vars)
  - Define constants for GSI names (from env vars)
  - Provide defaults for local development
  - _Requirements: 6.3, 10.1, 10.2_

- [x] 10. Create Terraform infrastructure configuration
  - [x] 10.1 Create terraform/main.tf with provider configuration
    - Define AWS provider for ap-southeast-1 region
    - Add required provider versions
    - _Requirements: 6.2_

  - [x] 10.2 Create terraform/lambda.tf for Lambda resources
    - Create Lambda function resource with Python 3.12 runtime
    - Set environment variables for Lambda (table names, region, GSI names)
    - Configure Lambda timeout and memory settings
    - _Requirements: 6.1, 6.3_

  - [x] 10.3 Create terraform/iam.tf for IAM resources
    - Create IAM role for Lambda execution
    - Create IAM policy for DynamoDB read permissions (GetItem, Query, Scan)
    - Attach policies to Lambda role
    - Grant access to golden-crosses, stock-prices, and ath tables
    - _Requirements: 10.5_

  - [x] 10.4 Create terraform/api_gateway.tf for API Gateway resources
    - Create REST API Gateway resource
    - Create /golden-crosses resource and GET method
    - Create /stocks resource, /{symbol} resource, and GET method
    - Create /ath resource and GET method
    - Configure Lambda proxy integration for all endpoints
    - Enable CORS on all methods
    - Create deployment and stage (dev)
    - _Requirements: 7.1, 7.2, 7.6, 7.7_

  - [x] 10.5 Create terraform/cognito.tf for Cognito resources (optional)
    - Create Cognito User Pool resource
    - Create Cognito User Pool Client for Angular app
    - Create API Gateway Cognito Authorizer
    - Document configuration for Angular (user pool ID, client ID)
    - Mark resources as optional/commented out for initial deployment
    - _Requirements: Design section on Authorization Strategy_

  - [x] 10.6 Create terraform/variables.tf and terraform/outputs.tf
    - Define variables for environment, AWS region, table names
    - Define outputs for API Gateway URL, Lambda function ARN
    - Add outputs for Cognito User Pool ID and Client ID (when enabled)
    - _Requirements: 10.1, 10.6_

- [x] 11. Create deployment scripts and documentation
  - Create deploy.sh script to package Lambda and run Terraform
  - Create README.md with setup, deployment, and API documentation
  - Document prerequisites (Python 3.12, Terraform, AWS credentials)
  - Document environment variables and deployment steps
  - Document API endpoints and parameters
  - _Requirements: 10.5, 10.7_

- [x] 12. Write tests and verify implementation
  - Write unit tests for validators, formatters, handlers, and router
  - Write property-based tests for filtering, validation, and response format
  - Write integration tests for Lambda handler with mocked DynamoDB
  - Run full test suite with coverage reporting
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Each task references specific requirements for traceability
- All DynamoDB operations are read-only (no write operations)
- The API uses Python 3.12 and will be deployed to AWS Lambda in ap-southeast-1 region
- Terraform configuration supports deployment to multiple environments through variables
- Testing is consolidated into task 11 to streamline the implementation process
