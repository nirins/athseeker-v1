.PHONY: all deploy clean test help

# Default target
all:
	@chmod +x deploy.sh
	@./deploy.sh

# Deploy to default environment
deploy:
	@chmod +x deploy.sh
	@./deploy.sh

# Deploy to specific environment
deploy-dev:
	@chmod +x deploy.sh
	@./deploy.sh dev

deploy-staging:
	@chmod +x deploy.sh
	@./deploy.sh staging

deploy-prod:
	@chmod +x deploy.sh
	@./deploy.sh prod

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf build/
	@rm -f terraform/tfplan
	@rm -f terraform/.terraform.lock.hcl
	@rm -rf terraform/.terraform/
	@echo "✓ Clean complete"

# Run tests
test:
	@echo "Running tests..."
	@python3 -m pytest tests/ -v

# Show help
help:
	@echo "Available targets:"
	@echo "  all           - Deploy to dev environment (default)"
	@echo "  deploy        - Deploy to dev environment"
	@echo "  deploy-dev    - Deploy to dev environment"
	@echo "  deploy-staging- Deploy to staging environment"
	@echo "  deploy-prod   - Deploy to prod environment"
	@echo "  test          - Run pytest test suite"
	@echo "  clean         - Clean build artifacts"
	@echo "  help          - Show this help message"