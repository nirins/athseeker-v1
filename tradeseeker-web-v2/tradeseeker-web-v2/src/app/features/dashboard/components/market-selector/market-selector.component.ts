import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-market-selector',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './market-selector.component.html',
  styleUrls: ['./market-selector.component.scss']
})
export class MarketSelectorComponent {
  @Input() selectedMarket: string = 'BK';
  @Output() marketChange = new EventEmitter<string>();

  // 'CH' is a virtual code covering both Chinese exchanges (Shanghai + Shenzhen) —
  // ApiService.withMarketExpansion() fans it out to the real SHG/SHE market codes.
  markets = ['BK', 'US', 'HK', 'CH', 'KO', 'TW', 'CC'];

  onMarketSelect(market: string): void {
    if (market !== this.selectedMarket) {
      this.marketChange.emit(market);
    }
  }
}
