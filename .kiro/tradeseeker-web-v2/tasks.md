# Implementation Plan: TradeSeekerWeb v2

## Overview

This implementation plan covers the complete Angular application development for TradeSeekerWeb v2, including authentication, API integration, chart rendering, responsive layout, and deployment infrastructure. The application will authenticate users via AWS Cognito, fetch golden cross stock data from the tradeseeker-api-v2 REST API, display interactive charts in a responsive grid, and deploy as a static website on S3 with CloudFront CDN.

## Tasks

- [x] 1. Set up Angular project structure and core configuration
  - Create Angular project with routing and SCSS support
  - Set up folder structure (core/, features/, shared/)
  - Install dependencies: Chart.js, chartjs-chart-financial, AWS Amplify, RxJS
  - Configure TypeScript strict mode and compiler options
  - Create environment configuration files with API base URL and Cognito settings
  - _Requirements: 1.1, 6.1_

- [x] 2. Implement core data models and interfaces
  - Create auth.models.ts with Credentials, AuthResult, AuthState interfaces
  - Create api.models.ts with GoldenCrossResponse, StockData, PricePoint, EMAData interfaces
  - Create chart.models.ts with ChartConfig, ChartData, ChartDataset interfaces
  - Define AppState and DashboardState interfaces for state management
  - _Requirements: 1.1, 2.1, 3.1, 5.1_

- [x] 3. Implement Authentication Service
  - [x] 3.1 Create AuthService with AWS Cognito integration
    - Implement login() method using AWS Amplify Auth
    - Implement logout() method to clear tokens and state
    - Implement getToken() method to retrieve stored JWT token
    - Implement isAuthenticated() method to check auth state
    - Create authState$ Observable for reactive auth state changes
    - Store JWT token in sessionStorage
    - _Requirements: 1.2, 1.3, 1.7_

  - [ ]* 3.2 Write property test for authentication token lifecycle
    - **Property 1: Authentication token lifecycle**
    - **Validates: Requirements 1.2, 1.3, 2.1, 3.1, 6.2**

  - [ ]* 3.3 Write unit tests for AuthService
    - Test successful login stores token and updates auth state
    - Test failed login does not store token
    - Test logout clears token and updates auth state
    - Test token expiration handling
    - _Requirements: 1.2, 1.3, 1.5, 1.6, 1.7_

- [x] 4. Implement HTTP Interceptor for authentication
  - [x] 4.1 Create AuthInterceptor to inject Bearer token
    - Intercept all HTTP requests
    - Get token from AuthService
    - Clone request and add Authorization header with Bearer token
    - Handle 401 Unauthorized responses by calling logout and redirecting to login
    - _Requirements: 1.6, 2.1, 2.4, 3.1, 6.2_

  - [ ]* 4.2 Write unit tests for AuthInterceptor
    - Test Authorization header is added when token exists
    - Test 401 response triggers logout and redirect
    - Test requests without token proceed normally
    - _Requirements: 1.6, 2.4, 6.2_

- [x] 5. Implement API Client Service
  - [x] 5.1 Create ApiService with HTTP client methods
    - Implement getGoldenCrosses(market: string) method
    - Implement getStockData(symbol: string) method
    - Implement getMultipleStocks(symbols: string[]) using forkJoin
    - Configure base URL from environment configuration
    - Implement retry logic (up to 2 retries) using RxJS retry operator
    - Implement error handling and mapping to user-friendly messages
    - _Requirements: 2.1, 2.5, 3.1, 6.1, 6.3, 6.4, 6.5, 6.6_

  - [ ]* 5.2 Write property test for API request format
    - **Property 5: Golden cross API request format**
    - **Validates: Requirements 2.1, 2.5**

  - [ ]* 5.3 Write property test for API response parsing
    - **Property 6: API response parsing**
    - **Validates: Requirements 2.2, 3.2**

  - [ ]* 5.4 Write property test for HTTP error handling
    - **Property 7: HTTP error handling**
    - **Validates: Requirements 2.3, 2.4, 6.4, 6.5**

  - [ ]* 5.5 Write unit tests for ApiService
    - Test getGoldenCrosses makes correct API call with market parameter
    - Test getStockData makes correct API call with symbol
    - Test retry logic on timeout
    - Test error handling for 4xx and 5xx responses
    - _Requirements: 2.1, 2.2, 2.3, 3.1, 6.3, 6.4, 6.5_

