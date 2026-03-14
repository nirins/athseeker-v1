# Near ATH Detection Feature

This document describes the Near All-Time High (Near ATH) detection system implemented for TradeSeekerAPI v2.

## Overview

The Near ATH detection system identifies stocks that are trading close to their all-time high prices but haven't quite reached new ATHs. This helps identify potential breakout candidates and stocks showing strong momentum.

## Key Features

- **Configurable Threshold**: Default 10% below ATH, configurable via `NEAR_ATH_THRESHOLD` environment variable
- **Volatility Filtering**: Rejects stocks with excessive daily volatility (>100% by default)
- **Beauty Score Integration**: Uses the same beauty score calculation as ATH detection
- **Recent Detection Window**: Focuses on the last 21 trading days
- **Closest Approach Selection**: Automatically selects the closest approach to ATH in the detection window

## Architecture

### Backend Components

#### 1. Near ATH Detector (`near_ath_detector.py`)
- Core detection logic
- Configurable thresholds for distance from ATH and volatility
- Finds the closest approach to ATH in recent trading days

#### 2. Storage Integration (`storage.py`)
- `save_near_ath_detection()` method
- Stores to `ts-batch-v2-{env}-near-ath` DynamoDB table
- 30-day TTL for automatic cleanup

#### 3. Downloader Integration (`downloader.py`)
- Added near ATH detection to the processing pipeline
- Integrated with existing beauty score calculation
- Parallel processing with ATH and cross signal detection

#### 4. API Handler (`near_ath_stocks.py`)
- GET `/near-ath` endpoint
- **Market-focused querying** for optimal performance
- Primary filtering options:
  - `market`: Market code filter (US, BK, CC) - **RECOMMENDED**
  - `max_distance`: Maximum distance from ATH percentage (default: 10)
  - `min_gain`: Minimum percentage gain filter (default: 0)
  - `limit`: Maximum results (default: 50, max: 100)
  - `offset`: Pagination offset (default: 0)
- Secondary filtering (ignored when market specified):
  - `date`: Specific date filter (YYYY-MM-DD)
  - `days`: Filter to last N days

#### 5. Database Client (`dynamodb_client.py`)
- `query_near_ath_stocks_by_date()`
- `query_near_ath_stocks_by_date_range()`
- `query_near_ath_stocks_by_beauty_score()`
- `scan_near_ath_stocks()`

#### 6. Validation (`validators.py`)
- `validate_near_ath_stocks_params()` function
- Parameter validation with appropriate error messages

### Frontend Components

#### TypeScript Interfaces (`api.models.ts`)
```typescript
export interface NearATHResponse {
  data: NearATHStock[];
}

export interface NearATHStock {
  symbol: string;
  detection_date: string;
  current_price: number;
  ath_price: number;
  ath_date: string;
  distance_from_ath_percentage: number;
  percentage_gain: number;
  market_code: string;
  detected_at: string;
  ttl: number;
}
```

## Detection Logic

### Algorithm
1. **Volatility Check**: Reject stocks with any day exceeding max daily volatility
2. **ATH Identification**: Find the highest price across entire price history
3. **Threshold Calculation**: Calculate near ATH threshold (e.g., 90% of ATH for 10% threshold)
4. **Recent Window Analysis**: Check last 21 trading days for prices within threshold
5. **Closest Selection**: Select the price closest to ATH (smallest distance percentage)
6. **Beauty Score**: Calculate breakout beauty score using the same algorithm as ATH

### Key Differences from ATH Detection
- **Threshold-based**: Must be within configurable percentage of ATH (not exactly at ATH)
- **Exclusion Logic**: Excludes prices that equal or exceed the ATH
- **Closest Approach**: Selects the closest approach rather than the highest price

## Configuration

### Environment Variables
- `NEAR_ATH_THRESHOLD`: Percentage threshold for "near" ATH (default: 10.0)
- `MAX_DAILY_VOLATILITY`: Maximum allowed daily volatility (default: 100.0)
- `NEAR_ATH_STOCKS_TABLE`: DynamoDB table name (default: ts-batch-v2-{env}-near-ath)

### Database Schema
The Near ATH table uses the same GSI structure as ATH:
- `market_code-detection_date-index`: For market + date queries
- `detection_date-index`: For date-only queries  
- `beauty_score-index`: For beauty score ordering

## API Usage Examples

### Get Near ATH stocks for US market (RECOMMENDED)
```bash
GET /near-ath?market=US&limit=20
```

### Get Near ATH stocks within 5% of ATH for US market
```bash
GET /near-ath?max_distance=5&market=US
```

### Get Near ATH stocks with minimum 10% gain for BK market
```bash
GET /near-ath?min_gain=10&market=BK
```

### Get Near ATH stocks for CC market with pagination
```bash
GET /near-ath?market=CC&limit=10&offset=20
```

### Alternative queries (less efficient, no market filter)
```bash
# Get Near ATH stocks from last 7 days (all markets)
GET /near-ath?days=7

# Get Near ATH stocks for specific date (all markets)
GET /near-ath?date=2024-03-14
```

## Response Format

```json
{
  "data": [
    {
      "symbol": "AAPL.US",
      "detection_date": "2024-03-14",
      "current_price": 185.50,
      "ath_price": 195.00,
      "ath_date": "2024-03-10",
      "distance_from_ath_percentage": 4.87,
      "percentage_gain": 23.45,
      "market_code": "US",
      "detected_at": "2024-03-14T10:30:00Z",
      "beauty_score": 78.5,
      "grade": "B",
      "ttl": 1710936600
    }
  ]
}
```

## Testing

The feature includes comprehensive unit tests covering:
- Basic near ATH detection
- Threshold boundary conditions
- Volatility filtering
- Closest approach selection
- Edge cases and error handling

## Integration Points

### Batch Processing
- Integrated into the existing downloader pipeline
- Runs alongside ATH and cross signal detection
- Uses the same beauty score calculation system

### API Layer
- Added to router with `/near-ath` endpoint
- Follows the same patterns as existing endpoints
- Consistent error handling and response formatting

### Frontend Ready
- TypeScript interfaces defined
- Consistent with existing API patterns
- Ready for dashboard integration

## Performance Considerations

- **Market-focused queries**: Primary query strategy uses beauty_score GSI with market filter for optimal performance
- **Date filters ignored**: When market is specified, date/days filters are ignored to use the most efficient query path
- Uses efficient DynamoDB GSI queries with automatic beauty score ordering
- 30-day TTL prevents table growth
- Configurable limits and pagination support
- Recommends always specifying market parameter for best performance

## Future Enhancements

1. **Multiple Thresholds**: Support for multiple distance thresholds (5%, 10%, 15%)
2. **Trend Analysis**: Integration with momentum indicators
3. **Alert System**: Real-time notifications for near ATH conditions
4. **Historical Analysis**: Tracking of near ATH success rates
5. **Sector Analysis**: Near ATH detection by sector/industry