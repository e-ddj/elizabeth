"""
AI model for extracting structured job data from HTML/plaintext job postings.
"""

import json
import os
import logging
from typing import Dict, Any, Optional

from openai import OpenAI
from config.log_config import get_logger
from config.timeout_config import OPENAI_API_TIMEOUT

logger = get_logger()

# Initialize OpenAI client
def create_openai_client() -> OpenAI:
    """Create and return an OpenAI client using API key from environment variables."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    # Set timeout for the OpenAI client from configuration
    return OpenAI(api_key=api_key, timeout=OPENAI_API_TIMEOUT)

# System prompt for job data extraction
SYSTEM_PROMPT = """
You are a data-extraction assistant. I will give you the HTML (or plaintext) of a job posting. 
Please parse it and return a single JSON object matching exactly this structure:

{
  "id": number,
  "title": string,
  "summary": string,
  "department": string,
  "location": string,
  "jobType": string,
  "status": string,
  "postedAt": string,        // YYYY-MM-DD
  "salaryRange": {
    "min": number,
    "max": number,
    "currency": string,
    "display": string
  } | null,                // null if not listed
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

Follow these rules:
1. If the salary range is not provided, use null
2. For dates, use the YYYY-MM-DD format
3. For boolean fields, determine their value based on the job description
4. If any field is not explicitly mentioned, make a reasonable inference based on the context
5. Return only the JSON object, with no additional text
"""

def process_job_posting(job_html_content: str) -> Dict[str, Any]:
    """
    Process job posting HTML/text through OpenAI to extract structured data.
    
    Args:
        job_html_content: HTML or plaintext content of the job posting
        
    Returns:
        Dictionary containing structured job data
    """
    logger.info("Processing job posting content with OpenAI")
    
    try:
        client = create_openai_client()
        
        # Get model name from environment or use default
        model_name = os.getenv("OPENAI_JOB_EXTRACTOR_MODEL", "gpt-4o-mini")
        logger.info(f"Using OpenAI model: {model_name}")
        
        # Make API call to OpenAI
        response = client.chat.completions.create(
            model=model_name,
            temperature=0,  # Use deterministic output
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": job_html_content}
            ],
            response_format={"type": "json_object"}  # Request JSON response
        )
        
        # Extract content from response
        result = response.choices[0].message.content
        
        # Parse JSON
        job_data = json.loads(result)
        logger.info("Successfully extracted job data from content")
        
        # Return parsed data
        return job_data
        
    except Exception as e:
        logger.error(f"Error processing job posting with OpenAI: {str(e)}", exc_info=True)
        raise