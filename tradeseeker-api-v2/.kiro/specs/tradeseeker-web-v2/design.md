# Design Document: TradeSeekerWeb v2

## Overview

TradeSeekerWeb v2 is an Angular single-page application (SPA) that provides a visual dashboard for monitoring golden cross stock signals. The application follows a component-based architecture with clear separation between authentication, API communication, data management, and presentation layers.

The system authenticates users via AWS Cognito, fetches golden cross signals and detailed stock data from the tradeseeker-api-v2 REST API, and displays interactive charts in a responsive grid layout optimized for large monitors.

## Architecture

### Project Folder Structure

```
tradeseeker-web-v2/
├── src/
│   ├── app/
│   │   ├── core/
│   │   │   ├── services/
│   │   │   │   ├── auth.service.ts
│   │   │   │   ├── api.service.ts
│   │   │   │   └── auth.interceptor.ts
│   │   │   ├── models/
│   │   │   │   ├── auth.models.ts
│   │   │   │   ├── api.models.ts
│   │   │   │   └── chart.models.ts
│   │   │   └── guards/
│   │   │       └── auth.guard.ts
│   │   ├── features/
│   │   │   ├── auth/
│   │   │   │   ├── login/
│   │   │   │   │   ├── login.component.ts
│   │   │   │   │   ├── login.component.html
│   │   │   │   │   ├── login.component.scss
│   │   │   │   │   └── login.component.spec.ts
│   │   │   │   └── auth.module.ts
│   │   │   └── dashboard/
│   │   │       ├── dashboard.component.ts
│   │   │       ├── dashboard.component.html
│   │   │       ├── dashboard.component.scss
│   │   │       ├── dashboard.component.spec.ts
│   │   │       ├── components/
│   │   │       │   ├── chart-grid/
│   │   │       │   │   ├── chart-grid.component.ts
│   │   │       │   │   ├── chart-grid.component.html
│   │   │       │   │   ├── chart-grid.component.scss
│   │   │       │   │   └── chart-grid.component.spec.ts
│   │   │       │   ├── stock-chart/
│   │   │       │   │   ├── stock-chart.component.ts
│   │   │       │   │   ├── stock-chart.component.html
│   │   │       │   │   ├── stock-chart.component.scss
│   │   │       │   │   └── stock-chart.component.spec.ts
│   │   │       │   └── market-selector/
│   │   │       │       ├── market-selector.component.ts
│   │   │       │       ├── market-selector.component.html
│   │   │       │       ├── market-selector.component.scss
│   │   │       │       └── market-selector.component.spec.ts
│   │   │       └── dashboard.module.ts
│   │   ├── shared/
│   │   │   ├── components/
│   │   │   │   ├── loading-spinner/
│   │   │   │   │   ├── loading-spinner.component.ts
│   │   │   │   │   ├── loading-spinner.component.html
│   │   │   │   │   └── loading-spinner.component.scss
│   │   │   │   └── error-message/
│   │   │   │       ├── error-message.component.ts
│   │   │   │       ├── error-message.component.html
│   │   │   │       └── error-message.component.scss
│   │   │   └── shared.module.ts
│   │   ├── app.component.ts
│   │   ├── app.component.html
│   │   ├── app.component.scss
│   │   ├── app.component.spec.ts
│   │   ├── app.module.ts
│   │   └── app-routing.module.ts
│   ├── assets/
│   │   ├── images/
│   │   └── styles/
│   │       └── variables.scss
│   ├── environments/
│   │   ├── environment.ts
│   │   └── environment.prod.ts
│   ├── index.html
│   ├── main.ts
│   ├── styles.scss
│   └── polyfills.ts
├── tests/
│   ├── unit/
│   │   ├── services/
│   │   │   ├── auth.service.spec.ts
│   │   │   └── api.service.spec.ts
│   │   └── components/
│   │       ├── login.component.spec.ts
│   │       ├── dashboard.component.spec.ts
│   │       ├── chart-grid.component.spec.ts
│   │       └── stock-chart.component.spec.ts
│   ├── property/
│   │   ├── auth.properties.spec.ts
│   │   ├── api.properties.spec.ts
│   │   ├── chart.properties.spec.ts
│   │   └── generators/
│   │       ├── stock-data.generator.ts
│   │       ├── auth.generator.ts
│   │       └── viewport.generator.ts
│   └── e2e/
│       ├── login.e2e.spec.ts
│       ├── dashboard.e2e.spec.ts
│       └── responsive.e2e.spec.ts
├── angular.json
├── package.json
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.spec.json
├── karma.conf.js
└── README.md
```

