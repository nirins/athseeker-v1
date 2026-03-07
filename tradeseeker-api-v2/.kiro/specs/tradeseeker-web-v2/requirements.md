# Requirements Document

## Introduction

The TradeSeekerWeb application is an Angular-based web interface that displays golden cross stock signals with interactive charts. The system connects to the tradeseeker-api-v2 REST API to fetch stock data and presents it in a responsive grid layout optimized for large monitors. Users authenticate via AWS Cognito to access the API endpoints.

## Glossary

- **Golden_Cross**: A technical analysis pattern where a shorter-term moving average crosses above a longer-term moving average, indicating a potential bullish signal
- **EMA**: Exponential Moving Average - a type of moving average that places greater weight on recent data points
- **TradeSeekerWeb**: The Angular web application system
- **API_Client**: The HTTP client component responsible for communicating with the tradeseeker-api-v2 REST API
- **Chart_Grid**: The responsive grid layout component that displays multiple stock charts
- **Auth_Service**: The authentication service that manages AWS Cognito integration and JWT tokens
- **Stock_Chart**: An individual chart component displaying price data and EMA lines for a single stock symbol
- **Market**: A stock market identifier (e.g., "US", "SG")
- **Symbol**: A stock ticker symbol (e.g., "AAPL", "MSFT")
- **Bearer_Token**: A JWT authentication token included in API request headers

## Requirements

### Requirement 1: User Authentication

**User Story:** As a user, I want to authenticate with my AWS Cognito credentials, so that I can access the golden cross stock data from the API.

#### Acceptance Criteria

1. WHEN a user visits the application without authentication, THE TradeSeekerWeb SHALL display a login form
2. WHEN a user submits valid Cognito credentials, THE Auth_Service SHALL authenticate with AWS Cognito and obtain a JWT token
3. WHEN authentication succeeds, THE Auth_Service SHALL store the Bearer_Token securely in the browser
4. WHEN a user is authenticated, THE TradeSeekerWeb SHALL redirect to the main dashboard view
5. WHEN authentication fails, THE TradeSeekerWeb SHALL display an error message and maintain the login form
6. WHEN a Bearer_Token expires, THE Auth_Service SHALL prompt the user to re-authenticate
7. WHEN a user logs out, THE Auth_Service SHALL clear the stored Bearer_Token and redirect to the login form

### Requirement 2: Golden Cross List Retrieval

**User Story:** As a user, I want to fetch the list of stocks with golden cross signals, so that I can see which stocks are showing bullish patterns.

#### Acceptance Criteria

1. WHEN a user accesses the dashboard, THE API_Client SHALL request the golden cross list from GET /golden-crosses?market=US with the Bearer_Token in the Authorization header
2. WHEN the API returns a successful response, THE TradeSeekerWeb SHALL parse the list of stock symbols
3. WHEN the API returns an error response, THE TradeSeekerWeb SHALL display an error message to the user
4. WHEN the Bearer_Token is missing or invalid, THE API_Client SHALL handle 401 Unauthorized responses by redirecting to login
5. WHERE a market parameter is specified, THE API_Client SHALL include it in the request query string
6. WHEN the golden cross list is empty, THE TradeSeekerWeb SHALL display a message indicating no golden crosses are currently available

### Requirement 3: Stock Data Retrieval

**User Story:** As a user, I want to fetch detailed stock data for each golden cross symbol, so that I can view price history and EMA lines.

#### Acceptance Criteria

1. WHEN the TradeSeekerWeb receives a list of symbols, THE API_Client SHALL request detailed data for each Symbol from GET /stocks/{symbol} with the Bearer_Token in the Authorization header
2. WHEN stock data is received, THE TradeSeekerWeb SHALL parse the price data and EMA values (7, 30, 50, 200)
3. WHEN a stock data request fails, THE TradeSeekerWeb SHALL log the error and continue processing remaining symbols
4. WHEN all stock data requests complete, THE TradeSeekerWeb SHALL render the Chart_Grid with available data
5. WHEN stock data is missing required fields, THE TradeSeekerWeb SHALL handle the incomplete data gracefully and display what is available

### Requirement 4: Responsive Chart Grid Layout

**User Story:** As a user, I want to view multiple stock charts in a responsive grid, so that I can efficiently monitor many stocks on my large monitor.

#### Acceptance Criteria

1. WHEN the viewport width corresponds to a 27-inch monitor, THE Chart_Grid SHALL display 6 Stock_Charts per row
2. WHEN the viewport width decreases, THE Chart_Grid SHALL adjust to display fewer charts per row while maintaining readability
3. WHEN the viewport width is mobile-sized, THE Chart_Grid SHALL display 1 Stock_Chart per row
4. WHEN the Chart_Grid renders, THE TradeSeekerWeb SHALL use CSS Grid or Flexbox for layout management
5. WHEN the browser window is resized, THE Chart_Grid SHALL reflow the layout responsively without page reload

