# Makefile for TradeSeeker Batch Processing System

.PHONY: help package deploy deploy-downloader deploy-all clean

# Default target
help:
	@echo "Available targets:"
	@echo "  deploy-downloader  - Package and deploy downloader lambda"
	@echo "  deploy-all         - Package and deploy all lambdas"
	@echo "  package            - Package all lambda functions"
	@echo "  deploy             - Deploy infrastructure with terraform"
	@echo "  clean              - Clean build artifacts"

# Package and deploy downloader lambda (most common use case)
deploy-downloader:
	@echo "Packaging downloader lambda..."
	./scripts/package-downloader.sh
	@echo "Deploying with terraform..."
	cd terraform && terraform apply -auto-approve

# Package and deploy all lambdas
deploy-all:
	@echo "Packaging all lambda functions..."
	./scripts/package-task-generator.sh
	./scripts/package-downloader.sh
	./scripts/package-dlq-replay.sh
	@echo "Deploying with terraform..."
	cd terraform && terraform apply -auto-approve

# Package all lambda functions
package:
	@echo "Packaging all lambda functions..."
	./scripts/package-task-generator.sh
	./scripts/package-downloader.sh
	./scripts/package-dlq-replay.sh

# Deploy infrastructure only (assumes packages are already built)
deploy:
	@echo "Deploying with terraform..."
	cd terraform && terraform apply -auto-approve

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -f lambdas/task-generator/task-generator.zip
	rm -f lambdas/downloader/downloader.zip
	rm -f lambdas/dlq-replay/dlq-replay.zip
	rm -rf lambdas/*/package/
	@echo "Clean complete"

# Quick deploy (alias for deploy-downloader)
quick: deploy-downloader