- [x] 6. Implement authentication guard and routing
  - [x] 6.1 Create AuthGuard to protect dashboard route
    - Check authentication state using AuthService
    - Redirect to /login if not authenticated
    - Allow access to /dashboard if authenticated
    - _Requirements: 1.1, 1.4_

  - [x] 6.2 Configure app routing module
    - Define /login route for LoginComponent
    - Define /dashboard route for DashboardComponent with AuthGuard
    - Set default redirect to /dashboard
    - Configure PathLocationStrategy for clean URLs
    - _Requirements: 1.1, 1.4_

  - [ ]* 6.3 Write unit tests for AuthGuard
    - Test authenticated users can access dashboard
    - Test unauthenticated users redirect to login
    - _Requirements: 1.1, 1.4_

- [x] 7. Implement Login Component
  - [x] 7.1 Create LoginComponent with form and authentication logic
    - Create reactive form with username and password fields
    - Implement form validation (required fields)
    - Implement onSubmit() method to call AuthService.login()
    - Display loading indicator during authentication
    - Display error messages on authentication failure
    - Navigate to /dashboard on successful authentication
    - _Requirements: 1.1, 1.2, 1.4, 1.5_

  - [x] 7.2 Create login component template and styles
    - Design login form with username and password inputs
    - Add submit button with loading state
    - Add error message display area
    - Style form for clean, professional appearance
    - _Requirements: 1.1, 1.5_

  - [ ]* 7.3 Write property test for authentication state navigation
    - **Property 2: Authentication state navigation**
    - **Validates: Requirements 1.4, 1.6**

  - [ ]* 7.4 Write unit tests for LoginComponent
    - Test form validation prevents submission with empty fields
    - Test successful login navigates to dashboard
    - Test failed login displays error message
    - Test loading indicator shows during authentication
    - _Requirements: 1.1, 1.2, 1.4, 1.5_

- [x] 8. Checkpoint - Authentication and API foundation complete
  - Verify login flow works end-to-end
  - Verify API service can make authenticated requests
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Implement shared UI components
  - [x] 9.1 Create LoadingSpinnerComponent
    - Create component with animated spinner
    - Style spinner for visibility and aesthetics
    - _Requirements: 5.6, 7.2, 9.4_

  - [x] 9.2 Create ErrorMessageComponent
    - Create component with @Input() for error message
    - Create component with @Input() for actionable guidance
    - Style error message for visibility
    - Add retry button or action button based on guidance
    - _Requirements: 2.3, 5.7, 9.1, 9.2, 9.6_

- [x] 10. Implement Market Selector Component
  - [x] 10.1 Create MarketSelectorComponent
    - Create component with @Input() selectedMarket
    - Create component with @Output() marketChange EventEmitter
    - Define markets array: ["US", "SG"]
    - Implement onMarketSelect() method to emit marketChange event
    - _Requirements: 8.1, 8.2, 8.4_

  - [x] 10.2 Create market selector template and styles
    - Design dropdown or button group for market selection
    - Highlight currently selected market
    - Style for clean appearance
    - _Requirements: 8.1, 8.4_

  - [ ]* 10.3 Write unit tests for MarketSelectorComponent
    - Test marketChange event emits when selection changes
    - Test selected market is highlighted
    - _Requirements: 8.2, 8.4_

- [x] 10a. Implement Chart Display Mode Selector Component
  - [x] 10a.1 Create ChartDisplayModeSelectorComponent
    - Create component with @Input() selectedMode ('prices' | 'ema' | 'both')
    - Create component with @Output() modeChange EventEmitter
    - Define displayModes array: [{ value: 'both', label: 'Both' }, { value: 'prices', label: 'Prices Only' }, { value: 'ema', label: 'EMA Only' }]
    - Implement onModeSelect() method to emit modeChange event
    - _Requirements: 5.8, 5.9_

  - [x] 10a.2 Create chart display mode selector template and styles
    - Design radio button group for display mode selection
    - Highlight currently selected mode
    - Style with modern radio button appearance (hidden input, styled labels)
    - Add hover and selected states
    - _Requirements: 5.8, 5.9_

  - [ ]* 10a.3 Write unit tests for ChartDisplayModeSelectorComponent
    - Test modeChange event emits when selection changes
    - Test selected mode is highlighted
    - _Requirements: 5.8, 5.9_