### Requirement 5: Stock Chart Display

**User Story:** As a user, I want to see individual stock charts with price data and EMA lines, so that I can analyze the golden cross pattern visually.

#### Acceptance Criteria

1. WHEN a Stock_Chart renders, THE TradeSeekerWeb SHALL display the Symbol name prominently
2. WHEN price data is available, THE Stock_Chart SHALL render price data as candlestick or line chart
3. WHEN EMA data is available, THE Stock_Chart SHALL overlay EMA lines for periods 7, 30, 50, and 200
4. WHEN rendering EMA lines, THE Stock_Chart SHALL use distinct colors for each EMA period for easy differentiation
5. WHEN a Stock_Chart is displayed, THE TradeSeekerWeb SHALL ensure the chart is sized appropriately for the grid cell
6. WHEN stock data is loading, THE Stock_Chart SHALL display a loading indicator
7. WHEN stock data fails to load, THE Stock_Chart SHALL display an error state with the Symbol name

### Requirement 6: API Communication

**User Story:** As a developer, I want the application to communicate reliably with the tradeseeker-api-v2 REST API, so that users receive accurate and timely stock data.

#### Acceptance Criteria

1. WHEN making API requests, THE API_Client SHALL use the base URL https://56qpa0i92h.execute-api.ap-southeast-1.amazonaws.com/dev
2. WHEN a Bearer_Token is available, THE API_Client SHALL include it in the Authorization header as "Bearer {token}"
3. WHEN an API request times out, THE API_Client SHALL retry the request up to 2 additional times
4. WHEN an API returns a 5xx error, THE API_Client SHALL handle it gracefully and display an appropriate error message
5. WHEN an API returns a 4xx error, THE API_Client SHALL handle it according to the error type (401 for auth, 404 for not found, etc.)
6. WHEN making multiple concurrent requests, THE API_Client SHALL manage request concurrency to avoid overwhelming the API

### Requirement 7: Data Refresh

**User Story:** As a user, I want to refresh the stock data, so that I can see the most current golden cross signals and price information.

#### Acceptance Criteria

1. WHEN a user clicks a refresh button, THE TradeSeekerWeb SHALL re-fetch the golden cross list and stock data
2. WHEN data is being refreshed, THE TradeSeekerWeb SHALL display a loading indicator
3. WHERE automatic refresh is enabled, THE TradeSeekerWeb SHALL refresh data at a configurable interval (default: 5 minutes)
4. WHEN a refresh is in progress, THE TradeSeekerWeb SHALL prevent duplicate refresh requests
5. WHEN a refresh completes, THE TradeSeekerWeb SHALL update all Stock_Charts with new data

### Requirement 8: Market Selection

**User Story:** As a user, I want to select different stock markets, so that I can view golden cross signals from various markets.

#### Acceptance Criteria

1. WHEN the dashboard loads, THE TradeSeekerWeb SHALL default to the "US" market
2. WHEN a user selects a different Market, THE TradeSeekerWeb SHALL fetch the golden cross list for that Market
3. WHEN the Market changes, THE TradeSeekerWeb SHALL clear existing charts and load new data for the selected Market
4. WHEN displaying market options, THE TradeSeekerWeb SHALL show available markets (e.g., "US", "SG")
5. WHEN a Market selection is made, THE TradeSeekerWeb SHALL persist the selection for the user session

### Requirement 9: Error Handling and User Feedback

**User Story:** As a user, I want clear feedback when errors occur, so that I understand what went wrong and what actions I can take.

#### Acceptance Criteria

1. WHEN a network error occurs, THE TradeSeekerWeb SHALL display a user-friendly error message
2. WHEN authentication fails, THE TradeSeekerWeb SHALL display the specific authentication error
3. WHEN API requests fail, THE TradeSeekerWeb SHALL log detailed error information to the browser console for debugging
4. WHEN data is loading, THE TradeSeekerWeb SHALL display loading indicators to inform the user
5. WHEN an operation succeeds after an error, THE TradeSeekerWeb SHALL clear previous error messages
6. WHEN displaying errors, THE TradeSeekerWeb SHALL provide actionable guidance (e.g., "Retry", "Login Again")

### Requirement 10: Application Deployment

**User Story:** As a developer, I want to deploy the application to static hosting, so that users can access it via a web URL.

#### Acceptance Criteria

1. WHEN the application is built for production, THE TradeSeekerWeb SHALL generate optimized static assets
2. WHEN deployed, THE TradeSeekerWeb SHALL be accessible via HTTPS
3. WHERE static hosting is used, THE TradeSeekerWeb SHALL support deployment to S3 with CloudFront or equivalent CDN
4. WHEN the application loads, THE TradeSeekerWeb SHALL serve all assets efficiently with appropriate caching headers
5. WHEN routing is used, THE TradeSeekerWeb SHALL configure the hosting to support Angular's client-side routing
