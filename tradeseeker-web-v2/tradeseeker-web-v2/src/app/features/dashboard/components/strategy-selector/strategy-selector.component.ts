import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

export type TradingStrategy = 'golden-cross' | 'death-cross' | 'ath' | 'near-ath' | 'hype' | 'divergence' | 'confirmed-reversal';

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

  // 'death-cross' is intentionally hidden from the UI (still a valid
  // TradingStrategy / API route if selected another way, e.g. sessionStorage).
  strategies: StrategyOption[] = [
    { value: 'ath', label: 'ATH' },
    { value: 'near-ath', label: 'Near ATH' },
    { value: 'golden-cross', label: 'Golden' },
    { value: 'hype', label: 'Hype' },
    { value: 'divergence', label: 'Div' },
    { value: 'confirmed-reversal', label: 'CR' }
  ];

  onStrategySelect(strategy: TradingStrategy): void {
    if (strategy !== this.selectedStrategy) {
      this.strategyChange.emit(strategy);
    }
  }
}