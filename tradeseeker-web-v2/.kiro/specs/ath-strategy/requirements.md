# ATH (All Time High) Strategy Feature Requirements

## Overview
Add support for displaying stocks that have recently reached all-time high prices as a new trading strategy option in the TradeSeeker dashboard.

## User Stories

### US-1: ATH Strategy Selection
**As a** trader  
**I want** to select "ATH" (All Time High) as a trading strategy  
**So that** I can view stocks that have recently reached all-time high prices

**Acceptance Criteria:**
- ATH option appears in the strategy selector dropdown
- ATH option is labeled as "All Time High" in the UI
- Selecting ATH strategy triggers data fetch for ATH stocks
- ATH strategy selection persists in session storage

### US-2: ATH Stock Data Display
**As a** trader  
**I want** to see charts for stocks that have reached all-time highs  
**So that** I can analyze their recent performance and potential opportunities

**Acceptance Criteria:**
- Dashboard displays stock charts for ATH stocks when ATH strategy is selected
- Charts show the same data visualization as other strategies (price, EMA lines)
- Stock data is filtered by selected market (US, BK, CC)
- Loading states and error handling work consistently with other strategies

### US-3: ATH API Integration
**As a** system  
**I want** to fetch ATH stock data from the backend API  
**So that** current all-time high stocks are displayed to users

**Acceptance Criteria:**
- Dashboard calls the ATH API endpoint when ATH strategy is selected
- API supports market filtering (US, BK, CC markets)
- API response is properly parsed and symbols extracted
- Error handling provides meaningful feedback for API failures

## Technical Requirements

### TR-1: Strategy Selector Component
- Add "ath" option to strategies array in StrategySelectorComponent
- Label should be "All Time High"
- Component should emit strategy change events for ATH selection

### TR-2: Dashboard Component Integration
- Dashboard component should handle "ath" strategy selection
- Should call appropriate API method (getATHStocks) for ATH strategy
- Should clear existing data when switching to/from ATH strategy
- Should maintain consistent loading and error states

### TR-3: API Service Integration
- Utilize existing getATHStocks() method in ApiService
- Support market parameter filtering
- Handle ATH API response format consistently with other strategy APIs
- Maintain error handling and retry logic

## Data Models

### ATH Stock Response
The ATH API returns data in the following format:
```typescript
interface ATHResponse {
  data: ATHStock[];
  count: number;
  market?: string;
}

interface ATHStock {
  symbol: string;                    // Stock symbol with market code (e.g., "AAPL.US")
  detection_date: string;            // Date when ATH was detected (YYYY-MM-DD)
  ath_price: number;                 // The all-time high price that was reached
  ath_percentage_gain: number;       // Percentage gain from lowest price to new ATH
  market_code: string;               // Market code (e.g., "US", "BK", "CC")
  detected_at: string;               // ISO timestamp when detection was processed
  ttl: number;                       // Unix timestamp for TTL (30 days from detection)
}
```

## Constraints

### C-1: Consistency with Existing Strategies
- ATH strategy should behave identically to golden-cross and death-cross strategies
- Same chart display modes, chart types, and market filtering should apply
- Same async data loading pattern should be used

### C-2: Session Persistence
- ATH strategy selection should persist in session storage like other strategies
- Should restore ATH selection on page refresh

### C-3: Market Filtering
- ATH stocks should be filtered by selected market (US, BK, CC)
- Market changes should trigger fresh ATH data fetch

## Success Criteria
- Users can select ATH strategy from dropdown
- ATH stocks display in chart grid when strategy is selected
- Charts show proper stock data with price and EMA information
- Market filtering works correctly for ATH stocks
- Loading and error states provide good user experience
- Strategy selection persists across browser sessions