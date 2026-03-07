# Design Document: TradeSeekerAPI v2

## Overview

The TradeSeekerAPI v2 is a serverless REST API built on AWS Lambda and API Gateway that provides read-only access to stock market data stored in DynamoDB. The API exposes two primary endpoints: one for querying golden cross signals with flexible filtering, and another for retrieving detailed stock price history with technical indicators.

### Key Design Principles

- **Serverless Architecture**: Leverage AWS Lambda for automatic scaling and cost efficiency
- **Read-Only Access**: No write operations to ensure data integrity
- **Efficient Queries**: Use DynamoDB GSIs for optimized query patterns
- **Separation of Concerns**: Clear separation between routing, validation, business logic, and data access
- **Error Transparency**: Comprehensive error handling with clear, actionable error messages
- **Separate Repository**: Implemented in tradeseeker-api-v2 repository, deployed independently

### Technology Stack

- **Runtime**: Python 3.12
- **Cloud Provider**: AWS (ap-southeast-1 region)
- **Compute**: AWS Lambda
- **API Layer**: AWS API Gateway (REST API)
- **Database**: Amazon DynamoDB (read-only access)
- **SDK**: boto3 (AWS SDK for Python)
- **Infrastructure as Code**: Terraform
- **Authorization**: AWS Cognito (for future Angular web app integration)

## Architecture

### High-Level Architecture

```
Client → API Gateway → Lambda → DynamoDB (golden-crosses, stock-prices)
                                    ↓
                              CloudWatch Logs
```

Key components:
- API Gateway: REST API endpoint, CORS handling
- Lambda: Request routing, validation, business logic
- DynamoDB: Read-only queries using GSIs
- CloudWatch: Logging and monitoring

### Project Structure

```
tradeseeker-api-v2/
├── src/
│   ├── lambda_handler.py          # Lambda entry point
│   ├── router.py                  # Request routing
│   ├── config.py                  # Environment configuration
│   ├── formatters.py              # Response formatting
│   ├── validators.py              # Input validation
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── golden_crosses.py      # Golden cross endpoint handler
│   │   └── stock_price.py         # Stock price endpoint handler
│   └── db/
│       ├── __init__.py
│       └── dynamodb_client.py     # DynamoDB operations
├── tests/
│   ├── unit/
│   │   ├── test_validators.py
│   │   ├── test_formatters.py
│   │   ├── test_handlers.py
│   │   ├── test_router.py
│   │   └── test_dynamodb_client.py
│   ├── property/
│   │   ├── test_filtering_properties.py
│   │   ├── test_validation_properties.py
│   │   └── test_response_properties.py
│   └── integration/
│       └── test_lambda_handler.py
├── terraform/
│   ├── main.tf                    # Provider and general config
│   ├── lambda.tf                  # Lambda function resources
│   ├── iam.tf                     # IAM roles and policies
│   ├── api_gateway.tf             # API Gateway configuration
│   ├── cognito.tf                 # Cognito User Pool (optional)
│   ├── variables.tf               # Terraform variables
│   └── outputs.tf                 # Terraform outputs
├── requirements.txt               # Lambda dependencies (boto3)
├── requirements-dev.txt           # Dev dependencies (pytest, hypothesis, moto)
├── deploy.sh                      # Deployment script
└── README.md                      # Documentation
```

### Request Flow

1. **Client Request**: HTTP GET request arrives at API Gateway
2. **API Gateway**: Routes request to Lambda function, handles CORS
3. **Lambda Handler**: Parses API Gateway event, extracts path and query parameters
4. **Request Router**: Routes to appropriate handler based on path
5. **Validation**: Validates query parameters and path parameters
6. **Business Logic**: Applies filters and business rules
7. **Data Access**: Queries DynamoDB using appropriate access pattern
8. **Response Formatting**: Formats data as JSON response
9. **API Gateway**: Returns HTTP response to client

### Routing Strategy: router.py vs API Gateway Resources

**Option 1: Single Lambda + router.py (Chosen)**

Pros:
- Simpler infrastructure (1 Lambda function)
- Shared code and dependencies (validators, DynamoDB client)
- Easier to add new endpoints (just add routes)
- Single deployment unit
- Lower cold start probability (one function stays warm)

