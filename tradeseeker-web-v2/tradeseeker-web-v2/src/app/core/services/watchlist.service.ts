import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject, of } from 'rxjs';
import { tap, catchError, map } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { AuthService } from './auth.service';

@Injectable({ providedIn: 'root' })
export class WatchlistService {
  private readonly baseUrl = environment.apiBaseUrl;

  private watchlistSymbols$ = new BehaviorSubject<Set<string>>(new Set());

  constructor(private http: HttpClient, private authService: AuthService) {}

  private get userId(): string {
    return this.authService.getAuthState().username || 'anonymous';
  }

  get symbols$(): Observable<Set<string>> {
    return this.watchlistSymbols$.asObservable();
  }

  isWatched(symbol: string): boolean {
    return this.watchlistSymbols$.value.has(symbol);
  }

  loadWatchlist(): Observable<string[]> {
    return this.http.get<{ data: { symbols: string[] } }>(`${this.baseUrl}/watchlist?user_id=${this.userId}`).pipe(
      map(res => res.data?.symbols ?? []),
      tap(symbols => this.watchlistSymbols$.next(new Set(symbols))),
      catchError(() => of([]))
    );
  }

  addToWatchlist(symbol: string): Observable<any> {
    return this.http.post(`${this.baseUrl}/watchlist`, { user_id: this.userId, symbol }).pipe(
      tap(() => {
        const current = new Set(this.watchlistSymbols$.value);
        current.add(symbol);
        this.watchlistSymbols$.next(current);
      }),
      catchError(err => { console.error('Failed to add to watchlist', err); return of(null); })
    );
  }

  removeFromWatchlist(symbol: string): Observable<any> {
    return this.http.delete(`${this.baseUrl}/watchlist`, {
      body: { user_id: this.userId, symbol }
    }).pipe(
      tap(() => {
        const current = new Set(this.watchlistSymbols$.value);
        current.delete(symbol);
        this.watchlistSymbols$.next(current);
      }),
      catchError(err => { console.error('Failed to remove from watchlist', err); return of(null); })
    );
  }

  toggle(symbol: string): Observable<any> {
    return this.isWatched(symbol)
      ? this.removeFromWatchlist(symbol)
      : this.addToWatchlist(symbol);
  }
}