- [x] 10b. Implement Chart Type Selector Component
  - [x] 10b.1 Create ChartTypeSelectorComponent
    - Create component with @Input() selectedType ('candlestick' | 'line')
    - Create component with @Output() typeChange EventEmitter
    - Define chartTypes array: [{ value: 'candlestick', label: 'Candlestick' }, { value: 'line', label: 'Line' }]
    - Implement onTypeSelect() method to emit typeChange event
    - _Requirements: 5.10, 5.11, 5.12_

  - [x] 10b.2 Create chart type selector template and styles
    - Design radio button group for chart type selection
    - Highlight currently selected type
    - Style with modern radio button appearance (hidden input, styled labels)
    - Add hover and selected states
    - _Requirements: 5.10, 5.11, 5.12_

  - [ ]* 10b.3 Write unit tests for ChartTypeSelectorComponent
    - Test typeChange event emits when selection changes
    - Test selected type is highlighted
    - _Requirements: 5.10, 5.11, 5.12_

- [x] 11. Implement Stock Chart Component
  - [x] 11.1 Create StockChartComponent with Chart.js integration
    - Create component with @Input() stockData
    - Create component with @Input() displayMode ('prices' | 'ema' | 'both')
    - Create component with @Input() chartType ('candlestick' | 'line')
    - Initialize Chart.js instance in ngOnInit()
    - Implement renderChart() method to create chart based on displayMode and chartType
    - Implement getDatasets() method to conditionally include price and/or EMA data
    - Implement getChartType() method to determine Chart.js chart type
    - For candlestick: render OHLC data with chartjs-chart-financial
    - For line: render close prices only as line chart
    - Overlay EMA lines (7, 30, 50, 200) with distinct colors (blue, orange, green, red)
    - Display symbol name as chart title
    - Handle loading state with LoadingSpinnerComponent
    - Handle error state with ErrorMessageComponent
    - Destroy chart instance in ngOnDestroy() to prevent memory leaks
    - Update chart when stockData, displayMode, or chartType input changes (ngOnChanges)
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10, 5.11, 5.12_

  - [x] 11.2 Create stock chart template and styles
    - Create canvas element for Chart.js rendering
    - Add loading and error state containers
    - Style chart container for responsive sizing
    - _Requirements: 5.1, 5.5, 5.6, 5.7_

  - [ ]* 11.3 Write property test for complete chart rendering
    - **Property 16: Complete chart rendering**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4**

  - [ ]* 11.4 Write property test for chart state indicators
    - **Property 17: Chart state indicators**
    - **Validates: Requirements 5.6, 5.7**

  - [ ]* 11.5 Write unit tests for StockChartComponent
    - Test chart renders with valid stock data
    - Test candlestick chart displays OHLC data
    - Test line chart displays close prices only
    - Test display mode 'prices' shows only price data
    - Test display mode 'ema' shows only EMA lines
    - Test display mode 'both' shows prices and EMA lines
    - Test loading indicator displays while data is loading
    - Test error state displays when data fails to load
    - Test chart updates when input data changes
    - Test chart updates when displayMode changes
    - Test chart updates when chartType changes
    - Test chart instance is destroyed on component destroy
    - _Requirements: 5.1, 5.2, 5.3, 5.6, 5.7, 5.8, 5.9, 5.10, 5.11, 5.12_

