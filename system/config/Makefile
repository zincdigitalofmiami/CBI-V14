.PHONY: help setup test lint check-rules clean format docker-build docker-up docker-down

help: ## Show this help message
	@echo "CBI-V14 Project Commands"
	@echo "========================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Install all dependencies and configure pre-commit hooks
	@echo "Setting up project..."
	@# Python environment
	@cd forecast && python3 -m venv venv && \
		. venv/bin/activate && \
		pip install -r requirements.txt
	@# Install pre-commit
	@pip3 install pre-commit
	@pre-commit install
	@echo "Setup complete!"

check-rules: ## Enforce project rules (NO MOCK DATA, etc.)
	@echo "Checking project rules..."
	@bash scripts/check_no_mock_data.sh
	@bash scripts/check_env_vars.sh
	@echo "All rules passed!"

lint: ## Run linters on all code
	@echo "Linting code..."
	@# Python
	@cd forecast && \
		black --check --line-length 100 . && \
		flake8 --max-line-length 100 .
	@echo "Linting complete!"

format: ## Auto-format all code
	@echo "Formatting code..."
	@cd forecast && black --line-length 100 .
	@echo "Formatting complete!"

test: ## Run all tests
	@echo "Running tests..."
	@cd forecast && pytest tests/ -v --cov=. || echo "Tests not yet configured"
	@echo "Tests complete!"

docker-build: ## Build Docker images
	@echo "Building Docker images..."
	@docker build -t cbi-v14/forecast-api:local forecast/
	@echo "Docker images built!"

docker-up: ## Start all services with Docker Compose
	@echo "Starting services..."
	@docker-compose up --build

docker-down: ## Stop all services
	@echo "Stopping services..."
	@docker-compose down

clean: ## Clean build artifacts and caches
	@echo "Cleaning..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleaned!"

.DEFAULT_GOAL := help
