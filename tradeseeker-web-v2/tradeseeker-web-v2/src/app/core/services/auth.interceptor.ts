import { Injectable } from '@angular/core';
import { HttpInterceptor, HttpRequest, HttpHandler, HttpEvent, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { Router } from '@angular/router';
import { AuthService } from './auth.service';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    // Get the auth token from the service
    const token = this.authService.getToken();

    // Clone the request and add the authorization header if token exists
    let authReq = req;
    if (token) {
      authReq = req.clone({
        setHeaders: {
          Authorization: `Bearer ${token}`
        }
      });
    }

    // Send the cloned request with the header to the next handler
    return next.handle(authReq).pipe(
      catchError((error: HttpErrorResponse) => {
        // Handle 401 Unauthorized responses
        if (error.status === 401) {
          // Token is invalid or expired, logout and redirect to login
          this.authService.logout();
          this.router.navigate(['/login']);
        }
        
        return throwError(() => error);
      })
    );
  }
}
