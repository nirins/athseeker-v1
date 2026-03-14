import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

export type TradingStrategy = 'golden-cross' | 'death-cross' | 'ath' | 'near-ath';

interface StrategyOption {
  value: TradingStrategy;
  label: string;
}

@Component({
  selector: 'app-strategy-selector',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './strategy-selector.component.html',
  styleUrls: ['./strategy-selector.component.scss']
})
export class StrategySelectorComponent {
  @Input() selectedStrategy: TradingStrategy = 'ath';
  @Output() strategyChange = new EventEmitter<TradingStrategy>();

  strategies: StrategyOption[] = [
    { value: 'ath', label: 'ATH' },
    { value: 'near-ath', label: 'Near ATH' },
    { value: 'golden-cross', label: 'Golden Cross' },
    { value: 'death-cross', label: 'Death Cross' }
  ];

  onStrategySelect(strategy: TradingStrategy): void {
    if (strategy !== this.selectedStrategy) {
      this.strategyChange.emit(strategy);
    }
  }
}