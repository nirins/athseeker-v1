# Property-Based Testing Infrastructure

This directory contains the property-based testing infrastructure for TradeSeekerWeb v2, built using [fast-check](https://github.com/dubzzz/fast-check).

## Overview

Property-based testing (PBT) validates that your code satisfies universal properties across a wide range of inputs, rather than testing specific examples. This approach helps discover edge cases and ensures correctness at scale.

## Directory Structure

```
tests/property/
├── generators/           # Custom generators for domain models
│   ├── stock-data.generator.ts
│   ├── auth.generator.ts
│   ├── viewport.generator.ts
│   └── index.ts
├── config.ts            # Test configuration and helpers
└── README.md           # This file
```

## Generators

### Stock Data Generators

Located in `generators/stock-data.generator.ts`:

- `stockDataArbitrary()` - Generates valid StockData objects
- `pricePointArbitrary()` - Generates valid OHLC price points
- `emaDataArbitrary()` - Generates EMA data arrays
- `invalidStockDataArbitrary()` - Generates invalid data for error testing

### Authentication Generators

Located in `generators/auth.generator.ts`:

- `credentialsArbitrary()` - Generates valid username/password pairs
- `jwtTokenArbitrary()` - Generates JWT-like tokens
- `authResultArbitrary()` - Generates authentication results
- `expiredJwtTokenArbitrary()` - Generates expired tokens
- `validJwtTokenArbitrary()` - Generates valid (non-expired) tokens

### Viewport Generators

Located in `generators/viewport.generator.ts`:

- `viewportWidthArbitrary()` - Generates viewport widths
- `viewportWithColumnsArbitrary()` - Generates viewport with expected column count
- `commonDeviceViewportArbitrary()` - Generates common device sizes
- `viewportResizeSequenceArbitrary()` - Generates resize sequences

## Configuration

The `config.ts` file provides pre-configured test settings:

- `DEFAULT_PBT_CONFIG` - 100 iterations per test (standard)
- `QUICK_PBT_CONFIG` - 20 iterations (for smoke tests)
- `THOROUGH_PBT_CONFIG` - 500 iterations (for comprehensive testing)
- `DEBUG_PBT_CONFIG` - 10 iterations with verbose output

## Usage Examples

### Basic Property Test

```typescript
import * as fc from 'fast-check';
import { stockDataArbitrary } from './generators';
import { DEFAULT_PBT_CONFIG } from './config';

describe('StockChart', () => {
  it('should render valid stock data', () => {
    fc.assert(
      fc.property(stockDataArbitrary(), (stockData) => {
        // Test that chart can render any valid stock data
        const chart = new StockChart(stockData);
        expect(chart.isValid()).toBe(true);
      }),
      DEFAULT_PBT_CONFIG
    );
  });
});
```

### Testing Error Handling

```typescript
import * as fc from 'fast-check';
import { invalidStockDataArbitrary } from './generators';

describe('ApiService', () => {
  it('should handle invalid data gracefully', () => {
    fc.assert(
      fc.property(invalidStockDataArbitrary(), (invalidData) => {
        // Test that service handles invalid data without crashing
        expect(() => {
          apiService.validateStockData(invalidData);
        }).toThrow();
      })
    );
  });
});
```

### Testing Responsive Behavior

```typescript
import * as fc from 'fast-check';
import { viewportWithColumnsArbitrary } from './generators';

describe('ChartGrid', () => {
  it('should display correct columns for viewport width', () => {
    fc.assert(
      fc.property(viewportWithColumnsArbitrary(), ({ width, expectedColumns }) => {
        const grid = new ChartGrid(width);
        expect(grid.getColumnCount()).toBe(expectedColumns);
      })
    );
  });
});
```

## Best Practices

1. **Start Simple**: Begin with basic properties and add complexity gradually
2. **Use Meaningful Properties**: Test universal truths, not implementation details
3. **Combine Generators**: Use `fc.tuple()` or `fc.record()` to combine generators
4. **Shrinking**: fast-check automatically finds minimal failing cases
5. **Reproducibility**: Use seed values to reproduce specific test failures
6. **Performance**: Use `QUICK_PBT_CONFIG` for CI, `THOROUGH_PBT_CONFIG` for releases

## Common Properties to Test

### Data Validation
- Valid data passes validation
- Invalid data fails validation
- Validation errors are descriptive

### State Management
- State transitions are consistent
- State can be serialized/deserialized
- Concurrent operations don't corrupt state

### UI Behavior
- Components render without errors
- User interactions produce expected results
- Responsive layouts adapt correctly

### API Integration
- Requests are properly formatted
- Responses are correctly parsed
- Errors are handled gracefully

## Debugging Failed Tests

When a property test fails:

1. **Check the counterexample**: fast-check shows the failing input
2. **Use DEBUG_PBT_CONFIG**: Enable verbose mode for detailed output
3. **Set a seed**: Reproduce the exact failure with the seed value
4. **Simplify the property**: Break complex properties into smaller ones
5. **Add logging**: Use console.log to trace execution

## Resources

- [fast-check Documentation](https://github.com/dubzzz/fast-check/tree/main/documentation)
- [Property-Based Testing Guide](https://fsharpforfunandprofit.com/posts/property-based-testing/)
- [Design Document](../../../.kiro/tradeseeker-web-v2/design.md) - See correctness properties section
