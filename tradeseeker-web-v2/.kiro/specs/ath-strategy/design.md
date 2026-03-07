# ATH Strategy Feature Design

## Architecture Overview

The ATH (All Time High) strategy feature integrates into the existing TradeSeeker dashboard architecture by extending the strategy selection system. It follows the same patterns as golden-cross and death-cross strategies for consistency.

## Component Design

### 1. Strategy Selector Component Updates

**File:** `tradeseeker-web-v2/src/app/features/dashboard/components/strategy-selector/strategy-selector.component.ts`

**Changes Required:**
- Add ATH option to strategies array
- Maintain existing TradingStrategy type (already includes 'ath')

```typescript
strategies: StrategyOption[] = [
  { value: 'golden-cross', label: 'Golden Cross' },
  { value: 'death-cross', label: 'Death Cross' },
  { value: 'ath', label: 'All Time High' }
];
```

### 2. Dashboard Component Integration

**File:** `tradeseeker-web-v2/src/app/features/dashboard/dashboard.component.ts`

**Changes Required:**
- Update `getStrategyStocks()` method to handle ATH strategy
- Modify strategy change handler to support ATH data fetching
- Ensure consistent async data loading pattern

**Strategy Handling Logic:**
```typescript
getStrategyStocks(strategy: TradingStrategy, market: string): Observable<any> {
  switch (strategy) {
    case 'ath':
      return this.getATHStocks(market);
    case 'death-cross':
      return this.getDeathCrosses(market);
    case 'golden-cross':
    default:
      return this.getGoldenCrosses(market);
  }
}
```

### 3. API Service Integration

**File:** `tradeseeker-web-v2/src/app/core/services/api.service.ts`

**Current State:** ✅ Already implemented
- `getATHStocks()` method exists and supports market filtering
- Returns `Observable<ATHResponse>` with proper error handling
- Follows same patterns as other strategy API methods

## Data Flow

### 1. Strategy Selection Flow
```
User selects ATH → StrategySelectorComponent emits 'ath' → 
Dashboard.onStrategyChange() → Clear existing data → 
Call getStrategyStocks('ath', market) → API call to /ath endpoint
```

### 2. Data Processing Flow
```
ATH API Response → Extract symbols from response.data → 
Store symbols in goldenCrosses array (reused for all strategies) → 
Fetch individual stock data asynchronously → 
Add to stockDataArray as data arrives
```

### 3. Market Change Flow
```
Market change → Clear data → Call getStrategyStocks(currentStrategy, newMarket) → 
If ATH strategy: call getATHStocks(newMarket) → Process response
```

## API Integration

### ATH Endpoint
- **URL:** `GET /ath`
- **Parameters:** 
  - `market` (optional): Filter by market code (US, BK, CC)
  - `days` (optional): Number of days to look back
  - `limit` (optional): Maximum number of results

### Response Format
```typescript
interface ATHResponse {
  data: ATHStock[];
  count: number;
  market?: string;
}
```

### Error Handling
- Reuse existing error handling patterns from ApiService
- Display user-friendly error messages
- Support retry logic for transient failures

## State Management

### Session Storage
- Key: `'tradingStrategy'`
- Value: `TradingStrategy` ('ath' | 'golden-cross' | 'death-cross')
- Restored on component initialization

### Component State
- `selectedStrategy`: Current strategy selection
- `goldenCrosses`: Array of symbols (reused for all strategies)
- `stockDataArray`: Array of StockData objects for chart display

## UI/UX Considerations

### Strategy Selector
- ATH option appears as "All Time High" in dropdown
- Maintains consistent styling with existing options
- No visual distinction needed - follows existing patterns

### Loading States
- Same loading spinner and states as other strategies
- Individual charts load asynchronously as data arrives
- Error states display consistently

### Chart Display
- ATH stocks display in same chart grid layout
- Same chart types (line/candlestick) and display modes available
- Stock detail navigation works identically (click to open new tab)

## Performance Considerations

### Async Data Loading
- Maintain existing pattern of fetching strategy symbols first
- Then fetch individual stock data asynchronously
- Add charts to grid as data arrives (progressive loading)

### Caching
- Leverage existing HTTP client caching
- No additional caching layer needed for ATH data

### Concurrency
- Reuse existing MAX_CONCURRENT_REQUESTS limit (6)
- Same error handling for individual stock data failures

## Testing Strategy

### Unit Tests
- Test strategy selector includes ATH option
- Test dashboard handles ATH strategy selection
- Test API service getATHStocks method integration

### Integration Tests
- Test complete ATH strategy selection flow
- Test market filtering with ATH strategy
- Test error handling for ATH API failures

### Property-Based Tests
- Test ATH data processing with various response formats
- Test symbol extraction from ATH response data
- Test error handling with malformed ATH responses

## Implementation Approach

### Phase 1: Strategy Selector Update
1. Add ATH option to strategies array
2. Verify strategy change events work correctly

### Phase 2: Dashboard Integration
3. Update getStrategyStocks method to handle ATH
4. Test ATH strategy selection and data fetching
5. Verify market filtering works with ATH

### Phase 3: Testing & Validation
6. Test error handling scenarios
7. Verify session persistence
8. Test integration with existing chart features

## Correctness Properties

### Property 1: Strategy Selection Consistency
**Validates: Requirements US-1**
```
For any valid strategy selection (golden-cross, death-cross, ath),
the dashboard should clear existing data and fetch new data for the selected strategy.
```

### Property 2: ATH Data Processing
**Validates: Requirements US-2, TR-3**
```
For any valid ATH API response,
the system should extract symbols and fetch individual stock data,
resulting in charts being displayed in the grid.
```

### Property 3: Market Filtering
**Validates: Requirements US-2**
```
For any market selection (US, BK, CC) with ATH strategy,
the API should be called with the correct market parameter,
and only stocks from that market should be displayed.
```

### Property 4: Session Persistence
**Validates: Requirements US-1**
```
For any strategy selection including ATH,
the selection should be stored in session storage,
and restored correctly on page refresh.
```

## Dependencies

### Existing Components
- ✅ StrategySelectorComponent (needs update)
- ✅ DashboardComponent (needs update)
- ✅ ApiService (already complete)
- ✅ ATH data models (already defined)

### No New Dependencies
- No new npm packages required
- No new services or components needed
- Leverages existing chart and grid components