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

  loadWatchlist(): Observable<{ symbols: string[]; beautyScores: Record<string, number> }> {
    return this.http.get<{ data: { symbols: string[]; beauty_scores: Record<string, number> } }>(
      `${this.baseUrl}/watchlist?user_id=${this.userId}`
    ).pipe(
      map(res => ({
        symbols: res.data?.symbols ?? [],
        beautyScores: res.data?.beauty_scores ?? {}
      })),
      tap(({ symbols }) => this.watchlistSymbols$.next(new Set(symbols))),
      catchError(() => of({ symbols: [], beautyScores: {} }))
    );
  }

  addToWatchlist(symbol: string, beautyScore?: number): Observable<any> {
    const body: any = { user_id: this.userId, symbol };
    if (beautyScore != null) body.beauty_score = beautyScore;
    return this.http.post(`${this.baseUrl}/watchlist`, body).pipe(
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

  toggle(symbol: string, beautyScore?: number): Observable<any> {
    return this.isWatched(symbol)
      ? this.removeFromWatchlist(symbol)
      : this.addToWatchlist(symbol, beautyScore);
  }
}
