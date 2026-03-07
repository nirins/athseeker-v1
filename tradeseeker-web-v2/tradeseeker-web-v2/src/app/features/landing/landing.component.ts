import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './landing.component.html',
  styleUrls: ['./landing.component.scss']
})
export class LandingComponent {

  constructor(private router: Router) {}

  navigateToLogin(): void {
    this.router.navigate(['/login']);
  }

  scrollToLearnMore(): void {
    const element = document.getElementById('learn-more');
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  }
}