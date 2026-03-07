# Design Document: TradeSeekerWeb v2

## Overview

TradeSeekerWeb v2 is an Angular single-page application (SPA) that provides a visual dashboard for monitoring golden cross stock signals. The application follows a component-based architecture with clear separation between authentication, API communication, data management, and presentation layers.

The system authenticates users via AWS Cognito, fetches golden cross signals and detailed stock data from the tradeseeker-api-v2 REST API, and displays interactive charts in a responsive grid layout optimized for large monitors.

## Architecture

### Infrastructure Architecture

The application is deployed as a static website on AWS using the following infrastructure components:

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Browser                             │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTPS
                         ▼
              ┌──────────────────────┐
              │  CloudFront CDN      │
              │  (Distribution)      │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  S3 Bucket           │
              │  (Static Website)    │
              │  - index.html        │
              │  - *.js, *.css       │
              │  - assets/           │
              └──────────────────────┘
```

**Infrastructure Components**:

1. **S3 Bucket**: Hosts static files (HTML, JS, CSS, assets)
   - Configured for static website hosting
   - Public read access via bucket policy
   - Versioning enabled for rollback capability

2. **CloudFront Distribution**: CDN for global content delivery
   - HTTPS/TLS termination
   - Edge caching for performance
   - Custom error responses for SPA routing
   - Origin: S3 bucket website endpoint

3. **Terraform**: Infrastructure as Code (IaC)
   - Manages all AWS resources
   - Enables reproducible deployments
   - Version controlled infrastructure

**Deployment Flow**:

```
Developer → Build (ng build --prod) → Static Assets
                                           ↓
                                    Upload to S3
                                           ↓
                              CloudFront Cache Invalidation
                                           ↓
                                    Users Access via CDN
```

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
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── s3.tf
│   ├── cloudfront.tf
│   └── iam.tf
├── scripts/
│   ├── build.sh
│   ├── deploy.sh
│   └── invalidate-cache.sh
├── angular.json
├── package.json
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.spec.json
├── karma.conf.js
└── README.md
```

**Folder Structure Explanation**:

- **terraform/**: Infrastructure as Code for AWS resources
  - **main.tf**: Main Terraform configuration and provider setup
  - **variables.tf**: Input variables for configuration
  - **outputs.tf**: Output values (CloudFront URL, S3 bucket name)
  - **s3.tf**: S3 bucket configuration for static hosting
  - **cloudfront.tf**: CloudFront distribution configuration
  - **iam.tf**: IAM policies for deployment access

- **scripts/**: Deployment automation scripts
  - **build.sh**: Build production Angular assets
  - **deploy.sh**: Upload assets to S3 and invalidate CloudFront cache
  - **invalidate-cache.sh**: Invalidate CloudFront cache for updates

- **src/app/core/**: Core application services, models, guards, and interceptors used throughout the app
  - **services/**: Singleton services (AuthService, ApiService, HTTP interceptor)
  - **models/**: TypeScript interfaces and types for data models
  - **guards/**: Route guards for authentication

- **src/app/features/**: Feature modules organized by domain
  - **auth/**: Authentication feature (login component)
  - **dashboard/**: Dashboard feature with chart display components
  - **stock-detail/**: Stock detail feature with multi-period chart analysis

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
         ┌───────────────┴───────────────┬───────────────────────┐
         │                               │                       │
         ▼                               ▼                       ▼
┌──────────────────┐          ┌──────────────────────┐  ┌─────────────────┐
│ Login Component  │          │ Dashboard Component  │  │ Stock Detail    │
└────────┬─────────┘          └──────────┬───────────┘  │ Component       │
         │                               │              └─────────┬───────┘
         │                    ┌──────────┼──────────┐             │
         │                    │          │          │             │
         │                    ▼          ▼          ▼             ▼
         │          ┌─────────────┐  ┌──────┐  ┌────────────┐  ┌──────────────┐
         │          │ Market      │  │Chart │  │Chart Grid  │  │ Multi-Period │
         │          │ Selector    │  │Grid  │  │Component   │  │ Chart Grid   │
         │          └─────────────┘  └──┬───┘  └────────────┘  └──────┬───────┘
         │                              │                             │
         │                              ▼                             ▼
         │                    ┌──────────────────┐          ┌──────────────────┐
         │                    │ Stock Chart      │          │ Stock Chart      │
         │                    │ Component        │          │ Component (×6)   │
         │                    │ (Clickable)      │          │ (Time Ranges)    │
         │                    └──────────────────┘          └──────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────────┐
│                      Service Layer                                │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │ Auth Service │    │ API Service  │    │ HTTP Interceptor │   │
│  │              │    │ (Enhanced)   │    │                  │   │
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

## Angular-Specific Patterns and Best Practices

### Module Organization

The application follows Angular's recommended module structure with feature modules for better code organization and lazy loading potential.

**App Module Structure**:
```typescript
@NgModule({
  declarations: [AppComponent],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    HttpClientModule,
    AppRoutingModule,
    CoreModule,
    SharedModule,
    AuthModule,
    DashboardModule
  ],
  providers: [
    { provide: HTTP_INTERCEPTORS, useClass: AuthInterceptor, multi: true }
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
```

**Core Module** (Singleton services):
```typescript
@NgModule({
  providers: [
    AuthService,
    ApiService,
    AuthGuard
  ]
})
export class CoreModule {
  constructor(@Optional() @SkipSelf() parentModule: CoreModule) {
    if (parentModule) {
      throw new Error('CoreModule is already loaded. Import it in AppModule only.');
    }
  }
}
```

**Shared Module** (Reusable components):
```typescript
@NgModule({
  declarations: [
    LoadingSpinnerComponent,
    ErrorMessageComponent
  ],
  imports: [CommonModule],
  exports: [
    CommonModule,
    LoadingSpinnerComponent,
    ErrorMessageComponent
  ]
})
export class SharedModule { }
```

### Change Detection Strategy

Use `OnPush` change detection strategy for better performance, especially in chart components that render frequently.

```typescript
@Component({
  selector: 'app-stock-chart',
  templateUrl: './stock-chart.component.html',
  styleUrls: ['./stock-chart.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class StockChartComponent {
  // Component implementation
}
```

**Benefits**:
- Reduces change detection cycles
- Improves performance with large numbers of charts
- Forces explicit state management through Observables and Inputs

### Reactive Forms

Use Angular Reactive Forms for the login component to enable better validation and testability.

```typescript
@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent implements OnInit {
  loginForm: FormGroup;
  isLoading = false;
  error: string | null = null;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loginForm = this.fb.group({
      username: ['', [Validators.required, Validators.minLength(3)]],
      password: ['', [Validators.required, Validators.minLength(6)]]
    });
  }

  onSubmit(): void {
    if (this.loginForm.invalid) {
      return;
    }

    this.isLoading = true;
    this.error = null;

    const { username, password } = this.loginForm.value;

    this.authService.login(username, password)
      .subscribe({
        next: (result) => {
          if (result.success) {
            this.router.navigate(['/dashboard']);
          } else {
            this.error = result.error || 'Login failed';
            this.isLoading = false;
          }
        },
        error: (err) => {
          this.error = 'An error occurred during login';
          this.isLoading = false;
        }
      });
  }

  get username() {
    return this.loginForm.get('username');
  }

  get password() {
    return this.loginForm.get('password');
  }
}
```

### RxJS Best Practices

**Subscription Management**:
Always unsubscribe from observables to prevent memory leaks. Use one of these patterns:

1. **takeUntil Pattern** (Recommended):
```typescript
private destroy$ = new Subject<void>();

ngOnInit(): void {
  this.apiService.getData()
    .pipe(takeUntil(this.destroy$))
    .subscribe(data => {
      // Handle data
    });
}

ngOnDestroy(): void {
  this.destroy$.next();
  this.destroy$.complete();
}
```

2. **Async Pipe** (Template):
```typescript
// Component
data$ = this.apiService.getData();

// Template
<div *ngIf="data$ | async as data">
  {{ data }}
</div>
```

**Error Handling**:
```typescript
this.apiService.getStockData(symbol)
  .pipe(
    retry(2), // Retry failed requests
    catchError(error => {
      console.error('Error fetching stock data:', error);
      return of(null); // Return fallback value
    }),
    takeUntil(this.destroy$)
  )
  .subscribe(data => {
    // Handle data
  });
```

**Concurrency Control**:
```typescript
// Fetch multiple stocks with concurrency limit
getMultipleStocks(symbols: string[]): Observable<StockData[]> {
  return from(symbols).pipe(
    mergeMap(
      symbol => this.getStockData(symbol).pipe(
        catchError(error => {
          console.error(`Error fetching ${symbol}:`, error);
          return of(null);
        })
      ),
      6 // Max 6 concurrent requests
    ),
    filter(data => data !== null),
    toArray()
  );
}
```

### Dependency Injection

Use Angular's dependency injection system for better testability and modularity.

**Service Injection**:
```typescript
@Injectable({
  providedIn: 'root' // Singleton service
})
export class AuthService {
  constructor(private http: HttpClient) {}
}
```

**Testing with Dependency Injection**:
```typescript
describe('DashboardComponent', () => {
  let component: DashboardComponent;
  let fixture: ComponentFixture<DashboardComponent>;
  let apiService: jasmine.SpyObj<ApiService>;

  beforeEach(() => {
    const apiServiceSpy = jasmine.createSpyObj('ApiService', [
      'getGoldenCrosses',
      'getMultipleStocks'
    ]);

    TestBed.configureTestingModule({
      declarations: [DashboardComponent],
      providers: [
        { provide: ApiService, useValue: apiServiceSpy }
      ]
    });

    fixture = TestBed.createComponent(DashboardComponent);
    component = fixture.componentInstance;
    apiService = TestBed.inject(ApiService) as jasmine.SpyObj<ApiService>;
  });

  it('should fetch data on init', () => {
    apiService.getGoldenCrosses.and.returnValue(of({ symbols: ['AAPL'] }));
    component.ngOnInit();
    expect(apiService.getGoldenCrosses).toHaveBeenCalledWith('US');
  });
});
```

### Route Guards

Implement authentication guard to protect routes:

```typescript
@Injectable({
  providedIn: 'root'
})
export class AuthGuard implements CanActivate {
  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  canActivate(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): boolean {
    if (this.authService.isAuthenticated()) {
      return true;
    }

    // Store the attempted URL for redirecting after login
    sessionStorage.setItem('redirectUrl', state.url);
    
    // Navigate to login page
    this.router.navigate(['/login']);
    return false;
  }
}
```

**Routing Configuration**:
```typescript
const routes: Routes = [
  { path: '', redirectTo: '/dashboard', pathMatch: 'full' },
  { path: 'login', component: LoginComponent },
  { 
    path: 'dashboard', 
    component: DashboardComponent,
    canActivate: [AuthGuard]
  },
  {
    path: 'stock/:symbol',
    component: StockDetailComponent,
    canActivate: [AuthGuard]
  },
  { path: '**', redirectTo: '/dashboard' }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
```

### Performance Optimization

**TrackBy Functions**:
```typescript
// In component
trackBySymbol(index: number, item: StockData): string {
  return item.symbol;
}

// In template
<app-stock-chart 
  *ngFor="let stock of stockData; trackBy: trackBySymbol"
  [stockData]="stock">
</app-stock-chart>
```

**Lazy Loading** (Future enhancement):
```typescript
const routes: Routes = [
  {
    path: 'dashboard',
    loadChildren: () => import('./features/dashboard/dashboard.module')
      .then(m => m.DashboardModule),
    canActivate: [AuthGuard]
  }
];
```

**Virtual Scrolling** (For large datasets):
```typescript
// If displaying hundreds of charts
<cdk-virtual-scroll-viewport itemSize="400" class="chart-viewport">
  <app-stock-chart 
    *cdkVirtualFor="let stock of stockData"
    [stockData]="stock">
  </app-stock-chart>
</cdk-virtual-scroll-viewport>
```

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
  
  // Fetch detailed stock data for a symbol (with optional time range for other features)
  getStockData(symbol: string, days?: number): Observable<StockData>
  
  // Fetch multiple stocks concurrently
  getMultipleStocks(symbols: string[]): Observable<StockData[]>
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
- Support optional time range parameter for stock data: `GET /stocks/{symbol}?days={number}`
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

**Detailed Data Orchestration Logic**:

The Dashboard Component is the central orchestrator that manages data fetching, state management, and coordination between child components.

**Component Implementation**:
```typescript
@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit, OnDestroy {
  selectedMarket: string = 'US';
  selectedDisplayMode: 'prices' | 'ema' | 'both' = 'both';
  selectedChartType: 'candlestick' | 'line' = 'candlestick';
  goldenCrosses: string[] = [];
  stockDataArray: StockData[] = [];
  isLoading: boolean = false;
  error: string | null = null;
  
  private destroy$ = new Subject<void>();
  private refreshInterval: any;
  private readonly REFRESH_INTERVAL_MS = 5 * 60 * 1000; // 5 minutes

  constructor(
    private apiService: ApiService,
    private router: Router
  ) {}

  ngOnInit(): void {
    // Restore market selection from session storage
    const savedMarket = sessionStorage.getItem('selectedMarket');
    if (savedMarket) {
      this.selectedMarket = savedMarket;
    }
    
    // Restore display mode from session storage
    const savedDisplayMode = sessionStorage.getItem('displayMode') as 'prices' | 'ema' | 'both';
    if (savedDisplayMode) {
      this.selectedDisplayMode = savedDisplayMode;
    }
    
    // Restore chart type from session storage
    const savedChartType = sessionStorage.getItem('chartType') as 'candlestick' | 'line';
    if (savedChartType) {
      this.selectedChartType = savedChartType;
    }
    
    // Initial data fetch
    this.fetchData();
    
    // Set up automatic refresh
    this.setupAutoRefresh();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }
  }

  fetchData(): void {
    this.isLoading = true;
    this.error = null;
    
    this.apiService.getGoldenCrosses(this.selectedMarket)
      .pipe(
        // Cancel previous request if new one comes in
        switchMap(response => {
          this.goldenCrosses = response.symbols;
          
          if (response.symbols.length === 0) {
            return of([]);
          }
          
          // Fetch stock data for all symbols with concurrency control
          return this.apiService.getMultipleStocks(response.symbols);
        }),
        // Unsubscribe when component is destroyed
        takeUntil(this.destroy$),
        // Handle errors gracefully
        catchError(error => {
          this.error = this.getErrorMessage(error);
          this.isLoading = false;
          return of([]);
        })
      )
      .subscribe(stockDataArray => {
        this.stockDataArray = stockDataArray;
        this.isLoading = false;
      });
  }

  onMarketChange(market: string): void {
    if (market === this.selectedMarket) {
      return;
    }
    
    this.selectedMarket = market;
    
    // Persist market selection
    sessionStorage.setItem('selectedMarket', market);
    
    // Clear existing data and fetch new data
    this.stockDataArray = [];
    this.goldenCrosses = [];
    this.fetchData();
  }

  onDisplayModeChange(mode: 'prices' | 'ema' | 'both'): void {
    this.selectedDisplayMode = mode;
    
    // Persist display mode selection
    sessionStorage.setItem('displayMode', mode);
  }

  onChartTypeChange(type: 'candlestick' | 'line'): void {
    this.selectedChartType = type;
    
    // Persist chart type selection
    sessionStorage.setItem('chartType', type);
  }

  onRefresh(): void {
    if (this.isLoading) {
      return; // Prevent duplicate refresh requests
    }
    
    this.fetchData();
  }

  private setupAutoRefresh(): void {
    this.refreshInterval = setInterval(() => {
      if (!this.isLoading) {
        this.fetchData();
      }
    }, this.REFRESH_INTERVAL_MS);
  }

  private getErrorMessage(error: any): string {
    if (error.status === 401) {
      return 'Session expired. Please log in again.';
    } else if (error.status === 404) {
      return 'Data not found for the selected market.';
    } else if (error.status >= 500) {
      return 'Server error occurred. Please try again later.';
    } else if (error.message?.includes('timeout')) {
      return 'Request timed out. Please check your connection.';
    } else {
      return 'An error occurred while fetching data.';
    }
  }
}
```

**Dashboard Template**:
```html
<div class="dashboard-container">
  <!-- Header with market selector, display mode selector, chart type selector, and refresh button -->
  <div class="dashboard-header">
    <h1>Golden Cross Signals</h1>
    
    <div class="controls">
      <app-market-selector
        [selectedMarket]="selectedMarket"
        (marketChange)="onMarketChange($event)">
      </app-market-selector>
      
      <app-chart-display-mode-selector
        [selectedMode]="selectedDisplayMode"
        (modeChange)="onDisplayModeChange($event)">
      </app-chart-display-mode-selector>
      
      <app-chart-type-selector
        [selectedType]="selectedChartType"
        (typeChange)="onChartTypeChange($event)">
      </app-chart-type-selector>
      
      <button 
        class="refresh-button"
        (click)="onRefresh()"
        [disabled]="isLoading">
        <span *ngIf="!isLoading">Refresh</span>
        <span *ngIf="isLoading">Refreshing...</span>
      </button>
    </div>
  </div>

  <!-- Loading state -->
  <div *ngIf="isLoading && stockDataArray.length === 0" class="loading-container">
    <app-loading-spinner></app-loading-spinner>
    <p>Loading golden cross data...</p>
  </div>

  <!-- Error state -->
  <div *ngIf="error" class="error-container">
    <app-error-message
      [message]="error"
      [guidance]="'Retry'"
      (action)="onRefresh()">
    </app-error-message>
  </div>

  <!-- Empty state -->
  <div *ngIf="!isLoading && !error && stockDataArray.length === 0" class="empty-state">
    <p>No golden cross signals found for {{ selectedMarket }} market.</p>
    <button (click)="onRefresh()">Refresh</button>
  </div>

  <!-- Chart grid with display mode and chart type passed to each chart -->
  <app-chart-grid
    *ngIf="!isLoading && !error && stockDataArray.length > 0"
    [stockData]="stockDataArray"
    [displayMode]="selectedDisplayMode"
    [chartType]="selectedChartType">
  </app-chart-grid>
</div>
```

**Dashboard Styling**:
```scss
.dashboard-container {
  width: 100%;
  min-height: 100vh;
  background: #f5f5f5;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  
  h1 {
    margin: 0;
    font-size: 24px;
    color: #333;
  }
  
  .controls {
    display: flex;
    gap: 16px;
    align-items: center;
  }
  
  .refresh-button {
    padding: 10px 20px;
    background: #2196F3;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    
    &:hover:not(:disabled) {
      background: #1976D2;
    }
    
    &:disabled {
      background: #ccc;
      cursor: not-allowed;
    }
  }
}

.loading-container,
.error-container,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  padding: 40px;
}
```

**RxJS Operators Used**:
- **switchMap**: Cancels previous API requests when new ones are initiated (prevents race conditions)
- **takeUntil**: Automatically unsubscribes when component is destroyed (prevents memory leaks)
- **catchError**: Handles errors gracefully without breaking the observable stream
- **of**: Creates observable from array for consistent return type

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

**Detailed Responsive Grid Implementation**:

The Chart Grid Component uses CSS Grid to create a flexible, responsive layout that adapts to different screen sizes while maintaining optimal chart visibility.

**Component Template**:
```html
<div class="chart-grid">
  <app-stock-chart 
    *ngFor="let stock of stockData; trackBy: trackBySymbol"
    [stockData]="stock"
    [displayMode]="displayMode"
    [chartType]="chartType"
    class="chart-grid-item">
  </app-stock-chart>
</div>

<div *ngIf="!stockData || stockData.length === 0" class="empty-state">
  <p>No charts to display</p>
</div>
```

**Component Logic**:
```typescript
@Component({
  selector: 'app-chart-grid',
  templateUrl: './chart-grid.component.html',
  styleUrls: ['./chart-grid.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ChartGridComponent {
  @Input() stockData: StockData[] = [];
  @Input() displayMode: 'prices' | 'ema' | 'both' = 'both';
  @Input() chartType: 'candlestick' | 'line' = 'candlestick';

  // TrackBy function for performance optimization
  trackBySymbol(index: number, item: StockData): string {
    return item.symbol;
  }
}
```

**Responsive Grid Styling**:
```scss
.chart-grid {
  display: grid;
  gap: 20px;
  padding: 20px;
  width: 100%;
  
  // Default: Auto-fit with minimum 300px per chart
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  
  // Large monitors (27" - 2560px+): 6 columns
  @media (min-width: 2560px) {
    grid-template-columns: repeat(6, 1fr);
  }
  
  // Desktop (1920px): 5 columns
  @media (min-width: 1920px) and (max-width: 2559px) {
    grid-template-columns: repeat(5, 1fr);
  }
  
  // Large desktop (1440px): 4 columns
  @media (min-width: 1440px) and (max-width: 1919px) {
    grid-template-columns: repeat(4, 1fr);
  }
  
  // Medium desktop (1024px): 3 columns
  @media (min-width: 1024px) and (max-width: 1439px) {
    grid-template-columns: repeat(3, 1fr);
  }
  
  // Tablet (768px): 2 columns
  @media (min-width: 768px) and (max-width: 1023px) {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
    padding: 16px;
  }
  
  // Mobile (<768px): 1 column
  @media (max-width: 767px) {
    grid-template-columns: 1fr;
    gap: 12px;
    padding: 12px;
  }
}

.chart-grid-item {
  min-height: 300px;
  max-height: 500px;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  font-size: 18px;
  color: #666;
}
```

**Grid Layout Behavior**:
- **Auto-fit**: Grid automatically adjusts number of columns based on available space
- **Minmax**: Each chart has minimum width of 300px, maximum of 1fr (equal fraction)
- **Gap**: Consistent spacing between charts (20px on desktop, scales down on mobile)
- **Responsive**: Media queries override auto-fit for precise control on specific screen sizes

### 6. Stock Chart Component

**Responsibility**: Render individual stock chart with price data and EMA lines.

**Interface**:
```typescript
interface StockChartComponent {
  @Input() stockData: StockData
  @Input() displayMode: 'prices' | 'ema' | 'both'
  @Input() chartType: 'candlestick' | 'line'
  
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
- Support two chart types for price data:
  - Candlestick: Shows open, high, low, close (via chartjs-chart-financial plugin)
  - Line: Shows only close prices
- Render 4 EMA lines with distinct colors:
  - EMA 7: Blue (#2196F3)
  - EMA 30: Orange (#FF9800)
  - EMA 50: Green (#4CAF50)
  - EMA 200: Red (#F44336)
- Display symbol name as chart title
- Handle loading and error states
- Destroy chart instance on component destroy to prevent memory leaks
- Update chart when input data or display mode changes
- Support three display modes: prices only, EMA only, or both

**Detailed Chart Rendering Logic**:

The Stock Chart Component is the core visualization component that transforms raw stock data into interactive charts. Here's the detailed implementation approach:

**Chart.js Configuration**:
```typescript
// Install dependencies
// npm install chart.js chartjs-chart-financial chartjs-adapter-date-fns

import { Chart, registerables } from 'chart.js';
import { CandlestickController, CandlestickElement } from 'chartjs-chart-financial';
import 'chartjs-adapter-date-fns';

// Register Chart.js components
Chart.register(...registerables, CandlestickController, CandlestickElement);
```

**Chart Data Transformation with Display Mode and Chart Type**:
```typescript
renderChart(): void {
  if (!this.stockData || !this.stockData.prices) {
    return;
  }

  const ctx = this.chartCanvas.nativeElement.getContext('2d');
  
  // Prepare datasets based on display mode and chart type
  const datasets = this.getDatasets();

  // Determine chart type based on display mode and chart type
  const chartType = this.getChartType();

  this.chart = new Chart(ctx, {
    type: chartType,
    data: { datasets },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      aspectRatio: 2,
      plugins: {
        title: {
          display: true,
          text: this.stockData.symbol,
          font: { size: 16, weight: 'bold' }
        },
        legend: {
          display: true,
          position: 'top'
        },
        tooltip: {
          mode: 'index',
          intersect: false
        }
      },
      scales: {
        x: {
          type: 'time',
          time: {
            unit: 'day',
            displayFormats: { day: 'MMM dd' }
          },
          title: { display: true, text: 'Date' }
        },
        y: {
          title: { display: true, text: 'Price' },
          beginAtZero: false
        }
      }
    }
  });
}

private getChartType(): string {
  // If only showing EMA, use line chart
  if (this.displayMode === 'ema') {
    return 'line';
  }
  
  // If showing prices with candlestick type, use candlestick
  if (this.chartType === 'candlestick' && 
      (this.displayMode === 'prices' || this.displayMode === 'both')) {
    return 'candlestick';
  }
  
  // Otherwise use line chart
  return 'line';
}

private getDatasets(): any[] {
  const dates = this.stockData.prices.map(p => new Date(p.date));
  const datasets: any[] = [];

  // Add price data if mode is 'prices' or 'both'
  if (this.displayMode === 'prices' || this.displayMode === 'both') {
    if (this.chartType === 'candlestick') {
      // Candlestick chart data
      const candlestickData = this.stockData.prices.map(p => ({
        x: new Date(p.date),
        o: p.open,
        h: p.high,
        l: p.low,
        c: p.close
      }));

      datasets.push({
        type: 'candlestick',
        label: this.stockData.symbol,
        data: candlestickData,
        borderColor: '#333',
        backgroundColor: 'rgba(0, 0, 0, 0.1)'
      });
    } else {
      // Line chart data (close prices only)
      const closePriceData = this.stockData.prices.map((p, idx) => ({
        x: dates[idx],
        y: p.close
      }));

      datasets.push({
        type: 'line',
        label: `${this.stockData.symbol} Close`,
        data: closePriceData,
        borderColor: '#333',
        borderWidth: 2,
        fill: false,
        pointRadius: 0
      });
    }
  }

  // Add EMA lines if mode is 'ema' or 'both'
  if (this.displayMode === 'ema' || this.displayMode === 'both') {
    datasets.push(
      {
        type: 'line',
        label: 'EMA 7',
        data: this.stockData.emas.ema7.map((val, idx) => ({ x: dates[idx], y: val })),
        borderColor: '#2196F3',
        borderWidth: 2,
        fill: false,
        pointRadius: 0
      },
      {
        type: 'line',
        label: 'EMA 30',
        data: this.stockData.emas.ema30.map((val, idx) => ({ x: dates[idx], y: val })),
        borderColor: '#FF9800',
        borderWidth: 2,
        fill: false,
        pointRadius: 0
      },
      {
        type: 'line',
        label: 'EMA 50',
        data: this.stockData.emas.ema50.map((val, idx) => ({ x: dates[idx], y: val })),
        borderColor: '#4CAF50',
        borderWidth: 2,
        fill: false,
        pointRadius: 0
      },
      {
        type: 'line',
        label: 'EMA 200',
        data: this.stockData.emas.ema200.map((val, idx) => ({ x: dates[idx], y: val })),
        borderColor: '#F44336',
        borderWidth: 2,
        fill: false,
        pointRadius: 0
      }
    );
  }

  return datasets;
}
```

**Lifecycle Management**:
```typescript
ngOnInit(): void {
  if (this.stockData) {
    this.renderChart();
  }
}

ngOnChanges(changes: SimpleChanges): void {
  if (changes['stockData'] && !changes['stockData'].firstChange) {
    this.updateChart();
  }
  
  // Update chart when display mode changes
  if (changes['displayMode'] && !changes['displayMode'].firstChange) {
    this.updateChart();
  }
  
  // Update chart when chart type changes
  if (changes['chartType'] && !changes['chartType'].firstChange) {
    this.updateChart();
  }
}

ngOnDestroy(): void {
  if (this.chart) {
    this.chart.destroy();
    this.chart = null;
  }
}

updateChart(): void {
  if (this.chart) {
    this.chart.destroy();
  }
  this.renderChart();
}
```

**Template Structure**:
```html
<div class="stock-chart-container">
  <div *ngIf="isLoading" class="loading-state">
    <app-loading-spinner></app-loading-spinner>
  </div>
  
  <div *ngIf="error" class="error-state">
    <app-error-message 
      [message]="'Failed to load chart for ' + stockData?.symbol"
      [guidance]="'Retry'">
    </app-error-message>
  </div>
  
  <canvas 
    *ngIf="!isLoading && !error" 
    #chartCanvas
    class="chart-canvas">
  </canvas>
</div>
```

**Styling Considerations**:
```scss
.stock-chart-container {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 300px;
  padding: 16px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  
  .chart-canvas {
    width: 100% !important;
    height: auto !important;
  }
  
  .loading-state,
  .error-state {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 300px;
  }
}
```

**Performance Optimizations**:
- Use `ChangeDetectionStrategy.OnPush` for better performance
- Destroy chart instances in `ngOnDestroy` to prevent memory leaks
- Debounce window resize events if implementing responsive chart resizing
- Use `trackBy` function in parent component's `*ngFor` to minimize re-renders

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

### 8. Chart Display Mode Selector Component

**Responsibility**: Allow users to toggle between different chart display modes.

**Interface**:
```typescript
interface ChartDisplayModeSelectorComponent {
  @Input() selectedMode: 'prices' | 'ema' | 'both'
  @Output() modeChange: EventEmitter<'prices' | 'ema' | 'both'>
  
  displayModes: Array<{ value: string, label: string }>
  
  onModeSelect(mode: 'prices' | 'ema' | 'both'): void
}
```

**Implementation Details**:
- Display radio button group for display mode selection
- Available modes:
  - 'prices': Show only candlestick/price data
  - 'ema': Show only EMA lines
  - 'both': Show both prices and EMA lines (default)
- Emit modeChange event when selection changes
- Highlight currently selected mode

**Component Implementation**:
```typescript
@Component({
  selector: 'app-chart-display-mode-selector',
  templateUrl: './chart-display-mode-selector.component.html',
  styleUrls: ['./chart-display-mode-selector.component.scss']
})
export class ChartDisplayModeSelectorComponent {
  @Input() selectedMode: 'prices' | 'ema' | 'both' = 'both';
  @Output() modeChange = new EventEmitter<'prices' | 'ema' | 'both'>();

  displayModes = [
    { value: 'both', label: 'Both' },
    { value: 'prices', label: 'Prices Only' },
    { value: 'ema', label: 'EMA Only' }
  ];

  onModeSelect(mode: 'prices' | 'ema' | 'both'): void {
    if (mode !== this.selectedMode) {
      this.selectedMode = mode;
      this.modeChange.emit(mode);
    }
  }
}
```

**Template**:
```html
<div class="chart-display-mode-selector">
  <label class="selector-label">Chart Display:</label>
  <div class="radio-group">
    <label 
      *ngFor="let mode of displayModes" 
      class="radio-option"
      [class.selected]="selectedMode === mode.value">
      <input 
        type="radio" 
        [name]="'displayMode'"
        [value]="mode.value"
        [checked]="selectedMode === mode.value"
        (change)="onModeSelect(mode.value)">
      <span class="radio-label">{{ mode.label }}</span>
    </label>
  </div>
</div>
```

**Styling**:
```scss
.chart-display-mode-selector {
  display: flex;
  align-items: center;
  gap: 12px;

  .selector-label {
    font-weight: 500;
    color: #333;
    font-size: 14px;
  }

  .radio-group {
    display: flex;
    gap: 8px;
    background: #f5f5f5;
    padding: 4px;
    border-radius: 6px;
  }

  .radio-option {
    display: flex;
    align-items: center;
    padding: 8px 16px;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s ease;
    background: transparent;

    &:hover {
      background: rgba(33, 150, 243, 0.1);
    }

    &.selected {
      background: #2196F3;
      color: white;

      .radio-label {
        color: white;
      }
    }

    input[type="radio"] {
      display: none;
    }

    .radio-label {
      font-size: 14px;
      color: #666;
      user-select: none;
    }
  }
}
```

### 9. Chart Type Selector Component

**Responsibility**: Allow users to toggle between candlestick and line chart for price display.

**Interface**:
```typescript
interface ChartTypeSelectorComponent {
  @Input() selectedType: 'candlestick' | 'line'
  @Output() typeChange: EventEmitter<'candlestick' | 'line'>
  
  chartTypes: Array<{ value: string, label: string }>
  
  onTypeSelect(type: 'candlestick' | 'line'): void
}
```

**Implementation Details**:
- Display radio button group for chart type selection
- Available types:
  - 'candlestick': Show OHLC candlestick chart (default)
  - 'line': Show line chart with close prices only
- Emit typeChange event when selection changes
- Highlight currently selected type
- Only affects price display (not EMA lines)

**Component Implementation**:
```typescript
@Component({
  selector: 'app-chart-type-selector',
  templateUrl: './chart-type-selector.component.html',
  styleUrls: ['./chart-type-selector.component.scss']
})
export class ChartTypeSelectorComponent {
  @Input() selectedType: 'candlestick' | 'line' = 'candlestick';
  @Output() typeChange = new EventEmitter<'candlestick' | 'line'>();

  chartTypes = [
    { value: 'candlestick', label: 'Candlestick' },
    { value: 'line', label: 'Line' }
  ];

  onTypeSelect(type: 'candlestick' | 'line'): void {
    if (type !== this.selectedType) {
      this.selectedType = type;
      this.typeChange.emit(type);
    }
  }
}
```

**Template**:
```html
<div class="chart-type-selector">
  <label class="selector-label">Price Chart:</label>
  <div class="radio-group">
    <label 
      *ngFor="let type of chartTypes" 
      class="radio-option"
      [class.selected]="selectedType === type.value">
      <input 
        type="radio" 
        [name]="'chartType'"
        [value]="type.value"
        [checked]="selectedType === type.value"
        (change)="onTypeSelect(type.value)">
      <span class="radio-label">{{ type.label }}</span>
    </label>
  </div>
</div>
```

**Styling**:
```scss
.chart-type-selector {
  display: flex;
  align-items: center;
  gap: 12px;

  .selector-label {
    font-weight: 500;
    color: #333;
    font-size: 14px;
  }

  .radio-group {
    display: flex;
    gap: 8px;
    background: #f5f5f5;
    padding: 4px;
    border-radius: 6px;
  }

  .radio-option {
    display: flex;
    align-items: center;
    padding: 8px 16px;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s ease;
    background: transparent;

    &:hover {
      background: rgba(33, 150, 243, 0.1);
    }

    &.selected {
      background: #2196F3;
      color: white;

      .radio-label {
        color: white;
      }
    }

    input[type="radio"] {
      display: none;
    }

    .radio-label {
      font-size: 14px;
      color: #666;
      user-select: none;
    }
  }
}
```

### 10. Login Component

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

### 11. Stock Detail Component

**Responsibility**: Display multi-period analysis for a single stock with 6 charts showing different time ranges.

**Interface**:
```typescript
interface StockDetailComponent {
  symbol: string
  stockDataArray: StockData[]
  isLoading: boolean
  error: string | null
  timeRanges: TimeRange[]
  
  // Lifecycle hooks
  ngOnInit(): void
  ngOnDestroy(): void
  
  // Navigation
  goBack(): void
  
  // Utility methods
  getTimeRangeLabel(index: number): string
}

interface TimeRange {
  label: string
  days: number
}
```

**Implementation Details**:
- Displays 6 charts simultaneously for different time periods:
  - 90 Days, 180 Days, 1 Year, 3 Years, 5 Years, 10 Years
- Fetches stock data for all time ranges concurrently using enhanced API service
- Uses responsive grid layout (2-3 charts per row on desktop, 1 on mobile)
- Each chart shows candlestick format with EMA overlays
- Includes back navigation to dashboard
- Handles loading states and error conditions gracefully
- Opens in new browser tab when accessed from dashboard

**Enhanced API Service Integration**:
The Stock Detail Component uses the regular API service and filters data client-side for different time periods:

```typescript
// Regular API service call (with proper CORS and auth headers)
this.apiService.getStockData(this.symbol).subscribe(fullStockData => {
  // Create filtered datasets for each time range
  this.stockDataArray = this.timeRanges.map(range => 
    this.filterStockDataByDays(fullStockData, range.days)
  );
});

// Client-side filtering method
private filterStockDataByDays(stockData: StockData, days: number): StockData | null {
  // Sort prices by date (newest first) and take the latest N items
  const sortedPrices = [...stockData.prices]
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
    .slice(0, days)
    .reverse(); // Reverse to get chronological order

  // Filter corresponding EMA data to match the same date range
  // ... (EMA filtering logic)
  
  return {
    symbol: stockData.symbol,
    prices: sortedPrices,
    emas: filteredEmas,
    lastUpdated: stockData.lastUpdated
  };
}
```

**Stock Chart Component Enhancement**:
The chart component now respects pre-filtered data in detail view:

```typescript
// In detail view, use data as-is. In dashboard view, filter to 360 days
const filteredData = this.isDetailView ? this.getDataAsIs() : this.getLatest360Days();

private getDataAsIs(): { prices: any[], emas: any } {
  return {
    prices: this.stockData.prices,
    emas: this.stockData.emas
  };
}
```

**Data Point Display**:
Each chart shows the actual number of data points used:
- 3 Months: Latest 90 price entries from the dataset
- 6 Months: Latest 180 price entries from the dataset
- 1 Year: Latest 365 price entries from the dataset
- 3 Years: Latest 1095 price entries from the dataset
- 5 Years: Latest 1825 price entries from the dataset
- 10 Years: Latest 3650 price entries from the dataset

**Responsive Grid Layout**:
```scss
.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
  
  @media (max-width: 1200px) {
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  }
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
}

.chart-wrapper {
  height: 250px; // Smaller charts for better overview
}
```

**Stock Chart Component Enhancement**:
The existing Stock Chart Component has been enhanced to support clickable stock symbols within the chart itself:

```typescript
// New input property
@Input() isDetailView: boolean = false;

// Canvas click handler method
onCanvasClick(event: MouseEvent): void {
  if (this.isDetailView || !this.chart) {
    return;
  }

  const rect = this.chartCanvas.nativeElement.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;

  // Check if click is in the title area (top portion of chart)
  if (y <= 50) {
    this.onStockClick();
  }
}

// Navigation method
onStockClick(): void {
  if (!this.isDetailView && this.currentStockData?.symbol) {
    const url = this.router.serializeUrl(
      this.router.createUrlTree(['/stock', this.currentStockData.symbol])
    );
    window.open(url, '_blank');
  }
}
```

**Chart Title Configuration**:
```typescript
plugins: {
  title: {
    display: !this.isDetailView, // Hide title in detail view for cleaner look
    text: this.currentStockData.symbol,
    font: { size: 16, weight: 'bold' },
    color: this.isDetailView ? '#333' : '#007bff'  // Blue for clickable, gray for detail view
  }
}
```

**Template Enhancement**:
```html
<canvas 
  #chartCanvas
  [class.clickable-chart]="!isDetailView"
  (click)="onCanvasClick($event)">
</canvas>
```

**Styling for Clickable Charts**:
```scss
canvas.clickable-chart {
  cursor: pointer;
}
```

**Navigation Flow**:
1. User clicks stock name (title) inside the chart area
2. New tab opens with URL `/stock/{symbol}`
3. Stock Detail Component loads and fetches data for all time ranges
4. 6 charts render simultaneously showing different periods
5. User can close tab or navigate back using browser controls

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

// Stock data response
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

### Stock Detail Navigation Flow

```
Dashboard Component → Stock Chart Click → New Tab Opens
                                              ↓
                                    Stock Detail Component
                                              ↓
                                    Route: /stock/{symbol}
                                              ↓
                                    Regular API Service Call
                                              ↓
                                    GET /stocks/{symbol}
                                              ↓
                                    Client-Side Data Filtering
                                              ↓
                                    ┌─────────────────────────────┐
                                    │ Filter by Data Points:      │
                                    │ - 3 Months: Latest 90 items│
                                    │ - 6 Months: Latest 180 items│
                                    │ - 1 Year: Latest 365 items │
                                    │ - 3 Years: Latest 1095 items│
                                    │ - 5 Years: Latest 1825 items│
                                    │ - 10 Years: Latest 3650 items│
                                    └─────────────────────────────┘
                                              ↓
                                    Render 6 Charts in Grid Layout
```

**Detailed Steps**:
1. User clicks on stock name inside the chart title area
2. Stock Chart Component calls `onCanvasClick()` method (detects click in title area)
3. Router creates URL for `/stock/{symbol}` route
4. New browser tab opens with the stock detail URL
5. Stock Detail Component initializes and extracts symbol from route params
6. Component makes API request using regular ApiService: `GET /stocks/{symbol}` (with proper CORS and auth headers)
7. Response contains complete historical dataset with prices and moving averages
8. Client-side filtering creates 6 different datasets with varying data points
9. Each dataset contains the latest N price entries and corresponding EMA values
10. Template renders 6 Stock Chart Components in responsive grid
11. Each chart displays the filtered data with actual data point count shown
12. User can close tab or navigate back using browser controls

## Infrastructure Components

### Terraform Configuration

The infrastructure is defined using Terraform to ensure reproducible and version-controlled deployments.

#### S3 Bucket Configuration (s3.tf)

```hcl
resource "aws_s3_bucket" "web_app" {
  bucket = var.bucket_name
  
  tags = {
    Name        = "TradeSeekerWeb"
    Environment = var.environment
  }
}

resource "aws_s3_bucket_website_configuration" "web_app" {
  bucket = aws_s3_bucket.web_app.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "index.html"  # SPA routing: all errors redirect to index.html
  }
}

resource "aws_s3_bucket_public_access_block" "web_app" {
  bucket = aws_s3_bucket.web_app.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "web_app" {
  bucket = aws_s3_bucket.web_app.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.web_app.arn}/*"
      }
    ]
  })
}

resource "aws_s3_bucket_versioning" "web_app" {
  bucket = aws_s3_bucket.web_app.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_cors_configuration" "web_app" {
  bucket = aws_s3_bucket.web_app.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "HEAD"]
    allowed_origins = ["*"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3600
  }
}
```

**S3 Configuration Details**:
- **Static Website Hosting**: Enabled with index.html as the default document
- **Error Document**: Points to index.html to support Angular client-side routing
- **Public Access**: Configured to allow public read access for website hosting
- **Versioning**: Enabled for rollback capability
- **CORS**: Configured to allow browser access to assets

#### CloudFront Distribution Configuration (cloudfront.tf)

```hcl
resource "aws_cloudfront_origin_access_identity" "web_app" {
  comment = "OAI for TradeSeekerWeb"
}

resource "aws_cloudfront_distribution" "web_app" {
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  price_class         = "PriceClass_100"  # US, Canada, Europe

  origin {
    domain_name = aws_s3_bucket_website_configuration.web_app.website_endpoint
    origin_id   = "S3-${var.bucket_name}"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${var.bucket_name}"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
    compress               = true
  }

  # Custom error response for SPA routing
  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Name        = "TradeSeekerWeb"
    Environment = var.environment
  }
}
```

**CloudFront Configuration Details**:
- **HTTPS Enforcement**: Redirects all HTTP requests to HTTPS
- **Caching**: Default TTL of 1 hour, max 24 hours
- **Compression**: Enabled for faster delivery
- **SPA Routing Support**: Custom error responses redirect 404/403 to index.html
- **Global Distribution**: Price class 100 covers US, Canada, and Europe

#### Variables Configuration (variables.tf)

```hcl
variable "bucket_name" {
  description = "Name of the S3 bucket for static website hosting"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "ap-southeast-1"
}
```

#### Outputs Configuration (outputs.tf)

```hcl
output "s3_bucket_name" {
  description = "Name of the S3 bucket"
  value       = aws_s3_bucket.web_app.id
}

output "s3_website_endpoint" {
  description = "S3 website endpoint"
  value       = aws_s3_bucket_website_configuration.web_app.website_endpoint
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.web_app.domain_name
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = aws_cloudfront_distribution.web_app.id
}
```

### Build and Deployment Process

#### Build Script (scripts/build.sh)

```bash
#!/bin/bash
set -e

echo "Building Angular application for production..."

# Install dependencies
npm ci

# Build with production configuration
ng build --configuration production

echo "Build complete! Output in dist/tradeseeker-web-v2/"
```

**Build Configuration**:
- Uses Angular CLI production build
- Enables AOT compilation
- Minifies and optimizes assets
- Generates source maps for debugging
- Outputs to `dist/tradeseeker-web-v2/`

#### Deployment Script (scripts/deploy.sh)

```bash
#!/bin/bash
set -e

BUCKET_NAME=$1
DISTRIBUTION_ID=$2

if [ -z "$BUCKET_NAME" ] || [ -z "$DISTRIBUTION_ID" ]; then
  echo "Usage: ./deploy.sh <bucket-name> <cloudfront-distribution-id>"
  exit 1
fi

echo "Deploying to S3 bucket: $BUCKET_NAME"

# Sync files to S3
aws s3 sync dist/tradeseeker-web-v2/ s3://$BUCKET_NAME/ \
  --delete \
  --cache-control "public, max-age=31536000, immutable" \
  --exclude "index.html"

# Upload index.html with no-cache to ensure updates are immediate
aws s3 cp dist/tradeseeker-web-v2/index.html s3://$BUCKET_NAME/index.html \
  --cache-control "no-cache, no-store, must-revalidate"

echo "Files uploaded to S3"

# Invalidate CloudFront cache
echo "Invalidating CloudFront cache..."
aws cloudfront create-invalidation \
  --distribution-id $DISTRIBUTION_ID \
  --paths "/*"

echo "Deployment complete!"
```

**Deployment Process**:
1. Sync all files to S3 with long cache headers (1 year)
2. Upload index.html separately with no-cache headers
3. Invalidate CloudFront cache to serve new content immediately

#### Cache Invalidation Script (scripts/invalidate-cache.sh)

```bash
#!/bin/bash
set -e

DISTRIBUTION_ID=$1

if [ -z "$DISTRIBUTION_ID" ]; then
  echo "Usage: ./invalidate-cache.sh <cloudfront-distribution-id>"
  exit 1
fi

echo "Invalidating CloudFront cache for distribution: $DISTRIBUTION_ID"

aws cloudfront create-invalidation \
  --distribution-id $DISTRIBUTION_ID \
  --paths "/*"

echo "Cache invalidation initiated"
```

### Environment Configuration

#### Environment Files

**src/environments/environment.ts** (Development):
```typescript
export const environment = {
  production: false,
  apiBaseUrl: 'https://56qpa0i92h.execute-api.ap-southeast-1.amazonaws.com/dev',
  cognitoUserPoolId: 'ap-southeast-1_XXXXXXXXX',
  cognitoClientId: 'XXXXXXXXXXXXXXXXXXXXXXXXXX',
  cognitoRegion: 'ap-southeast-1'
};
```

**src/environments/environment.prod.ts** (Production):
```typescript
export const environment = {
  production: true,
  apiBaseUrl: 'https://56qpa0i92h.execute-api.ap-southeast-1.amazonaws.com/dev',
  cognitoUserPoolId: 'ap-southeast-1_XXXXXXXXX',
  cognitoClientId: 'XXXXXXXXXXXXXXXXXXXXXXXXXX',
  cognitoRegion: 'ap-southeast-1'
};
```

**Environment Configuration Details**:
- API base URL configured per environment
- Cognito credentials configured per environment
- Angular CLI replaces environment.ts with environment.prod.ts during production build
- No hardcoded credentials in source code

### SPA Routing Configuration

To support Angular's client-side routing on S3/CloudFront:

1. **S3 Error Document**: Set to `index.html` so all 404s serve the Angular app
2. **CloudFront Custom Error Responses**: Return 200 status with index.html for 404/403 errors
3. **Angular Router**: Uses PathLocationStrategy (default) for clean URLs without hash

This ensures that direct navigation to routes like `/dashboard` works correctly, as CloudFront/S3 will serve index.html, and Angular will handle the routing client-side.

### CORS Configuration

**S3 CORS**: Configured to allow browser access to static assets
**API CORS**: The tradeseeker-api-v2 backend must have CORS configured to allow requests from the CloudFront domain

**Required API CORS Headers**:
```
Access-Control-Allow-Origin: https://<cloudfront-domain>
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Authorization, Content-Type
Access-Control-Max-Age: 3600
```


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

**Property 12: Partial failure resilience**
*For any* list of stock symbols where some requests fail, the application should continue processing remaining symbols and render charts for successfully fetched data.
**Validates: Requirements 3.3**

**Property 13: Chart rendering after data load**
*For any* set of successfully fetched stock data, once all requests complete, the application should render the Chart Grid with all available data.
**Validates: Requirements 3.4**

### Responsive Layout Properties

**Property 14: Responsive grid columns**
*For any* viewport width, the chart grid should display an appropriate number of columns: 6 for large monitors (2560px+), 4-5 for desktops (1920px), 3 for medium (1440px), 2 for tablets (768px), and 1 for mobile (<768px).
**Validates: Requirements 4.1, 4.2**

**Property 15: Dynamic layout reflow**
*For any* browser window resize event, the chart grid should reflow the layout to match the new viewport width without requiring a page reload.
**Validates: Requirements 4.5**

### Chart Display Properties

**Property 16: Complete chart rendering**
*For any* stock data with symbol, prices, and EMA values, the rendered chart should display the symbol name, price data as a candlestick or line chart, and all four EMA lines (7, 30, 50, 200) with distinct colors.
**Validates: Requirements 5.1, 5.2, 5.3, 5.4**

**Property 17: Chart state indicators**
*For any* stock chart, the component should display appropriate state indicators: loading indicator while data is fetching, error state with symbol name when data fails to load, and rendered chart when data is available.
**Validates: Requirements 5.6, 5.7**

### Data Refresh Properties

**Property 18: Manual refresh triggers data fetch**
*For any* dashboard state, clicking the refresh button should trigger a new fetch of the golden cross list and stock data for all symbols.
**Validates: Requirements 7.1**

**Property 19: Refresh loading state**
*For any* refresh operation in progress, the application should display a loading indicator and prevent duplicate refresh requests until the current refresh completes.
**Validates: Requirements 7.2, 7.4**

**Property 20: Automatic refresh interval**
*For any* configured refresh interval (default 5 minutes), when automatic refresh is enabled, the application should automatically fetch new data at that interval.
**Validates: Requirements 7.3**

**Property 21: Chart updates after refresh**
*For any* completed refresh operation, all stock charts should update to display the newly fetched data.
**Validates: Requirements 7.5**

### Market Selection Properties

**Property 22: Market change triggers new data fetch**
*For any* market selection change, the application should clear existing chart data and fetch the golden cross list for the newly selected market.
**Validates: Requirements 8.2, 8.3**

**Property 23: Market selection persistence**
*For any* market selection made during a user session, the selection should be persisted and restored if the user navigates within the application.
**Validates: Requirements 8.5**

### Error Handling Properties

**Property 24: Comprehensive error display**
*For any* error (network, authentication, API), the application should display a user-friendly error message with actionable guidance (e.g., "Retry", "Login Again") and log detailed error information to the browser console.
**Validates: Requirements 9.1, 9.2, 9.3, 9.6**

**Property 25: Error clearing on success**
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

### Multi-Chart Stock Detail Properties

**Property 26: Stock symbol click navigation**
*For any* stock symbol displayed in a dashboard chart, clicking the symbol should open a new browser tab with the URL `/stock/{symbol}` and load the Stock Detail Component.
**Validates: Multi-chart navigation requirement**

**Property 27: History endpoint usage for stock detail**
*For any* stock symbol in the Stock Detail Component, the application should make exactly 1 API request using the regular ApiService `GET /stocks/{symbol}` (with proper CORS and authentication headers) and then filter it client-side to create 6 different time period views with varying numbers of data points (90, 180, 365, 1095, 1825, 3650 latest entries).
**Validates: Multi-chart data requirement**

**Property 28: Data point accuracy**
*For any* time range filter in Stock Detail Component, the filtered dataset should contain exactly the requested number of latest price entries (or fewer if insufficient data exists), sorted chronologically from oldest to newest for time periods: 3 Months (90), 6 Months (180), 1 Year (365), 3 Years (1095), 5 Years (1825), 10 Years (3650).
**Validates: Client-side filtering requirement**

**Property 29: Multi-chart grid rendering**
*For any* successfully fetched stock data array in Stock Detail Component, the application should render exactly 6 charts in a responsive grid layout, each labeled with its corresponding time period.
**Validates: Multi-chart display requirement**

**Property 30: Partial multi-chart failure resilience**
*For any* set of 6 time range requests where some fail, the Stock Detail Component should render charts only for successfully fetched data and handle failed requests gracefully without crashing.
**Validates: Multi-chart error handling requirement**

**Property 31: Stock Detail responsive layout**
*For any* viewport width in Stock Detail Component, the chart grid should display an appropriate number of columns: 2-3 for desktop (1200px+), 2 for tablet (768-1199px), and 1 for mobile (<768px).
**Validates: Multi-chart responsive requirement**

**Property 32: Simplified navigation**
*For any* Stock Detail Component instance, users can navigate back using standard browser controls (back button, close tab) without requiring custom navigation buttons.
**Validates: Simplified UX requirement**

### Deployment and Infrastructure Properties

**Property 33: Static deployment accessibility**
*For any* production deployment, the application should be accessible via HTTPS through CloudFront, serve optimized static assets with appropriate cache headers, and support Angular client-side routing by serving index.html for all routes.
**Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5**

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
- Error handling with various error types
- Responsive layout with different viewport sizes
- Chart rendering with randomized stock data
- Refresh and market selection with various states

### Infrastructure Testing

**Terraform Validation**:
- Run `terraform validate` to check configuration syntax
- Run `terraform plan` to preview infrastructure changes
- Use Terraform Cloud or local state management

**Deployment Testing**:
- Verify S3 bucket is publicly accessible
- Verify CloudFront distribution serves content over HTTPS
- Test SPA routing by directly accessing routes (e.g., /dashboard)
- Verify cache headers on static assets
- Test cache invalidation after deployment

**Manual Verification Checklist**:
- [ ] Application loads via CloudFront URL
- [ ] HTTPS redirect works (HTTP → HTTPS)
- [ ] Direct navigation to /dashboard works
- [ ] Static assets load with correct cache headers
- [ ] API calls work from deployed application
- [ ] Authentication flow works end-to-end

### Integration Testing

**Framework**: Cypress or Playwright for E2E testing

**Focus Areas**:
- Complete user flows (login → dashboard → view charts)
- API integration with mocked backend
- Responsive behavior across device sizes
- Error recovery flows

### Test Coverage Goals

- Unit test coverage: >80% for services and components
- Property test coverage: All 26 correctness properties implemented
- E2E test coverage: All critical user flows
- Edge case coverage: All identified edge cases tested
- Infrastructure validation: Terraform configuration validated before each deployment

### Continuous Integration

- Run all tests on every commit
- Block merges if tests fail
- Generate coverage reports
- Run E2E tests on staging environment before production deployment
