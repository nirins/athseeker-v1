# TradeSeekerWeb v2 - Makefile
# Automates build and deployment process

# Variables
BUCKET_NAME = ts-dev-web-v2-app
DISTRIBUTION_ID = E379OF6HGDUSPS
BUILD_DIR = dist/tradeseeker-web-v2/browser

# Default target
.PHONY: help
help:
	@echo "TradeSeekerWeb v2 - Available commands:"
	@echo "  make build     - Build the Angular application"
	@echo "  make deploy    - Deploy to S3 and invalidate CloudFront"
	@echo "  make all       - Build and deploy (recommended)"
	@echo "  make clean     - Clean build directory"
	@echo "  make status    - Show deployment status"

# Build the application
.PHONY: build
build:
	@echo "🔨 Building TradeSeekerWeb v2..."
	npm run build
	@echo "✅ Build complete!"

# Deploy to S3 and CloudFront
.PHONY: deploy
deploy:
	@echo "🚀 Deploying to AWS..."
	./scripts/deploy.sh $(BUCKET_NAME) $(DISTRIBUTION_ID)
	@echo "✅ Deployment complete!"

# Build and deploy in one command (no tests)
.PHONY: all
all: build deploy
	@echo "🎉 Build and deployment complete!"
	@echo "🌐 Your application is available at:"
	@echo "   • https://athseeker.com"
	@echo "   • https://www.athseeker.com"
	@echo "   • https://d310shk0w5mump.cloudfront.net"

# Clean build directory
.PHONY: clean
clean:
	@echo "🧹 Cleaning build directory..."
	rm -rf $(BUILD_DIR)
	rm -rf dist/
	@echo "✅ Clean complete!"

# Show deployment status
.PHONY: status
status:
	@echo "📊 Deployment Status:"
	@echo "  S3 Bucket: $(BUCKET_NAME)"
	@echo "  CloudFront Distribution: $(DISTRIBUTION_ID)"
	@echo "  Custom Domain: https://athseeker.com"
	@echo "  CloudFront URL: https://d310shk0w5mump.cloudfront.net"
	@echo "  Build Directory: $(BUILD_DIR)"
	@if [ -d "$(BUILD_DIR)" ]; then \
		echo "  Build Status: ✅ Built"; \
		echo "  Build Size: $$(du -sh $(BUILD_DIR) | cut -f1)"; \
	else \
		echo "  Build Status: ❌ Not built"; \
	fi

# Install dependencies
.PHONY: install
install:
	@echo "📦 Installing dependencies..."
	npm ci
	@echo "✅ Dependencies installed!"

# Run tests
.PHONY: test
test:
	@echo "🧪 Running tests..."
	npm test
	@echo "✅ Tests complete!"

# Development server (for local testing)
.PHONY: serve
serve:
	@echo "🔧 Starting development server..."
	@echo "⚠️  Note: This will start a long-running process"
	@echo "   Press Ctrl+C to stop the server"
	npm start

# Invalidate CloudFront cache only
.PHONY: invalidate
invalidate:
	@echo "🔄 Invalidating CloudFront cache..."
	./scripts/invalidate-cache.sh $(DISTRIBUTION_ID)
	@echo "✅ Cache invalidation complete!"

# Quick deploy (no build, just upload existing files)
.PHONY: quick-deploy
quick-deploy:
	@if [ ! -d "$(BUILD_DIR)" ]; then \
		echo "❌ No build found. Run 'make build' first."; \
		exit 1; \
	fi
	@echo "⚡ Quick deploy (using existing build)..."
	./scripts/deploy.sh $(BUCKET_NAME) $(DISTRIBUTION_ID)
	@echo "✅ Quick deployment complete!"