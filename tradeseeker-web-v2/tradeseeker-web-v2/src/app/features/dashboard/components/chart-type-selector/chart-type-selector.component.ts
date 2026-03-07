import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ChartType } from '../../../../core/models';

interface ChartTypeOption {
  value: ChartType;
  label: string;
}

@Component({
  selector: 'app-chart-type-selector',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './chart-type-selector.component.html',
  styleUrls: ['./chart-type-selector.component.scss']
})
export class ChartTypeSelectorComponent {
  @Input() selectedType: ChartType = 'candlestick';
  @Output() typeChange = new EventEmitter<ChartType>();

  chartTypes: ChartTypeOption[] = [
    { value: 'line', label: 'Line' },
    { value: 'candlestick', label: 'Candlestick' }
  ];

  onTypeSelect(type: ChartType): void {
    if (type !== this.selectedType) {
      this.typeChange.emit(type);
    }
  }
}
