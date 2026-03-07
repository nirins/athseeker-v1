import * as fc from 'fast-check';
import {
  stockDataArbitrary,
  pricePointArbitrary,
  credentialsArbitrary,
  jwtTokenArbitrary,
  viewportWidthArbitrary,
  getExpectedGridColumns
} from './index';
import { DEFAULT_PBT_CONFIG } from '../config';

describe('Property Test Generators', () => {
  describe('Stock Data Generators', () => {
    it('should generate valid stock data', () => {
      fc.assert(
        fc.property(stockDataArbitrary(), (stockData) => {
          // Verify structure
          expect(stockData).toBeDefined();
          expect(stockData.symbol).toBeDefined();
          expect(typeof stockData.symbol).toBe('string');
          expect(stockData.symbol.length).toBeGreaterThan(0);
          
          // Verify prices array
          expect(Array.isArray(stockData.prices)).toBe(true);
          expect(stockData.prices.length).toBeGreaterThan(0);
          
          // Verify EMAs
          expect(stockData.emas).toBeDefined();
          expect(Array.isArray(stockData.emas.ema7)).toBe(true);
          expect(Array.isArray(stockData.emas.ema30)).toBe(true);
          expect(Array.isArray(stockData.emas.ema50)).toBe(true);
          expect(Array.isArray(stockData.emas.ema200)).toBe(true);
          
          // Verify EMA lengths match price length
          expect(stockData.emas.ema7.length).toBe(stockData.prices.length);
          expect(stockData.emas.ema30.length).toBe(stockData.prices.length);
          expect(stockData.emas.ema50.length).toBe(stockData.prices.length);
          expect(stockData.emas.ema200.length).toBe(stockData.prices.length);
        }),
        DEFAULT_PBT_CONFIG
      );
    });

    it('should generate valid OHLC relationships', () => {
      fc.assert(
        fc.property(pricePointArbitrary(), (pricePoint) => {
          // Verify OHLC relationships
          expect(pricePoint.low).toBeLessThanOrEqual(pricePoint.open);
          expect(pricePoint.low).toBeLessThanOrEqual(pricePoint.close);
          expect(pricePoint.low).toBeLessThanOrEqual(pricePoint.high);
          expect(pricePoint.high).toBeGreaterThanOrEqual(pricePoint.open);
          expect(pricePoint.high).toBeGreaterThanOrEqual(pricePoint.close);
          
          // Verify all prices are positive
          expect(pricePoint.open).toBeGreaterThan(0);
          expect(pricePoint.high).toBeGreaterThan(0);
          expect(pricePoint.low).toBeGreaterThan(0);
          expect(pricePoint.close).toBeGreaterThan(0);
          
          // Verify no NaN values
          expect(isNaN(pricePoint.open)).toBe(false);
          expect(isNaN(pricePoint.high)).toBe(false);
          expect(isNaN(pricePoint.low)).toBe(false);
          expect(isNaN(pricePoint.close)).toBe(false);
        }),
        DEFAULT_PBT_CONFIG
      );
    });
  });

  describe('Authentication Generators', () => {
    it('should generate valid credentials', () => {
      fc.assert(
        fc.property(credentialsArbitrary(), (credentials) => {
          expect(credentials).toBeDefined();
          expect(credentials.username).toBeDefined();
          expect(credentials.password).toBeDefined();
          expect(typeof credentials.username).toBe('string');
          expect(typeof credentials.password).toBe('string');
          expect(credentials.username.length).toBeGreaterThanOrEqual(3);
          expect(credentials.password.length).toBeGreaterThanOrEqual(8);
        }),
        DEFAULT_PBT_CONFIG
      );
    });

    it('should generate valid JWT tokens', () => {
      fc.assert(
        fc.property(jwtTokenArbitrary(), (token) => {
          expect(token).toBeDefined();
          expect(typeof token).toBe('string');
          
          // JWT should have at least 2 dots (3 parts)
          const parts = token.split('.');
          expect(parts.length).toBeGreaterThanOrEqual(3);
          
          // Each part should be non-empty
          expect(parts[0].length).toBeGreaterThan(0);
          expect(parts[1].length).toBeGreaterThan(0);
          expect(parts[2].length).toBeGreaterThan(0);
        }),
        DEFAULT_PBT_CONFIG
      );
    });
  });

  describe('Viewport Generators', () => {
    it('should generate valid viewport widths', () => {
      fc.assert(
        fc.property(viewportWidthArbitrary(), (width) => {
          expect(width).toBeDefined();
          expect(typeof width).toBe('number');
          expect(width).toBeGreaterThanOrEqual(320);
          expect(width).toBeLessThanOrEqual(3840);
        }),
        DEFAULT_PBT_CONFIG
      );
    });

    it('should calculate correct grid columns for viewport', () => {
      fc.assert(
        fc.property(viewportWidthArbitrary(), (width) => {
          const columns = getExpectedGridColumns(width);
          
          expect(columns).toBeGreaterThanOrEqual(1);
          expect(columns).toBeLessThanOrEqual(6);
          
          // Verify column count matches breakpoints
          if (width >= 2560) {
            expect(columns).toBe(6);
          } else if (width >= 1920) {
            expect(columns).toBe(4);
          } else if (width >= 1440) {
            expect(columns).toBe(3);
          } else if (width >= 768) {
            expect(columns).toBe(2);
          } else {
            expect(columns).toBe(1);
          }
        }),
        DEFAULT_PBT_CONFIG
      );
    });
  });
});
