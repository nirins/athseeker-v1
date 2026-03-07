import * as fc from 'fast-check';
import { Credentials, AuthResult } from '../../../app/core/models';

/**
 * Generator for valid usernames
 */
export const usernameArbitrary = (): fc.Arbitrary<string> => {
  return fc.string({
    minLength: 3,
    maxLength: 30
  }).filter(s => /^[a-zA-Z0-9_-]+$/.test(s));
};

/**
 * Generator for valid passwords
 */
export const passwordArbitrary = (): fc.Arbitrary<string> => {
  return fc.string({
    minLength: 8,
    maxLength: 128
  });
};

/**
 * Generator for valid credentials
 */
export const credentialsArbitrary = (): fc.Arbitrary<Credentials> => {
  return fc.record({
    username: usernameArbitrary(),
    password: passwordArbitrary()
  });
};

/**
 * Generator for JWT tokens (simplified structure)
 */
export const jwtTokenArbitrary = (): fc.Arbitrary<string> => {
  // Generate a simple JWT-like token with 3 base64 parts
  const base64String = (length: number) => 
    fc.string({ minLength: length, maxLength: length })
      .filter(s => !s.includes('.')); // Ensure no dots in parts

  return fc.tuple(
    base64String(36),
    base64String(200),
    base64String(43)
  ).map(([header, payload, signature]) => `${header}.${payload}.${signature}`);
};

/**
 * Generator for successful AuthResult
 */
export const successfulAuthResultArbitrary = (): fc.Arbitrary<AuthResult> => {
  return fc.record({
    success: fc.constant(true),
    token: jwtTokenArbitrary(),
    error: fc.constant(undefined)
  });
};

/**
 * Generator for failed AuthResult
 */
export const failedAuthResultArbitrary = (): fc.Arbitrary<AuthResult> => {
  const errorMessages = [
    'Invalid username or password',
    'User not found',
    'User account not confirmed',
    'Network error. Please check your connection',
    'Authentication failed'
  ];

  return fc.record({
    success: fc.constant(false),
    token: fc.constant(undefined),
    error: fc.constantFrom(...errorMessages)
  });
};

/**
 * Generator for any AuthResult (success or failure)
 */
export const authResultArbitrary = (): fc.Arbitrary<AuthResult> => {
  return fc.oneof(
    successfulAuthResultArbitrary(),
    failedAuthResultArbitrary()
  );
};

/**
 * Generator for invalid credentials (for error testing)
 */
export const invalidCredentialsArbitrary = (): fc.Arbitrary<any> => {
  return fc.oneof(
    fc.constant(null),
    fc.constant(undefined),
    fc.constant({}),
    fc.record({
      username: fc.constant(''),
      password: fc.constant('')
    }),
    fc.record({
      username: usernameArbitrary(),
      password: fc.constant('')
    }),
    fc.record({
      username: fc.constant(''),
      password: passwordArbitrary()
    })
  );
};

/**
 * Generator for expired JWT tokens
 * Creates tokens with exp claim in the past
 */
export const expiredJwtTokenArbitrary = (): fc.Arbitrary<string> => {
  const base64String = (length: number) => 
    fc.string({ minLength: length, maxLength: length })
      .filter(s => !s.includes('.'));

  // Create a payload with expired timestamp
  const expiredTime = Math.floor(Date.now() / 1000) - 3600; // 1 hour ago
  const payload = btoa(JSON.stringify({ exp: expiredTime }));

  return fc.tuple(
    base64String(36),
    fc.constant(payload),
    base64String(43)
  ).map(([header, payload, signature]) => `${header}.${payload}.${signature}`);
};

/**
 * Generator for valid (non-expired) JWT tokens
 * Creates tokens with exp claim in the future
 */
export const validJwtTokenArbitrary = (): fc.Arbitrary<string> => {
  const base64String = (length: number) => 
    fc.string({ minLength: length, maxLength: length })
      .filter(s => !s.includes('.'));

  // Create a payload with future timestamp
  const futureTime = Math.floor(Date.now() / 1000) + 3600; // 1 hour from now
  const payload = btoa(JSON.stringify({ exp: futureTime }));

  return fc.tuple(
    base64String(36),
    fc.constant(payload),
    base64String(43)
  ).map(([header, payload, signature]) => `${header}.${payload}.${signature}`);
};
