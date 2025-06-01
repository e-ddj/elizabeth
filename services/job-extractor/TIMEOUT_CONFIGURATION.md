# Timeout Configuration Guide

## Overview

The job extractor service has been optimized to handle long-running job extraction processes. This document explains the timeout configurations and how to resolve frontend timeout issues.

## Current Timeout Settings

### Backend Timeouts

| Component | Default Timeout | Environment Variable | Description |
|-----------|----------------|---------------------|-------------|
| HTTP Requests | 30 seconds | `HTTP_REQUEST_TIMEOUT` | Timeout for fetching job posting URLs |
| Selenium WebDriver | 30 seconds | `SELENIUM_PAGE_LOAD_TIMEOUT` | Timeout for browser page loading |
| OpenAI API | 60 seconds | `OPENAI_API_TIMEOUT` | Timeout for AI model processing |
| Gunicorn Worker | 120 seconds | `GUNICORN_TIMEOUT` | Overall request timeout |

### Content Processing Limits

- **Max Content Length**: 50,000 characters (configurable via `MAX_CONTENT_LENGTH`)
- Content is automatically truncated to improve processing speed

## Frontend Timeout Issue Resolution

### Problem
The frontend times out after 30 seconds, but job extraction can take 20-60 seconds depending on:
- Job posting complexity
- Website response time
- AI model processing time

### Solution Options

#### Option 1: Increase Frontend Timeout (Recommended)
Update your frontend code to use a timeout of at least **150 seconds** (2.5 minutes):

```javascript
// Example for fetch API
const response = await fetch('/api/job-extractor/extract', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ job_url: url }),
  signal: AbortSignal.timeout(150000) // 150 seconds
});

// Example for axios
const response = await axios.post('/api/job-extractor/extract', 
  { job_url: url },
  { timeout: 150000 } // 150 seconds
);
```

#### Option 2: Implement Async Processing
For better UX, implement async processing:

1. Submit job for processing (returns immediately with job ID)
2. Poll for completion status
3. Retrieve results when ready

#### Option 3: Adjust Backend Timeouts
You can customize timeouts via environment variables:

```bash
# Reduce OpenAI timeout for faster failures
export OPENAI_API_TIMEOUT=30

# Reduce overall request timeout
export GUNICORN_TIMEOUT=90

# Reduce content size for faster processing
export MAX_CONTENT_LENGTH=30000
```

## Performance Optimizations Implemented

1. **Content Optimization**: Removes unnecessary HTML elements (scripts, styles, navigation)
2. **Content Truncation**: Limits content to 50KB for faster AI processing
3. **Gunicorn Configuration**: Uses production WSGI server with proper timeout handling
4. **OpenAI Timeout**: Prevents indefinite hanging on AI API calls

## Monitoring and Debugging

### Log Messages to Watch For
- `Content truncated to X characters for processing efficiency`
- `Successfully fetched HTML content from URL (length: X characters)`
- `Processed content length: X characters`

### Common Timeout Scenarios
1. **Website blocking**: Falls back to browser emulation (adds 10-20 seconds)
2. **Large content**: Automatic truncation reduces processing time
3. **AI model delays**: OpenAI API can occasionally be slow

## Environment Variables Reference

```bash
# HTTP and Browser Timeouts
HTTP_REQUEST_TIMEOUT=30
SELENIUM_PAGE_LOAD_TIMEOUT=30

# AI Processing
OPENAI_API_TIMEOUT=60.0
OPENAI_JOB_EXTRACTOR_MODEL=gpt-4o-mini

# Server Configuration
GUNICORN_TIMEOUT=120

# Content Processing
MAX_CONTENT_LENGTH=50000
```

## Recommended Frontend Implementation

```javascript
const extractJobData = async (jobUrl, timeoutMs = 150000) => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  
  try {
    const response = await fetch('/api/job-extractor/extract', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ job_url: jobUrl }),
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    clearTimeout(timeoutId);
    
    if (error.name === 'AbortError') {
      throw new Error(`Request timed out after ${timeoutMs / 1000} seconds`);
    }
    
    throw error;
  }
};
```

This configuration ensures reliable job extraction while providing appropriate error handling for timeout scenarios. 