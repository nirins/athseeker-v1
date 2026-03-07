# TradeSeekerWeb v2

A modern Angular application for visualizing golden cross stock data with interactive charts and real-time market analysis.

## 🌐 Live Application

**[View Live Application](https://d310shk0w5mump.cloudfront.net/)**

## Overview

TradeSeekerWeb v2 is a comprehensive stock analysis dashboard that:
- Authenticates users via AWS Cognito
- Fetches golden cross stock data from the tradeseeker-api-v2 REST API
- Displays interactive charts with Chart.js and chartjs-chart-financial
- Provides responsive grid layout for multiple stock charts
- Supports both candlestick and line chart views
- Includes EMA (Exponential Moving Average) overlays
- Deployed as a static website on AWS S3 with CloudFront CDN

## Quick Start

### Using Makefile (Recommended)
```bash
# Build and deploy
make all

# Just build
make build

# Just deploy
make deploy

# Show help
make help
```

This project was generated with [Angular CLI](https://github.com/angular/angular-cli) version 17.3.17.

## Development server

Run `ng serve` for a dev server. Navigate to `http://localhost:4200/`. The application will automatically reload if you change any of the source files.

## Deployment

The application is deployed to AWS S3 with CloudFront CDN. See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

### Quick Deployment
```bash
# Build and deploy in one command
make all

# Or manually:
npm run build
./scripts/deploy.sh ts-dev-web-v2-app E379OF6HGDUSPS
```

## Code scaffolding

Run `ng generate component component-name` to generate a new component. You can also use `ng generate directive|pipe|service|class|guard|interface|enum|module`.

## Build

Run `ng build` to build the project. The build artifacts will be stored in the `dist/` directory.

## Running unit tests

Run `ng test` to execute the unit tests via [Karma](https://karma-runner.github.io).

## Running end-to-end tests

Run `ng e2e` to execute the end-to-end tests via a platform of your choice. To use this command, you need to first add a package that implements end-to-end testing capabilities.

## Further help

To get more help on the Angular CLI use `ng help` or go check out the [Angular CLI Overview and Command Reference](https://angular.io/cli) page.