Cons:
- Cannot scale endpoints independently
- Larger deployment package
- All endpoints share same timeout/memory settings

**Option 2: Separate Lambda per Endpoint**

Pros:
- Independent scaling per endpoint
- Smaller deployment packages (faster cold starts)
- Can configure different timeout/memory per endpoint
- Clearer CloudWatch metrics per endpoint

Cons:
- More infrastructure to manage (2+ Lambda functions)
- Code duplication (validators, DynamoDB client in each)
- More complex deployment
- Higher cold start probability (multiple functions)

**Decision**: Use router.py approach for this API because:
- Only 2 endpoints (low complexity)
- Shared validation and data access logic
- Simpler deployment and maintenance
- Expected similar traffic patterns for both endpoints

### Authorization Strategy (Future Angular Web App)

**Chosen Approach: AWS Cognito + JWT Tokens**

For the Angular web application, use AWS Cognito for user authentication with JWT tokens:

**Architecture**:
```
Angular App → Cognito (Login) → JWT Token → API Gateway (Cognito Authorizer) → Lambda
```

**Implementation Steps**:
1. **Create Cognito User Pool**: Manage users and authentication
2. **Configure API Gateway Authorizer**: Validate JWT tokens automatically
3. **Angular Integration**: Use AWS Amplify library for authentication
4. **Token Flow**:
   - User logs in through Angular app
   - Cognito returns JWT access token
   - Angular includes token in `Authorization: Bearer <token>` header
   - API Gateway validates token before invoking Lambda
   - Lambda receives user identity in event context

**Angular Configuration**:
```typescript
// Install: npm install aws-amplify @aws-amplify/auth

import { Amplify } from 'aws-amplify';
import { Auth } from '@aws-amplify/auth';

Amplify.configure({
  Auth: {
    region: 'ap-southeast-1',
    userPoolId: 'ap-southeast-1_XXXXXXXXX',
    userPoolWebClientId: 'XXXXXXXXXXXXXXXXXXXXXXXXXX'
  }
});

// Login
await Auth.signIn(username, password);

// Get token and make API call
const session = await Auth.currentSession();
const token = session.getIdToken().getJwtToken();

// HTTP request
headers: {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
}
```

**Benefits**:
- ✅ **Secure**: JWT tokens are user-specific and expire automatically
- ✅ **No exposed secrets**: Tokens are temporary (1 hour default)
- ✅ **User management**: Built-in user registration, password reset, MFA
- ✅ **Scalable**: Cognito handles millions of users
- ✅ **No Lambda code changes**: API Gateway validates tokens
- ✅ **User context**: Lambda receives user ID and attributes

**Security Features**:
- Tokens expire automatically (configurable, default 1 hour)
- Refresh tokens for seamless re-authentication
- MFA support (SMS, TOTP)
- Password policies and account recovery
- Token revocation on logout
- HTTPS-only communication

**Terraform Resources Needed**:
- `aws_cognito_user_pool`: User pool for authentication
- `aws_cognito_user_pool_client`: App client for Angular
- `aws_api_gateway_authorizer`: Cognito authorizer for API Gateway
- Attach authorizer to API Gateway methods

**Initial Phase**: API can be deployed without Cognito authorizer for development. Authorizer can be added later through Terraform without changing Lambda code.

### Deployment Architecture

```
GitHub (tradeseeker-api-v2) → CI/CD → Terraform → AWS Resources
                                                      ↓
                                          Lambda + API Gateway + IAM
```

## Components and Interfaces

### 1. Lambda Handler (lambda_handler.py)

**Responsibility**: Entry point for Lambda function, parses API Gateway events, routes requests

**Interface**:
```python
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    """
    AWS Lambda handler function.
    
    Args:
        event: API Gateway proxy integration event
        context: Lambda context object
        
    Returns:
        API Gateway proxy integration response with statusCode, headers, body
    """
```

**Key Functions**:
- Parse API Gateway event structure
- Extract HTTP method, path, query parameters, path parameters
- Route to appropriate handler function
- Catch unhandled exceptions and return 500 errors
- Format responses for API Gateway

