import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { Subject, takeUntil, finalize } from 'rxjs';
import { ApiService } from '../../core/services/api.service';
import { ATHStock, ATHResponse } from '../../core/models';

@Component({
  selector: 'app-ath',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './ath.component.html',
  styleUrls: ['./ath.component.scss']
})
export class AthComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  
  // Data
  athStocks: ATHStock[] = [];
  
  // Loading states
  isLoading = false;
  
  // Market filter
  selectedMarket = 'US';
  markets = [
    { value: 'US', label: 'US Stocks' },
    { value: 'BK', label: 'Thailand (BK)' },
    { value: 'CC', label: 'Crypto (CC)' }
  ];

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.loadATHStocks();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Load ATH stocks from API
   */
  loadATHStocks(): void {
    this.isLoading = true;
    
    this.apiService.getATHStocks(this.selectedMarket) // All ATH stocks (no date filter)
      .pipe(
        takeUntil(this.destroy$),
        finalize(() => this.isLoading = false)
      )
      .subscribe({
        next: (response: ATHResponse) => {
          this.athStocks = response.data;
          console.log(`Loaded ${this.athStocks.length} ATH stocks for ${this.selectedMarket}`);
          console.log('API Response timestamp:', new Date().toISOString());
        },
        error: (error) => {
          console.error('Error loading ATH stocks:', error);
          this.athStocks = [];
        }
      });
  }

  /**
   * Handle market change
   */
  onMarketChange(): void {
    this.loadATHStocks();
  }

  /**
   * Format percentage with sign
   */
  formatPercentage(value: number): string {
    return `+${value.toFixed(2)}%`;
  }

  /**
   * Format currency
   */
  formatCurrency(value: number): string {
    return `${value.toFixed(2)}`;
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
  trackBySymbol(index: number, stock: ATHStock): string {
    return stock.symbol;
  }
}