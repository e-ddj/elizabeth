# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is an AWS-optimized microservices platform for healthcare job matching. It consists of four Python microservices orchestrated with Docker Compose locally and deployable to AWS ECS/Fargate.

## Architecture

The platform uses a microservices architecture with:
- **Nginx reverse proxy** (port 8080) routing to all services
- **Redis** for caching and session storage
- **Four core services**:
  - Job Enricher (port 5001): Enhances job postings with AI
  - Job Extractor (port 5002): Extracts job data from URLs
  - Job Matcher (port 5003): Matches jobs to candidates
  - Resume Parser (port 5004): Parses resumes to structured data

All services communicate through REST APIs and share common utilities via the `/shared` directory.

## Essential Commands

### Development
```bash
# Initial setup
make setup                    # Copies services and creates .env file
make dev                      # Start all services with hot reload
make dev-detached            # Start in background
make logs                    # View all logs
make logs-service SERVICE=job-matcher  # View specific service logs
make health                  # Check health of all services
make stop                    # Stop all services
make clean                   # Stop and remove volumes
```

### Testing
```bash
# Run integration tests
./tests/test_integration.py

# Test individual services (from service directory)
cd services/job-enricher && pytest .
cd services/job-matcher && make test
```

### Code Quality
```bash
# Python formatting and linting (in each service)
ruff format .               # Format code
ruff check .               # Lint code
```

### Production Deployment
```bash
# Build production images
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Deploy to AWS ECS (assumes infrastructure exists)
aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_URI
docker-compose push
```

## Service Communication Pattern

Services are accessed through the Nginx proxy:
- Job Enricher: `http://localhost:8080/api/job-enricher/*`
- Job Extractor: `http://localhost:8080/api/job-extractor/*`
- Job Matcher: `http://localhost:8080/api/job-matcher/*`
- Resume Parser: `http://localhost:8080/api/hcp/*`

Each service has a `/health` endpoint for monitoring.

## Shared Components

The `/shared` directory contains:
- `config/gunicorn_config.py`: Unified Gunicorn configuration for all services
- `utils/circuit_breaker.py`: Fault tolerance utility
- `utils/health_check.py`: Health check implementation

Services mount this directory as `/app/shared` in their containers.

## Environment Configuration

Required environment variables in `.env`:
```
OPENAI_API_KEY=your_key
SUPABASE_URL=your_url
SUPABASE_PRIVATE_SERVICE_ROLE_KEY=your_key
WEB_CONCURRENCY=4
WORKER_CLASS=sync
REDIS_HOST=redis
```

## AWS Deployment Architecture

The platform is designed for AWS ECS with:
- Services deployed as Fargate tasks
- Application Load Balancer for routing
- ElastiCache for Redis
- ECR for container registry
- CloudWatch for logging/monitoring
- Secrets Manager for sensitive config

Infrastructure configuration is stored in:
- `infrastructure-config.env`: VPC and network IDs
- `deployment-config.env`: AWS account and region info
- `vpc-stack.yaml`: CloudFormation template for VPC

## Key Implementation Details

1. **Gunicorn Configuration**: All services use a shared Gunicorn config with configurable workers, timeouts, and health monitoring hooks.

2. **Service Isolation**: Each service has its own Dockerfile, requirements.txt, and can be developed/tested independently.

3. **Circuit Breakers**: Services implement circuit breakers for fault tolerance when calling external APIs.

4. **Async Job Processing**: Job matching and user matching run asynchronously, updating status in the database.

5. **Health Checks**: Docker and ECS health checks ensure service availability with proper retry logic.

## Current Deployment Status

According to the README, the platform was deployed to AWS with some services experiencing startup issues. The job-enricher service was running successfully while others needed environment variable configuration. Check CloudWatch logs for debugging deployment issues.