### 2. Request Router (router.py)

**Responsibility**: Routes requests to appropriate handler based on path

**Interface**:
```python
def route_request(method: str, path: str, query_params: dict, path_params: dict) -> dict:
    """
    Routes request to appropriate handler.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        path: Request path
        query_params: Query string parameters
        path_params: Path parameters
        
    Returns:
        Handler response dict with statusCode, body
    """
```

**Routing Logic**:
- `GET /golden-crosses` → golden_crosses_handler
- `GET /stocks/{symbol}` → stock_price_handler
- Other paths → 404 error
- Non-GET methods → 405 error

### 3. Golden Cross Handler (handlers/golden_crosses.py)

**Responsibility**: Handles golden cross queries with filtering

**Interface**:
```python
def handle_golden_crosses(query_params: dict) -> dict:
    """
    Handles GET /golden-crosses requests.
    
    Args:
        query_params: Dict with optional keys:
            - min_green: int (default 70)
            - max_red_candle: int (default -5)
            - market: str (US, BK, CC)
            - date: str (YYYY-MM-DD)
            - days: int
            
    Returns:
        Response dict with statusCode and body containing data array
    """
```

**Logic Flow**:
1. Validate query parameters using validator
2. Apply default filters (min_green=70, max_red_candle=-5)
3. Determine optimal DynamoDB query strategy:
   - If date + market: use market_code-cross_date-index GSI
   - If date only: use cross_date-index GSI
   - If days: calculate date range and use cross_date-index GSI
   - Otherwise: scan table (with warning in logs)
4. Execute DynamoDB query
5. Apply additional filters in memory (green_days, max_red_candle)
6. Format and return results

### 4. Stock Price Handler (handlers/stock_price.py)

**Responsibility**: Handles stock price queries for specific symbols

**Interface**:
```python
def handle_stock_price(symbol: str, query_params: dict) -> dict:
    """
    Handles GET /stocks/{symbol} requests.
    
    Args:
        symbol: Stock symbol with market code (e.g., AAPL.US)
        query_params: Dict with optional keys:
            - start_date: str (YYYY-MM-DD)
            - end_date: str (YYYY-MM-DD)
            - limit: int
            
    Returns:
        Response dict with statusCode and body containing data object
    """
```

**Logic Flow**:
1. Validate symbol format (must contain market code suffix)
2. Validate query parameters
3. Execute DynamoDB GetItem with symbol as partition key
4. If not found, return 404
5. Filter prices array based on date range
6. Apply limit if specified (take most recent N records)
7. Format and return results

### 5. Validator (validators.py)

**Responsibility**: Validates all input parameters

**Interface**:
```python
def validate_golden_cross_params(params: dict) -> tuple[dict, list[str]]:
    """
    Validates golden cross query parameters.
    
    Args:
        params: Raw query parameters
        
    Returns:
        Tuple of (validated_params, errors)
        validated_params: Dict with validated and type-converted values
        errors: List of error messages (empty if valid)
    """

def validate_stock_price_params(symbol: str, params: dict) -> tuple[str, dict, list[str]]:
    """
    Validates stock price query parameters.
    
    Args:
        symbol: Stock symbol
        params: Raw query parameters
        
    Returns:
        Tuple of (validated_symbol, validated_params, errors)
    """
```

**Validation Rules**:
- `min_green`: Must be number 0-100, default 70
- `max_red_candle`: Must be number -100 to 0, default -5
- `market`: Must be one of US, BK, CC
- `date`: Must match YYYY-MM-DD format, must be valid date
- `days`: Must be positive integer
- `limit`: Must be positive integer
- `start_date`/`end_date`: Must match YYYY-MM-DD format, start <= end
- `symbol`: Must contain market code suffix (.US, .BK, .CC)

### 6. DynamoDB Client (db/dynamodb_client.py)

**Responsibility**: Encapsulates all DynamoDB operations

