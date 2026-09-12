import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { Location } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { ApiService } from '../../core/services/api.service';
import { WatchlistService } from '../../core/services/watchlist.service';
import { StockData, ChartType, ChartDisplayMode } from '../../core/models';
import { StockChartComponent } from '../dashboard/components/stock-chart/stock-chart.component';
import { ChartTypeSelectorComponent } from '../dashboard/components/chart-type-selector/chart-type-selector.component';
import { ChartDisplayModeSelectorComponent } from '../dashboard/components/chart-display-mode-selector/chart-display-mode-selector.component';
import { LoadingSpinnerComponent } from '../../shared/components/loading-spinner/loading-spinner.component';
import { ErrorMessageComponent } from '../../shared/components/error-message/error-message.component';

export interface TimeRange {
  label: string;
  days: number;
}

export interface OpenAIAnalysisResponse {
  data: {
    symbol: string;
    analysis_type: string;
    model: string;
    analysis: string;
    news_sources_checked: boolean;
    usage: {
      prompt_tokens: number;
      completion_tokens: number;
      total_tokens: number;
    };
  };
}

@Component({
  selector: 'app-stock-detail',
  standalone: true,
  imports: [
    CommonModule,
    StockChartComponent,
    ChartTypeSelectorComponent,
    ChartDisplayModeSelectorComponent,
    LoadingSpinnerComponent,
    ErrorMessageComponent
  ],
  templateUrl: './stock-detail.component.html',
  styleUrls: ['./stock-detail.component.scss']
})
export class StockDetailComponent implements OnInit, OnDestroy {
  symbol: string = '';
  stockDataArray: StockData[] = [];
  isLoading = false;
  error: string | null = null;
  selectedChartType: ChartType = 'candlestick';
  selectedDisplayMode: ChartDisplayMode = 'both';
  
  // OpenAI Analysis properties
  openAIAnalysis: OpenAIAnalysisResponse['data'] | null = null;
  isLoadingOpenAI = false;
  openAIError: string | null = null;

  // Refresh properties
  isRefreshing = false;
  refreshMessage: string | null = null;
  refreshError: string | null = null;
  
  private destroy$ = new Subject<void>();
  
  readonly timeRanges: TimeRange[] = [
    { label: '3 Months', days: 90 },
    { label: '6 Months', days: 180 },
    { label: '1 Year', days: 365 },
    { label: '3 Years', days: 1095 },
    { label: '5 Years', days: 1825 },
    { label: '10 Years', days: 3650 }
  ];