- [x] 12. Implement Chart Grid Component
  - [x] 12.1 Create ChartGridComponent with responsive layout
    - Create component with @Input() stockData array
    - Create component with @Input() displayMode ('prices' | 'ema' | 'both')
    - Create component with @Input() chartType ('candlestick' | 'line')
    - Iterate over stockData and render StockChartComponent for each
    - Pass displayMode and chartType to each StockChartComponent
    - Use CSS Grid for responsive layout
    - Configure grid columns based on viewport width using media queries
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 5.8, 5.9, 5.10, 5.11, 5.12_

  - [x] 12.2 Create chart grid template and styles
    - Create container with CSS Grid layout
    - Configure grid-template-columns: repeat(auto-fit, minmax(300px, 1fr))
    - Add media queries for responsive columns:
      - 2560px+: 6 columns
      - 1920px: 4-5 columns
      - 1440px: 3 columns
      - 768px: 2 columns
      - <768px: 1 column
    - Style grid for proper spacing and alignment
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [ ]* 12.3 Write property test for responsive grid columns
    - **Property 14: Responsive grid columns**
    - **Validates: Requirements 4.1, 4.2**

  - [ ]* 12.4 Write property test for dynamic layout reflow
    - **Property 15: Dynamic layout reflow**
    - **Validates: Requirements 4.5**

  - [ ]* 12.5 Write unit tests for ChartGridComponent
    - Test grid renders correct number of charts
    - Test responsive layout adjusts to viewport width
    - Test displayMode is passed to child charts
    - Test chartType is passed to child charts
    - _Requirements: 4.1, 4.2, 4.5, 5.8, 5.9, 5.10, 5.11, 5.12_

- [x] 13. Implement Dashboard Component
  - [x] 13.1 Create DashboardComponent with data orchestration
    - Create component with selectedMarket property (default: "US")
    - Create component with selectedDisplayMode property (default: "both")
    - Create component with selectedChartType property (default: "candlestick")
    - Create component with goldenCrosses, stockDataMap, isLoading, error properties
    - Implement ngOnInit() to fetch golden cross list and stock data
    - Restore selectedMarket, selectedDisplayMode, and selectedChartType from sessionStorage
    - Implement onMarketChange() to handle market selection changes
    - Implement onDisplayModeChange() to handle display mode changes and persist to sessionStorage
    - Implement onChartTypeChange() to handle chart type changes and persist to sessionStorage
    - Implement onRefresh() to manually refresh data
    - Implement automatic refresh with configurable interval (default: 5 minutes)
    - Use RxJS operators (switchMap, forkJoin) for data fetching
    - Handle loading states and errors
    - Pass stock data array, displayMode, and chartType to ChartGridComponent
    - _Requirements: 2.1, 2.2, 2.6, 3.1, 3.3, 3.4, 5.8, 5.9, 5.10, 5.11, 5.12, 7.1, 7.3, 8.1, 8.2, 8.3_

  - [x] 13.2 Create dashboard template and styles
    - Add MarketSelectorComponent with event binding
    - Add ChartDisplayModeSelectorComponent with event binding
    - Add ChartTypeSelectorComponent with event binding
    - Add refresh button with click handler
    - Add LoadingSpinnerComponent for loading state
    - Add ErrorMessageComponent for error state
    - Add ChartGridComponent with stockData, displayMode, and chartType inputs
    - Add empty state message for no golden crosses
    - Style dashboard header with controls in a row
    - Style dashboard for clean layout
    - _Requirements: 2.6, 5.8, 5.9, 5.10, 5.11, 5.12, 7.1, 8.1, 8.2, 9.1, 9.4_

  - [ ]* 13.3 Write property test for market change triggers data fetch
    - **Property 22: Market change triggers new data fetch**
    - **Validates: Requirements 8.2, 8.3**

  - [ ]* 13.4 Write property test for manual refresh
    - **Property 18: Manual refresh triggers data fetch**
    - **Validates: Requirements 7.1**

  - [ ]* 13.5 Write property test for refresh loading state
    - **Property 19: Refresh loading state**
    - **Validates: Requirements 7.2, 7.4**

  - [ ]* 13.6 Write property test for automatic refresh interval
    - **Property 20: Automatic refresh interval**
    - **Validates: Requirements 7.3**

  - [ ]* 13.7 Write unit tests for DashboardComponent
    - Test component fetches golden crosses on initialization
    - Test component fetches stock data for each symbol
    - Test market change clears existing data and fetches new data
    - Test display mode change updates charts without refetching data
    - Test chart type change updates charts without refetching data
    - Test display mode persists to sessionStorage
    - Test chart type persists to sessionStorage
    - Test refresh button triggers data fetch
    - Test automatic refresh works at configured interval
    - Test empty state displays when no golden crosses
    - Test error state displays on API failure
    - _Requirements: 2.1, 2.2, 2.6, 3.1, 5.8, 5.9, 5.10, 5.11, 5.12, 7.1, 7.3, 8.2, 8.3_