**Interface**:
```python
class DynamoDBClient:
    def __init__(self, region: str = 'ap-southeast-1'):
        """Initialize DynamoDB client."""
        
    def query_golden_crosses_by_date(
        self, 
        date: str, 
        market_code: str = None
    ) -> list[dict]:
        """
        Query golden crosses by date using GSI.
        
        Args:
            date: Cross date (YYYY-MM-DD)
            market_code: Optional market filter
            
        Returns:
            List of golden cross records
        """
        
    def query_golden_crosses_by_date_range(
        self,
        start_date: str,
        end_date: str,
        market_code: str = None
    ) -> list[dict]:
        """
        Query golden crosses within date range using GSI.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            market_code: Optional market filter
            
        Returns:
            List of golden cross records
        """
        
    def scan_golden_crosses(self, market_code: str = None) -> list[dict]:
        """
        Scan golden crosses table (use sparingly).
        
        Args:
            market_code: Optional market filter
            
        Returns:
            List of golden cross records
        """
        
    def get_stock_price(self, symbol: str) -> dict | None:
        """
        Get stock price data by symbol.
        
        Args:
            symbol: Stock symbol with market code
            
        Returns:
            Stock price record or None if not found
        """
```

**Implementation Details**:
- Use boto3 DynamoDB resource for cleaner API
- Configure region from environment variable
- Use GSI names from environment variables
- Implement exponential backoff for throttling
- Log all queries with execution time
- Handle pagination for large result sets

### 7. Response Formatter (formatters.py)

**Responsibility**: Formats responses consistently

**Interface**:
```python
def success_response(data: any, status_code: int = 200) -> dict:
    """
    Creates successful API Gateway response.
    
    Args:
        data: Response data (will be JSON serialized)
        status_code: HTTP status code
        
    Returns:
        API Gateway response dict
    """

def error_response(message: str, status_code: int = 400, errors: list = None) -> dict:
    """
    Creates error API Gateway response.
    
    Args:
        message: Error message
        status_code: HTTP status code
        errors: Optional list of detailed errors
        
    Returns:
        API Gateway response dict
    """
```

**Response Format**:
```python
# Success response
{
    "statusCode": 200,
    "headers": {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type"
    },
    "body": json.dumps({"data": [...]})
}

# Error response
{
    "statusCode": 400,
    "headers": {...},
    "body": json.dumps({
        "error": "Invalid parameters",
        "details": ["min_green must be between 0 and 100"]
    })
}
```

## Data Models

### Golden Cross Record

**Source**: ts-batch-v2-dev-golden-crosses DynamoDB table

**Schema**:
```python
{
    "symbol": str,              # PK: Stock symbol with market code
    "cross_date": str,          # SK: Date of golden cross (YYYY-MM-DD)
    "market_code": str,         # Market identifier (US, BK, CC)
    "signal": str,              # Signal type (GOLDEN_CROSS)
    "ema_50": float,            # 50-day EMA value
    "ema_200": float,           # 200-day EMA value
    "crossover_strength": float,# Strength of crossover signal
    "green_days_30d_pct": float,# Percentage of green days in 30d
    "max_red_candle_30d_pct": float, # Largest red candle in 30d
    "detected_at": str,         # ISO timestamp of detection
    "ttl": float                # TTL for record expiration
}
```

**Indexes**:
- Primary: symbol (PK), cross_date (SK)
- GSI: cross_date-index (cross_date as PK)
- GSI: market_code-cross_date-index (market_code as PK, cross_date as SK)

### Stock Price Record

**Source**: ts-batch-v2-dev-stock-prices DynamoDB table

**Schema**:
```python
{
    "symbol": str,              # PK: Stock symbol with market code
    "market_code": str,         # Market identifier
    "prices": [                 # Array of price records
        {
            "date": str,        # YYYY-MM-DD
            "open": float,
            "high": float,
            "low": float,
            "close": float,
            "volume": int
        }
    ],
    "moving_averages": [        # Array of MA records with EMAs
        {
            "date": str,        # YYYY-MM-DD
            "ema_7": float,
            "ema_30": float,
            "ema_50": float,
            "ema_200": float
        }
    ],
    "golden_cross": bool,       # Current golden cross status
    "golden_cross_date": str,   # Date of most recent golden cross
    "death_cross_date": str,    # Date of most recent death cross
    "green_days_30d_pct": float,
    "max_red_candle_30d_pct": float
}
```

