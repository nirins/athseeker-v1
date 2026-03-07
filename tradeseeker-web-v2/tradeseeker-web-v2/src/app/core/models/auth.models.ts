/**
 * Authentication-related data models
 */

/**
 * User credentials for login
 */
export interface Credentials {
  username: string;
  password: string;
}

/**
 * Authentication result from login attempt
 */
export interface AuthResult {
  success: boolean;
  token?: string;
  error?: string;
}

/**
 * Authentication state for reactive state management
 */
export interface AuthState {
  isAuthenticated: boolean;
  token: string | null;
  username: string | null;
}
