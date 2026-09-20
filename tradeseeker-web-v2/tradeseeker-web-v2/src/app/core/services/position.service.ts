import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject, of } from 'rxjs';
import { tap, catchError, map } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { AuthService } from './auth.service';

/**
 * Tracks whether the user holds a position in a symbol — independent of the
 * watchlist. A symbol can be held without being watched, and removing it
 * from the watchlist never clears its position flag (separate DynamoDB
 * table, separate endpoints).
 */
@Injectable({ providedIn: 'root' })
export class PositionService {
  private readonly baseUrl = environment.apiBaseUrl;

  private positionSymbols$ = new BehaviorSubject<Set<string>>(new Set());

  constructor(private http: HttpClient, private authService: AuthService) {}

  private get userId(): string {
    return this.authService.getAuthState().username || 'anonymous';
  }

  get symbols$(): Observable<Set<string>> {
    return this.positionSymbols$.asObservable();
  }

  hasPosition(symbol: string): boolean {
    return this.positionSymbols$.value.has(symbol);
  }

  loadPositions(): Observable<{ symbols: string[] }> {
    return this.http.get<{ data: { symbols: string[] } }>(
      `${this.baseUrl}/positions?user_id=${this.userId}`
    ).pipe(
      map(res => ({ symbols: res.data?.symbols ?? [] })),
      tap(({ symbols }) => this.positionSymbols$.next(new Set(symbols))),
      catchError(() => of({ symbols: [] }))
    );
  }

  addPosition(symbol: string): Observable<any> {
    return this.http.post(`${this.baseUrl}/positions`, { user_id: this.userId, symbol }).pipe(
      tap(() => {
        const current = new Set(this.positionSymbols$.value);
        current.add(symbol);
        this.positionSymbols$.next(current);
      }),
      catchError(err => { console.error('Failed to add position', err); return of(null); })
    );
  }

  removePosition(symbol: string): Observable<any> {
    return this.http.delete(`${this.baseUrl}/positions`, {
      body: { user_id: this.userId, symbol }
    }).pipe(
      tap(() => {
        const current = new Set(this.positionSymbols$.value);
        current.delete(symbol);
        this.positionSymbols$.next(current);
      }),
      catchError(err => { console.error('Failed to remove position', err); return of(null); })
    );
  }

  toggle(symbol: string): Observable<any> {
    return this.hasPosition(symbol)
      ? this.removePosition(symbol)
      : this.addPosition(symbol);
  }
}
