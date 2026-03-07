import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-error-message',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './error-message.component.html',
  styleUrls: ['./error-message.component.scss']
})
export class ErrorMessageComponent {
  @Input() message: string = '';
  @Input() guidance: string = '';
  @Input() showRetry: boolean = false;
  @Output() retry = new EventEmitter<void>();

  onRetry(): void {
    this.retry.emit();
  }
}
