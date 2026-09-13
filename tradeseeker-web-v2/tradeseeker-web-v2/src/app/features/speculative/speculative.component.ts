import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { Subject, takeUntil, finalize } from 'rxjs';
import { ApiService } from '../../core/services/api.service';
import { SpeculativeStock, SpeculativeResponse } from '../../core/models';

@Component({
  selector: 'app-speculative',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './speculative.component.html',
  styleUrls: ['./speculative.component.scss']
})
export class SpeculativeComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  // Data
  speculativeStocks: SpeculativeStock[] = [];

  // Loading states
  isLoading = false;

  // Market filter
  selectedMarket = 'BK';
  // 'CH' is a virtual code covering both Chinese exchanges (Shanghai + Shenzhen) —
  // ApiService.withMarketExpansion() fans it out to the real SHG/SHE market codes.
  markets = [
    { value: 'BK', label: 'Thailand (BK)' },
    { value: 'US', label: 'US Stocks' },
    { value: 'HK', label: 'Hong Kong (HK)' },
    { value: 'CH', label: 'China (CH)' },
    { value: 'KO', label: 'Korea (KO)' },
    { value: 'TW', label: 'Taiwan (TW)' },
    { value: 'CC', label: 'Crypto (CC)' }
  ];

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.loadSpeculativeStocks();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Load speculative stocks from API
   */
  loadSpeculativeStocks(): void {
    this.isLoading = true;

    this.apiService.getSpeculativeStocks(this.selectedMarket)
      .pipe(
        takeUntil(this.destroy$),
        finalize(() => this.isLoading = false)
      )
      .subscribe({
        next: (response: SpeculativeResponse) => {
          // Highest speculative score first
          this.speculativeStocks = [...response.data].sort(
            (a, b) => b.speculative_score - a.speculative_score
          );
        },
        error: (error) => {
          console.error('Error loading speculative stocks:', error);
          this.speculativeStocks = [];
        }
      });
  }

  /**
   * Handle market change
   */
  onMarketChange(): void {
    this.loadSpeculativeStocks();
  }

  /**
   * Human-readable label for each reason code
   */
  formatReason(reason: string): string {
    const labels: Record<string, string> = {
      volume_spike: 'Volume spike',
      volatility_spike: 'Volatility spike',
      severe_red_candle: 'Severe red candle',
      parabolic_run_up: 'Parabolic run-up'
    };
    return labels[reason] || reason;
  }

  /**
   * Format percentage with sign
   */
  formatPercentage(value: number | null): string {
    if (value === null || value === undefined) return '—';
    const sign = value > 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
  }

  /**
   * Format currency
   */
  formatCurrency(value: number): string {
    return `${value.toFixed(2)}`;
  }

  /**
   * Format ratio (e.g. volume spike)
   */
  formatRatio(value: number): string {
    return `${value.toFixed(1)}x`;
  }

  /**
   * Format date
   */
  formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString();
  }

  /**
   * TrackBy function for ngFor performance
   */
  trackBySymbol(index: number, stock: SpeculativeStock): string {
    return stock.symbol;
  }
}