- [x] 14. Checkpoint - Core application features complete
  - Verify dashboard displays charts for golden cross stocks
  - Verify market selection changes displayed data
  - Verify refresh functionality works
  - Ensure all tests pass, ask the user if questions arise.

- [x] 15. Implement comprehensive error handling
  - [x] 15.1 Add error handling to AuthService
    - Handle token expiration with proactive refresh
    - Handle invalid credentials with specific error messages
    - Handle network errors during authentication
    - _Requirements: 1.5, 1.6, 9.1, 9.2_

  - [x] 15.2 Add error handling to ApiService
    - Handle 401 Unauthorized (redirect to login)
    - Handle 404 Not Found (log and continue with other symbols)
    - Handle 5xx Server Errors (display user-friendly message)
    - Handle network timeout (retry with exponential backoff)
    - Handle network offline state
    - Handle malformed API responses
    - Handle missing required fields in data
    - _Requirements: 2.3, 2.4, 3.3, 3.5, 6.3, 6.4, 6.5, 9.1, 9.2, 9.3_

  - [x] 15.3 Add error handling to chart components
    - Handle Chart.js initialization failures
    - Handle invalid price data
    - Validate data before rendering
    - _Requirements: 3.5, 5.7_

  - [ ]* 15.4 Write property test for comprehensive error display
    - **Property 24: Comprehensive error display**
    - **Validates: Requirements 9.1, 9.2, 9.3, 9.6**

  - [ ]* 15.5 Write property test for error clearing on success
    - **Property 25: Error clearing on success**
    - **Validates: Requirements 9.5**

- [x] 16. Implement state management and concurrency control
  - [x] 16.1 Add concurrency control to ApiService
    - Limit concurrent stock data requests to avoid overwhelming API
    - Use RxJS mergeMap with concurrency parameter
    - _Requirements: 6.6_

  - [x] 16.2 Add duplicate request prevention to DashboardComponent
    - Use flag to track refresh in progress
    - Ignore duplicate refresh requests while one is active
    - Use RxJS switchMap to cancel previous requests on market change
    - Cancel pending requests when component is destroyed (takeUntil)
    - _Requirements: 7.4, 8.3_

  - [x] 16.3 Add session persistence for user preferences
    - Store selected market in sessionStorage
    - Store selected display mode in sessionStorage
    - Store selected chart type in sessionStorage
    - Restore all preferences on component initialization
    - _Requirements: 8.5_

  - [ ]* 16.4 Write property test for concurrent request management
    - **Property 10: Concurrent request management**
    - **Validates: Requirements 6.6**

  - [ ]* 16.5 Write property test for market selection persistence
    - **Property 23: Market selection persistence**
    - **Validates: Requirements 8.5**

- [x] 17. Implement property-based test generators
  - Create custom generators in tests/property/generators/
  - Implement stock-data.generator.ts with generators for StockData, PricePoint, EMAData
  - Implement auth.generator.ts with generators for Credentials, AuthResult
  - Implement viewport.generator.ts with generator for viewport widths
  - Configure fast-check with 100 iterations per test
  - _Requirements: All requirements (testing infrastructure)_

- [x] 18. Checkpoint - Application complete and tested
  - Verify all features work end-to-end
  - Verify all unit tests pass
  - Verify all property tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 19. Set up Terraform infrastructure configuration
  - Create terraform/ directory structure
  - Configure AWS provider and backend
  - Define input variables for bucket name, environment, and region
  - Define outputs for S3 bucket name, website endpoint, CloudFront domain, and distribution ID
  - _Requirements: 10.1, 10.2, 10.3_

- [ ] 20. Implement S3 bucket configuration
  - [x] 20.1 Create S3 bucket resource with static website hosting
    - Configure bucket with website hosting enabled
    - Set index.html as index document
    - Set index.html as error document for SPA routing support
    - Enable versioning for rollback capability
    - _Requirements: 10.3, 10.5_

  - [x] 20.2 Configure S3 bucket public access and CORS
    - Set up public access block configuration
    - Create bucket policy for public read access
    - Configure CORS rules for browser access
    - _Requirements: 10.3_

