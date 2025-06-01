.PHONY: help setup copy-services dev prod stop clean logs test health scale

# Default target
.DEFAULT_GOAL := help

# Colors for output
YELLOW := \033[1;33m
GREEN := \033[1;32m
RED := \033[1;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "${GREEN}AWS Microservices Management${NC}"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "${YELLOW}Targets:${NC}"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  ${GREEN}%-15s${NC} %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Initial setup - copy services and create env file
	@echo "${YELLOW}Setting up AWS Microservices...${NC}"
	@$(MAKE) copy-services
	@$(MAKE) create-env
	@echo "${GREEN}Setup complete!${NC}"

copy-services: ## Copy microservices from original locations
	@echo "${YELLOW}Copying microservices...${NC}"
	@mkdir -p services
	@cp -R ../micro-service-job-enricher services/job-enricher
	@cp -R ../micro-service-job-extractor services/job-extractor
	@cp -R ../micro-service-job-matcher services/job-matcher
	@cp -R ../micro-service-resume-parser services/resume-parser
	@echo "${GREEN}Services copied successfully${NC}"

create-env: ## Create .env file from example
	@if [ ! -f .env ]; then \
		echo "${YELLOW}Creating .env file...${NC}"; \
		cp .env.example .env; \
		echo "${GREEN}.env file created. Please update with your values.${NC}"; \
	else \
		echo "${YELLOW}.env file already exists${NC}"; \
	fi

dev: ## Start all services in development mode
	@echo "${GREEN}Starting services in development mode...${NC}"
	docker-compose up --build

dev-detached: ## Start all services in background
	@echo "${GREEN}Starting services in background...${NC}"
	docker-compose up -d --build

prod: ## Start all services in production mode
	@echo "${GREEN}Starting services in production mode...${NC}"
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

stop: ## Stop all services
	@echo "${YELLOW}Stopping all services...${NC}"
	docker-compose down

clean: ## Stop services and remove volumes
	@echo "${RED}Stopping services and removing volumes...${NC}"
	docker-compose down -v

logs: ## Show logs for all services
	docker-compose logs -f

logs-service: ## Show logs for specific service (e.g., make logs-service SERVICE=job-matcher)
	@if [ -z "$(SERVICE)" ]; then \
		echo "${RED}Error: SERVICE is required${NC}"; \
		echo "Usage: make logs-service SERVICE=<service-name>"; \
		exit 1; \
	fi
	docker-compose logs -f $(SERVICE)

ps: ## Show status of all services
	@docker-compose ps

health: ## Check health of all services
	@echo "${YELLOW}Checking service health...${NC}"
	@curl -s http://localhost:8080/health || echo "${RED}Nginx not responding${NC}"
	@echo ""
	@curl -s http://localhost:8080/api/job-enricher/health || echo "${RED}Job Enricher not responding${NC}"
	@echo ""
	@curl -s http://localhost:8080/api/job-extractor/health || echo "${RED}Job Extractor not responding${NC}"
	@echo ""
	@curl -s http://localhost:8080/api/job-matcher/health || echo "${RED}Job Matcher not responding${NC}"
	@echo ""
	@curl -s http://localhost:8080/api/hcp/health || echo "${RED}Resume Parser not responding${NC}"

scale: ## Scale a service (e.g., make scale SERVICE=job-matcher COUNT=3)
	@if [ -z "$(SERVICE)" ] || [ -z "$(COUNT)" ]; then \
		echo "${RED}Error: SERVICE and COUNT are required${NC}"; \
		echo "Usage: make scale SERVICE=<service-name> COUNT=<number>"; \
		exit 1; \
	fi
	docker-compose up -d --scale $(SERVICE)=$(COUNT)

restart: ## Restart a specific service
	@if [ -z "$(SERVICE)" ]; then \
		echo "${RED}Error: SERVICE is required${NC}"; \
		echo "Usage: make restart SERVICE=<service-name>"; \
		exit 1; \
	fi
	docker-compose restart $(SERVICE)

exec: ## Execute command in service (e.g., make exec SERVICE=job-matcher CMD=bash)
	@if [ -z "$(SERVICE)" ] || [ -z "$(CMD)" ]; then \
		echo "${RED}Error: SERVICE and CMD are required${NC}"; \
		echo "Usage: make exec SERVICE=<service-name> CMD=<command>"; \
		exit 1; \
	fi
	docker-compose exec $(SERVICE) $(CMD)

build: ## Build all Docker images
	@echo "${YELLOW}Building Docker images...${NC}"
	docker-compose build

build-service: ## Build specific service image
	@if [ -z "$(SERVICE)" ]; then \
		echo "${RED}Error: SERVICE is required${NC}"; \
		echo "Usage: make build-service SERVICE=<service-name>"; \
		exit 1; \
	fi
	docker-compose build $(SERVICE)

redis-cli: ## Connect to Redis CLI
	docker-compose exec redis redis-cli

grafana: ## Open Grafana dashboard
	@echo "${GREEN}Opening Grafana at http://localhost:3000${NC}"
	@echo "Default credentials: admin/admin"
	@open http://localhost:3000 || xdg-open http://localhost:3000

prometheus: ## Open Prometheus dashboard
	@echo "${GREEN}Opening Prometheus at http://localhost:9090${NC}"
	@open http://localhost:9090 || xdg-open http://localhost:9090

test-endpoints: ## Test all API endpoints
	@echo "${YELLOW}Testing all endpoints...${NC}"
	@echo "\n${GREEN}Job Enricher:${NC}"
	curl -X GET http://localhost:8080/api/job-enricher/health
	@echo "\n\n${GREEN}Job Extractor:${NC}"
	curl -X GET http://localhost:8080/api/job-extractor/health
	@echo "\n\n${GREEN}Job Matcher:${NC}"
	curl -X GET http://localhost:8080/api/job-matcher/health
	@echo "\n\n${GREEN}Resume Parser:${NC}"
	curl -X GET http://localhost:8080/api/hcp/health

monitor: ## Show real-time resource usage
	docker stats

update-shared: ## Update shared code in all services
	@echo "${YELLOW}Updating shared code...${NC}"
	@for service in job-enricher job-extractor job-matcher resume-parser; do \
		echo "Updating $$service..."; \
		docker-compose exec $$service sh -c "cp -r /app/shared/* /app/" || true; \
	done
	@echo "${GREEN}Shared code updated${NC}"