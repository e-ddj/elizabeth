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

.PHONY: run-api