- [ ] 21. Implement CloudFront distribution configuration
  - [x] 21.1 Create CloudFront distribution with S3 origin
    - Configure origin to use S3 website endpoint
    - Set default root object to index.html
    - Enable IPv6 support
    - Set price class for US, Canada, Europe
    - _Requirements: 10.2, 10.3_

  - [x] 21.2 Configure CloudFront caching and HTTPS
    - Set up default cache behavior with GET/HEAD/OPTIONS methods
    - Configure viewer protocol policy to redirect HTTP to HTTPS
    - Set cache TTL values (min: 0, default: 3600, max: 86400)
    - Enable compression
    - _Requirements: 10.2, 10.4_

  - [x] 21.3 Configure custom error responses for SPA routing
    - Add custom error response for 404 errors (return 200 with index.html)
    - Add custom error response for 403 errors (return 200 with index.html)
    - _Requirements: 10.5_

- [ ] 22. Create build and deployment scripts
  - [x] 22.1 Create build script (scripts/build.sh)
    - Install npm dependencies with npm ci
    - Run Angular production build with ng build --configuration production
    - Add error handling and status messages
    - _Requirements: 10.1_

  - [x] 22.2 Create deployment script (scripts/deploy.sh)
    - Sync built files to S3 with long cache headers (1 year) for versioned assets
    - Upload index.html separately with no-cache headers
    - Create CloudFront cache invalidation for all paths
    - Add input validation for bucket name and distribution ID
    - _Requirements: 10.3, 10.4_

  - [x] 22.3 Create cache invalidation script (scripts/invalidate-cache.sh)
    - Accept CloudFront distribution ID as parameter
    - Create cache invalidation for all paths
    - Add error handling and status messages
    - _Requirements: 10.4_

- [x] 23. Configure environment files for deployment
  - Update environment.ts with development API configuration
  - Update environment.prod.ts with production API configuration
  - Ensure API base URL points to tradeseeker-api-v2 endpoint
  - Configure Cognito user pool ID, client ID, and region
  - _Requirements: 10.1_

- [x] 24. Update Angular configuration for production build
  - Verify angular.json production configuration enables AOT compilation
  - Ensure production build includes optimization, minification, and source maps
  - Configure output hashing for cache busting
  - Set base href for correct asset paths
  - _Requirements: 10.1_

- [x] 25. Checkpoint - Validate Terraform configuration
  - Run terraform init to initialize providers
  - Run terraform validate to check syntax
  - Run terraform plan to preview infrastructure changes
  - Ensure all tests pass, ask the user if questions arise.

- [x] 26. Deploy infrastructure and application
  - [x] 26.1 Apply Terraform configuration
    - Run terraform apply to create S3 bucket and CloudFront distribution
    - Capture outputs (bucket name, CloudFront domain, distribution ID)
    - _Requirements: 10.2, 10.3_

  - [x] 26.2 Build and deploy application
    - Run build script to generate production assets
    - Run deployment script with S3 bucket name and CloudFront distribution ID
    - Verify files uploaded to S3
    - _Requirements: 10.1, 10.3, 10.4_

  - [ ]* 26.3 Verify deployment
    - Test application loads via CloudFront URL
    - Verify HTTPS redirect works
    - Test direct navigation to /dashboard route
    - Verify static assets load with correct cache headers
    - Test API calls work from deployed application
    - Test authentication flow works end-to-end
    - _Requirements: 10.2, 10.3, 10.4, 10.5_

- [ ] 27. Final checkpoint - Complete application deployed
  - Verify all infrastructure is deployed correctly
  - Verify application is accessible and fully functional
  - Verify all features work in production environment
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property-based tests validate universal correctness properties with 100+ iterations
- Unit tests validate specific examples, edge cases, and component integration
- Terraform state should be managed securely (consider using Terraform Cloud or S3 backend)
- AWS credentials must be configured before running Terraform and deployment scripts
- CloudFront distribution creation can take 15-20 minutes
- All 26 correctness properties from the design document should be implemented as property-based tests
