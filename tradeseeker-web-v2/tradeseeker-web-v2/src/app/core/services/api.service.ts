import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, forkJoin, from, throwError } from 'rxjs';
import { map, catchError, retry, mergeMap, toArray, filter } from 'rxjs/operators';
import { GoldenCrossResponse, StockData, StockDataResponse, RawStockData, MovingAveragePoint, ATHResponse } from '../models';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private readonly baseUrl = environment.apiBaseUrl;
  private readonly MAX_CONCURRENT_REQUESTS = 6;

  constructor(private http: HttpClient) {}

  /**
   * Get the base URL for API requests
   */
  getBaseUrl(): string {
    return this.baseUrl;
  }

  /**
   * Fetch list of golden cross stocks for a market
   */
  getGoldenCrosses(market: string, limit?: number, offset?: number): Observable<GoldenCrossResponse> {
      let url = `${this.baseUrl}/golden-crosses?market=${market}`;
      const params: string[] = [];

      if (limit) {
        params.push(`limit=${limit}`);
      }
      if (offset) {
        params.push(`offset=${offset}`);
      }

      if (params.length > 0) {
        url += `&${params.join('&')}`;
      }

      return this.http.get<GoldenCrossResponse>(url).pipe(
        retry(2),
        catchError(this.handleError)
      );
    }

  /**
   * Fetch list of all-time high stocks for a market
   */
  getATHStocks(market?: string, days?: number, limit?: number, offset?: number): Observable<ATHResponse> {
      let url = `${this.baseUrl}/ath`;
      const params: string[] = [];

      if (market) {
        params.push(`market=${market}`);
      }
      if (days) {
        params.push(`days=${days}`);
      }
      if (limit) {
        params.push(`limit=${limit}`);
      }
      if (offset) {
        params.push(`offset=${offset}`);
      }

      // Add aggressive cache-busting parameters
      params.push(`_t=${Date.now()}`);
      params.push(`_r=${Math.random().toString(36).substring(7)}`);

      if (params.length > 0) {
        url += `?${params.join('&')}`;
      }

      return this.http.get<ATHResponse>(url).pipe(
        retry(2),
        catchError(this.handleError)
      );
    }

  /**
   * Fetch list of death cross stocks for a market
   */
  getDeathCrosses(market: string, limit?: number, offset?: number): Observable<GoldenCrossResponse> {
      let url = `${this.baseUrl}/death-crosses?market=${market}`;
      const params: string[] = [];

      if (limit) {
        params.push(`limit=${limit}`);
      }
      if (offset) {
        params.push(`offset=${offset}`);
      }

      if (params.length > 0) {
        url += `&${params.join('&')}`;
      }

      return this.http.get<GoldenCrossResponse>(url).pipe(
        retry(2),
        catchError(this.handleError)
      );
    }

  /**
   * Fetch stocks based on strategy (golden cross, death cross, or ath)
   */
  getStrategyStocks(strategy: 'golden-cross' | 'death-cross' | 'ath', market: string, limit?: number, offset?: number): Observable<GoldenCrossResponse | ATHResponse> {
      if (strategy === 'death-cross') {
        return this.getDeathCrosses(market, limit, offset);
      } else if (strategy === 'ath') {
        return this.getATHStocks(market, undefined, limit, offset);
      } else {
        return this.getGoldenCrosses(market, limit, offset);
      }
    }

  /**
   * Fetch detailed stock data for a symbol
   */
  getStockData(symbol: string, days?: number): Observable<StockData> {
    let url = `${this.baseUrl}/stocks/${symbol}`;
    
    // Add days parameter if provided
    if (days) {
      url += `?days=${days}`;
    }
    
    return this.http.get<any>(url).pipe(
      retry(2),
      map(response => {
        // Handle nested data structure
        const stockData = response.data || response;
        return this.validateStockData(stockData);
      }),
      catchError((error) => this.handleStockDataError(error, symbol))
    );
  }

  /**
   * Fetch multiple stocks concurrently with concurrency limit
   */
  getMultipleStocks(symbols: string[], concurrency?: number): Observable<StockData[]> {
    if (symbols.length === 0) {
      return from([[]]);
    }

    const maxConcurrency = concurrency || this.MAX_CONCURRENT_REQUESTS;

    // Use mergeMap with concurrency limit to avoid overwhelming the API
    return from(symbols).pipe(
      mergeMap(
        symbol => this.getStockData(symbol).pipe(
          catchError(error => {
            console.error(`Error fetching data for ${symbol}:`, error);
            // Return null for failed requests to continue with other symbols
            // Don't throw - we want to continue fetching other stocks
            return from([null]);
          })
        ),
        maxConcurrency // Configurable concurrent requests
      ),
      filter((data): data is StockData => data !== null),
      toArray(),
      catchError(error => {
        console.error('Error in getMultipleStocks:', error);
        // Return empty array instead of throwing to prevent complete failure
        return from([[]]);
      })
    );
  }

  /**
   * Validate stock data has required fields and transform moving_averages to emas
   */
  private validateStockData(data: any): StockData {
    
    if (!data) {
      throw new Error('No data received from API');
    }

    if (!data.symbol || typeof data.symbol !== 'string') {
      throw new Error('Invalid stock data: missing or invalid symbol');
    }

    if (!data.prices || !Array.isArray(data.prices) || data.prices.length === 0) {
      throw new Error(`No price data available for ${data.symbol}`);
    }

    // Validate price data structure
    const hasValidPrices = data.prices.every((p: any) => 
      p.date && 
      typeof p.open === 'number' && 
      typeof p.high === 'number' && 
      typeof p.low === 'number' && 
      typeof p.close === 'number'
    );

    if (!hasValidPrices) {
      throw new Error(`Invalid price data structure for ${data.symbol}`);
    }

    // Transform moving_averages array to emas object structure
    let emas: any = {
      ema7: [],
      ema30: [],
      ema50: [],
      ema200: []
    };

    if (data.moving_averages && Array.isArray(data.moving_averages)) {
      
      // Extract EMA values from moving_averages array
      data.moving_averages.forEach((ma: any, index: number) => {
        emas.ema7.push(ma.ema_7);
        emas.ema30.push(ma.ema_30);
        emas.ema50.push(ma.ema_50);
        emas.ema200.push(ma.ema_200);
      });
    }

    // Set lastUpdated
    const lastUpdated = data.updated_at || data.lastUpdated || new Date().toISOString();

    // Return transformed data
    return {
      symbol: data.symbol,
      prices: data.prices,
      emas: emas,
      lastUpdated: lastUpdated
    } as StockData;
  }

  /**
   * Handle stock data specific errors
   */
  private handleStockDataError(error: HttpErrorResponse, symbol: string): Observable<never> {
    let errorMessage = `Error fetching data for ${symbol}`;

    if (error.error instanceof ErrorEvent) {
      // Client-side or network error
      errorMessage = `Network error while fetching ${symbol}: ${error.error.message}`;
    } else {
      // Backend returned an unsuccessful response code
      switch (error.status) {
        case 404:
          errorMessage = `Stock ${symbol} not found`;
          // For 404, we log but don't throw - let the caller handle it
          break;
        case 401:
          errorMessage = 'Session expired. Please log in again';
          break;
        case 500:
        case 502:
        case 503:
          errorMessage = `Server error while fetching ${symbol}. Please try again later`;
          break;
        default:
          errorMessage = `Error fetching ${symbol}: ${error.status}`;
      }
    }

    console.error('Stock data error:', errorMessage, error);
    return throwError(() => new Error(errorMessage));
  }

  /**
   * Handle HTTP errors and map to user-friendly messages
   */
  private handleError(error: HttpErrorResponse): Observable<never> {
    let errorMessage = 'An error occurred';
    let isRetryable = false;

    if (error.error instanceof ErrorEvent) {
      // Client-side or network error
      errorMessage = `Network error: ${error.error.message}`;
      isRetryable = true;
    } else if (error.status === 0) {
      // Network offline or CORS error
      errorMessage = 'Unable to connect to server. Please check your internet connection';
      isRetryable = true;
    } else {
      // Backend returned an unsuccessful response code
      switch (error.status) {
        case 400:
          errorMessage = 'Bad request. Please check your input';
          break;
        case 401:
          errorMessage = 'Session expired. Please log in again';
          // Don't retry auth errors
          break;
        case 403:
          errorMessage = 'Access forbidden. You do not have permission to access this resource';
          break;
        case 404:
          errorMessage = 'Resource not found';
          break;
        case 408:
          errorMessage = 'Request timeout. Please try again';
          isRetryable = true;
          break;
        case 429:
          errorMessage = 'Too many requests. Please wait a moment and try again';
          isRetryable = true;
          break;
        case 500:
          errorMessage = 'Server error. Please try again later';
          isRetryable = true;
          break;
        case 502:
          errorMessage = 'Bad gateway. The server is temporarily unavailable';
          isRetryable = true;
          break;
        case 503:
          errorMessage = 'Service unavailable. Please try again later';
          isRetryable = true;
          break;
        case 504:
          errorMessage = 'Gateway timeout. The server took too long to respond';
          isRetryable = true;
          break;
        default:
          errorMessage = `Error: ${error.status} - ${error.message || 'Unknown error'}`;
          isRetryable = error.status >= 500;
      }
    }

    // Add retry guidance for retryable errors
    if (isRetryable) {
      errorMessage += ' (Retryable)';
    }

    console.error('API Error:', {
      message: errorMessage,
      status: error.status,
      statusText: error.statusText,
      url: error.url,
      isRetryable,
      error
    });

    return throwError(() => ({
      message: errorMessage,
      status: error.status,
      isRetryable,
      originalError: error
    }));
  }

  /**
   * Save stock data with grade label to S3 for training dataset
   */
  saveStockDataByGrade(symbol: string, grade: string, stockData: StockData): Observable<any> {
    const url = `${this.baseUrl}/training-data/save-by-grade`;
    
    const payload = {
      symbol: symbol,
      grade: grade,
      stockData: stockData,
      timestamp: new Date().toISOString()
    };

    return this.http.post<any>(url, payload).pipe(
      retry(1),
      catchError(this.handleError)
    );
  }
}
