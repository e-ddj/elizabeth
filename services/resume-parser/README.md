# Resume Parser Microservice

This microservice is responsible for parsing resumes (CVs) into structured data using AI. It extracts key information from resumes and returns it in a structured JSON format.

## Features

- Resume parsing from various file formats (PDF, DOCX, DOC, TXT)
- AI-powered extraction of profile information using OpenAI's models
- Profile photo extraction capabilities
- Structured data output in JSON format

## Architecture

The microservice follows a clean architecture pattern:

- **API Layer** (`/api/hcp`): REST endpoint for accessing the resume parsing service
- **Core Layer** (`/core/user_profile`): Business logic for resume parsing
- **Models Layer** (`/models/user_profile`): AI models for text extraction and processing
- **Utils Layer** (`/utils`): Shared utilities for file handling, serialization, etc.

## Setup and Installation

```bash
# Setup Python environment (Python 3.12+ required)
# Install pyenv (recommended)
brew install pyenv

# Install pipenv
brew install pipenv

# Clone and setup
cd micro-service-resume-parser
cp .env.example .env  # Create .env and set up required values

# Install dependencies
pipenv install --dev

# Activate virtual environment
pipenv shell

# Optional: Install pre-commit hooks
pre-commit install
```

## Environment Variables

Create a `.env` file with the following variables:

```
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_ORG_ID=your_openai_org_id
OPENAI_PROJECT_ID=your_openai_project_id
OPENAI_PARSER_MODEL=gpt-4o-mini  # Or another suitable model

# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_PRIVATE_SERVICE_ROLE_KEY=your_supabase_key

# Resume Processing Configuration
CV_PAGES_LIMIT=6  # Max pages to process per resume
CV_DPI=180  # DPI for PDF rendering
DEBUG_IMAGES=0  # Set to 1 to save debug images of extracted photos

# Logging
LOG_LEVEL=INFO
```

## API Endpoints

### Parse Resume

```
POST /api/hcp/user-profile
```

Parses a resume and extracts structured information.

**Request:**
```json
{
  "file_path": "path/to/your/file.pdf"
}
```

**Response:**
```json
{
  "profile": {
    "title": "Dr.",
    "first_name": "John",
    "last_name": "Doe",
    "position": "Radiologist",
    "street": "123 Medical Plaza",
    "city": "Singapore",
    "country": "Singapore",
    "phone": "+65123456789",
    "citizenships": ["Singapore"],
    "about_me": "Experienced radiologist with 10+ years in diagnostic imaging...",
    "photo_base64": "base64_encoded_image_data..."
  },
  "experiences": [
    {
      "job_title": "Senior Radiologist",
      "organization": "Singapore General Hospital",
      "city": "Singapore",
      "country": "Singapore",
      "start_date": "05/15/2018",
      "end_date": "present",
      "description": "Lead diagnostician for CT and MRI..."
    }
  ],
  "educations": [
    {
      "degree_name": "Doctor of Medicine",
      "degree_type": "MD",
      "description": "Specialization in Radiology",
      "start_date": "2008",
      "end_date": "2012",
      "school_name": "National University of Singapore",
      "city": "Singapore",
      "country": "Singapore"
    }
  ],
  "languages": ["English", "Mandarin", "Malay"],
  "certifications": [
    {
      "title": "Board Certification in Diagnostic Radiology",
      "issuing_organization": "American Board of Radiology",
      "city": "Tucson",
      "country": "United States",
      "issue_date": "06/10/2013"
    }
  ],
  "publications": [
    {
      "title": "Advanced MRI Techniques in Neuroimaging",
      "journal": "Journal of Radiology",
      "date": "2019"
    }
  ],
  "awards": [
    {
      "title": "Excellence in Clinical Practice",
      "awarding_organization": "Singapore Medical Association",
      "city": "Singapore",
      "country": "Singapore",
      "date": "2020",
      "description": "Awarded for outstanding contribution to patient care"
    }
  ],
  "scores": {
    "completion_score": 95,
    "data_strength_score": 90,
    "healthcare_confidence": 100,
    "messages": ["Profile looks good — you can proceed to the next step."]
  }
}
```

## Common Commands

```bash
# Run the Flask API
python api/index.py
# or
make run-api

# Run tests
pytest .

# Run tests with coverage
pytest --cov=.

# Format code
ruff format .
# or
make format

# Lint code
ruff check .
# or
make lint

# Run all pre-commit hooks
pre-commit run --all-files
# or
make run-pre-commit

# Run specific model
PYTHONPATH=$PWD python models/user_profile/model.py base64_file=<file>
# or
make run-user-profile-model
```

## Docker Usage

The microservice can be run in Docker:

```bash
# Build and start Docker container
docker-compose build
docker-compose up -d

# Check container status
docker-compose ps

# View logs
docker-compose logs -f
```

## AWS Deployment

This microservice is designed to be deployed as a container service on AWS. Recommended options include:

- AWS ECS (Elastic Container Service) for container orchestration
- AWS ECR (Elastic Container Registry) for storing Docker images
- AWS CloudWatch for logging and monitoring
- AWS Secrets Manager for storing sensitive environment variables

## Dependencies

- Python 3.12+
- Flask for API endpoints
- OpenAI API for AI-powered text analysis
- PyMuPDF (fitz) for PDF parsing 
- Supabase for storage and retrieval
- Document processing libs (pdf, docx, etc.)
- OpenCV for face detection in profile photos