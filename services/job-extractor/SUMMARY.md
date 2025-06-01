# Job Extractor Microservice Summary

## Overview

This microservice is designed to extract structured data from job postings using AI. It provides a simple REST API that accepts a job posting URL, fetches the content, and processes it using OpenAI's GPT model to extract detailed information in a consistent JSON format.

## How It Works

1. **Request Processing**:
   - The frontend sends a POST request to `/api/job-extractor/extract` with a job URL
   - The API validates the request and extracts the URL

2. **HTML Fetching**:
   - The service fetches the HTML content from the provided URL
   - BeautifulSoup is used to clean and preprocess the HTML

3. **AI Processing**:
   - The cleaned HTML is sent to OpenAI's API
   - A specialized prompt instructs the model to extract job details in a structured format
   - The model returns a JSON object with standardized fields

4. **Response**:
   - The structured data is returned to the frontend
   - Includes comprehensive job details like title, salary, responsibilities, etc.

## Key Components

### API Layer
- `api/job_extractor/extract.py`: Handles HTTP requests and responses
- Provides the main endpoint for job data extraction

### Core Layer
- `core/job_extractor/extract_job_data.py`: Contains the business logic
- Handles URL fetching, HTML cleaning, and orchestrates the AI processing

### Model Layer
- `models/job_extractor/model.py`: Manages AI model interactions
- Contains the prompt and handles OpenAI API calls

## Data Structure

The service extracts and returns a JSON object with the following structure:

```json
{
  "id": number,
  "title": string,
  "summary": string,
  "department": string,
  "location": string,
  "jobType": string,
  "status": string,
  "postedAt": string,
  "salaryRange": {
    "min": number,
    "max": number,
    "currency": string,
    "display": string
  },
  "responsibilities": string[],
  "qualifications": string[],
  "perks": string[],
  "benefitsData": number[],
  "specialty": string,
  "organization": string,
  "country": string,
  "isRemote": boolean,
  "visaSponsorship": boolean,
  "fullTime": boolean,
  "partTime": boolean,
  "nightShift": boolean
}
```

## Deployment

The service is containerized using Docker and can be deployed independently:

```bash
docker-compose up -d
```

It runs on port 5001 by default (configurable in docker-compose.yml).

## Integration with Frontend

The frontend can integrate with this service by making a simple HTTP POST request:

```javascript
const extractJobData = async (jobUrl) => {
  const response = await fetch('/api/job-extractor/extract', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ job_url: jobUrl }),
  });
  
  if (!response.ok) {
    throw new Error('Failed to extract job data');
  }
  
  return await response.json();
};
```

The service handles all the complex processing, allowing the frontend to focus on displaying the structured data to users.