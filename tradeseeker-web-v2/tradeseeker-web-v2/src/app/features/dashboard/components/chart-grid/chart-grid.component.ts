import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { StockData, ChartDisplayMode, ChartType } from '../../../../core/models';
import { StockChartComponent } from '../stock-chart/stock-chart.component';

@Component({
  selector: 'app-chart-grid',
  standalone: true,
  imports: [CommonModule, StockChartComponent],
  templateUrl: './chart-grid.component.html',
  styleUrls: ['./chart-grid.component.scss']
})
export class ChartGridComponent {
  @Input() stockData: StockData[] = [];
  @Input() displayMode: ChartDisplayMode = 'both';
  @Input() chartType: ChartType = 'candlestick';
  @Output() gradeSelectionRequested = new EventEmitter<{symbol: string, stockData: StockData}>();

  onGradeSelectionRequested(event: {symbol: string, stockData: StockData}): void {
    this.gradeSelectionRequested.emit(event);
  }
}
