import { Injectable } from '@angular/core';
import { Observable, BehaviorSubject, from, of } from 'rxjs';
import { map, catchError, tap } from 'rxjs/operators';
import { Amplify } from 'aws-amplify';
import { signIn, signOut, signUp, confirmSignUp, fetchAuthSession } from 'aws-amplify/auth';
import { AuthResult, AuthState } from '../models';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly TOKEN_KEY = 'auth_token';
  private readonly USERNAME_KEY = 'auth_username';
  
  private authStateSubject = new BehaviorSubject<boolean>(this.isAuthenticated());
  public authState$ = this.authStateSubject.asObservable();

  constructor() {
    this.configureAmplify();
    this.checkExistingSession();
  }

  /**
   * Configure AWS Amplify with Cognito settings
   */
  private configureAmplify(): void {
    Amplify.configure({
      Auth: {
        Cognito: {
          userPoolId: environment.cognito.userPoolId,
          userPoolClientId: environment.cognito.clientId
        }
      }
    });
  }

  /**
   * Check if there's an existing Cognito session and restore it
   */
  private async checkExistingSession(): Promise<void> {
    try {
      const session = await fetchAuthSession();
      const token = session.tokens?.idToken?.toString();
      
      if (token && this.isTokenValid(token) && !this.isTokenExpired(token)) {
        // Store the existing valid token
        // Check if we're in browser environment
        if (typeof window !== 'undefined' && typeof localStorage !== 'undefined') {
          localStorage.setItem(this.TOKEN_KEY, token);
        }
        
        // Try to get user info
        try {
          const userAttributes = session.userSub;
          if (userAttributes && typeof window !== 'undefined' && typeof localStorage !== 'undefined') {
            localStorage.setItem(this.USERNAME_KEY, userAttributes);
          }
        } catch (e) {
          console.warn('Could not get user attributes:', e);
        }
        
        this.authStateSubject.next(true);
        console.log('Restored existing Cognito session');
      }
    } catch (error) {
      console.log('No existing Cognito session found:', error);
      // This is normal if user isn't signed in
    }
  }

  /**
   * Authenticate user with AWS Cognito
   */
  login(username: string, password: string): Observable<AuthResult> {
    return from(
      signIn({ username, password }).then(async (signInResult) => {
        // Check if user needs to complete a challenge (e.g., NEW_PASSWORD_REQUIRED)
        if (signInResult.isSignedIn) {
          // User is fully signed in, fetch session
          const session = await fetchAuthSession();
          const token = session.tokens?.idToken?.toString();
          
          if (token) {
            // Validate token before storing
            if (this.isTokenValid(token)) {
              // Check if we're in browser environment
              if (typeof window !== 'undefined' && typeof localStorage !== 'undefined') {
                localStorage.setItem(this.TOKEN_KEY, token);
                localStorage.setItem(this.USERNAME_KEY, username);
              }
              this.authStateSubject.next(true);
              
              return {
                success: true,
                token
              } as AuthResult;
            } else {
              throw new Error('Invalid token received from authentication');
            }
          } else {
            throw new Error('No token received from authentication');
          }
        }
        
        // If not signed in, there might be a challenge
        throw new Error('Authentication incomplete. Please check if password change is required.');
      }).catch(async (error) => {
        // Handle "There is already a signed in user" error
        if (error.message?.includes('already a signed in user') || error.name === 'UserAlreadyAuthenticatedException') {
          console.log('User already signed in, fetching existing session...');
          try {
            const session = await fetchAuthSession();
            const token = session.tokens?.idToken?.toString();
            
            if (token && this.isTokenValid(token) && !this.isTokenExpired(token)) {
              // Check if we're in browser environment
              if (typeof window !== 'undefined' && typeof localStorage !== 'undefined') {
                localStorage.setItem(this.TOKEN_KEY, token);
                localStorage.setItem(this.USERNAME_KEY, username);
              }
              this.authStateSubject.next(true);
              
              return {
                success: true,
                token
              } as AuthResult;
            }
          } catch (sessionError) {
            console.error('Error fetching existing session:', sessionError);
          }
        }
        
        throw error;
      })
    ).pipe(
      catchError((error) => {
        console.error('Login error:', error);
        
        // Clear any partial session data on error
        this.clearSession();
        
        return of({
          success: false,
          error: this.getErrorMessage(error)
        } as AuthResult);
      })
    );
  }

  /**
   * Sign up a new user with AWS Cognito
   */
  signUp(email: string, username: string, password: string, fullName?: string): Observable<AuthResult> {
    const displayName = fullName || username;
    
    console.log('Attempting sign up with:', { email, username, displayName }); // Debug log
    
    return from(
      signUp({
        username,
        password,
        options: {
          userAttributes: {
            email: email.toLowerCase().trim(), // Ensure clean email format
            'name': displayName.trim(),
            'given_name': displayName.split(' ')[0]?.trim() || displayName.trim(),
            'family_name': displayName.split(' ').slice(1).join(' ').trim() || ''
            // Removed 'name.formatted' as it's not in the schema
          }
        }
      }).then((signUpResult) => {
        console.log('Sign up successful:', signUpResult);
        
        return {
          success: true,
          message: 'Account created successfully'
        } as AuthResult;
      }).catch((error) => {
        console.error('Cognito sign up error:', error);
        throw error;
      })
    ).pipe(
      catchError((error) => {
        console.error('Sign up error:', error);
        
        return of({
          success: false,
          error: this.getSignUpErrorMessage(error)
        } as AuthResult);
      })
    );
  }

  /**
   * Confirm user sign up with verification code
   */
  confirmSignUp(username: string, confirmationCode: string): Observable<AuthResult> {
    return from(
      confirmSignUp({
        username,
        confirmationCode
      }).then((confirmResult) => {
        console.log('Confirmation successful:', confirmResult);
        
        return {
          success: true,
          message: 'Account confirmed successfully'
        } as AuthResult;
      }).catch((error) => {
        console.error('Cognito confirmation error:', error);
        throw error;
      })
    ).pipe(
      catchError((error) => {
        console.error('Confirmation error:', error);
        
        return of({
          success: false,
          error: this.getConfirmationErrorMessage(error)
        } as AuthResult);
      })
    );
  }

  /**
   * Log out current user and clear tokens
   */
  logout(): void {
    from(signOut()).subscribe({
      next: () => {
        this.clearSession();
      },
      error: (error) => {
        console.error('Logout error:', error);
        // Clear session even if logout fails
        this.clearSession();
      }
    });
  }

  /**
   * Clear session storage and update auth state
   */
  private clearSession(): void {
    // Check if we're in browser environment
    if (typeof window !== 'undefined' && typeof localStorage !== 'undefined') {
      localStorage.removeItem(this.TOKEN_KEY);
      localStorage.removeItem(this.USERNAME_KEY);
    }
    this.authStateSubject.next(false);
  }

  /**
   * Get current authentication token
   */
  getToken(): string | null {
    // Check if we're in browser environment
    if (typeof window === 'undefined' || typeof localStorage === 'undefined') {
      return null;
    }
    
    const token = localStorage.getItem(this.TOKEN_KEY);
    
    // Check if token is expired
    if (token && this.isTokenExpired(token)) {
      console.warn('Token has expired');
      this.clearSession();
      return null;
    }
    
    return token;
  }

  /**
   * Validate token format (basic JWT structure check)
   */
  private isTokenValid(token: string): boolean {
    if (!token || token.trim().length === 0) {
      return false;
    }
    
    // JWT should have 3 parts separated by dots
    const parts = token.split('.');
    if (parts.length !== 3) {
      return false;
    }
    
    return true;
  }

  /**
   * Check if token is expired
   */
  private isTokenExpired(token: string): boolean {
    try {
      const parts = token.split('.');
      if (parts.length !== 3) {
        return true;
      }
      
      // Decode the payload (second part)
      const payload = JSON.parse(atob(parts[1]));
      
      // Check expiration time (exp is in seconds)
      if (payload.exp) {
        const expirationTime = payload.exp * 1000; // Convert to milliseconds
        const currentTime = Date.now();
        
        // Add 60 second buffer to refresh before actual expiration
        return currentTime >= (expirationTime - 60000);
      }
      
      return false;
    } catch (error) {
      console.error('Error checking token expiration:', error);
      return true; // Treat as expired if we can't parse it
    }
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    const token = this.getToken();
    return token !== null && token.length > 0;
  }

  /**
   * Get current authentication state
   */
  getAuthState(): AuthState {
    return {
      isAuthenticated: this.isAuthenticated(),
      token: this.getToken(),
      username: typeof window !== 'undefined' && typeof localStorage !== 'undefined' 
        ? localStorage.getItem(this.USERNAME_KEY) 
        : null
    };
  }

  /**
   * Map Cognito errors to user-friendly messages
   */
  private getErrorMessage(error: any): string {
    // Handle specific Cognito error types
    if (error.name === 'NotAuthorizedException') {
      return 'Invalid username or password. Please try again.';
    }
    if (error.name === 'UserNotFoundException') {
      return 'User not found. Please check your username.';
    }
    if (error.name === 'UserNotConfirmedException') {
      return 'User account not confirmed. Please check your email for confirmation link.';
    }
    if (error.name === 'PasswordResetRequiredException') {
      return 'Password reset required. Please contact your administrator.';
    }
    if (error.name === 'TooManyRequestsException') {
      return 'Too many login attempts. Please wait a few minutes and try again.';
    }
    if (error.name === 'InvalidPasswordException') {
      return 'Password does not meet requirements. Please use a stronger password.';
    }
    
    // Handle network errors
    if (error.name === 'NetworkError' || error.message?.includes('Network')) {
      return 'Network error. Please check your internet connection and try again.';
    }
    
    // Handle timeout errors
    if (error.name === 'TimeoutError' || error.message?.includes('timeout')) {
      return 'Request timed out. Please check your connection and try again.';
    }
    
    // Handle generic errors
    if (error.message) {
      // Don't expose technical error messages to users
      if (error.message.includes('token') || error.message.includes('Token')) {
        return 'Authentication error. Please try logging in again.';
      }
      return error.message;
    }
    
    return 'Authentication failed. Please try again.';
  }

  /**
   * Map Cognito sign up errors to user-friendly messages
   */
  private getSignUpErrorMessage(error: any): string {
    console.log('Full Cognito error:', error); // Debug log
    
    // Handle specific Cognito sign up error types
    if (error.name === 'UsernameExistsException') {
      return 'An account with this email already exists. Please try signing in instead.';
    }
    if (error.name === 'InvalidPasswordException') {
      return 'Password does not meet requirements. Please use a stronger password with at least 8 characters, including uppercase, lowercase, numbers, and special characters.';
    }
    if (error.name === 'InvalidParameterException') {
      // Log the full error message for debugging
      console.log('InvalidParameterException details:', error.message);
      
      // Handle the specific email alias error
      if (error.message?.includes('Username cannot be of email format') && error.message?.includes('email alias')) {
        return 'There was a configuration issue. Please try again.';
      }
      
      // Check for other specific parameter issues
      if (error.message?.includes('username') && error.message?.includes('email')) {
        return 'There was an issue with the account setup. Please try again.';
      }
      if (error.message?.includes('email') && !error.message?.includes('username')) {
        return 'Please enter a valid email address.';
      }
      if (error.message?.includes('name.formatted')) {
        return 'User pool configuration issue. Please contact support.';
      }
      if (error.message?.includes('not defined in schema')) {
        return 'Account setup issue. Please try again or contact support.';
      }
      
      return 'Please check your information and try again.';
    }
    if (error.name === 'TooManyRequestsException') {
      return 'Too many sign up attempts. Please wait a few minutes and try again.';
    }
    if (error.name === 'LimitExceededException') {
      return 'Sign up limit exceeded. Please try again later.';
    }
    
    // Handle network errors
    if (error.name === 'NetworkError' || error.message?.includes('Network')) {
      return 'Network error. Please check your internet connection and try again.';
    }
    
    // Handle timeout errors
    if (error.name === 'TimeoutError' || error.message?.includes('timeout')) {
      return 'Request timed out. Please check your connection and try again.';
    }
    
    // Handle generic errors - include more details for debugging
    if (error.message) {
      return 'Sign up failed: ' + error.message;
    }
    
    return 'Sign up failed. Please try again.';
  }

  /**
   * Map Cognito confirmation errors to user-friendly messages
   */
  private getConfirmationErrorMessage(error: any): string {
    console.log('Full Cognito confirmation error:', error);
    
    if (error.name === 'CodeMismatchException') {
      return 'Invalid confirmation code. Please check the code and try again.';
    }
    if (error.name === 'ExpiredCodeException') {
      return 'Confirmation code has expired. Please request a new code.';
    }
    if (error.name === 'LimitExceededException') {
      return 'Too many attempts. Please wait and try again later.';
    }
    if (error.name === 'NotAuthorizedException') {
      return 'User is already confirmed or confirmation failed.';
    }
    
    if (error.message) {
      return 'Confirmation failed: ' + error.message;
    }
    
    return 'Confirmation failed. Please try again.';
  }
}
