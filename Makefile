# TradeSeekerV2 - Root Makefile
# Orchestrates all three components: API, Batch, and Web

.PHONY: help all api batch web deploy-all clean test status

# Default target
help:
	@echo "🚀 TradeSeekerV2 - Monorepo Management"
	@echo ""
	@echo "Available targets:"
	@echo "  make all        - Build and deploy all components (API + Batch + Web)"
	@echo "  make api        - Build and deploy API only"
	@echo "  make batch      - Build and deploy Batch processing only"
	@echo "  make web        - Build and deploy Web frontend only"
	@echo ""
	@echo "Individual operations:"
	@echo "  make deploy-all - Deploy all components"
	@echo "  make test       - Run tests for all components"
	@echo "  make clean      - Clean all build artifacts"
	@echo "  make status     - Show status of all components"
	@echo ""
	@echo "Component-specific targets:"
	@echo "  make api-test   - Test API only"
	@echo "  make batch-test - Test Batch only"
	@echo "  make web-test   - Test Web only"

# Build and deploy all components
all: api batch web
	@echo "🎉 All components deployed successfully!"
	@echo ""
	@echo "📋 Deployment Summary:"
	@echo "  ✅ API: Serverless backend deployed"
	@echo "  ✅ Batch: ETL pipeline deployed"
	@echo "  ✅ Web: Frontend deployed to S3/CloudFront"

# API component
api:
	@echo "🔧 Deploying API component..."
	@cd tradeseeker-api-v2 && $(MAKE) all
	@echo "✅ API deployment complete!"

# Batch component
batch:
	@echo "🔧 Deploying Batch component..."
	@cd tradeseeker-batch-v2 && $(MAKE) deploy-all
	@echo "✅ Batch deployment complete!"

# Web component
web:
	@echo "🔧 Deploying Web component..."
	@cd tradeseeker-web-v2/tradeseeker-web-v2 && $(MAKE) all
	@echo "✅ Web deployment complete!"

# Deploy all (alias for all)
deploy-all: all

# Run tests for all components
test: api-test batch-test web-test
	@echo "🧪 All tests completed!"

# Test individual components
api-test:
	@echo "🧪 Running API tests..."
	@cd tradeseeker-api-v2 && $(MAKE) test

batch-test:
	@echo "🧪 Running Batch tests..."
	@cd tradeseeker-batch-v2 && python -m pytest

web-test:
	@echo "🧪 Running Web tests..."
	@cd tradeseeker-web-v2/tradeseeker-web-v2 && $(MAKE) test

# Clean all build artifacts
clean:
	@echo "🧹 Cleaning all components..."
	@cd tradeseeker-api-v2 && $(MAKE) clean
	@cd tradeseeker-batch-v2 && $(MAKE) clean
	@cd tradeseeker-web-v2/tradeseeker-web-v2 && $(MAKE) clean
	@echo "✅ All components cleaned!"

# Show status of all components
status:
	@echo "📊 TradeSeekerV2 - Component Status"
	@echo ""
	@echo "🔧 API Component:"
	@cd tradeseeker-api-v2 && $(MAKE) help | head -3
	@echo ""
	@echo "🔧 Batch Component:"
	@cd tradeseeker-batch-v2 && $(MAKE) help | head -3
	@echo ""
	@echo "🔧 Web Component:"
	@cd tradeseeker-web-v2/tradeseeker-web-v2 && $(MAKE) status

# Quick deployment targets (for development)
api-quick:
	@echo "⚡ Quick API deployment..."
	@cd tradeseeker-api-v2 && $(MAKE) deploy

batch-quick:
	@echo "⚡ Quick Batch deployment..."
	@cd tradeseeker-batch-v2 && $(MAKE) deploy-downloader

web-quick:
	@echo "⚡ Quick Web deployment..."
	@cd tradeseeker-web-v2/tradeseeker-web-v2 && $(MAKE) quick-deploy

# Development targets
install:
	@echo "📦 Installing dependencies for all components..."
	@echo "Installing API dependencies..."
	@cd tradeseeker-api-v2 && pip install -r requirements.txt -r requirements-dev.txt
	@echo "Installing Batch dependencies..."
	@cd tradeseeker-batch-v2 && pip install -r requirements.txt
	@echo "Installing Web dependencies..."
	@cd tradeseeker-web-v2/tradeseeker-web-v2 && npm ci
	@echo "✅ All dependencies installed!"

# Environment-specific deployments
deploy-dev: all
deploy-staging:
	@cd tradeseeker-api-v2 && $(MAKE) deploy-staging
	@cd tradeseeker-batch-v2 && $(MAKE) deploy-all
	@cd tradeseeker-web-v2/tradeseeker-web-v2 && $(MAKE) all

deploy-prod:
	@cd tradeseeker-api-v2 && $(MAKE) deploy-prod
	@cd tradeseeker-batch-v2 && $(MAKE) deploy-all
	@cd tradeseeker-web-v2/tradeseeker-web-v2 && $(MAKE) all