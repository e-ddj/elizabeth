
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

# Run model
run-user-profile-model:
	PYTHONPATH=$(ROOT_DIR) python models/user_profile/model.py base64_file=blablabla


.PHONY: run-user-profile-core
FILE_PATH ?= blablabla
# use it like make run-user-profile-core FILE_PATH=custom/path/to/file
run-user-profile-core:
	@echo "Running user profile core with FILE_PATH=$(FILE_PATH)"
    PYTHONPATH=$(ROOT_DIR) python core/user_profile/extract_profile_from_resume.py file_path=$(FILE_PATH)

