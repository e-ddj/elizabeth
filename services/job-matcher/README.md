# Job Matcher Microservice

An AI-powered microservice that matches job openings with user profiles based on skills, experience, location preferences, and other relevant factors.

## Overview

This microservice receives a job ID, fetches the job details and all user profiles from Supabase, performs intelligent matching using both rule-based algorithms and OpenAI, and returns a ranked list of suitable candidates.

## Features

- **Multi-factor Matching**: Evaluates candidates based on skills, experience, location, and salary expectations
- **AI-Enhanced Scoring**: Uses OpenAI to provide nuanced matching beyond simple keyword matching
- **Configurable Thresholds**: Adjustable matching criteria for different use cases
- **Supabase Integration**: Seamless data fetching and optional result storage
- **RESTful API**: Simple POST endpoint for easy integration

## Architecture

```
micro-service-job-matcher/
├── api/                    # REST endpoints
│   └── job_matcher/       # Matching endpoint
├── core/                   # Business logic
│   └── job_matcher/       # Matching algorithms
├── models/                 # AI integrations
│   └── job_matcher/       # OpenAI matching model
├── utils/                  # Shared utilities
│   ├── supabase/          # Database client
│   └── openai/            # AI client
└── config/                 # Configuration
```

## API Endpoints

### Match Job to Users

**POST** `/api/job-matcher/match`

Finds all users that match a specific job's requirements.

Request:
```json
{
  "job_id": "uuid-string",
  "overwrite_existing_matches": false  // optional
}
```

Response (202 Accepted):
```json
{
  "status": "accepted",
  "job_id": "uuid-string",
  "message": "Job matching process started successfully"
}
```

### Match User to Jobs

**POST** `/api/job-matcher/match-user`

Finds all jobs that match a specific user's medical specialties and qualifications.

Request:
```json
{
  "user_id": "uuid-string",
  "overwrite_existing_matches": false  // optional
}
```

Response (202 Accepted):
```json
{
  "status": "accepted",
  "user_id": "uuid-string",
  "message": "User matching process started successfully"
}
```

**Status Updates:**
- When the process starts, the user's `matching_status` in `user_profile` table is set to `"processing"`
- When the process completes (successfully or with errors), the `matching_status` is set to `"finished"`

Both endpoints run asynchronously and store results in the `match` table in Supabase.

## Setup

### Prerequisites

- Python 3.12+
- Pipenv
- Docker (optional)
- Supabase account with configured tables
- OpenAI API key

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_ORG_ID=your_openai_org_id
OPENAI_PROJECT_ID=your_openai_project_id
OPENAI_MATCHER_MODEL=gpt-4o-mini

# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_PRIVATE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# Application Configuration
PORT=5000
LOG_LEVEL=INFO
DEBUG=false

# Matching Configuration
MIN_SKILL_MATCH_RATIO=0.3
EXPERIENCE_TOLERANCE_YEARS=2
MIN_SCORE_THRESHOLD=0.5
MAX_RESULTS=10
```

### Installation

```bash
# Install dependencies
pipenv install --dev

# Activate virtual environment
pipenv shell
```

### Running Locally

```bash
# Run the Flask API
make run-api
# or
python api/index.py
```

The service will be available at `http://localhost:5004`

### Running with Docker

```bash
# Build and start container
make docker-up

# View logs
make docker-logs

# Stop container
make docker-down
```

## Database Schema

### Required Tables

1. **jobs** table:
   - id (uuid)
   - title (text)
   - description (text)
   - requirements (jsonb array)
   - skills (jsonb array)
   - experience_years (integer)
   - location (text)
   - salary_range (jsonb)
   - company (text)
   - department (text)
   - job_type (text)

2. **user_profiles** table:
   - id (uuid)
   - name (text)
   - email (text)
   - skills (jsonb array)
   - experience (jsonb array)
   - education (jsonb array)
   - total_experience_years (float)
   - current_location (text)
   - desired_locations (jsonb array)
   - desired_salary (float)
   - job_preferences (jsonb)
   - active (boolean)

3. **job_matches** table (optional):
   - id (uuid)
   - job_id (uuid)
   - user_id (uuid)
   - match_score (float)
   - match_reasons (jsonb array)
   - created_at (timestamp)

## Matching Algorithm

The matching process combines multiple factors:

1. **Skill Matching** (50% weight)
   - Direct skill matches between job requirements and user skills
   - Minimum threshold configurable via `MIN_SKILL_MATCH_RATIO`

2. **Experience Matching** (20% weight)
   - Compares required experience with user's total experience
   - Allows tolerance (default: ±2 years)

3. **Location Matching** (15% weight)
   - Matches job location with user's current/desired locations
   - Remote jobs match all users

4. **Salary Matching** (15% weight)
   - Ensures user expectations align with job salary range
   - 10% flexibility buffer applied

5. **AI Enhancement** (30% of final score)
   - OpenAI analyzes nuanced factors
   - Considers career progression, transferable skills, and cultural fit

## Testing

```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Run specific test
pipenv run pytest tests/test_matching.py::test_match_skills
```

## Development

### Code Quality

```bash
# Format code
make format

# Run linting
make lint

# Fix linting issues
make lint-fix
```

### Testing the API

```bash
# Test with curl
curl -X POST http://localhost:5004/api/job-matcher/match \
  -H "Content-Type: application/json" \
  -d '{"job_id": "your-job-id"}'

# Or use the make command
make run-match JOB_ID=your-job-id
```

## Deployment

The service is containerized and can be deployed to any Docker-compatible platform:

- AWS ECS/Fargate
- Google Cloud Run
- Azure Container Instances
- Kubernetes
- Docker Swarm

Ensure all environment variables are properly configured in your deployment environment.

## Monitoring

The service uses structured logging with configurable levels. In production, logs are output as JSON for easy parsing by log aggregation systems.

Key metrics to monitor:
- Response times for match requests
- Number of matches per job
- AI API usage and costs
- Error rates and types

## Future Enhancements

- Batch processing for multiple jobs
- Webhook notifications for new matches
- Machine learning model for improved scoring
- Candidate preference matching (two-way matching)
- Real-time matching with WebSocket support
- Caching layer for improved performance