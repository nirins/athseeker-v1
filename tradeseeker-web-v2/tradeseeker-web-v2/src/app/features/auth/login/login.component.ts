import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule, AbstractControl } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent implements OnInit {
  loginForm!: FormGroup;
  signUpForm!: FormGroup;
  confirmationForm!: FormGroup;
  isSignUpMode = false;
  showConfirmation = false;
  pendingUsername = '';
  isLoading = false;
  error: string | null = null;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    // If user is already authenticated, redirect to dashboard
    if (this.authService.isAuthenticated()) {
      this.router.navigate(['/dashboard']);
      return;
    }
    
    this.initializeForms();
  }

  initializeForms(): void {
    this.loginForm = this.fb.group({
      username: ['', [Validators.required, Validators.email]], // Keep email validation for login
      password: ['', [Validators.required, Validators.minLength(6)]]
    });

    this.signUpForm = this.fb.group({
      fullName: ['', [Validators.required, Validators.minLength(2)]],
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(6)]],
      confirmPassword: ['', [Validators.required]]
    }, { validators: this.passwordMatchValidator });

    this.confirmationForm = this.fb.group({
      confirmationCode: ['', [Validators.required, Validators.minLength(6), Validators.maxLength(6)]]
    });
  }

  passwordMatchValidator(control: AbstractControl): { [key: string]: boolean } | null {
    const password = control.get('password');
    const confirmPassword = control.get('confirmPassword');
    
    if (!password || !confirmPassword) {
      return null;
    }
    
    return password.value === confirmPassword.value ? null : { passwordMismatch: true };
  }

  switchToLogin(): void {
    this.isSignUpMode = false;
    this.showConfirmation = false;
    this.error = null;
    this.loginForm.reset();
  }

  switchToSignUp(): void {
    this.isSignUpMode = true;
    this.showConfirmation = false;
    this.error = null;
    this.signUpForm.reset();
  }

  onLogin(): void {
    if (this.loginForm.invalid) {
      return;
    }

    this.isLoading = true;
    this.error = null;

    const { username, password } = this.loginForm.value;

    this.authService.login(username, password).subscribe({
      next: (result) => {
        if (result.success) {
          this.router.navigate(['/dashboard']);
        } else {
          // Check if it's an unconfirmed user error
          if (result.error?.includes('not confirmed') || result.error?.includes('UserNotConfirmedException')) {
            this.pendingUsername = username;
            this.showConfirmation = true;
            this.error = 'Please enter the confirmation code sent to your email.';
          } else {
            this.error = result.error || 'Login failed';
          }
          this.isLoading = false;
        }
      },
      error: (err) => {
        this.error = 'An error occurred during login';
        this.isLoading = false;
      }
    });
  }

  onConfirmAccount(): void {
    if (this.confirmationForm.invalid) {
      return;
    }

    this.isLoading = true;
    this.error = null;

    const { confirmationCode } = this.confirmationForm.value;

    this.authService.confirmSignUp(this.pendingUsername, confirmationCode).subscribe({
      next: (result) => {
        if (result.success) {
          this.showConfirmation = false;
          this.error = null;
          alert('Account confirmed successfully! Please sign in.');
          // Try auto-login after confirmation
          const password = this.loginForm.get('password')?.value;
          if (password) {
            this.authService.login(this.pendingUsername, password).subscribe({
              next: (loginResult) => {
                if (loginResult.success) {
                  this.router.navigate(['/dashboard']);
                } else {
                  this.isLoading = false;
                }
              },
              error: () => {
                this.isLoading = false;
              }
            });
          } else {
            this.isLoading = false;
          }
        } else {
          this.error = result.error || 'Confirmation failed';
          this.isLoading = false;
        }
      },
      error: (err) => {
        this.error = 'An error occurred during confirmation';
        this.isLoading = false;
      }
    });
  }

  onSignUp(): void {
    if (this.signUpForm.invalid) {
      return;
    }

    this.isLoading = true;
    this.error = null;

    const { fullName, email, password } = this.signUpForm.value;

    // Generate a unique username from email (remove @ and domain, add timestamp)
    const baseUsername = email.split('@')[0].replace(/[^a-zA-Z0-9]/g, '');
    const timestamp = Date.now().toString().slice(-6); // Last 6 digits of timestamp
    const username = baseUsername + timestamp;

    console.log('Generated username:', username); // Debug log

    this.authService.signUp(email, username, password, fullName).subscribe({
      next: (result) => {
        if (result.success) {
          // Show confirmation form immediately after successful signup
          this.pendingUsername = username;
          this.showConfirmation = true;
          this.isSignUpMode = false;
          this.error = null;
          this.isLoading = false;
          
          // Show success message
          alert('Account created successfully! Please check your email for the confirmation code and enter it below.');
        } else {
          this.error = result.error || 'Sign up failed';
          this.isLoading = false;
        }
      },
      error: (err) => {
        this.error = 'An error occurred during sign up';
        this.isLoading = false;
      }
    });
  }

  // Login form getters
  get username() {
    return this.loginForm.get('username');
  }

  get password() {
    return this.loginForm.get('password');
  }

  // Sign up form getters
  get fullName() {
    return this.signUpForm.get('fullName');
  }

  get email() {
    return this.signUpForm.get('email');
  }

  get signUpPassword() {
    return this.signUpForm.get('password');
  }

  get confirmPassword() {
    return this.signUpForm.get('confirmPassword');
  }

  get confirmationCode() {
    return this.confirmationForm.get('confirmationCode');
  }
}
