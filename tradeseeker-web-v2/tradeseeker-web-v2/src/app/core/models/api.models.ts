/**
 * API-related data models for tradeseeker-api-v2
 */

/**
 * Response from golden cross API endpoint
 */
export interface GoldenCrossResponse {
  data: GoldenCrossStock[];
}

/**
 * Individual golden cross stock data
 */
export interface GoldenCrossStock {
  symbol: string;
  market_code: string;
  signal: string;
  cross_date: string;
  detected_at: string;
  ema_50: number;
  ema_200: number;
  crossover_strength: number;
  green_days_30d_pct: number;
  max_red_candle_30d_pct: number;
  ttl: number;
}

/**
 * Response from all-time high API endpoint
 */
export interface ATHResponse {
  data: ATHStock[];
}

/**
 * Individual all-time high stock data
 */
export interface ATHStock {
  symbol: string;                    // Stock symbol with market code (e.g., "AAPL.US")
  detection_date: string;            // Date when ATH was detected (YYYY-MM-DD)
  ath_price: number;                 // The all-time high price that was reached
  ath_percentage_gain: number;       // Percentage gain from lowest price to new ATH
  market_code: string;               // Market code (e.g., "US", "BK", "CC")
  detected_at: string;               // ISO timestamp when detection was processed
  ttl: number;                       // Unix timestamp for TTL (30 days from detection)
}

/**
 * Response wrapper for stock data API endpoint
 */
export interface StockDataResponse {
  data: StockData;
}

/**
 * Complete stock data including prices and EMAs
 */
export interface StockData {
  symbol: string;
  prices: PricePoint[];
  emas: EMAData;
  lastUpdated: string;
}

/**
 * Extended stock data that includes both price/chart data and golden cross metadata
 */
export interface EnhancedStockData {
  stockData: StockData;
  goldenCrossData: GoldenCrossStock;
}

/**
 * Raw stock data from API (before transformation)
 */
export interface RawStockData {
  symbol: string;
  prices: PricePoint[];
  moving_averages: MovingAveragePoint[];
  updated_at: string;
  [key: string]: any; // Allow other fields from API
}

/**
 * Single moving average point with date and EMA values
 */
export interface MovingAveragePoint {
  date: string;
  ema_7: number | null;
  ema_30: number | null;
  ema_50: number | null;
  ema_200: number | null;
}

/**
 * Single price point for candlestick/line chart
 */
export interface PricePoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

/**
 * Exponential Moving Average data for all periods
 */
export interface EMAData {
  ema7: number[];
  ema30: number[];
  ema50: number[];
  ema200: number[];
}
