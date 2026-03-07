/**
 * Property-based test generators for TradeSeekerWeb v2
 * 
 * This module exports all custom generators for use in property-based tests.
 * All generators are built using fast-check library.
 */

// Stock data generators
export {
  dateStringArbitrary,
  priceArbitrary,
  pricePointArbitrary,
  pricePointArrayArbitrary,
  emaValueArbitrary,
  emaArrayArbitrary,
  emaDataArbitrary,
  stockSymbolArbitrary,
  stockDataArbitrary,
  stockDataArrayArbitrary,
  invalidStockDataArbitrary
} from './stock-data.generator';

// Authentication generators
export {
  usernameArbitrary,
  passwordArbitrary,
  credentialsArbitrary,
  jwtTokenArbitrary,
  successfulAuthResultArbitrary,
  failedAuthResultArbitrary,
  authResultArbitrary,
  invalidCredentialsArbitrary,
  expiredJwtTokenArbitrary,
  validJwtTokenArbitrary
} from './auth.generator';

// Viewport generators
export {
  VIEWPORT_BREAKPOINTS,
  mobileViewportArbitrary,
  tabletViewportArbitrary,
  desktopViewportArbitrary,
  largeDesktopViewportArbitrary,
  extraLargeDesktopViewportArbitrary,
  viewportWidthArbitrary,
  viewportDimensionsArbitrary,
  getExpectedGridColumns,
  viewportWithColumnsArbitrary,
  commonDeviceViewportArbitrary,
  viewportResizeSequenceArbitrary
} from './viewport.generator';
