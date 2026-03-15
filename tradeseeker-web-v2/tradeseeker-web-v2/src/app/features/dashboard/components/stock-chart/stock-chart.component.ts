import { Component, Input, Output, EventEmitter, OnInit, OnChanges, OnDestroy, AfterViewInit, SimpleChanges, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { Chart, ChartConfiguration, registerables, TimeScale, LinearScale } from 'chart.js';
import { CandlestickController, CandlestickElement, OhlcController, OhlcElement } from 'chartjs-chart-financial';
import 'chartjs-adapter-date-fns';
import { StockData, ChartDisplayMode, ChartType, EnhancedStockData } from '../../../../core/models';
import { LoadingSpinnerComponent } from '../../../../shared/components/loading-spinner/loading-spinner.component';
import { ErrorMessageComponent } from '../../../../shared/components/error-message/error-message.component';

// Register Chart.js components
Chart.register(...registerables, CandlestickController, CandlestickElement, OhlcController, OhlcElement, TimeScale, LinearScale);

@Component({
  selector: 'app-stock-chart',
  standalone: true,
  imports: [CommonModule, LoadingSpinnerComponent, ErrorMessageComponent],
  templateUrl: './stock-chart.component.html',
  styleUrls: ['./stock-chart.component.scss']
})
export class StockChartComponent implements OnInit, OnChanges, OnDestroy, AfterViewInit {
  @Input() stockData!: StockData; // Keep for backward compatibility
  @Input() enhancedStockData!: EnhancedStockData;
  @Input() displayMode: ChartDisplayMode = 'both';
  @Input() chartType: ChartType = 'candlestick';
  @Input() isDetailView: boolean = false;
  @Input() isLabelMode: boolean = false;
  @Input() beautyScore: number | null = null;
  @Input() grade: string | null = null;

  get displayScore(): string | null {
    if (this.beautyScore === null) return null;
    return (this.beautyScore / 10).toFixed(1);
  }
  @Output() gradeSelectionRequested = new EventEmitter<{symbol: string, stockData: StockData}>();
  @ViewChild('chartCanvas', { static: false }) chartCanvas!: ElementRef<HTMLCanvasElement>;
  @ViewChild('volumeCanvas', { static: false }) volumeCanvas!: ElementRef<HTMLCanvasElement>;

  chart: Chart | null = null;
  volumeChart: Chart | null = null;
  isLoading = false;
  error: string | null = null;

  constructor(private router: Router) {}

  private isMobileDevice(): boolean {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || 
           window.innerWidth <= 768;
  }

  // Getter to get the actual stock data
  get currentStockData(): StockData {
    return this.enhancedStockData?.stockData || this.stockData;
  }

  // Getter to get golden cross percentages
  get greenDaysPercent(): number | null {
    return this.enhancedStockData?.goldenCrossData?.green_days_30d_pct || null;
  }

  get maxRedCandlePercent(): number | null {
    return this.enhancedStockData?.goldenCrossData?.max_red_candle_30d_pct || null;
  }

  ngOnInit(): void {
    // Don't render immediately - wait for view to be fully initialized
  }

  ngAfterViewInit(): void {
    // Render chart after view is initialized
    if (this.stockData) {
      // Use setTimeout to ensure the canvas is fully rendered
      setTimeout(() => {
        this.renderChart();
      }, 0);
    }
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['stockData']) {
      if (changes['stockData'].firstChange && this.stockData) {
        // First time receiving data - render after view init
        setTimeout(() => {
          this.renderChart();
        }, 0);
      } else if (!changes['stockData'].firstChange) {
        // Subsequent changes - update chart
        this.updateChart();
      }
    }

    if (changes['displayMode'] && !changes['displayMode'].firstChange) {
      this.updateChart();
    }

    if (changes['chartType'] && !changes['chartType'].firstChange) {
      this.updateChart();
    }
  }

  ngOnDestroy(): void {
    if (this.chart) {
      this.chart.destroy();
      this.chart = null;
    }
    if (this.volumeChart) {
      this.volumeChart.destroy();
      this.volumeChart = null;
    }
  }

  renderChart(): void {
    // Validate stock data before rendering
    if (!this.validateStockData()) {
      return;
    }

    if (!this.chartCanvas || !this.chartCanvas.nativeElement) {
      console.warn('Chart canvas not available yet, retrying...');
      // Retry after a short delay
      setTimeout(() => {
        this.renderChart();
      }, 100);
      return;
    }

    try {
      // Destroy existing chart if it exists
      if (this.chart) {
        this.chart.destroy();
        this.chart = null;
      }

      const ctx = this.chartCanvas.nativeElement.getContext('2d');
      if (!ctx) {
        this.error = 'Failed to get canvas context';
        return;
      }

      const datasets = this.getDatasets();
      
      // Validate datasets before creating chart
      if (!datasets || datasets.length === 0) {
        this.error = 'No data to display';
        return;
      }

      const chartType = this.getChartType();
      console.log('Chart type:', chartType, 'Display mode:', this.displayMode, 'Chart type setting:', this.chartType);

      const config: ChartConfiguration = {
        type: chartType === 'candlestick' ? 'candlestick' as any : chartType as any,
        data: { datasets },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          backgroundColor: 'white',
          interaction: {
            intersect: false,
            mode: 'index'
          },
          layout: {
            padding: {
              left: 10,
              right: 10,
              top: 10,
              bottom: 10
            }
          },
          plugins: {
            title: {
              display: false // Always hide the chart.js title since we have our own header
            },
            legend: {
              display: false
            },
            tooltip: {
              enabled: !this.isMobileDevice(), // Disable tooltips on mobile devices
              mode: 'index',
              intersect: false,
              callbacks: chartType === 'candlestick' ? {
                label: function(context: any) {
                  const data = context.raw;
                  if (data && typeof data === 'object' && 'o' in data) {
                    return [
                      `Open: ${data.o?.toFixed(2)}`,
                      `High: ${data.h?.toFixed(2)}`,
                      `Low: ${data.l?.toFixed(2)}`,
                      `Close: ${data.c?.toFixed(2)}`
                    ];
                  }
                  return context.formattedValue;
                }
              } : undefined
            }
          },
          scales: {
            x: {
              type: 'time',
              time: {
                unit: 'day',
                displayFormats: { day: 'MMM dd' }
              },
              title: { display: false },
              ticks: {
                display: false
              },
              grid: {
                display: false
              }
            },
            y: {
              type: 'linear',
              beginAtZero: false,
              ticks: {
                display: true
              },
              title: {
                display: false
              },
              grid: {
                display: false
              }
            }
          },
          elements: {
            point: {
              radius: 0
            }
          }
        }
      };

      this.chart = new Chart(ctx, config);
      
      // Ensure canvas background is white
      if (this.chart.canvas) {
        this.chart.canvas.style.backgroundColor = 'white';
      }
      
      // Render volume chart only in detail view
      if (this.isDetailView) {
        this.renderVolumeChart();
      }
      
      this.error = null;
      console.log(`Chart rendered successfully for ${this.stockData.symbol}`);
    } catch (err) {
      console.error('Error rendering chart:', err);
      this.error = this.getChartErrorMessage(err);
    }
  }

  /**
   * Validate stock data before rendering
   */
  private validateStockData(): boolean {
    if (!this.stockData) {
      this.error = 'No stock data provided';
      return false;
    }

    if (!this.stockData.symbol) {
      this.error = 'Invalid stock data: missing symbol';
      return false;
    }

    if (!this.stockData.prices || !Array.isArray(this.stockData.prices)) {
      this.error = 'Invalid stock data: prices must be an array';
      return false;
    }

    if (this.stockData.prices.length === 0) {
      this.error = 'No price data available';
      return false;
    }

    // Validate price data structure
    const hasValidPrices = this.stockData.prices.every(p => 
      p.date && 
      typeof p.open === 'number' && 
      typeof p.high === 'number' && 
      typeof p.low === 'number' && 
      typeof p.close === 'number' &&
      !isNaN(p.open) && !isNaN(p.high) && !isNaN(p.low) && !isNaN(p.close)
    );

    if (!hasValidPrices) {
      this.error = 'Invalid price data: missing or invalid values';
      return false;
    }

    // Validate EMA data if needed
    if (this.displayMode === 'ema' || this.displayMode === 'both') {
      if (!this.stockData.emas) {
        this.error = 'Invalid stock data: missing EMA data';
        return false;
      }

      const requiredEmas = ['ema7', 'ema30', 'ema50', 'ema200'];
      const hasValidEmas = requiredEmas.every(ema => 
        Array.isArray(this.stockData.emas[ema as keyof typeof this.stockData.emas]) && 
        this.stockData.emas[ema as keyof typeof this.stockData.emas].length > 0
      );

      if (!hasValidEmas) {
        this.error = 'Invalid EMA data: missing or invalid values';
        return false;
      }
    }

    return true;
  }

  /**
   * Get user-friendly error message for chart errors
   */
  private getChartErrorMessage(error: any): string {
    if (error instanceof Error) {
      // Check for specific Chart.js errors
      if (error.message.includes('Canvas')) {
        return 'Failed to initialize chart canvas';
      }
      if (error.message.includes('context')) {
        return 'Failed to get chart rendering context';
      }
      if (error.message.includes('data')) {
        return 'Invalid chart data format';
      }
      if (error.message.includes('scale') || error.message.includes('axis')) {
        return 'Failed to configure chart axes';
      }
      
      // Generic error with message
      return `Chart error: ${error.message}`;
    }
    
    return 'Failed to render chart';
  }

  updateChart(): void {
    if (this.chart) {
      this.chart.destroy();
      this.chart = null;
    }
    if (this.volumeChart) {
      this.volumeChart.destroy();
      this.volumeChart = null;
    }
    this.renderChart();
  }

  /**
   * Render the volume chart at the bottom (only in detail view)
   */
  private renderVolumeChart(): void {
    // Only render volume chart in detail view
    if (!this.isDetailView) {
      return;
    }

    if (!this.volumeCanvas || !this.volumeCanvas.nativeElement) {
      console.warn('Volume canvas not available yet');
      return;
    }

    try {
      // Destroy existing volume chart if it exists
      if (this.volumeChart) {
        this.volumeChart.destroy();
        this.volumeChart = null;
      }

      const ctx = this.volumeCanvas.nativeElement.getContext('2d');
      if (!ctx) {
        console.error('Failed to get volume canvas context');
        return;
      }

      // Get the same filtered data as the main chart
      const filteredData = this.isDetailView ? this.getDataAsIs() : this.getLatest360Days();
      
      // Create volume data with same dates as price data to maintain alignment
      const volumeData = filteredData.prices.map(p => ({
        x: new Date(p.date).getTime(),
        y: Math.max(p.volume || 1, 1) // Use 1 as minimum for zero/null volumes
      }));

      const config: ChartConfiguration = {
        type: 'bar',
        data: {
          datasets: [{
            label: 'Volume',
            data: volumeData,
            backgroundColor: '#666666', // Darker gray
            borderColor: '#444444', // Even darker border
            borderWidth: 0
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          backgroundColor: 'white',
          interaction: {
            intersect: false,
            mode: 'index'
          },
          layout: {
            padding: {
              left: 5, // Reduced from 10px
              right: 5, // Reduced from 10px
              top: 0, // Removed top padding
              bottom: 2 // Minimal bottom padding
            }
          },
          plugins: {
            title: {
              display: false
            },
            legend: {
              display: false
            },
            tooltip: {
              enabled: false // Disable volume tooltips
            }
          },
          scales: {
            x: {
              type: 'time',
              time: {
                unit: 'day',
                displayFormats: { day: 'MMM dd' }
              },
              title: { display: false },
              ticks: {
                display: false
              },
              grid: {
                display: false
              }
            },
            y: {
              type: 'logarithmic',
              ticks: {
                display: true, // Show ticks to reserve space
                maxTicksLimit: 4,
                color: '#666', // Normal text color (though labels will be empty)
                callback: function(value: any) {
                  return ''; // Return empty string to hide numbers but keep spacing
                }
              },
              title: {
                display: false
              },
              grid: {
                display: false
              },
              border: {
                display: true // Show the axis line
              }
            }
          },
          elements: {
            bar: {
              borderRadius: 0
            }
          }
        }
      };

      this.volumeChart = new Chart(ctx, config);
      
      // Ensure canvas background is white
      if (this.volumeChart.canvas) {
        this.volumeChart.canvas.style.backgroundColor = 'white';
      }
      
      console.log(`Volume chart rendered successfully for ${this.stockData.symbol}`);
    } catch (err) {
      console.error('Error rendering volume chart:', err);
    }
  }

  private getChartType(): string {
    if (this.displayMode === 'ema') {
      return 'line';
    }

    if (this.chartType === 'candlestick' &&
        (this.displayMode === 'prices' || this.displayMode === 'both')) {
      return 'candlestick';
    }

    return 'line';
  }

  private getDatasets(): any[] {
    // In detail view, use data as-is. In dashboard view, filter to latest 360 days
    const filteredData = this.isDetailView ? this.getDataAsIs() : this.getLatest360Days();
    const dates = filteredData.prices.map(p => new Date(p.date));
    const datasets: any[] = [];

    try {
      // Add price data if mode is 'prices' or 'both'
      if (this.displayMode === 'prices' || this.displayMode === 'both') {
        if (this.chartType === 'candlestick') {
          const candlestickData = filteredData.prices.map(p => ({
            x: new Date(p.date).getTime(), // Use timestamp instead of Date object
            o: Number(p.open),
            h: Number(p.high),
            l: Number(p.low),
            c: Number(p.close)
          }));

          console.log('Candlestick data sample:', candlestickData.slice(0, 3));

          datasets.push({
            type: 'candlestick',
            label: this.currentStockData.symbol,
            data: candlestickData,
            color: {
              up: '#26a69a',      // Green for bullish candles
              down: '#ef5350',    // Red for bearish candles
              unchanged: '#999'   // Gray for unchanged
            },
            borderColor: {
              up: '#26a69a',
              down: '#ef5350',
              unchanged: '#999'
            },
            wickColor: {
              up: '#26a69a',
              down: '#ef5350',
              unchanged: '#999'
            }
          });
        } else {
          const closePriceData = filteredData.prices.map((p, idx) => ({
            x: dates[idx],
            y: p.close
          }));

          datasets.push({
            type: 'line',
            label: `${this.stockData.symbol} Close`,
            data: closePriceData,
            borderColor: '#888',
            borderWidth: 1,
            fill: false,
            pointRadius: 0
          });
        }
      }

      // Add EMA lines if mode is 'ema' or 'both'
      if (this.displayMode === 'ema' || this.displayMode === 'both') {
        // Validate EMA data exists
        if (!this.currentStockData.emas) {
          throw new Error('EMA data not available');
        }

        // Create EMA datasets with proper date alignment
        const emaDatasets = [
          {
            type: 'line',
            label: 'EMA 7',
            data: dates.map((date, idx) => {
              const emaValue = filteredData.emas.ema7[idx];
              return emaValue !== null && emaValue !== undefined ? { x: date, y: emaValue } : null;
            }).filter(point => point !== null),
            borderColor: '#bbb',
            borderWidth: 1,
            fill: false,
            pointRadius: 0
          },
          {
            type: 'line',
            label: 'EMA 30',
            data: dates.map((date, idx) => {
              const emaValue = filteredData.emas.ema30[idx];
              return emaValue !== null && emaValue !== undefined ? { x: date, y: emaValue } : null;
            }).filter(point => point !== null),
            borderColor: '#bbb',
            borderWidth: 1,
            fill: false,
            pointRadius: 0
          },
          {
            type: 'line',
            label: 'EMA 50',
            data: dates.map((date, idx) => {
              const emaValue = filteredData.emas.ema50[idx];
              return emaValue !== null && emaValue !== undefined ? { x: date, y: emaValue } : null;
            }).filter(point => point !== null),
            borderColor: '#bbb',
            borderWidth: 1,
            fill: false,
            pointRadius: 0
          },
          {
            type: 'line',
            label: 'EMA 200',
            data: dates.map((date, idx) => {
              const emaValue = filteredData.emas.ema200[idx];
              return emaValue !== null && emaValue !== undefined ? { x: date, y: emaValue } : null;
            }).filter(point => point !== null),
            borderColor: '#bbb',
            borderWidth: 1,
            fill: false,
            pointRadius: 0
          }
        ];

        datasets.push(...emaDatasets);
      }
    } catch (err) {
      console.error('Error creating datasets:', err);
      throw new Error('Failed to create chart datasets');
    }

    return datasets;
  }

  /**
   * Use stock data as-is without additional filtering (for detail view)
   */
  private getDataAsIs(): { prices: any[], emas: any } {
    console.log(`Using data as-is for ${this.stockData.symbol}: ${this.stockData.prices.length} data points`);
    
    return {
      prices: this.stockData.prices,
      emas: this.stockData.emas
    };
  }

  /**
   * Filter stock data to show only the latest 360 days
   */
  private getLatest360Days(): { prices: any[], emas: any } {
    const maxDays = 360;
    
    // For sparse data, use a different approach - take the last N records instead of date-based filtering
    const totalRecords = this.stockData.prices.length;
    const recordsToShow = Math.min(maxDays, totalRecords);
    
    // Take the last N records (most recent data)
    const sortedPrices = this.stockData.prices.slice(-recordsToShow);

    // Filter EMA data to match the same records
    const filteredEmas: any = {
      ema7: [] as (number | null)[],
      ema30: [] as (number | null)[],
      ema50: [] as (number | null)[],
      ema200: [] as (number | null)[]
    };

    if (this.stockData.emas) {
      // Take the corresponding EMA values for the same record range
      filteredEmas.ema7 = this.stockData.emas.ema7.slice(-recordsToShow);
      filteredEmas.ema30 = this.stockData.emas.ema30.slice(-recordsToShow);
      filteredEmas.ema50 = this.stockData.emas.ema50.slice(-recordsToShow);
      filteredEmas.ema200 = this.stockData.emas.ema200.slice(-recordsToShow);
    }

    console.log(`Filtered to latest ${sortedPrices.length} records for ${this.stockData.symbol}`, {
      prices: sortedPrices.length,
      ema7: filteredEmas.ema7.length,
      ema30: filteredEmas.ema30.length,
      ema50: filteredEmas.ema50.length,
      ema200: filteredEmas.ema200.length,
      ema7_valid: filteredEmas.ema7.filter((v: any) => v !== null && v !== undefined).length,
      ema30_valid: filteredEmas.ema30.filter((v: any) => v !== null && v !== undefined).length,
      ema50_valid: filteredEmas.ema50.filter((v: any) => v !== null && v !== undefined).length,
      ema200_valid: filteredEmas.ema200.filter((v: any) => v !== null && v !== undefined).length
    });
    
    return {
      prices: sortedPrices,
      emas: filteredEmas
    };
  }

  /**
   * Navigate to stock detail page in new tab
   */
  navigateToDetail(): void {
    if (!this.isDetailView && this.currentStockData?.symbol) {
      const url = this.router.serializeUrl(
        this.router.createUrlTree(['/stock', this.currentStockData.symbol])
      );
      window.open(url, '_blank');
    }
  }

  /**
   * Handle stock symbol click to navigate to detail view
   */
  onStockClick(): void {
    this.navigateToDetail();
  }

  /**
   * Show grade selection popup for manual labeling
   */
  showGradeSelectionPopup(): void {
    // Emit event to parent component to show grade selection
    this.gradeSelectionRequested.emit({
      symbol: this.currentStockData?.symbol,
      stockData: this.currentStockData
    });
  }

  /**
   * Handle canvas click events - navigate to detail page in new tab
   */
  onCanvasClick(event: MouseEvent): void {
    if (this.isDetailView) {
      return;
    }

    // Navigate to detail page in new tab when clicking anywhere on the chart
    this.navigateToDetail();
  }

  /**
   * Handle canvas auxiliary click events (middle mouse button)
   */
  onCanvasAuxClick(event: MouseEvent): void {
    if (this.isDetailView) {
      return;
    }

    // Handle middle mouse button click (button === 1)
    if (event.button === 1) {
      event.preventDefault();
      this.navigateToDetail();
    }
  }
}