**Indexes**:
- Primary: symbol (PK)

### API Response Models

**Golden Cross List Response**:
```python
{
    "data": [
        {
            "symbol": str,
            "cross_date": str,
            "market_code": str,
            "signal": str,
            "ema_50": float,
            "ema_200": float,
            "crossover_strength": float,
            "green_days_30d_pct": float,
            "max_red_candle_30d_pct": float,
            "detected_at": str
        }
    ]
}
```

**Stock Price Response**:
```python
{
    "data": {
        "symbol": str,
        "market_code": str,
        "prices": [...],
        "moving_averages": [...],
        "golden_cross": bool,
        "golden_cross_date": str,
        "death_cross_date": str,
        "green_days_30d_pct": float,
        "max_red_candle_30d_pct": float
    }
}
```

**Error Response**:
```python
{
    "error": str,
    "details": [str]  # Optional array of specific errors
}
```


## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property 1: Golden Cross Default Filters

*For any* request to /golden-crosses without query parameters, all returned records should have green_days_30d_pct >= 70 and max_red_candle_30d_pct >= -5.

**Validates: Requirements 1.2**

### Property 2: Golden Cross Filter Compliance

*For any* request to /golden-crosses with min_green and max_red_candle parameters, all returned records should satisfy both green_days_30d_pct >= min_green AND max_red_candle_30d_pct >= max_red_candle.

**Validates: Requirements 1.3, 1.4**

### Property 3: Symbol Validation

*For any* symbol path parameter, if it does not contain a valid market code suffix (.US, .BK, or .CC), the API should return a 400 status code with an error message.

**Validates: Requirements 2.2**

### Property 4: Date Range Filtering

*For any* request to /stocks/{symbol} with start_date and/or end_date parameters, all returned price records should have dates within the specified range (date >= start_date AND date <= end_date).

**Validates: Requirements 2.3, 2.4**

### Property 5: Parameter Validation

*For any* request with invalid parameters (min_green not in 0-100, max_red_candle not in -100 to 0, invalid date format, non-positive integers for days/limit), the API should return a 400 status code with a descriptive error message.

**Validates: Requirements 3.1, 3.2, 3.4, 3.5, 3.6**

### Property 6: Read-Only DynamoDB Access

*For any* API request, the system should never invoke DynamoDB write operations (PutItem, UpdateItem, DeleteItem, BatchWriteItem).

**Validates: Requirements 4.6**

### Property 7: Response Format Consistency

*For any* successful response, it should have a 200 status code, Content-Type: application/json header, CORS headers, and a JSON body with a data field. For any error response, it should have an appropriate error status code (4xx or 5xx) and a JSON body with an error field.

**Validates: Requirements 6.2, 6.3, 7.1, 7.4**

### Property 8: Numeric Field Types

*For any* response containing numeric fields (ema values, crossover_strength, percentages), they should be represented as numbers, not strings.

**Validates: Requirements 7.6**

## Error Handling

### Error Categories

The API implements comprehensive error handling across four categories:

1. **Client Errors (4xx)**:
   - 400 Bad Request: Invalid parameters, malformed requests
   - 404 Not Found: Symbol not found, invalid endpoint
   - 405 Method Not Allowed: Unsupported HTTP method

2. **Server Errors (5xx)**:
   - 500 Internal Server Error: Unhandled exceptions, configuration errors
   - 503 Service Unavailable: DynamoDB throttling

### Error Response Structure

All errors return a consistent JSON structure:

```python
{
    "error": "Brief error description",
    "details": ["Specific error 1", "Specific error 2"]  # Optional
}
```

### Validation Error Handling

The validator accumulates all validation errors and returns them together in a single response. This allows clients to fix multiple issues at once rather than discovering them one at a time.

Example multi-error response:
```python
{
    "error": "Invalid parameters",
    "details": [
        "min_green must be between 0 and 100",
        "market must be one of: US, BK, CC",
        "date must be in YYYY-MM-DD format"
    ]
}
```

### DynamoDB Error Handling

DynamoDB errors are caught and translated to appropriate HTTP responses:

- **ProvisionedThroughputExceededException**: Return 503 with retry suggestion
- **ResourceNotFoundException**: Return 500 and log configuration error
- **ValidationException**: Return 400 with error details
- **Other exceptions**: Return 500 with generic error message

### Exception Handling Strategy

```python
try:
    # Request processing
    validate_params()
    query_dynamodb()
    format_response()
except ValidationError as e:
    return error_response(str(e), 400, e.details)
except ResourceNotFoundError as e:
    logger.error(f"DynamoDB table not found: {e}")
    return error_response("Service configuration error", 500)
except ThrottlingError as e:
    return error_response("Service temporarily unavailable", 503)
except Exception as e:
    logger.error(f"Unhandled exception: {e}", exc_info=True)
    return error_response("Internal server error", 500)
```

### Logging Strategy

All errors are logged to CloudWatch with:
- Request ID (from Lambda context)
- Request parameters (sanitized)
- Stack trace (for unhandled exceptions)
- Timestamp
- Error category

Sensitive information (credentials, internal paths) is filtered from logs and error messages.

## Testing Strategy

### Dual Testing Approach

The API will be validated using both unit tests and property-based tests:

- **Unit tests**: Verify specific examples, edge cases, and error conditions
- **Property tests**: Verify universal properties across all inputs

Both approaches are complementary and necessary for comprehensive coverage. Unit tests catch concrete bugs and validate specific scenarios, while property tests verify general correctness across a wide range of inputs.

### Property-Based Testing

Property-based tests will be implemented using **Hypothesis** (Python's property-based testing library). Each test will:

- Run a minimum of 100 iterations with randomized inputs
- Reference the corresponding design property in a comment
- Use the tag format: **Feature: tradeseeker-api-v2, Property {number}: {property_text}**

Example property test structure:

```python
from hypothesis import given, strategies as st

# Feature: tradeseeker-api-v2, Property 2: Golden Cross Min Green Filter
@given(min_green=st.integers(min_value=0, max_value=100))
def test_golden_cross_min_green_filter(min_green):
    """For any min_green parameter, all results should have green_days >= min_green"""
    response = api.get_golden_crosses(min_green=min_green)
    assert response.status_code == 200
    for record in response.data:
        assert record['green_days_30d_pct'] >= min_green
```

### Unit Testing Strategy

Unit tests will focus on:

1. **Specific Examples**: Test known good inputs and expected outputs
2. **Edge Cases**: Empty results, boundary values, symbol not found
3. **Error Conditions**: Invalid inputs, DynamoDB failures, malformed requests
4. **Integration Points**: Lambda handler parsing, response formatting, DynamoDB client

Example unit test structure:

```python
def test_golden_crosses_default_filters():
    """Test that default filters are applied when no parameters provided"""
    response = api.get_golden_crosses()
    assert response.status_code == 200
    for record in response.data:
        assert record['green_days_30d_pct'] >= 70
        assert record['max_red_candle_30d_pct'] >= -5

def test_stock_price_not_found():
    """Test 404 response when symbol doesn't exist"""
    response = api.get_stock_price('NONEXISTENT.US')
    assert response.status_code == 404
    assert 'error' in response.body
```

### Test Coverage Goals

- **Line coverage**: Minimum 90%
- **Branch coverage**: Minimum 85%
- **All properties**: 100% (every property must have a property test)
- **All error paths**: 100% (every error condition must be tested)

### Mocking Strategy

Tests will mock external dependencies:

- **DynamoDB**: Use moto library for DynamoDB mocking
- **Environment variables**: Use unittest.mock.patch
- **Lambda context**: Create mock context objects

This allows tests to run quickly without AWS credentials or network access.

### Test Organization

```
tests/
├── unit/
│   ├── test_handlers.py
│   ├── test_validators.py
│   ├── test_dynamodb_client.py
│   └── test_formatters.py
├── property/
│   ├── test_filtering_properties.py
│   ├── test_validation_properties.py
│   └── test_response_properties.py
└── integration/
    └── test_lambda_handler.py
```

### Continuous Integration

Tests will run automatically on:
- Every pull request
- Every commit to main branch
- Before deployment to any environment

CI pipeline will fail if:
- Any test fails
- Coverage drops below thresholds
- Linting errors are present
