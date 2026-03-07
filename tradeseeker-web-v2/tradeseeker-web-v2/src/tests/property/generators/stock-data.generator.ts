import * as fc from 'fast-check';
import { StockData, PricePoint, EMAData } from '../../../app/core/models';

/**
 * Generator for valid date strings in ISO format
 */
export const dateStringArbitrary = (): fc.Arbitrary<string> => {
  return fc.date({
    min: new Date('2020-01-01'),
    max: new Date('2025-12-31')
  }).map(date => date.toISOString().split('T')[0]);
};

/**
 * Generator for positive stock prices
 */
export const priceArbitrary = (): fc.Arbitrary<number> => {
  return fc.double({
    min: 0.01,
    max: 10000,
    noNaN: true,
    noDefaultInfinity: true
  }).map(price => Math.round(price * 100) / 100); // Round to 2 decimal places
};

/**
 * Generator for valid OHLC price point
 * Ensures: low <= open, close <= high and low <= high
 */
export const pricePointArbitrary = (): fc.Arbitrary<PricePoint> => {
  return fc.tuple(
    dateStringArbitrary(),
    priceArbitrary(),
    priceArbitrary(),
    priceArbitrary(),
    priceArbitrary()
  ).map(([date, p1, p2, p3, p4]) => {
    // Sort prices to ensure valid OHLC relationships
    const prices = [p1, p2, p3, p4].sort((a, b) => a - b);
    const low = prices[0];
    const high = prices[3];
    const open = prices[1];
    const close = prices[2];

    return {
      date,
      open,
      high,
      low,
      close,
      volume: Math.floor(Math.random() * 10000000)
    };
  });
};

/**
 * Generator for array of price points with sequential dates
 */
export const pricePointArrayArbitrary = (
  minLength: number = 50,
  maxLength: number = 200
): fc.Arbitrary<PricePoint[]> => {
  return fc.integer({ min: minLength, max: maxLength }).chain(length => {
    const startDate = new Date('2024-01-01');
    
    return fc.array(pricePointArbitrary(), { minLength: length, maxLength: length })
      .map((points) => {
        // Assign sequential dates
        return points.map((point, i) => {
          const date = new Date(startDate);
          date.setDate(date.getDate() + i);
          return {
            ...point,
            date: date.toISOString().split('T')[0]
          };
        });
      });
  });
};

/**
 * Generator for EMA values
 * EMA values should be positive and generally follow price trends
 */
export const emaValueArbitrary = (): fc.Arbitrary<number> => {
  return fc.double({
    min: 0.01,
    max: 10000,
    noNaN: true,
    noDefaultInfinity: true
  }).map(value => Math.round(value * 100) / 100);
};

/**
 * Generator for EMA data arrays
 */
export const emaArrayArbitrary = (length: number): fc.Arbitrary<number[]> => {
  return fc.array(emaValueArbitrary(), { minLength: length, maxLength: length });
};

/**
 * Generator for complete EMA data structure
 */
export const emaDataArbitrary = (priceLength: number): fc.Arbitrary<EMAData> => {
  return fc.record({
    ema7: emaArrayArbitrary(priceLength),
    ema30: emaArrayArbitrary(priceLength),
    ema50: emaArrayArbitrary(priceLength),
    ema200: emaArrayArbitrary(priceLength)
  });
};

/**
 * Generator for valid stock symbols
 */
export const stockSymbolArbitrary = (): fc.Arbitrary<string> => {
  return fc.string({ minLength: 1, maxLength: 5 })
    .filter(s => s.length > 0 && /^[A-Z]+$/.test(s.toUpperCase()))
    .map(s => s.toUpperCase());
};

/**
 * Generator for complete valid StockData
 */
export const stockDataArbitrary = (): fc.Arbitrary<StockData> => {
  return pricePointArrayArbitrary().chain(prices => {
    return fc.record({
      symbol: stockSymbolArbitrary(),
      prices: fc.constant(prices),
      emas: emaDataArbitrary(prices.length),
      lastUpdated: dateStringArbitrary()
    });
  });
};

/**
 * Generator for array of StockData
 */
export const stockDataArrayArbitrary = (
  minLength: number = 1,
  maxLength: number = 20
): fc.Arbitrary<StockData[]> => {
  return fc.array(stockDataArbitrary(), { minLength, maxLength });
};

/**
 * Generator for invalid StockData (for error testing)
 */
export const invalidStockDataArbitrary = (): fc.Arbitrary<any> => {
  return fc.oneof(
    fc.constant(null),
    fc.constant(undefined),
    fc.constant({}),
    fc.record({
      symbol: fc.constant(''),
      prices: fc.constant([]),
      emas: fc.constant({})
    }),
    fc.record({
      symbol: stockSymbolArbitrary(),
      prices: fc.constant(null),
      emas: fc.constant({})
    }),
    fc.record({
      symbol: stockSymbolArbitrary(),
      prices: fc.array(fc.record({
        date: dateStringArbitrary(),
        open: fc.constant(NaN),
        high: fc.constant(NaN),
        low: fc.constant(NaN),
        close: fc.constant(NaN)
      })),
      emas: fc.constant({})
    })
  );
};
