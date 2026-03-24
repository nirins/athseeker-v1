# TradeSeekerV2 - Root Makefile
# Orchestrates all three components: API, Batch, and Web

.PHONY: help all api batch web ios deploy-all clean test status train train-migrate train-check train-install train-analyze train-apply model-list model-switch model-test model-config dynamodb x-poster

# Default target
help:
	@echo "🚀 TradeSeekerV2 - Monorepo Management"
	@echo ""
	@echo "Available targets:"
	@echo "  make all        - Build and deploy all components (API + Batch + Web)"
	@echo "  make api        - Build and deploy API only"
	@echo "  make batch      - Build and deploy Batch processing only"
	@echo "  make web        - Build and deploy Web frontend only"
	@echo "  make ios        - Build web and open iOS project in Xcode"
	@echo "  make x-poster   - Package and deploy X Poster Lambda"
	@echo "  make train      - Run beauty score model calibration workflow"
	@echo ""
	@echo "Training data management:"
	@echo "  make train-migrate - Migrate old training data to new grade system"
	@echo "  make train-check   - Check training data status"
	@echo ""
	@echo "Model management:"
	@echo "  make model-list    - List available beauty score models"
	@echo "  make model-switch MODEL=<name> - Switch active model"
	@echo "  make model-test [MODEL=<name>] - Test model with sample data"
	@echo "  make model-config  - Show model configuration"
	@echo ""
	@echo "ATH table management:"
	@echo "  make ath-info      - Show ATH table information"
	@echo "  make ath-clear     - Clear all ATH records (keep table structure)"
	@echo "  make ath-recreate  - Delete and recreate ATH table"
	@echo "  make dynamodb      - Delete and recreate ALL DynamoDB tables"
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

# iOS component
ios:
	@echo "🍎 Building iOS app..."
	@cd tradeseeker-web-v2/tradeseeker-web-v2 && ng build --configuration production
	@cd tradeseeker-web-v2/tradeseeker-web-v2 && npx cap sync ios
	@cd tradeseeker-web-v2/tradeseeker-web-v2 && npx cap open ios
	@echo "✅ iOS project opened in Xcode!"

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

# Beauty Score Model Training and Calibration
train-migrate:
	@echo "🔄 Migrating training data to new grade system..."
	@cd tradeseeker-batch-v2/scripts && python3 migrate_training_data.py

train-check:
	@echo "📊 Checking training data status..."
	@cd tradeseeker-batch-v2/scripts && python3 check_training_data.py

train-install:
	@echo "📦 Installing calibration dependencies..."
	@cd tradeseeker-batch-v2/scripts && pip3 install -r requirements-calibration.txt
	@echo "✅ Calibration dependencies installed"

train-analyze:
	@echo "🔬 Running calibration analysis..."
	@cd tradeseeker-batch-v2/scripts && python3 calibrate_beauty_model.py

train-apply:
	@echo "⚖️  Applying optimized weights..."
	@cd tradeseeker-batch-v2/scripts && python3 update_beauty_weights.py

# Model Management
model-list:
	@echo "📋 Listing beauty score models..."
	@cd tradeseeker-batch-v2/scripts && python3 manage_beauty_models.py list

model-switch:
	@echo "🔄 Switching beauty score model..."
	@if [ -z "$(MODEL)" ]; then \
		echo "❌ Usage: make model-switch MODEL=<model_name>"; \
		echo "   Available models: original, calibrated"; \
	else \
		cd tradeseeker-batch-v2/scripts && python3 manage_beauty_models.py switch $(MODEL); \
	fi

model-test:
	@echo "🧪 Testing beauty score model..."
	@if [ -z "$(MODEL)" ]; then \
		cd tradeseeker-batch-v2/scripts && python3 manage_beauty_models.py test; \
	else \
		cd tradeseeker-batch-v2/scripts && python3 manage_beauty_models.py test $(MODEL); \
	fi

model-config:
	@echo "⚙️  Showing model configuration..."
	@cd tradeseeker-batch-v2/scripts && python3 manage_beauty_models.py config

train: train-check train-install train-analyze train-apply
	@echo ""
	@echo "🎯 Training workflow completed!"
	@echo ""
	@echo "💡 Next steps:"
	@echo "   1. Review the calibration report: tradeseeker-batch-v2/scripts/beauty_model_calibration_report.json"
	@echo "   2. If weights were updated, deploy the changes: make batch"
	@echo "   3. Monitor beauty score performance with new model"
	@echo "   4. Review volatility filtering: tradeseeker-batch-v2/VOLATILITY_FILTERING.md"

# ATH Table Management (delegate to batch project)
ath-info:
	@echo "📋 Showing ATH table information..."
	@cd tradeseeker-batch-v2 && $(MAKE) ath-info

ath-clear:
	@echo "🧹 Clearing ATH table records..."
	@cd tradeseeker-batch-v2 && $(MAKE) ath-clear

ath-recreate:
	@echo "🔨 Recreating ATH table..."
	@cd tradeseeker-batch-v2 && $(MAKE) ath-recreate

# X Poster - package and deploy
x-poster:
	@echo "🐦 Packaging and deploying X Poster Lambda..."
	@cd tradeseeker-batch-v2 && $(MAKE) deploy-x-poster
	@echo "✅ X Poster deployed!"

# Recreate all DynamoDB tables
dynamodb:
	@echo "🗄️  Recreating all DynamoDB tables..."
	@cd tradeseeker-batch-v2 && python3 scripts/recreate_tables.py
	@echo "✅ DynamoDB tables recreated!"