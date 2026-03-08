import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './landing.component.html',
  styleUrls: ['./landing.component.scss']
})
export class LandingComponent implements OnInit {

  constructor(
    private router: Router,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    // Don't auto-redirect - let users see the landing page and choose to get started
    // The landing page will be shown by default, users can click "Get Started" to proceed
  }

  navigateToLogin(): void {
    // If user is already authenticated, go directly to dashboard
    // Otherwise, go to login page
    if (this.authService.isAuthenticated()) {
      this.router.navigate(['/dashboard']);
    } else {
      this.router.navigate(['/login']);
    }
  }

  startFindingWinners(): void {
    // Same logic as navigateToLogin - check auth status and redirect accordingly
    if (this.authService.isAuthenticated()) {
      this.router.navigate(['/dashboard']);
    } else {
      this.router.navigate(['/login']);
    }
  }

  scrollToLearnMore(): void {
    const element = document.getElementById('learn-more');
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  }
}