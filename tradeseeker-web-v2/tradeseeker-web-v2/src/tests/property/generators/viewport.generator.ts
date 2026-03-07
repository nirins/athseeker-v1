import * as fc from 'fast-check';

/**
 * Viewport breakpoints based on design requirements
 */
export const VIEWPORT_BREAKPOINTS = {
  MOBILE: 768,
  TABLET: 1440,
  DESKTOP: 1920,
  LARGE_DESKTOP: 2560
} as const;

/**
 * Generator for mobile viewport widths (< 768px)
 */
export const mobileViewportArbitrary = (): fc.Arbitrary<number> => {
  return fc.integer({ min: 320, max: VIEWPORT_BREAKPOINTS.MOBILE - 1 });
};

/**
 * Generator for tablet viewport widths (768px - 1439px)
 */
export const tabletViewportArbitrary = (): fc.Arbitrary<number> => {
  return fc.integer({ 
    min: VIEWPORT_BREAKPOINTS.MOBILE, 
    max: VIEWPORT_BREAKPOINTS.TABLET - 1 
  });
};

/**
 * Generator for desktop viewport widths (1440px - 1919px)
 */
export const desktopViewportArbitrary = (): fc.Arbitrary<number> => {
  return fc.integer({ 
    min: VIEWPORT_BREAKPOINTS.TABLET, 
    max: VIEWPORT_BREAKPOINTS.DESKTOP - 1 
  });
};

/**
 * Generator for large desktop viewport widths (1920px - 2559px)
 */
export const largeDesktopViewportArbitrary = (): fc.Arbitrary<number> => {
  return fc.integer({ 
    min: VIEWPORT_BREAKPOINTS.DESKTOP, 
    max: VIEWPORT_BREAKPOINTS.LARGE_DESKTOP - 1 
  });
};

/**
 * Generator for extra large desktop viewport widths (>= 2560px)
 */
export const extraLargeDesktopViewportArbitrary = (): fc.Arbitrary<number> => {
  return fc.integer({ 
    min: VIEWPORT_BREAKPOINTS.LARGE_DESKTOP, 
    max: 3840 // 4K resolution
  });
};

/**
 * Generator for any valid viewport width
 */
export const viewportWidthArbitrary = (): fc.Arbitrary<number> => {
  return fc.oneof(
    mobileViewportArbitrary(),
    tabletViewportArbitrary(),
    desktopViewportArbitrary(),
    largeDesktopViewportArbitrary(),
    extraLargeDesktopViewportArbitrary()
  );
};

/**
 * Generator for viewport dimensions (width and height)
 */
export const viewportDimensionsArbitrary = (): fc.Arbitrary<{ width: number; height: number }> => {
  return viewportWidthArbitrary().chain(width => {
    // Generate reasonable height based on common aspect ratios
    const minHeight = Math.floor(width * 0.5); // 2:1 aspect ratio
    const maxHeight = Math.floor(width * 1.5); // 2:3 aspect ratio
    
    return fc.integer({ min: minHeight, max: maxHeight }).map(height => ({
      width,
      height
    }));
  });
};

/**
 * Get expected grid columns for a given viewport width
 * Based on design requirements
 */
export const getExpectedGridColumns = (width: number): number => {
  if (width >= VIEWPORT_BREAKPOINTS.LARGE_DESKTOP) {
    return 6; // 2560px+: 6 columns
  } else if (width >= VIEWPORT_BREAKPOINTS.DESKTOP) {
    return 4; // 1920px: 4-5 columns (using 4 as baseline)
  } else if (width >= VIEWPORT_BREAKPOINTS.TABLET) {
    return 3; // 1440px: 3 columns
  } else if (width >= VIEWPORT_BREAKPOINTS.MOBILE) {
    return 2; // 768px: 2 columns
  } else {
    return 1; // <768px: 1 column
  }
};

/**
 * Generator for viewport width with expected column count
 */
export const viewportWithColumnsArbitrary = (): fc.Arbitrary<{ 
  width: number; 
  expectedColumns: number 
}> => {
  return viewportWidthArbitrary().map(width => ({
    width,
    expectedColumns: getExpectedGridColumns(width)
  }));
};

/**
 * Generator for common device viewport sizes
 */
export const commonDeviceViewportArbitrary = (): fc.Arbitrary<{ 
  width: number; 
  height: number; 
  device: string 
}> => {
  const devices = [
    { width: 375, height: 667, device: 'iPhone SE' },
    { width: 390, height: 844, device: 'iPhone 12/13' },
    { width: 428, height: 926, device: 'iPhone 14 Pro Max' },
    { width: 768, height: 1024, device: 'iPad' },
    { width: 1024, height: 1366, device: 'iPad Pro' },
    { width: 1440, height: 900, device: 'MacBook Air' },
    { width: 1920, height: 1080, device: 'Full HD Desktop' },
    { width: 2560, height: 1440, device: '27" Monitor' },
    { width: 3840, height: 2160, device: '4K Monitor' }
  ];

  return fc.constantFrom(...devices);
};

/**
 * Generator for viewport resize sequence
 * Useful for testing responsive behavior during resize
 */
export const viewportResizeSequenceArbitrary = (
  minSteps: number = 2,
  maxSteps: number = 5
): fc.Arbitrary<number[]> => {
  return fc.array(viewportWidthArbitrary(), { 
    minLength: minSteps, 
    maxLength: maxSteps 
  });
};
