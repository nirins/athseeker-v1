import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ChartDisplayMode } from '../../../../core/models';

interface DisplayModeOption {
  value: ChartDisplayMode;
  label: string;
}

@Component({
  selector: 'app-chart-display-mode-selector',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './chart-display-mode-selector.component.html',
  styleUrls: ['./chart-display-mode-selector.component.scss']
})
export class ChartDisplayModeSelectorComponent {
  @Input() selectedMode: ChartDisplayMode = 'both';
  @Output() modeChange = new EventEmitter<ChartDisplayMode>();

  displayModes: DisplayModeOption[] = [
    { value: 'both', label: 'Both' },
    { value: 'prices', label: 'Prices Only' },
    { value: 'ema', label: 'EMA Only' }
  ];

  onModeSelect(mode: ChartDisplayMode): void {
    if (mode !== this.selectedMode) {
      this.modeChange.emit(mode);
    }
  }
}
