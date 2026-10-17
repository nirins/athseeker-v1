import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, forkJoin, from, throwError, of } from 'rxjs';
import { map, catchError, retry, mergeMap, toArray, filter, tap } from 'rxjs/operators';
import { GoldenCrossResponse, StockData, StockDataResponse, RawStockData, MovingAveragePoint, ATHResponse, NearATHResponse, SpeculativeResponse, DivergenceResponse, ConfirmedReversalResponse, ShowcaseResponse, ShowcaseStock } from '../models';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private readonly baseUrl = environment.apiBaseUrl;
  private readonly MAX_CONCURRENT_REQUESTS = 6;
  private readonly CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes

  private stockCache = new Map<string, { data: StockData; timestamp: number }>();

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
      const fetchOne = (marketCode?: string): Observable<GoldenCrossResponse> => {
        let url = `${this.baseUrl}/golden-crosses?market=${marketCode}`;
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
      };

      return this.withMarketExpansion(market, fetchOne);
    }

  /**
   * Fetch list of all-time high stocks for a market
   */
  getATHStocks(market?: string, days?: number, limit?: number, offset?: number): Observable<ATHResponse> {
      const fetchOne = (marketCode?: string): Observable<ATHResponse> => {
        let url = `${this.baseUrl}/ath`;
        const params: string[] = [];

        if (marketCode) {
          params.push(`market=${marketCode}`);
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
      };

      return this.withMarketExpansion(market, fetchOne);
    }

  /**
   * Fetch list of death cross stocks for a market
   */
  getDeathCrosses(market: string, limit?: number, offset?: number): Observable<GoldenCrossResponse> {
      const fetchOne = (marketCode?: string): Observable<GoldenCrossResponse> => {
        let url = `${this.baseUrl}/death-crosses?market=${marketCode}`;
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
      };

      return this.withMarketExpansion(market, fetchOne);
    }

  /**
   * Fetch stocks based on strategy (golden cross, death cross, or ath)
   */
  getStrategyStocks(strategy: 'golden-cross' | 'death-cross' | 'ath' | 'near-ath' | 'hype' | 'divergence' | 'confirmed-reversal', market: string, limit?: number, offset?: number): Observable<GoldenCrossResponse | ATHResponse | NearATHResponse | SpeculativeResponse | DivergenceResponse | ConfirmedReversalResponse> {
      if (strategy === 'death-cross') {
        return this.getDeathCrosses(market, limit, offset);
      } else if (strategy === 'ath') {
        return this.getATHStocks(market, undefined, limit, offset);
      } else if (strategy === 'near-ath') {
        return this.getNearATHStocks(market, limit, offset);
      } else if (strategy === 'hype') {
        return this.getSpeculativeStocks(market, undefined, limit, offset);
      } else if (strategy === 'divergence') {
        return this.getDivergenceStocks(market, undefined, limit, offset);
      } else if (strategy === 'confirmed-reversal') {
        return this.getConfirmedReversalStocks(market, undefined, limit, offset);
      } else {
        return this.getGoldenCrosses(market, limit, offset);
      }
    }

  /**
   * Showcase: top stocks across every strategy on one page, capped at
   * `maxTotal` overall. Each strategy stores its score under a different
   * field name (beauty_score, speculative_score, divergence_score,
   * confirmed_reversal_score) with a different realistic range — a
   * Divergence score sitting right at its entry gate commonly lands in the
   * 20s-40s, while a strong ATH breakout commonly lands in the 60s-90s.
   * Ranking directly on those raw numbers lets whichever strategy scores
   * highest by nature crowd out every other strategy's results.
   *
   * To fix that, each stock is ranked by its *percentile within its own
   * strategy's pool* (rankScore, 0-100) rather than its raw score — "this is
   * one of my strategy's best results today" is comparable across
   * strategies even when the underlying formulas aren't. The real score
   * (`score`) is still what's shown on the card.
   *
   * Note: "hype" (speculative) is a risk/caution score, not an opportunity
   * score like the others — a high number there means more caution
   * warranted, not a better setup. It's still included per strategy choice;
   * percentile ranking means its *most unusual* (riskiest) stocks surface,
   * same as the others' best stocks, rather than this being fixed by the
   * normalization itself.
   *
   * `perStrategyCap` additionally caps how many of any one strategy's own
   * (already percentile-ranked) results are even eligible for the final
   * list — so no single strategy can fill all `maxTotal` slots just because
   * it happened to have more/stronger signals than the others that day.
   */
  getShowcaseStocks(market: string, maxTotal: number = 12, perStrategyLimit: number = 30, perStrategyCap: number = 3): Observable<ShowcaseResponse> {
    const STRATEGIES: Array<{ key: ShowcaseStock['strategy']; label: string; scoreField: string }> = [
      { key: 'ath', label: 'ATH', scoreField: 'beauty_score' },
      { key: 'near-ath', label: 'Near ATH', scoreField: 'beauty_score' },
      { key: 'golden-cross', label: 'Golden Cross', scoreField: 'beauty_score' },
      { key: 'divergence', label: 'Divergence', scoreField: 'divergence_score' },
      { key: 'confirmed-reversal', label: 'Confirmed Reversal', scoreField: 'confirmed_reversal_score' },
      { key: 'hype', label: 'Hype', scoreField: 'speculative_score' },
    ];

    const requests = STRATEGIES.map(({ key, label, scoreField }) =>
      this.getStrategyStocks(key, market, perStrategyLimit).pipe(
        map((response: any): ShowcaseStock[] => {
          const items = (response?.data ?? []).filter((item: any) => item[scoreField] != null);

          // Percentile rank within this strategy's own pool: lowest score
          // in the pool -> 0, highest -> 100. A pool of 1 item ranks at 100
          // (nothing to compare against, so don't penalize it).
          const sortedAsc = [...items].sort((a: any, b: any) => a[scoreField] - b[scoreField]);
          const rankByScore = new Map<number, number>();
          sortedAsc.forEach((item: any, i: number) => {
            rankByScore.set(item[scoreField], sortedAsc.length > 1 ? (i / (sortedAsc.length - 1)) * 100 : 100);
          });

          const ranked: ShowcaseStock[] = items.map((item: any): ShowcaseStock => ({
            symbol: item.symbol,
            market_code: item.market_code,
            strategy: key,
            strategyLabel: label,
            score: item[scoreField],
            rankScore: rankByScore.get(item[scoreField]) ?? 0,
            grade: item.grade,
          }));

          // Cap this strategy's own contribution before it ever competes
          // for a final slot, so no single strategy can crowd out the rest.
          return ranked
            .sort((a, b) => b.rankScore - a.rankScore)
            .slice(0, perStrategyCap);
        }),
        catchError(() => of([] as ShowcaseStock[]))
      )
    );

    return forkJoin(requests).pipe(
      map((resultsPerStrategy: ShowcaseStock[][]) => {
        const all = resultsPerStrategy.flat();

        // Dedupe by symbol, keeping whichever strategy ranks it highest
        // within its own pool
        const bestBySymbol = new Map<string, ShowcaseStock>();
        for (const item of all) {
          const existing = bestBySymbol.get(item.symbol);
          if (!existing || item.rankScore > existing.rankScore) {
            bestBySymbol.set(item.symbol, item);
          }
        }

        // Selection uses rankScore (percentile within each strategy) so no
        // one strategy's naturally-higher-scoring formula crowds out the
        // rest. Display order is the stock's own real score, descending —
        // separate concerns: rankScore picks who gets a seat, score orders
        // the room once they're in it.
        const selected = Array.from(bestBySymbol.values())
          .sort((a, b) => b.rankScore - a.rankScore)
          .slice(0, maxTotal);

        const ranked = selected.sort((a, b) => b.score - a.score);

        return { data: ranked };
      })
    );
  }

  getNearATHStocks(market?: string, limit?: number, offset?: number): Observable<NearATHResponse> {
    const fetchOne = (marketCode?: string): Observable<NearATHResponse> => {
      let url = `${this.baseUrl}/near-ath`;
      const params: string[] = [];

      if (marketCode) params.push(`market=${marketCode}`);
      if (limit) params.push(`limit=${limit}`);
      if (offset) params.push(`offset=${offset}`);
      params.push(`_t=${Date.now()}`);

      if (params.length > 0) url += `?${params.join('&')}`;

      return this.http.get<NearATHResponse>(url).pipe(
        retry(2),
        catchError(this.handleError)
      );
    };

    return this.withMarketExpansion(market, fetchOne);
  }

  /**
   * Fetch list of speculative-activity stocks for a market (volume spikes,
   * violent swings, severe red candles, parabolic run-ups)
   */
  getSpeculativeStocks(market?: string, minScore?: number, limit?: number, offset?: number): Observable<SpeculativeResponse> {
    const fetchOne = (marketCode?: string): Observable<SpeculativeResponse> => {
      let url = `${this.baseUrl}/speculative`;
      const params: string[] = [];

      if (marketCode) params.push(`market=${marketCode}`);
      if (minScore) params.push(`min_score=${minScore}`);
      if (limit) params.push(`limit=${limit}`);
      if (offset) params.push(`offset=${offset}`);
      params.push(`_t=${Date.now()}`);

      if (params.length > 0) url += `?${params.join('&')}`;

      return this.http.get<SpeculativeResponse>(url).pipe(
        retry(2),
        catchError(this.handleError)
      );
    };

    return this.withMarketExpansion(market, fetchOne);
  }

  /**
   * Fetch list of bullish price/RSI divergence stocks for a market
   * ("turning point at the bottom": price makes a lower low, RSI makes a
   * higher low at the same time)
   */
  getDivergenceStocks(market?: string, minScore?: number, limit?: number, offset?: number): Observable<DivergenceResponse> {
    const fetchOne = (marketCode?: string): Observable<DivergenceResponse> => {
      let url = `${this.baseUrl}/divergence`;
      const params: string[] = [];

      if (marketCode) params.push(`market=${marketCode}`);
      if (minScore) params.push(`min_score=${minScore}`);
      if (limit) params.push(`limit=${limit}`);
      if (offset) params.push(`offset=${offset}`);
      params.push(`_t=${Date.now()}`);

      if (params.length > 0) url += `?${params.join('&')}`;

      return this.http.get<DivergenceResponse>(url).pipe(
        retry(2),
        catchError(this.handleError)
      );
    };

    return this.withMarketExpansion(market, fetchOne);
  }

  /**
   * Fetch list of confirmed-reversal stocks for a market ("CR") — a bullish
   * divergence where price has already bounced meaningfully off the swing
   * low, not just a structural RSI signal that hasn't turned yet
   */
  getConfirmedReversalStocks(market?: string, minScore?: number, limit?: number, offset?: number): Observable<ConfirmedReversalResponse> {
    const fetchOne = (marketCode?: string): Observable<ConfirmedReversalResponse> => {
      let url = `${this.baseUrl}/confirmed-reversal`;
      const params: string[] = [];

      if (marketCode) params.push(`market=${marketCode}`);
      if (minScore) params.push(`min_score=${minScore}`);
      if (limit) params.push(`limit=${limit}`);
      if (offset) params.push(`offset=${offset}`);
      params.push(`_t=${Date.now()}`);

      if (params.length > 0) url += `?${params.join('&')}`;

      return this.http.get<ConfirmedReversalResponse>(url).pipe(
        retry(2),
        catchError(this.handleError)
      );
    };

    return this.withMarketExpansion(market, fetchOne);
  }

  /**
   * Some UI market options are a single virtual code that fans out to several
   * real backend market codes (e.g. "CH" covers Shanghai + Shenzhen, since
   * EODHD/DynamoDB track them as separate exchanges "SHG"/"SHE"). Callers
   * pass one market string; this expands it, fires one request per real
   * code in parallel, and merges the `data` arrays back into a single
   * response so the rest of the app never needs to know about the split.
   */
  private readonly VIRTUAL_MARKETS: Record<string, string[]> = {
    CH: ['SHG', 'SHE'],
  };

  private withMarketExpansion<T extends { data: any[] }>(
    market: string | undefined,
    fetchOne: (marketCode?: string) => Observable<T>
  ): Observable<T> {
    const realCodes = market ? this.VIRTUAL_MARKETS[market] : undefined;

    if (!realCodes) {
      return fetchOne(market);
    }

    return forkJoin(realCodes.map(code => fetchOne(code))).pipe(
      map(responses => ({ data: responses.flatMap(r => r.data) } as T))
    );
  }

  /**
   * Fetch stock data for multiple symbols in a single batch request
   */
  getBatchStockData(symbols: string[]): Observable<Map<string, StockData>> {
    if (symbols.length === 0) {
      return of(new Map());
    }

    // Check cache — return cached entries and only fetch missing ones
    const resultMap = new Map<string, StockData>();
    const toFetch: string[] = [];
    const now = Date.now();

    for (const symbol of symbols) {
      const cached = this.stockCache.get(`batch_${symbol}`);
      if (cached && now - cached.timestamp < this.CACHE_TTL_MS) {
        resultMap.set(symbol, cached.data);
      } else {
        toFetch.push(symbol);
      }
    }

    if (toFetch.length === 0) {
      return of(resultMap);
    }

    const symbolsParam = toFetch.join(',');
    const url = `${this.baseUrl}/stocks/batch?symbols=${encodeURIComponent(symbolsParam)}`;

    return this.http.get<any>(url).pipe(
      retry(2),
      map(response => {
        const results = response?.data?.results || response?.results || {};
        for (const [symbol, raw] of Object.entries(results)) {
          try {
            const data = this.validateStockData(raw);
            this.stockCache.set(`batch_${symbol}`, { data, timestamp: now });
            resultMap.set(symbol, data);
          } catch (e) {
            console.warn(`Skipping invalid batch data for ${symbol}:`, e);
          }
        }
        return resultMap;
      }),
      catchError(error => {
        console.error('Batch stock data error:', error);
        return throwError(() => error);
      })
    );
  }

  /**
   * Fetch detailed stock data for a symbol
   */
  getStockData(symbol: string, days?: number): Observable<StockData> {
    const cacheKey = days ? `${symbol}_${days}` : symbol;
    const cached = this.stockCache.get(cacheKey);

    if (cached && Date.now() - cached.timestamp < this.CACHE_TTL_MS) {
      return of(cached.data);
    }

    let url = `${this.baseUrl}/stocks/${symbol}`;
    if (days) {
      url += `?days=${days}`;
    }

    return this.http.get<any>(url).pipe(
      retry(2),
      map(response => {
        const stockData = response.data || response;
        return this.validateStockData(stockData);
      }),
      tap(data => this.stockCache.set(cacheKey, { data, timestamp: Date.now() })),
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
