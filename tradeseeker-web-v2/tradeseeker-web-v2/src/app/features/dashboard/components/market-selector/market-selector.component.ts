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
  @Input() selectedMarket: string = 'US';
  @Output() marketChange = new EventEmitter<string>();

  markets = ['US', 'BK', 'CC'];

  onMarketSelect(market: string): void {
    if (market !== this.selectedMarket) {
      this.marketChange.emit(market);
    }
  }
}
