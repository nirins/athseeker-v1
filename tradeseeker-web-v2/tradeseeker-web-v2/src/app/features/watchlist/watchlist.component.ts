import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { ApiService } from '../../core/services/api.service';
import { WatchlistService } from '../../core/services/watchlist.service';
import { StockData, ChartDisplayMode, ChartType } from '../../core/models';
import { ChartGridComponent } from '../dashboard/components/chart-grid/chart-grid.component';
import { LoadingSpinnerComponent } from '../../shared/components/loading-spinner/loading-spinner.component';
import { ErrorMessageComponent } from '../../shared/components/error-message/error-message.component';

@Component({
  selector: 'app-watchlist',
  standalone: true,
  imports: [CommonModule, RouterModule, ChartGridComponent, LoadingSpinnerComponent, ErrorMessageComponent],
  templateUrl: './watchlist.component.html',
  styleUrls: ['./watchlist.component.scss']
})
export class WatchlistComponent implements OnInit, OnDestroy {
  stockDataArray: StockData[] = [];
  beautyScoreMap: Map<string, number> = new Map();
  isLoading = false;
  error: string | null = null;
  selectedDisplayMode: ChartDisplayMode = 'both';
  selectedChartType: ChartType = 'candlestick';
  showScrollTop = false;

  private destroy$ = new Subject<void>();
  private onScrollBound = this.onScroll.bind(this);
  private onTouchStartBound = this.onTouchStart.bind(this);
  private onTouchEndBound = this.onTouchEnd.bind(this);
  private touchStartY = 0;
  private readonly PULL_THRESHOLD = 80;

  constructor(
    private apiService: ApiService,
    private watchlistService: WatchlistService,
    private router: Router
  ) {}

  get isNative(): boolean {
    return !!(window as any).Capacitor?.isNativePlatform?.();
  }

  goToDashboard(): void {
    this.router.navigate(['/dashboard']);
  }

  ngOnInit(): void {
    this.loadWatchlist();
    if (typeof window !== 'undefined') {
      window.addEventListener('scroll', this.onScrollBound, { passive: true });
      window.addEventListener('touchstart', this.onTouchStartBound, { passive: true });
      window.addEventListener('touchend', this.onTouchEndBound, { passive: true });
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    if (typeof window !== 'undefined') {
      window.removeEventListener('scroll', this.onScrollBound);
      window.removeEventListener('touchstart', this.onTouchStartBound);
      window.removeEventListener('touchend', this.onTouchEndBound);
    }
  }

  private onTouchStart(e: TouchEvent): void {
    this.touchStartY = e.touches[0].clientY;
  }

  private onTouchEnd(e: TouchEvent): void {
    const deltaY = e.changedTouches[0].clientY - this.touchStartY;
    if (deltaY > this.PULL_THRESHOLD && window.scrollY === 0) {
      this.onRefresh();
    }
  }

  private onScroll(): void {
    this.showScrollTop = window.scrollY > 300;
  }

  scrollToTop(): void {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  loadWatchlist(): void {
    this.isLoading = true;
    this.error = null;
    this.stockDataArray = [];

    this.watchlistService.loadWatchlist().pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: ({ symbols, beautyScores }) => {
        // Populate beauty score map
        this.beautyScoreMap = new Map(Object.entries(beautyScores));
        if (symbols.length === 0) {
          this.isLoading = false;
          return;
        }
        this.fetchStockData(symbols);
      },
      error: (err) => {
        this.error = 'Failed to load watchlist';
        this.isLoading = false;
      }
    });
  }

  private fetchStockData(symbols: string[]): void {
    const orderedData: (StockData | null)[] = new Array(symbols.length).fill(null);
    let completed = 0;

    symbols.forEach((symbol, index) => {
      this.apiService.getStockData(symbol).pipe(
        takeUntil(this.destroy$)
      ).subscribe({
        next: (data) => {
          orderedData[index] = data;
          completed++;
          // Render in order as they arrive
          const filled: StockData[] = [];
          for (const item of orderedData) {
            if (item === null) break;
            filled.push(item);
          }
          this.stockDataArray = filled;
          if (completed === symbols.length) {
            this.stockDataArray = orderedData.filter((d): d is StockData => d !== null);
            this.isLoading = false;
          }
        },
        error: () => {
          completed++;
          if (completed === symbols.length) {
            this.stockDataArray = orderedData.filter((d): d is StockData => d !== null);
            this.isLoading = false;
          }
        }
      });
    });
  }

  onRefresh(): void {
    this.loadWatchlist();
  }
}
