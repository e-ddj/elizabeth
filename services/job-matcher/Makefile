.PHONY: help install run-api docker-build docker-up docker-down test lint format clean

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies using pipenv
	pipenv install --dev

run-api: ## Run the Flask API locally
	pipenv run python api/index.py

docker-build: ## Build Docker container
	docker-compose build

docker-up: ## Start Docker container
	docker-compose up -d

docker-down: ## Stop Docker container
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

test: ## Run tests with pytest
	pipenv run pytest tests/ -v

test-coverage: ## Run tests with coverage report
	pipenv run pytest tests/ --cov=. --cov-report=html

lint: ## Run linting with ruff
	pipenv run ruff check .

format: ## Format code with ruff
	pipenv run ruff format .

lint-fix: ## Fix linting issues
	pipenv run ruff check . --fix

clean: ## Clean up cache and temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".DS_Store" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage

generate-requirements: ## Generate requirements.txt from Pipfile
	pipenv requirements > requirements.txt

run-match: ## Run job matching for a specific job ID
	@echo "Usage: make run-match JOB_ID=<job_id>"
	@if [ -z "$(JOB_ID)" ]; then \
		echo "Error: JOB_ID is required"; \
		exit 1; \
	fi
	curl -X POST http://localhost:5004/api/job-matcher/match \
		-H "Content-Type: application/json" \
		-d '{"job_id": "$(JOB_ID)"}'