**Folder Structure Explanation**:

- **src/app/core/**: Core application services, models, guards, and interceptors used throughout the app
  - **services/**: Singleton services (AuthService, ApiService, HTTP interceptor)
  - **models/**: TypeScript interfaces and types for data models
  - **guards/**: Route guards for authentication

- **src/app/features/**: Feature modules organized by domain
  - **auth/**: Authentication feature (login component)
  - **dashboard/**: Dashboard feature with chart display components

- **src/app/shared/**: Shared components, directives, and pipes used across features
  - **components/**: Reusable UI components (loading spinner, error message)

- **src/environments/**: Environment-specific configuration (API URLs, Cognito config)

- **tests/**: All test files organized by test type
  - **unit/**: Unit tests for services and components
  - **property/**: Property-based tests with custom generators
  - **e2e/**: End-to-end integration tests

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Browser                             │
└────────────────────────┬────────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
┌──────────────────┐          ┌──────────────────────┐
│ Login Component  │          │ Dashboard Component  │
└────────┬─────────┘          └──────────┬───────────┘
         │                               │
         │                    ┌──────────┼──────────┐
         │                    │          │          │
         │                    ▼          ▼          ▼
         │          ┌─────────────┐  ┌──────┐  ┌────────────┐
         │          │ Market      │  │Chart │  │Chart Grid  │
         │          │ Selector    │  │Grid  │  │Component   │
         │          └─────────────┘  └──┬───┘  └────────────┘
         │                              │
         │                              ▼
         │                    ┌──────────────────┐
         │                    │ Stock Chart      │
         │                    │ Component        │
         │                    └──────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────────┐
│                      Service Layer                                │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │ Auth Service │    │ API Service  │    │ HTTP Interceptor │   │
│  └──────┬───────┘    └──────┬───────┘    └──────────────────┘   │
└─────────┼───────────────────┼──────────────────────────────────┘
          │                   │
          ▼                   ▼
┌──────────────────┐  ┌──────────────────────┐
│  AWS Cognito     │  │ TradeSeeker API v2   │
└──────────────────┘  └──────────────────────┘
```

### Component Architecture

The application follows Angular's component-based architecture with the following layers:

1. **Presentation Layer**: Angular components for UI rendering
2. **Service Layer**: Injectable services for business logic and API communication
3. **State Management Layer**: RxJS-based state management for reactive data flow
4. **Authentication Layer**: AWS Cognito integration for user authentication

### Key Design Decisions

1. **Angular Framework**: Use latest Angular version for modern features, TypeScript support, and robust tooling
2. **Reactive Programming**: Leverage RxJS Observables for asynchronous data streams and state management
3. **Component Isolation**: Each chart is an independent component that can load and render autonomously
4. **CSS Grid Layout**: Use CSS Grid for responsive layout to achieve 6 charts per row on large monitors
5. **Chart.js**: Use Chart.js library for rendering stock charts with candlestick/line charts and EMA overlays
6. **JWT Token Management**: Store JWT tokens securely and include in all API requests via HTTP interceptor

## Components and Interfaces

### 1. Authentication Service (AuthService)

**Responsibility**: Manage user authentication with AWS Cognito and JWT token lifecycle.

**Interface**:
```typescript
interface AuthService {
  // Authenticate user with Cognito credentials
  login(username: string, password: string): Observable<AuthResult>
  
  // Log out current user and clear tokens
  logout(): void
  
  // Get current authentication token
  getToken(): string | null
  
  // Check if user is authenticated
  isAuthenticated(): boolean
  
  // Observable stream of authentication state
  authState$: Observable<boolean>
}

interface AuthResult {
  success: boolean
  token?: string
  error?: string
}
```

**Implementation Details**:
- Use AWS Amplify library or AWS SDK for Cognito integration
- Store JWT token in browser's sessionStorage or localStorage
- Emit authentication state changes via RxJS Subject
- Handle token expiration and refresh logic

### 2. API Client Service (ApiService)

**Responsibility**: Communicate with tradeseeker-api-v2 REST API endpoints.

**Interface**:
```typescript
interface ApiService {
  // Fetch list of golden cross stocks for a market
  getGoldenCrosses(market: string): Observable<GoldenCrossResponse>
  
  // Fetch detailed stock data for a symbol
  getStockData(symbol: string): Observable<StockData>
  
  // Fetch full stock price history with EMAs from EODHD API
  getStockHistory(symbol: string, params?: HistoryParams): Observable<StockHistoryData>
  
  // Fetch multiple stocks concurrently
  getMultipleStocks(symbols: string[]): Observable<StockData[]>
}

interface HistoryParams {
  start_date?: string  // YYYY-MM-DD format
  end_date?: string    // YYYY-MM-DD format
  period?: 'd' | 'w' | 'm'  // daily, weekly, monthly
}

interface GoldenCrossResponse {
  market: string
  symbols: string[]
  timestamp: string
}

interface StockData {
  symbol: string
  prices: PricePoint[]
  emas: EMAData
  lastUpdated: string
}

interface StockHistoryData {
  symbol: string
  market_code: string
  period: string
  start_date: string
  end_date: string
  prices: PricePoint[]
  moving_averages: EMAPoint[]
  total_records: number
}

interface EMAPoint {
  date: string
  ema_7?: number
  ema_30?: number
  ema_50?: number
  ema_200?: number
}

interface PricePoint {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

interface EMAData {
  ema7: number[]
  ema30: number[]
  ema50: number[]
  ema200: number[]
}
```

**Implementation Details**:
- Use Angular HttpClient for HTTP requests
- Base URL: `https://56qpa0i92h.execute-api.ap-southeast-1.amazonaws.com/dev`
- Available endpoints:
  - `GET /golden-crosses?market={market}` - Get golden cross signals
  - `GET /stocks/{symbol}` - Get current stock data with EMAs
  - `GET /stocks/{symbol}/history` - Get full price history with EMAs from EODHD API
- Implement HTTP interceptor to automatically add Bearer token to all requests
- Implement retry logic (up to 2 retries) for failed requests
- Handle HTTP errors and map to user-friendly error messages
- Use RxJS operators (forkJoin, mergeMap) for concurrent requests

### 3. HTTP Interceptor (AuthInterceptor)

**Responsibility**: Automatically inject authentication token into all API requests.

**Interface**:
```typescript
interface AuthInterceptor implements HttpInterceptor {
  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>>
}
```

**Implementation Details**:
- Intercept all outgoing HTTP requests
- Add `Authorization: Bearer {token}` header if token exists
- Handle 401 Unauthorized responses by redirecting to login
- Clone requests to add headers (HttpRequest is immutable)

### 4. Dashboard Component

**Responsibility**: Main container component that orchestrates data fetching and chart display.

**Interface**:
```typescript
interface DashboardComponent {
  selectedMarket: string
  goldenCrosses: string[]
  stockDataMap: Map<string, StockData>
  isLoading: boolean
  error: string | null
  
  // Lifecycle hooks
  ngOnInit(): void
  
  // Event handlers
  onMarketChange(market: string): void
  onRefresh(): void
}
```

**Implementation Details**:
- Fetch golden cross list on initialization
- Fetch stock data for each symbol in the list
- Pass stock data to Chart Grid Component
- Handle loading states and errors
- Implement refresh functionality with debouncing

### 5. Chart Grid Component

**Responsibility**: Render responsive grid layout of stock charts.

**Interface**:
```typescript
interface ChartGridComponent {
  @Input() stockData: StockData[]
  
  // Computed properties
  gridColumns: number
}
```

**Implementation Details**:
- Use CSS Grid with `grid-template-columns: repeat(auto-fit, minmax(300px, 1fr))`
- Adjust grid columns based on viewport width using CSS media queries
- 27" monitor (2560px+): 6 columns
- Large desktop (1920px): 4-5 columns
- Medium desktop (1440px): 3 columns
- Tablet (768px): 2 columns
- Mobile (<768px): 1 column
- Iterate over stockData array and render Stock Chart Component for each

### 6. Stock Chart Component

**Responsibility**: Render individual stock chart with price data and EMA lines.

**Interface**:
```typescript
interface StockChartComponent {
  @Input() stockData: StockData
  
  chart: Chart | null
  
  // Lifecycle hooks
  ngOnInit(): void
  ngOnChanges(changes: SimpleChanges): void
  ngOnDestroy(): void
  
  // Chart rendering
  renderChart(): void
  updateChart(): void
}
```

**Implementation Details**:
- Use Chart.js library for rendering
- Chart type: Candlestick (via chartjs-chart-financial plugin) or Line chart
- Render 4 EMA lines with distinct colors:
  - EMA 7: Blue
  - EMA 30: Orange
  - EMA 50: Green
  - EMA 200: Red
- Display symbol name as chart title
- Handle loading and error states
- Destroy chart instance on component destroy to prevent memory leaks
- Update chart when input data changes

### 7. Market Selector Component

**Responsibility**: Allow users to select different stock markets.

**Interface**:
```typescript
interface MarketSelectorComponent {
  @Input() selectedMarket: string
  @Output() marketChange: EventEmitter<string>
  
  markets: string[]
  
  onMarketSelect(market: string): void
}
```

**Implementation Details**:
- Display dropdown or button group for market selection
- Available markets: ["US", "SG"] (can be extended)
- Emit marketChange event when selection changes
- Highlight currently selected market

### 8. Login Component

**Responsibility**: Provide user interface for authentication.

**Interface**:
```typescript
interface LoginComponent {
  username: string
  password: string
  isLoading: boolean
  error: string | null
  
  onSubmit(): void
}
```

**Implementation Details**:
- Form with username and password fields
- Call AuthService.login() on form submission
- Display loading indicator during authentication
- Display error messages on authentication failure
- Redirect to dashboard on successful authentication
- Use Angular Reactive Forms for form validation

## Data Models

### Authentication Models

```typescript
// Cognito user credentials
interface Credentials {
  username: string
  password: string
}

// Authentication result from Cognito
interface CognitoAuthResult {
  accessToken: string
  idToken: string
  refreshToken: string
  expiresIn: number
}

// Stored authentication state
interface AuthState {
  isAuthenticated: boolean
  token: string | null
  expiresAt: number | null
}
```

### API Response Models

```typescript
// Golden cross list response
interface GoldenCrossResponse {
  market: string
  symbols: string[]
  timestamp: string
}

// Stock data response (current data with EMAs)
interface StockDataResponse {
  symbol: string
  prices: PricePoint[]
  emas: {
    ema7: number[]
    ema30: number[]
    ema50: number[]
    ema200: number[]
  }
  lastUpdated: string
}

// Stock history response (full history from EODHD API)
interface StockHistoryResponse {
  symbol: string
  market_code: string
  period: string
  start_date: string
  end_date: string
  prices: PricePoint[]
  moving_averages: EMAPoint[]
  total_records: number
}

// EMA data point with calculated values
interface EMAPoint {
  date: string
  ema_7?: number
  ema_30?: number
  ema_50?: number
  ema_200?: number
}

// Price point for candlestick chart
interface PricePoint {
  date: string  // ISO 8601 format
  open: number
  high: number
  low: number
  close: number
  volume: number
}
```

### Chart Configuration Models

```typescript
// Chart.js configuration
interface ChartConfig {
  type: 'candlestick' | 'line'
  data: ChartData
  options: ChartOptions
}

interface ChartData {
  labels: string[]  // Dates
  datasets: ChartDataset[]
}

interface ChartDataset {
  label: string
  data: number[] | PricePoint[]
  borderColor?: string
  backgroundColor?: string
  borderWidth?: number
}
```

### State Management Models

```typescript
// Application state
interface AppState {
  auth: AuthState
  dashboard: DashboardState
}

interface DashboardState {
  selectedMarket: string
  goldenCrosses: string[]
  stockData: Map<string, StockData>
  isLoading: boolean
  error: string | null
  lastRefresh: Date | null
}
```

## Data Flow

### Authentication Flow

```
User → Login Component → Auth Service → AWS Cognito
                              ↓
                        Store JWT Token
                              ↓
                    Navigate to Dashboard
```

**Detailed Steps**:
1. User enters credentials in Login Component
2. Login Component calls AuthService.login(username, password)
3. Auth Service authenticates with AWS Cognito
4. Cognito returns JWT tokens (access, id, refresh)
5. Auth Service stores token in browser storage
6. Auth Service emits authentication state change
7. Router navigates to /dashboard

### Data Fetching Flow

```
Dashboard Component
    ↓
    ├─→ API Service.getGoldenCrosses("US")
    │       ↓
    │   GET /golden-crosses?market=US → API
    │       ↓
    │   Returns: {symbols: ["AAPL", "MSFT", ...]}
    │
    └─→ For each symbol:
            ↓
        API Service.getStockData(symbol)
            ↓
        GET /stocks/{symbol} → API
            ↓
        Returns: StockData (prices, EMAs)
            ↓
        Dashboard collects all StockData
            ↓
        Pass to Chart Grid Component
            ↓
        Chart Grid renders Stock Chart Components
```

**Detailed Steps**:
1. Dashboard component initializes
2. Calls ApiService.getGoldenCrosses("US")
3. API Service makes GET request to /golden-crosses?market=US
4. API returns list of symbols
5. Dashboard loops through symbols
6. For each symbol, calls ApiService.getStockData(symbol)
7. API Service makes GET request to /stocks/{symbol}
8. API returns stock data with prices and EMAs
9. Dashboard collects all stock data
10. Passes array to Chart Grid Component
11. Chart Grid renders individual Stock Chart Components

### HTTP Interceptor Flow

```
API Service makes HTTP Request
    ↓
Auth Interceptor intercepts
    ↓
Get token from Auth Service
    ↓
Add "Authorization: Bearer {token}" header
    ↓
Forward request to API
    ↓
    ├─→ Success (200 OK)
    │       ↓
    │   Return response to API Service
    │
    └─→ Unauthorized (401)
            ↓
        Auth Service.logout()
            ↓
        Clear stored token
            ↓
        Navigate to /login
```

**Detailed Steps**:
1. API Service initiates HTTP request
2. Auth Interceptor intercepts the request
3. Interceptor calls AuthService.getToken()
4. Auth Service returns JWT token
5. Interceptor clones request and adds Authorization header
6. Modified request sent to API
7. If response is 200 OK, return to API Service
8. If response is 401 Unauthorized:
   - Call AuthService.logout()
   - Clear stored token
   - Navigate to /login route


## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property Reflection

After analyzing all acceptance criteria, I've identified the following redundancies to eliminate:

1. **Authentication token handling**: Multiple properties (1.2, 1.3, 2.1, 3.1, 6.2) test token storage and header inclusion. These can be consolidated into comprehensive properties about token lifecycle.

2. **Error display**: Properties 2.3, 5.7, 9.1, 9.2 all test error message display. These can be combined into a general error handling property.

3. **Loading indicators**: Properties 5.6, 7.2, 9.4 all test loading state display. These are redundant and can be combined.

4. **API error handling**: Properties 2.4, 6.4, 6.5 all test HTTP error responses. These can be consolidated into comprehensive error handling properties.

5. **Chart rendering**: Properties 5.1, 5.2, 5.3 all test chart rendering with different data. These can be combined into a comprehensive chart rendering property.

### Authentication Properties

**Property 1: Authentication token lifecycle**
*For any* valid Cognito credentials, successful authentication should result in a JWT token being stored in browser storage, and that token should be included in the Authorization header as "Bearer {token}" for all subsequent API requests.
**Validates: Requirements 1.2, 1.3, 2.1, 3.1, 6.2**

**Property 2: Authentication state navigation**
*For any* authentication state change, the application should navigate to the appropriate route: authenticated users to dashboard, unauthenticated users to login, and expired token users to login.
**Validates: Requirements 1.4, 1.6**

**Property 3: Logout clears authentication**
*For any* authenticated session, calling logout should clear the stored token from browser storage and navigate to the login route.
**Validates: Requirements 1.7**

**Property 4: Failed authentication handling**
*For any* invalid credentials, authentication should fail, display an error message, and keep the user on the login form without storing any token.
**Validates: Requirements 1.5**

### API Communication Properties

**Property 5: Golden cross API request format**
*For any* market parameter, requesting golden crosses should make a GET request to `/golden-crosses` with the market as a query parameter and the Bearer token in the Authorization header.
**Validates: Requirements 2.1, 2.5**

**Property 6: API response parsing**
*For any* valid API response containing stock symbols or stock data, the application should successfully parse all required fields (symbols, prices, EMA values) without errors.
**Validates: Requirements 2.2, 3.2**

**Property 7: HTTP error handling**
*For any* HTTP error response (4xx or 5xx), the application should handle it gracefully: 401 errors redirect to login, other errors display user-friendly messages and log details to console.
**Validates: Requirements 2.3, 2.4, 6.4, 6.5**

**Property 8: API base URL consistency**
*For any* API request, the request URL should start with the base URL `https://56qpa0i92h.execute-api.ap-southeast-1.amazonaws.com/dev`.
**Validates: Requirements 6.1**

**Property 9: Request retry on timeout**
*For any* API request that times out, the application should retry the request exactly 2 additional times before failing.
**Validates: Requirements 6.3**

**Property 10: Concurrent request management**
*For any* list of stock symbols, fetching stock data should manage concurrency appropriately, not overwhelming the API with unlimited simultaneous requests.
**Validates: Requirements 6.6**

### Stock Data Retrieval Properties

**Property 11: Multiple stock data requests**
*For any* list of symbols from the golden cross response, the application should make individual GET requests to `/stocks/{symbol}` for each symbol with the Bearer token.
**Validates: Requirements 3.1**

**Property 12: Stock history data retrieval**
*For any* stock symbol and optional date range parameters, requesting stock history should make a GET request to `/stocks/{symbol}/history` with query parameters and return full price history with calculated EMAs from EODHD API.
**Validates: New stock history endpoint functionality**

**Property 13: Partial failure resilience**
*For any* list of stock symbols where some requests fail, the application should continue processing remaining symbols and render charts for successfully fetched data.
**Validates: Requirements 3.3**

**Property 14: Chart rendering after data load**
*For any* set of successfully fetched stock data, once all requests complete, the application should render the Chart Grid with all available data.
**Validates: Requirements 3.4**

### Responsive Layout Properties

**Property 15: Responsive grid columns**
*For any* viewport width, the chart grid should display an appropriate number of columns: 6 for large monitors (2560px+), 4-5 for desktops (1920px), 3 for medium (1440px), 2 for tablets (768px), and 1 for mobile (<768px).
**Validates: Requirements 4.1, 4.2**

**Property 16: Dynamic layout reflow**
*For any* browser window resize event, the chart grid should reflow the layout to match the new viewport width without requiring a page reload.
**Validates: Requirements 4.5**

### Chart Display Properties

**Property 17: Complete chart rendering**
*For any* stock data with symbol, prices, and EMA values, the rendered chart should display the symbol name, price data as a candlestick or line chart, and all four EMA lines (7, 30, 50, 200) with distinct colors.
**Validates: Requirements 5.1, 5.2, 5.3, 5.4**

**Property 18: Chart state indicators**
*For any* stock chart, the component should display appropriate state indicators: loading indicator while data is fetching, error state with symbol name when data fails to load, and rendered chart when data is available.
**Validates: Requirements 5.6, 5.7**

### Data Refresh Properties

**Property 19: Manual refresh triggers data fetch**
*For any* dashboard state, clicking the refresh button should trigger a new fetch of the golden cross list and stock data for all symbols.
**Validates: Requirements 7.1**

**Property 20: Refresh loading state**
*For any* refresh operation in progress, the application should display a loading indicator and prevent duplicate refresh requests until the current refresh completes.
**Validates: Requirements 7.2, 7.4**

**Property 21: Automatic refresh interval**
*For any* configured refresh interval (default 5 minutes), when automatic refresh is enabled, the application should automatically fetch new data at that interval.
**Validates: Requirements 7.3**

**Property 22: Chart updates after refresh**
*For any* completed refresh operation, all stock charts should update to display the newly fetched data.
**Validates: Requirements 7.5**

### Market Selection Properties

**Property 23: Market change triggers new data fetch**
*For any* market selection change, the application should clear existing chart data and fetch the golden cross list for the newly selected market.
**Validates: Requirements 8.2, 8.3**

**Property 24: Market selection persistence**
*For any* market selection made during a user session, the selection should be persisted and restored if the user navigates within the application.
**Validates: Requirements 8.5**

### Error Handling Properties

**Property 25: Comprehensive error display**
*For any* error (network, authentication, API), the application should display a user-friendly error message with actionable guidance (e.g., "Retry", "Login Again") and log detailed error information to the browser console.
**Validates: Requirements 9.1, 9.2, 9.3, 9.6**

**Property 26: Error clearing on success**
*For any* operation that succeeds after a previous error, the application should clear the previous error message from the UI.
**Validates: Requirements 9.5**

### Edge Cases and Examples

**Edge Case 1: Empty golden cross list**
When the API returns an empty list of golden cross symbols, the application should display a message indicating no golden crosses are currently available.
**Validates: Requirements 2.6**

**Edge Case 2: Incomplete stock data**
When stock data is missing required fields (e.g., missing EMA values), the application should handle it gracefully and display available data without crashing.
**Validates: Requirements 3.5**

**Edge Case 3: Mobile viewport**
When the viewport width is mobile-sized (<768px), the chart grid should display exactly 1 chart per row.
**Validates: Requirements 4.3**

**Example 1: Large monitor layout**
When the viewport width corresponds to a 27-inch monitor (2560px+), the chart grid should display exactly 6 charts per row.
**Validates: Requirements 4.1**

**Example 2: Default market selection**
When the dashboard loads for the first time, the application should default to the "US" market.
**Validates: Requirements 8.1**

## Error Handling

### Authentication Errors

**Token Expiration**:
- Monitor token expiration time
- Proactively refresh tokens before expiration when possible
- On 401 responses, clear stored token and redirect to login
- Display message: "Your session has expired. Please log in again."

**Invalid Credentials**:
- Display specific error from Cognito (e.g., "Incorrect username or password")
- Do not store any token
- Keep user on login form
- Clear password field for security

**Network Errors During Auth**:
- Display message: "Unable to connect to authentication service. Please check your internet connection."
- Provide retry option

### API Errors

**HTTP 401 Unauthorized**:
- Clear stored token
- Redirect to login
- Display message: "Your session has expired. Please log in again."

**HTTP 404 Not Found**:
- Log error with symbol/endpoint details
- Display message: "Stock data not found for {symbol}"
- Continue processing other symbols

**HTTP 5xx Server Errors**:
- Log full error details to console
- Display message: "Server error occurred. Please try again later."
- Implement exponential backoff for retries

**Network Timeout**:
- Retry up to 2 times with increasing timeout
- Display message: "Request timed out. Retrying..."
- After all retries fail: "Unable to fetch data. Please check your connection."

**Network Offline**:
- Detect offline state using browser API
- Display message: "You are offline. Please check your internet connection."
- Disable refresh and data fetch operations

### Data Errors

**Malformed API Response**:
- Log parsing error with response details
- Display message: "Received invalid data from server"
- Skip the malformed data and continue with other symbols

**Missing Required Fields**:
- Log warning about missing fields
- Render chart with available data
- Display note on chart: "Some data unavailable"

**Empty Data Sets**:
- Display message: "No golden cross signals found for {market}"
- Show empty state UI with refresh option

### Chart Rendering Errors

**Chart.js Initialization Failure**:
- Log error details
- Display error state in chart component
- Show message: "Unable to render chart for {symbol}"

**Invalid Price Data**:
- Validate price data before rendering
- Skip invalid data points
- Log warning about data quality issues

### Concurrency Errors

**Duplicate Refresh Requests**:
- Use flag to track refresh in progress
- Ignore subsequent refresh requests while one is active
- Display message: "Refresh already in progress"

**Race Conditions**:
- Use RxJS operators (switchMap, takeUntil) to cancel previous requests
- Ensure only latest market selection data is displayed
- Cancel pending requests when component is destroyed

## Testing Strategy

### Dual Testing Approach

The application will use both unit tests and property-based tests to ensure comprehensive coverage:

- **Unit tests**: Verify specific examples, edge cases, error conditions, and component integration
- **Property tests**: Verify universal properties across all inputs using randomized test data

### Unit Testing

**Framework**: Jasmine + Karma (Angular default testing stack)

**Focus Areas**:
- Component lifecycle and initialization
- User interactions (button clicks, form submissions)
- Navigation and routing
- Error state rendering
- Edge cases (empty data, missing fields, mobile viewport)
- Integration between components and services

**Example Unit Tests**:
- Login component displays error message when authentication fails
- Dashboard component shows empty state when golden cross list is empty
- Chart component displays loading indicator while data is fetching
- Market selector emits correct event when selection changes
- HTTP interceptor adds Authorization header to requests

### Property-Based Testing

**Framework**: fast-check (TypeScript property-based testing library)

**Configuration**:
- Minimum 100 iterations per property test
- Each test tagged with: `Feature: tradeseeker-web-v2, Property {number}: {property_text}`
- Use custom generators for domain models (StockData, PricePoint, etc.)

**Property Test Implementation**:

Each correctness property from the design document should be implemented as a single property-based test. For example:

```typescript
// Property 1: Authentication token lifecycle
it('Feature: tradeseeker-web-v2, Property 1: Authentication token lifecycle', () => {
  fc.assert(
    fc.property(
      fc.record({
        username: fc.string(),
        password: fc.string()
      }),
      (credentials) => {
        // Test that valid credentials result in token storage and header inclusion
        // ... test implementation
      }
    ),
    { numRuns: 100 }
  );
});
```

**Custom Generators**:
- `fc.stockSymbol()`: Generate valid stock symbols
- `fc.pricePoint()`: Generate valid price data points
- `fc.emaData()`: Generate valid EMA arrays
- `fc.stockData()`: Generate complete stock data objects
- `fc.viewportWidth()`: Generate viewport widths for responsive testing

**Property Test Focus**:
- Authentication token handling across different credentials
- API request formatting with various parameters
- Response parsing with randomized valid data
- Stock history endpoint with various date ranges and periods
- Error handling with various error types
- Responsive layout with different viewport sizes
- Chart rendering with randomized stock data
- Refresh and market selection with various states

### Integration Testing

**Framework**: Cypress or Playwright for E2E testing

**Focus Areas**:
- Complete user flows (login → dashboard → view charts)
- API integration with mocked backend
- Stock history data fetching and display
- Responsive behavior across device sizes
- Error recovery flows

### Test Coverage Goals

- Unit test coverage: >80% for services and components
- Property test coverage: All 26 correctness properties implemented
- E2E test coverage: All critical user flows
- Edge case coverage: All identified edge cases tested

### Continuous Integration

- Run all tests on every commit
- Block merges if tests fail
- Generate coverage reports
- Run E2E tests on staging environment before production deployment
