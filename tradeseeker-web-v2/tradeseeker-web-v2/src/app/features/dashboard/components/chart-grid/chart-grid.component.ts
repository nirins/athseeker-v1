import { Component, Input } from '@angular/core';
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
}
