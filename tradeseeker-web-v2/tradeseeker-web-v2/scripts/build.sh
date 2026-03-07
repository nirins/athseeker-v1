#!/bin/bash

# Build script for TradeSeekerWeb v2
# This script builds the Angular application for production deployment

set -e  # Exit on error

echo "🔨 Building TradeSeekerWeb v2..."

# Install dependencies
echo "📦 Installing dependencies..."
npm ci

# Run production build
echo "🏗️  Running production build..."
npm run build -- --configuration production

echo "✅ Build complete! Output in dist/tradeseeker-web-v2/browser/"
