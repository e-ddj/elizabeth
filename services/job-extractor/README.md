# Job Extractor Microservice

This microservice is responsible for extracting structured data from job postings using AI. It fetches the HTML content from a job posting URL and returns the data in a structured JSON format.

## Features

- Job posting extraction from URLs
- AI-powered extraction of job details using OpenAI's models
- Structured JSON output with comprehensive job information
- Simple REST API interface

## Architecture

The microservice follows a clean architecture pattern:

- **API Layer** (`/api/job_extractor`): REST endpoint for accessing the job extraction service
- **Core Layer** (`/core/job_extractor`): Business logic for job data extraction
- **Models Layer** (`/models/job_extractor`): AI models for text extraction and processing
- **Utils Layer** (`/utils`): Shared utilities

## Setup and Installation

```bash
# Setup Python environment (Python 3.12+ required)
# Install pipenv (recommended)
brew install pipenv

# Clone and setup
cd micro-service-job-extractor
cp .env.example .env  # Create .env and set up required values

# Install dependencies
pipenv install --dev

# Activate virtual environment
pipenv shell
```

## Environment Variables

Create a `.env` file with the following variables:

```
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_JOB_EXTRACTOR_MODEL=gpt-4o-mini  # Or another suitable model

# Logging
LOG_LEVEL=INFO
```

## API Endpoints

### Extract Job Data

```
POST /api/job-extractor/extract
```

Extracts structured data from a job posting URL.

**Request:**
```json
{
  "job_url": "https://example.com/job-posting"
}
```

**Response:**
```json
{
  "id": 12345,
  "title": "Senior Software Engineer",
  "summary": "Join our engineering team to build innovative healthcare solutions...",
  "department": "Engineering",
  "location": "Auckland, New Zealand",
  "jobType": "Full-time",
  "status": "Open",
  "postedAt": "2025-05-15",
  "salaryRange": {
    "min": 120000,
    "max": 150000,
    "currency": "NZD",
    "display": "$120,000 - $150,000 NZD per year"
  },
  "responsibilities": [
    "Design and implement new features",
    "Collaborate with cross-functional teams",
    "Participate in code reviews"
  ],
  "qualifications": [
    "5+ years of software engineering experience",
    "Experience with modern JavaScript frameworks",
    "Strong problem-solving skills"
  ],
  "perks": [
    "Flexible working hours",
    "Professional development budget",
    "Health insurance"
  ],
  "benefitsData": [1, 3, 5, 7],
  "specialty": "Full-stack development",
  "organization": "Green Cross Health",
  "country": "New Zealand",
  "isRemote": true,
  "visaSponsorship": false,
  "fullTime": true,
  "partTime": false,
  "nightShift": false
}
```

## Common Commands

```bash
# Run the Flask API
python api/index.py

# Format code
ruff format .

# Lint code
ruff check .

# Run tests
pytest .
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

## Dependencies

- Python 3.12+
- Flask for API endpoints
- OpenAI API for AI-powered text analysis
- BeautifulSoup for HTML parsing
- Requests for HTTP requests