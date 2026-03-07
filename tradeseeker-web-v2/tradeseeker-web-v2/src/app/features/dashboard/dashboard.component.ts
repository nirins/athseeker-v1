import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { Subject, of } from 'rxjs';
import { switchMap, takeUntil, catchError } from 'rxjs/operators';
import { ApiService } from '../../core/services/api.service';
import { StockData, ChartDisplayMode, ChartType } from '../../core/models';
import { MarketSelectorComponent } from './components/market-selector/market-selector.component';
import { ChartDisplayModeSelectorComponent } from './components/chart-display-mode-selector/chart-display-mode-selector.component';
import { ChartTypeSelectorComponent } from './components/chart-type-selector/chart-type-selector.component';
import { StrategySelectorComponent, TradingStrategy } from './components/strategy-selector/strategy-selector.component';
import { ChartGridComponent } from './components/chart-grid/chart-grid.component';
import { LoadingSpinnerComponent } from '../../shared/components/loading-spinner/loading-spinner.component';
import { ErrorMessageComponent } from '../../shared/components/error-message/error-message.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    MarketSelectorComponent,
    ChartDisplayModeSelectorComponent,
    ChartTypeSelectorComponent,
    StrategySelectorComponent,
    ChartGridComponent,
    LoadingSpinnerComponent,
    ErrorMessageComponent
  ],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit, OnDestroy {
  selectedMarket: string = 'US';
  selectedDisplayMode: ChartDisplayMode = 'both';
  selectedChartType: ChartType = 'candlestick';
  selectedStrategy: TradingStrategy = 'ath';
  
  goldenCrosses: string[] = [];
  stockDataArray: StockData[] = [];
  isLoading = false;
  error: string | null = null;
  
  // Label mode for training data
  isLabelMode = false;
  
  // Pagination properties
  private readonly PAGE_SIZE = 50;
  private currentOffset = 0;
  allSymbols: string[] = []; // Made public for template access
  hasMoreData = false;
  isLoadingMore = false;
  
  private readonly REFRESH_INTERVAL_MS = 60 * 60 * 1000; // 1 hour
  private refreshInterval: any;
  private destroy$ = new Subject<void>();
  private refreshInProgress = false;
  private marketChange$ = new Subject<string>();

  // Grade selection for training data
  showGradePopup = false;
  selectedStockForGrading: StockData | null = null;
  availableGrades = [
    { value: 'A', label: 'A - Excellent' },
    { value: 'B', label: 'B - Good' },
    { value: 'C', label: 'C - Average' },
    { value: 'D', label: 'D - Poor' },
    { value: 'F', label: 'F - Failed' }
  ];

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    // Restore preferences from sessionStorage (only in browser)
    if (typeof window !== 'undefined' && typeof sessionStorage !== 'undefined') {
      const savedMarket = sessionStorage.getItem('selectedMarket');
      if (savedMarket) {
        this.selectedMarket = savedMarket;
      }

      const savedDisplayMode = sessionStorage.getItem('displayMode') as ChartDisplayMode;
      if (savedDisplayMode) {
        this.selectedDisplayMode = savedDisplayMode;
      }

      const savedChartType = sessionStorage.getItem('chartType') as ChartType;
      if (savedChartType) {
        this.selectedChartType = savedChartType;
      }

      const savedStrategy = sessionStorage.getItem('tradingStrategy') as TradingStrategy;
      if (savedStrategy) {
        this.selectedStrategy = savedStrategy;
      }
    }

    // Set up market change handler with switchMap to cancel previous requests
    this.setupMarketChangeHandler();

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
      // Prevent duplicate requests
      if (this.refreshInProgress) {
        console.log('Refresh already in progress, ignoring duplicate request');
        return;
      }

      this.refreshInProgress = true;
      this.isLoading = true;
      this.error = null;

      // Reset pagination state
      this.currentOffset = 0;
      this.allSymbols = [];
      this.hasMoreData = false;

      // Clear existing data to show loading state
      this.stockDataArray = [];

      this.loadStockPageWithFallback();
    }
  /**
   * Load a page of stocks with fallback to client-side pagination
   */
  private loadStockPageWithFallback(): void {
    // For ATH strategy, fetch all data on first load since API doesn't support proper pagination
    const shouldFetchAll = this.selectedStrategy === 'ath' && this.currentOffset === 0;
    const requestLimit = shouldFetchAll ? 100 : this.PAGE_SIZE; // Use max allowed limit (100) to get ATH data
    
    this.apiService.getStrategyStocks(this.selectedStrategy, this.selectedMarket, requestLimit, this.currentOffset)
      .pipe(
        switchMap(response => {
          console.log(`${this.selectedStrategy} API response (offset: ${this.currentOffset}):`, response);

          // Validate response structure
          if (!response || typeof response !== 'object') {
            throw new Error('Invalid API response: expected object');
          }

          if (!response.data || !Array.isArray(response.data)) {
            console.warn('API response missing data array:', response);
            this.goldenCrosses = this.currentOffset === 0 ? [] : this.goldenCrosses;
            this.hasMoreData = false;
            return of([]);
          }

          // Extract symbols from the data array
          const symbols = response.data.map(item => item.symbol);

          // For ATH strategy, always use client-side pagination since API doesn't support proper offset
          if (this.selectedStrategy === 'ath') {
            console.log('Using client-side pagination for ATH strategy, total symbols:', symbols.length);
            
            // Only update allSymbols on first load to avoid overwriting
            if (this.currentOffset === 0) {
              // Ensure no duplicates in allSymbols
              this.allSymbols = [...new Set(symbols)];
              console.log(`ATH strategy: Set allSymbols to ${this.allSymbols.length} total symbols`);
            }

            // Calculate which symbols to show for current page
            const startIndex = this.currentOffset;
            const endIndex = startIndex + this.PAGE_SIZE;
            const pageSymbols = this.allSymbols.slice(startIndex, endIndex);

            this.hasMoreData = endIndex < this.allSymbols.length;
            console.log(`ATH pagination: showing ${startIndex}-${Math.min(endIndex, this.allSymbols.length)} of ${this.allSymbols.length}, hasMoreData: ${this.hasMoreData}`);

            if (this.currentOffset === 0) {
              this.goldenCrosses = pageSymbols;
            } else {
              // Append new page symbols, avoiding duplicates
              const newSymbols = pageSymbols.filter(symbol => !this.goldenCrosses.includes(symbol));
              this.goldenCrosses = [...this.goldenCrosses, ...newSymbols];
            }

            // Use pageSymbols for fetching stock data
            symbols.splice(0, symbols.length, ...pageSymbols);
          } else {
            // For other strategies, check if backend supports pagination
            const backendSupportsPagination = this.currentOffset > 0 || symbols.length <= this.PAGE_SIZE;

            if (backendSupportsPagination) {
              // Backend supports pagination - use server-side pagination
              console.log('Using server-side pagination');
              this.hasMoreData = symbols.length === this.PAGE_SIZE;

              if (this.currentOffset === 0) {
                // Ensure no duplicates in the initial load
                this.goldenCrosses = [...new Set(symbols)];
                this.allSymbols = [...new Set(symbols)];
              } else {
                // Append new symbols, avoiding duplicates
                const newSymbols = symbols.filter(symbol => !this.allSymbols.includes(symbol));
                this.goldenCrosses = [...this.goldenCrosses, ...newSymbols];
                this.allSymbols = [...this.allSymbols, ...newSymbols];
              }
            } else {
              // Backend doesn't support pagination - use client-side pagination
              console.log('Using client-side pagination, total symbols:', symbols.length);
              
              // Only update allSymbols on first load to avoid overwriting
              if (this.currentOffset === 0) {
                // Ensure no duplicates in allSymbols
                this.allSymbols = [...new Set(symbols)];
              }

              // Calculate which symbols to show for current page
              const startIndex = this.currentOffset;
              const endIndex = startIndex + this.PAGE_SIZE;
              const pageSymbols = this.allSymbols.slice(startIndex, endIndex);

              this.hasMoreData = endIndex < this.allSymbols.length;

              if (this.currentOffset === 0) {
                this.goldenCrosses = pageSymbols;
              } else {
                // Append new page symbols, avoiding duplicates
                const newSymbols = pageSymbols.filter(symbol => !this.goldenCrosses.includes(symbol));
                this.goldenCrosses = [...this.goldenCrosses, ...newSymbols];
              }

              // Use pageSymbols for fetching stock data
              symbols.splice(0, symbols.length, ...pageSymbols);
            }
          }

          if (symbols.length === 0) {
            console.log(`No ${this.selectedStrategy} symbols found for market:`, this.selectedMarket);
            return of([]);
          }

          console.log(`Displaying ${symbols.length} ${this.selectedStrategy} symbols (total available: ${this.allSymbols.length})`);
          console.log('hasMoreData:', this.hasMoreData);

          // Fetch stock data individually and render as they arrive
          this.fetchStockDataAsync(symbols);

          return of([]);
        }),
        takeUntil(this.destroy$),
        catchError(error => {
          this.error = this.getErrorMessage(error);
          this.isLoading = false;
          this.isLoadingMore = false;
          this.refreshInProgress = false;
          return of([]);
        })
      )
      .subscribe(() => {
        this.isLoading = false;
        this.isLoadingMore = false;
        this.refreshInProgress = false;
      });
  }

  /**
   * Load more stocks (next page)
   */
  loadMore(): void {
    if (this.isLoadingMore || !this.hasMoreData) {
      console.log('Load more blocked:', { 
        isLoadingMore: this.isLoadingMore, 
        hasMoreData: this.hasMoreData,
        currentOffset: this.currentOffset,
        allSymbolsLength: this.allSymbols.length,
        stockDataArrayLength: this.stockDataArray.length
      });
      return;
    }

    console.log('Loading more stocks:', {
      currentOffset: this.currentOffset,
      pageSize: this.PAGE_SIZE,
      allSymbolsLength: this.allSymbols.length,
      stockDataArrayLength: this.stockDataArray.length,
      hasMoreData: this.hasMoreData
    });
    
    this.isLoadingMore = true;
    this.currentOffset += this.PAGE_SIZE;
    this.loadStockPageWithFallback();
  }

  /**
   * Fetch stock data asynchronously and add to array as they arrive
   */
  private fetchStockDataAsync(symbols: string[]): void {
    // Deduplicate symbols before fetching
    const uniqueSymbols = [...new Set(symbols)];
    
    uniqueSymbols.forEach(symbol => {
      this.apiService.getStockData(symbol).pipe(
        takeUntil(this.destroy$),
        catchError(error => {
          console.error(`Error fetching data for ${symbol}:`, error);
          // Don't add to array if failed, just continue
          return of(null);
        })
      ).subscribe(stockData => {
        if (stockData) {
          // Check if this symbol already exists in stockDataArray to prevent duplicates
          const existingIndex = this.stockDataArray.findIndex(data => data.symbol === stockData.symbol);
          if (existingIndex === -1) {
            // Add to array as soon as data arrives (only if not already present)
            this.stockDataArray = [...this.stockDataArray, stockData];
            console.log(`Added ${symbol} to chart grid (${this.stockDataArray.length}/${uniqueSymbols.length})`);
          } else {
            console.log(`Skipped duplicate ${symbol} - already in chart grid`);
          }
        }
      });
    });
  }

  onMarketChange(market: string): void {
      if (market === this.selectedMarket) {
        return;
      }

      this.selectedMarket = market;
      if (typeof window !== 'undefined' && typeof sessionStorage !== 'undefined') {
        sessionStorage.setItem('selectedMarket', market);
      }

      // Clear existing data and reset pagination
      this.stockDataArray = [];
      this.goldenCrosses = [];
      this.allSymbols = [];
      this.currentOffset = 0;
      this.hasMoreData = false;

      // Emit market change to trigger data fetch with switchMap
      // This will cancel any pending requests for the previous market
      this.marketChange$.next(market);
    }

  /**
   * Set up market change handler with switchMap to cancel previous requests
   */
  private setupMarketChangeHandler(): void {
    this.marketChange$
      .pipe(
        switchMap(market => {
          this.isLoading = true;
          this.error = null;
          this.refreshInProgress = true;
          
          // Clear existing data immediately
          this.stockDataArray = [];

          return this.apiService.getStrategyStocks(this.selectedStrategy, market).pipe(
            switchMap(response => {
              console.log(`Market change - ${this.selectedStrategy} API response:`, response);
              
              // Validate response structure
              if (!response || typeof response !== 'object') {
                throw new Error('Invalid API response: expected object');
              }
              
              if (!response.data || !Array.isArray(response.data)) {
                console.warn('Market change - API response missing data array:', response);
                this.goldenCrosses = [];
                return of([]);
              }

              // Extract symbols from the data array
              const symbols = response.data.map(item => item.symbol);
              this.goldenCrosses = symbols;

              if (symbols.length === 0) {
                console.log(`Market change - No ${this.selectedStrategy} symbols found for market:`, market);
                return of([]);
              }

              console.log(`Market change - Found ${symbols.length} ${this.selectedStrategy} symbols:`, symbols);
              
              // Fetch stock data individually and render as they arrive
              this.fetchStockDataAsync(symbols);
              
              // Return empty array since we're handling async rendering
              return of([]);
            }),
            catchError(error => {
              this.error = this.getErrorMessage(error);
              this.isLoading = false;
              this.refreshInProgress = false;
              return of([]);
            })
          );
        }),
        takeUntil(this.destroy$)
      )
      .subscribe(() => {
        console.log(`Market change - ${this.selectedStrategy} fetched, individual stock data will be added async`);
        this.isLoading = false;
        this.refreshInProgress = false;
      });
  }

  onDisplayModeChange(mode: ChartDisplayMode): void {
    this.selectedDisplayMode = mode;
    if (typeof window !== 'undefined' && typeof sessionStorage !== 'undefined') {
      sessionStorage.setItem('displayMode', mode);
    }
  }

  onChartTypeChange(type: ChartType): void {
    this.selectedChartType = type;
    if (typeof window !== 'undefined' && typeof sessionStorage !== 'undefined') {
      sessionStorage.setItem('chartType', type);
    }
  }

  onStrategyChange(strategy: TradingStrategy): void {
      this.selectedStrategy = strategy;
      if (typeof window !== 'undefined' && typeof sessionStorage !== 'undefined') {
        sessionStorage.setItem('tradingStrategy', strategy);
      }

      // Clear existing data and reset pagination
      this.stockDataArray = [];
      this.goldenCrosses = [];
      this.allSymbols = [];
      this.currentOffset = 0;
      this.hasMoreData = false;
      this.fetchData();
    }

  onRefresh(): void {
    // Prevent duplicate refresh requests
    if (this.isLoading || this.refreshInProgress) {
      console.log('Refresh already in progress, ignoring duplicate request');
      return;
    }

    this.fetchData();
  }

  /**
   * Toggle between view mode and label mode
   */
  toggleLabelMode(): void {
    this.isLabelMode = !this.isLabelMode;
    console.log(`Switched to ${this.isLabelMode ? 'label' : 'view'} mode`);
  }

  private setupAutoRefresh(): void {
    this.refreshInterval = setInterval(() => {
      // Only auto-refresh if not currently loading
      if (!this.isLoading && !this.refreshInProgress) {
        this.fetchData();
      }
    }, this.REFRESH_INTERVAL_MS);
  }

  private getErrorMessage(error: any): string {
    // Log the full error for debugging
    console.error('Dashboard error:', error);
    
    // Handle error object from ApiService (has message, status, isRetryable)
    const status = error?.status || error?.originalError?.status;
    const message = error?.message || error?.error?.message || error?.toString();
    
    if (status === 401) {
      return 'Session expired. Please log in again.';
    } else if (status === 404) {
      return 'Data not found for the selected market.';
    } else if (status >= 500) {
      return 'Server error occurred. Please try again later.';
    } else if (message?.includes('timeout')) {
      return 'Request timed out. Please check your connection.';
    } else if (message) {
      // Return the actual error message from the API service
      return message;
    } else {
      return 'An error occurred while fetching data.';
    }
  }

  // Grade selection methods for training data
  onGradeSelectionRequested(event: {symbol: string, stockData: StockData}): void {
    this.selectedStockForGrading = event.stockData;
    this.showGradePopup = true;
  }

  closeGradePopup(): void {
    this.showGradePopup = false;
    this.selectedStockForGrading = null;
  }

  selectGrade(grade: {value: string, label: string}): void {
    if (!this.selectedStockForGrading) {
      return;
    }

    // Call API to save stock data with grade to S3
    this.apiService.saveStockDataByGrade(
      this.selectedStockForGrading.symbol,
      grade.value,
      this.selectedStockForGrading
    ).pipe(
      takeUntil(this.destroy$),
      catchError(error => {
        console.error('Error saving stock data by grade:', error);
        this.error = `Failed to save training data: ${error.message || 'Unknown error'}`;
        return of(null);
      })
    ).subscribe(response => {
      if (response) {
        console.log(`Successfully saved ${this.selectedStockForGrading?.symbol} with grade ${grade.value}`);
        // Show success feedback (optional)
        // You could add a toast notification here
      }
    });

    this.closeGradePopup();
  }

  getGradeClass(gradeValue: string): string {
    const gradeClasses: {[key: string]: string} = {
      'A': 'grade-a',
      'B': 'grade-b',
      'C': 'grade-c',
      'D': 'grade-d',
      'F': 'grade-f'
    };
    return gradeClasses[gradeValue] || 'grade-default';
  }
}
