import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
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

  private destroy$ = new Subject<void>();

  constructor(
    private apiService: ApiService,
    private watchlistService: WatchlistService
  ) {}

  ngOnInit(): void {
    this.loadWatchlist();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
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
