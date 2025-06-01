# Job Enricher Microservice

This microservice is responsible for enriching job posting data to make it more appealing for candidates using AI. It takes raw job data and transforms it with engaging, marketing-optimized content.

## Features

- Job data enrichment with engaging, candidate-focused content
- Enhanced job titles, summaries, and responsibilities
- Addition of appealing perks and benefits
- AI-powered content generation using OpenAI's models
- Simple REST API interface

## Architecture

The microservice follows a clean architecture pattern:

- **API Layer** (`/api/job_enricher`): REST endpoint for accessing the job enrichment service
- **Core Layer** (`/core/job_enricher`): Business logic for job data enrichment
- **Models Layer** (`/models/job_enricher`): AI models for content enhancement and processing
- **Utils Layer** (`/utils`): Shared utilities

## Setup and Installation

```bash
# Setup Python environment (Python 3.12+ required)
# Install pipenv (recommended)
brew install pipenv

# Clone and setup
cd micro-service-job-enricher
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
OPENAI_JOB_ENRICHER_MODEL=gpt-4o-mini
OPENAI_JOB_ENRICHER_TEMPERATURE=0.7

# Logging
LOG_LEVEL=INFO

# Flask Configuration
FLASK_APP=api/index.py
FLASK_ENV=development
FLASK_DEBUG=1
```

## API Endpoints

### Enrich Job Data

```
POST /api/job-enricher/enrich
```

Enriches job data to make it more appealing for candidates.

**Request:**
```json
{
  "id": 50220,
  "title": "Registered Nurses - Medplus",
  "summary": "Permanent Full Time Registered Nurse roles; Join our committed, fun and supportive general practice team environment. Conveniently located.",
  "department": "Medplus",
  "location": "Auckland, New Zealand",
  "jobType": "Permanent Full Time",
  "status": "Open",
  "postedAt": "2025-05-13",
  "salaryRange": null,
  "responsibilities": [
    "Work at busy clinics at Hauraki Corner, Takapuna and Anne Street, Devonport.",
    "Join our committed, fun and supportive general practice team environment."
  ],
  "qualifications": [
    "Certified vaccinator",
    "Cannulation"
  ],
  "perks": [],
  "benefitsData": [],
  "specialty": "Healthcare & Medical",
  "organization": "Green Cross Health",
  "country": "NZ",
  "isRemote": false,
  "visaSponsorship": false,
  "fullTime": true,
  "partTime": false,
  "nightShift": true
}
```

**Response:**
```json
{
  "id": 50220,
  "title": "Senior Registered Nurses - Join Our Award-Winning Practice!",
  "summary": "Join our vibrant team at Medplus, where your skills will thrive in our supportive, collaborative environment. Build your career in our modern facilities while enjoying the stunning coastal lifestyle of Auckland's North Shore. Our convenient Takapuna and Devonport locations offer the perfect work-life balance.",
  "department": "Medplus",
  "location": "Auckland, New Zealand",
  "jobType": "Permanent Full Time",
  "status": "Open",
  "postedAt": "2025-05-13",
  "salaryRange": {
    "min": 60000,
    "max": 80000,
    "currency": "NZD",
    "display": "NZD 60,000–80,000"
  },
  "responsibilities": [
    "Elevate patient care at our premium North Shore clinics, where you'll work alongside top healthcare professionals.",
    "Contribute to our positive team culture while growing your clinical leadership skills in a supportive environment."
  ],
  "qualifications": [
    "Apply your vaccination expertise to protect our community's health and well-being.",
    "Utilize your cannulation skills in a practice that values and rewards clinical excellence."
  ],
  "perks": [
    "Professional development allowance",
    "Flexible scheduling options",
    "Healthcare staff discounts",
    "Wellness program",
    "Career advancement pathways"
  ],
  "benefitsData": [1, 4, 7, 10, 12],
  "specialty": "Healthcare & Medical",
  "organization": "Green Cross Health",
  "country": "NZ",
  "isRemote": false,
  "visaSponsorship": false,
  "fullTime": true,
  "partTime": false,
  "nightShift": true,
  "highlightedBenefits": [
    "Comprehensive professional development program with paid study leave",
    "Supportive team culture with regular social events and wellness initiatives",
    "Prime locations in Auckland's desirable North Shore neighborhoods"
  ]
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
- OpenAI API for AI-powered content enhancement
- Structlog for structured logging