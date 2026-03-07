import * as fc from 'fast-check';

/**
 * Default configuration for property-based tests
 * 
 * This configuration is used across all property tests to ensure
 * consistent behavior and adequate test coverage.
 */
export const DEFAULT_PBT_CONFIG: fc.Parameters<unknown> = {
  // Number of test iterations per property
  numRuns: 100,
  
  // Seed for reproducible tests (can be overridden)
  // seed: 42,
  
  // Path for shrinking (finding minimal failing case)
  path: undefined,
  
  // Verbose mode for debugging
  verbose: false,
  
  // Mark tests as slow if they take longer than this (ms)
  markInterruptAsFailure: false,
  
  // Interrupt after this many milliseconds
  interruptAfterTimeLimit: 5000,
  
  // Skip all runs after first failure
  skipAllAfterTimeLimit: undefined,
  
  // Enable async property support
  asyncReporter: undefined
};

/**
 * Configuration for quick smoke tests
 * Runs fewer iterations for faster feedback
 */
export const QUICK_PBT_CONFIG: fc.Parameters<unknown> = {
  ...DEFAULT_PBT_CONFIG,
  numRuns: 20
};

/**
 * Configuration for thorough tests
 * Runs more iterations for comprehensive coverage
 */
export const THOROUGH_PBT_CONFIG: fc.Parameters<unknown> = {
  ...DEFAULT_PBT_CONFIG,
  numRuns: 500
};

/**
 * Configuration for debugging
 * Enables verbose output and uses a fixed seed
 */
export const DEBUG_PBT_CONFIG: fc.Parameters<unknown> = {
  ...DEFAULT_PBT_CONFIG,
  numRuns: 10,
  verbose: true,
  seed: 42
};

/**
 * Helper function to run a property test with default config
 */
export const runPropertyTest = <T>(
  property: fc.IProperty<T>,
  config: fc.Parameters<unknown> = DEFAULT_PBT_CONFIG
): void => {
  fc.assert(property, config);
};

/**
 * Helper function to create a property test
 */
export const createProperty = <Ts extends [unknown, ...unknown[]]>(
  ...args: [...arbitraries: { [K in keyof Ts]: fc.Arbitrary<Ts[K]> }, predicate: (...args: Ts) => boolean | void]
): fc.IProperty<Ts> => {
  return fc.property(...args);
};