  showScrollTop = false;
  private onScrollBound = this.onScroll.bind(this);

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private location: Location,
    private apiService: ApiService,
    private watchlistService: WatchlistService,
    private http: HttpClient
  ) {}

  get isWatched(): boolean {
    return this.watchlistService.isWatched(this.symbol);
  }

  toggleWatchlist(): void {
    this.watchlistService.toggle(this.symbol).subscribe();
  }

  get isNative(): boolean {
    return !!(window as any).Capacitor?.isNativePlatform?.();
  }

  goBack(): void {
    this.location.back();
  }

  ngOnInit(): void {
    window.addEventListener('scroll', this.onScrollBound);

    // Load watchlist state so isWatched is accurate
    this.watchlistService.loadWatchlist().pipe(takeUntil(this.destroy$)).subscribe();

    // Restore chart type from session storage
    const savedChartType = sessionStorage.getItem('detailChartType') as ChartType;
    if (savedChartType) {
      this.selectedChartType = savedChartType;
    }

    // Restore display mode from session storage
    const savedDisplayMode = sessionStorage.getItem('detailDisplayMode') as ChartDisplayMode;
    if (savedDisplayMode) {
      this.selectedDisplayMode = savedDisplayMode;
    }

    this.route.params.pipe(
      takeUntil(this.destroy$)
    ).subscribe(params => {
      this.symbol = params['symbol'];
      if (this.symbol) {
        this.loadStockData();
      }
    });
  }

  ngOnDestroy(): void {
    window.removeEventListener('scroll', this.onScrollBound);
    this.destroy$.next();
    this.destroy$.complete();
  }

  onScroll(): void {
    this.showScrollTop = window.scrollY > 300;
  }

  scrollToTop(): void {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  private loadStockData(): void {
    this.isLoading = true;
    this.error = null;
    this.stockDataArray = [];

    // Use the regular API service which has proper CORS and auth headers
    this.apiService.getStockData(this.symbol).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: (fullStockData) => {
        if (fullStockData) {
          // Create filtered datasets for each time range
          this.stockDataArray = this.timeRanges.map(range => 
            this.filterStockDataByDays(fullStockData, range.days)
          ).filter(data => data !== null) as StockData[];
          
          this.isLoading = false;
          
          if (this.stockDataArray.length === 0) {
            this.error = `No data available for ${this.symbol}`;
          }
        } else {
          this.error = `No data available for ${this.symbol}`;
          this.isLoading = false;
        }
      },
      error: (error) => {
        console.error('Error loading stock data:', error);
        this.error = `Failed to load data for ${this.symbol}`;
        this.isLoading = false;
      }
    });
  }

  /**
   * Filter stock data to show only the latest N days of data
   */
  private filterStockDataByDays(stockData: StockData, days: number): StockData | null {
    if (!stockData.prices || stockData.prices.length === 0) {
      return null;
    }

    // Sort prices by date (newest first) and take the latest N items
    const sortedPrices = [...stockData.prices]
      .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
      .slice(0, days)
      .reverse(); // Reverse to get chronological order (oldest to newest)

    if (sortedPrices.length === 0) {
      return null;
    }

    // Filter EMA data to match the same date range
    const filteredEmas: any = {
      ema7: [] as (number | null)[],
      ema30: [] as (number | null)[],
      ema50: [] as (number | null)[],
      ema200: [] as (number | null)[]
    };

    if (stockData.emas) {
      // Create a map of dates to their indices in the original arrays
      const dateToIndexMap = new Map<string, number>();
      stockData.prices.forEach((price, index) => {
        dateToIndexMap.set(price.date, index);
      });

      // For each filtered price date, get the corresponding EMA values
      sortedPrices.forEach(price => {
        const originalIndex = dateToIndexMap.get(price.date);
        if (originalIndex !== undefined) {
          filteredEmas.ema7.push(stockData.emas.ema7[originalIndex] ?? null);
          filteredEmas.ema30.push(stockData.emas.ema30[originalIndex] ?? null);
          filteredEmas.ema50.push(stockData.emas.ema50[originalIndex] ?? null);
          filteredEmas.ema200.push(stockData.emas.ema200[originalIndex] ?? null);
        } else {
          // If date not found, push null
          filteredEmas.ema7.push(null);
          filteredEmas.ema30.push(null);
          filteredEmas.ema50.push(null);
          filteredEmas.ema200.push(null);
        }
      });
    }

    return {
      symbol: stockData.symbol,
      prices: sortedPrices,
      emas: filteredEmas,
      lastUpdated: stockData.lastUpdated
    };
  }

  getTimeRangeLabel(index: number): string {
    return this.timeRanges[index]?.label || '';
  }

  onChartTypeChange(type: ChartType): void {
    this.selectedChartType = type;
    
    // Persist chart type selection
    sessionStorage.setItem('detailChartType', type);
  }

  onDisplayModeChange(mode: ChartDisplayMode): void {
    this.selectedDisplayMode = mode;
    
    // Persist display mode selection
    sessionStorage.setItem('detailDisplayMode', mode);
  }

  /**
   * Get debug info for a specific chart (useful for development)
   */
  getChartDebugInfo(index: number): string {
    const stockData = this.stockDataArray[index];
    const timeRange = this.timeRanges[index];
    
    if (!stockData || !timeRange) {
      return 'No data';
    }
    
    return `${timeRange.label}: ${stockData.prices.length}/${timeRange.days} data points`;
  }

  /**
   * Request a data refresh from EODHD via the API
   */
  refreshData(): void {
    if (!this.symbol || this.isRefreshing) return;

    this.isRefreshing = true;
    this.refreshMessage = null;
    this.refreshError = null;

    const apiUrl = `https://56qpa0i92h.execute-api.ap-southeast-1.amazonaws.com/dev/stocks/${encodeURIComponent(this.symbol)}/refresh`;

    this.http.post<any>(apiUrl, {}).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: (response) => {
        this.isRefreshing = false;
        this.refreshMessage = response?.data?.message || `Refresh queued for ${this.symbol}. Data will update in ~1–2 minutes.`;
        // Auto-clear message after 6 seconds
        setTimeout(() => { this.refreshMessage = null; }, 6000);
      },
      error: (error) => {
        console.error('Error requesting refresh:', error);
        this.isRefreshing = false;
        this.refreshError = `Failed to queue refresh for ${this.symbol}. Please try again.`;
        setTimeout(() => { this.refreshError = null; }, 6000);
      }
    });
  }

  /**
   * Get OpenAI analysis for the current stock
   */
  getOpenAIAnalysis(): void {
    if (!this.symbol) {
      return;
    }

    this.isLoadingOpenAI = true;
    this.openAIError = null;
    this.openAIAnalysis = null;

    const apiUrl = `https://56qpa0i92h.execute-api.ap-southeast-1.amazonaws.com/dev/openai-summary?symbol=${this.symbol}`;

    this.http.get<OpenAIAnalysisResponse>(apiUrl).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: (response) => {
        this.openAIAnalysis = response.data;
        this.isLoadingOpenAI = false;
      },
      error: (error) => {
        console.error('Error fetching OpenAI analysis:', error);
        this.openAIError = `Failed to get AI analysis for ${this.symbol}. Please try again.`;
        this.isLoadingOpenAI = false;
      }
    });
  }

  /**
   * Format the analysis text for HTML display
   */
  getFormattedAnalysis(): string {
    if (!this.openAIAnalysis?.analysis) {
      return '';
    }

    // Remove the "Overall Sentiment Classification" section
    let cleanedAnalysis = this.openAIAnalysis.analysis
      .replace(/\d+\.\s*\*\*Overall Sentiment Classification\*\*:\s*[A-Z]+/gi, '')
      .replace(/Overall Sentiment Classification:\s*[A-Z]+/gi, '')
      .trim();

    // Handle numbered list format (1. **Title**: Content) - remove numbers
    let formatted = cleanedAnalysis
      // Convert numbered points with bold titles, removing the number
      .replace(/(\d+)\.\s*\*\*(.*?)\*\*:\s*(.*?)(?=\d+\.|$)/gs, '<div class="analysis-point"><div class="point-content"><h4>$2</h4><p>$3</p></div></div>')
      // Handle remaining bold text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      // Handle italic text
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      // Convert line breaks
      .replace(/\n\n/g, '</p><p>')
      .replace(/\n/g, '<br>');

    // If no numbered format detected, use the original formatting
    if (!formatted.includes('analysis-point')) {
      formatted = cleanedAnalysis
        .replace(/### (.*?)$/gm, '<h3>$1</h3>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');
      
      return `<p>${formatted}</p>`;
    }

    return formatted;
  }

  /**
   * Extract sentiment from analysis text
   */
  getSentimentFromAnalysis(): string {
    if (!this.openAIAnalysis?.analysis) {
      return 'neutral';
    }

    const analysis = this.openAIAnalysis.analysis.toUpperCase();
    
    // Look for explicit sentiment classification
    if (analysis.includes('OVERALL SENTIMENT CLASSIFICATION')) {
      const sentimentMatch = analysis.match(/OVERALL SENTIMENT CLASSIFICATION.*?:\s*(POSITIVE|NEGATIVE|NEUTRAL)/);
      if (sentimentMatch) {
        return sentimentMatch[1].toLowerCase();
      }
    }

    // Fallback: analyze sentiment keywords
    const positiveKeywords = ['POSITIVE', 'OPTIMISTIC', 'BULLISH', 'GROWTH', 'OPPORTUNITY'];
    const negativeKeywords = ['NEGATIVE', 'PESSIMISTIC', 'BEARISH', 'DECLINE', 'RISK'];
    
    const positiveCount = positiveKeywords.filter(keyword => analysis.includes(keyword)).length;
    const negativeCount = negativeKeywords.filter(keyword => analysis.includes(keyword)).length;
    
    if (positiveCount > negativeCount) return 'positive';
    if (negativeCount > positiveCount) return 'negative';
    return 'neutral';
  }

  /**
   * Get CSS class for sentiment badge
   */
  getSentimentClass(): string {
    const sentiment = this.getSentimentFromAnalysis();
    return `sentiment-${sentiment}`;
  }
}