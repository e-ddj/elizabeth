##############################################################
# DOCKER PLATFORM CONFIGURATION
# IMPORTANT: Always use linux/amd64 for AWS ECS deployment
##############################################################
DOCKER_PLATFORM := linux/amd64
export DOCKER_DEFAULT_PLATFORM := $(DOCKER_PLATFORM)

##############################################################
# PIP & PIPENV
##############################################################
install-deps:
	pip install -r requirements.txt

purge-deps-cache:
	pip cache purge

generate-requirements-txt:
	pipenv requirements > requirements.txt


##############################################################
# Formatters & Linters
##############################################################
format:
	ruff format .

lint:
	ruff check .

lint-fix:
	ruff check . --fix

run-pre-commit:
	pre-commit run --all-files

##############################################################
# SETUP
##############################################################

ROOT_DIR = $(CURDIR)

# Run Flask API
run-api: 
	python $(ROOT_DIR)/api/index.py

# Run model test
run-model-test:
	PYTHONPATH=$(ROOT_DIR) python models/job_extractor/model.py url=https://example.com/job

##############################################################
# DOCKER COMMANDS (with platform configuration)
##############################################################

# Build Docker image for deployment (linux/amd64)
docker-build:
	docker build --platform $(DOCKER_PLATFORM) -t job-extractor .

# Build and run locally (with platform warning on ARM Macs)
docker-run: docker-build
	docker run --platform $(DOCKER_PLATFORM) -d \
		--name job-extractor-local \
		-p 5001:5001 \
		-e OPENAI_API_KEY="$${OPENAI_API_KEY}" \
		-e SUPABASE_URL="$${SUPABASE_URL}" \
		-e SUPABASE_PRIVATE_SERVICE_ROLE_KEY="$${SUPABASE_PRIVATE_SERVICE_ROLE_KEY}" \
		job-extractor

# Stop local Docker container
docker-stop:
	docker stop job-extractor-local || true
	docker rm job-extractor-local || true

# View Docker logs
docker-logs:
	docker logs -f job-extractor-local

.PHONY: run-api run-model-test docker-build docker-run docker-stop docker-logs