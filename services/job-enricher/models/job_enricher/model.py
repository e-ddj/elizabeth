"""
AI model for enriching job data to make it more appealing for candidates.
"""

import json
import os
import logging
from typing import Dict, Any

from openai import OpenAI
from config.log_config import get_logger

logger = get_logger()

# Initialize OpenAI client
def create_openai_client() -> OpenAI:
    """Create and return an OpenAI client using API key from environment variables."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    return OpenAI(api_key=api_key)

# System prompt for job data enrichment
SYSTEM_PROMPT = """You enrich and market-optimize healthcare job listings."""

def process_job_enrichment(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process job data through OpenAI to enrich and make it more appealing.
    
    Args:
        job_data: Original job data dictionary
        
    Returns:
        Dictionary containing the enriched job data
    """
    logger.info("Processing job enrichment with OpenAI")
    
    # Log the input data
    logger.info(f"Input job data: {json.dumps(job_data)}")
    
    try:
        client = create_openai_client()
        
        # Get model name from environment or use default
        model_name = os.getenv("OPENAI_JOB_ENRICHER_MODEL", "gpt-4o-mini")
        temperature = float(os.getenv("OPENAI_JOB_ENRICHER_TEMPERATURE", "0.7"))
        logger.info(f"Using OpenAI model: {model_name} with temperature: {temperature}")
        
        # Prepare the prompt
        user_prompt = f"""
You are a marketing copywriter for a healthcare company. 
Take the following raw job data JSON and return a single JSON object with exactly the same keys, but:
- Rewrite "title" to be more engaging.
- Expand "summary" into a 2–3 sentence hook highlighting team culture, growth paths, and location perks.
- For "responsibilities" and "qualifications", rewrite each bullet into action-oriented, benefit-driven bullets.
- Under "perks", add at least five high-impact perks (e.g. "Wellness stipend", "Professional development budget", etc.).
- Under "benefitsData", add relevant benefit IDs based on jobBenefits mapping (e.g. [1,4,7]).
- Add a new field "highlightedBenefits" as an array of 3 strings calling out the top perks.
  
Return valid JSON only.
  
Raw job JSON:
{json.dumps(job_data, indent=2)}
"""
        
        # Log the prepared prompt
        logger.info(f"Prompt sent to OpenAI: {user_prompt}")
        
        # Make API call to OpenAI
        logger.info("Sending request to OpenAI API")
        response = client.chat.completions.create(
            model=model_name,
            temperature=temperature,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}  # Request JSON response
        )
        
        # Log the raw response information
        usage = getattr(response, 'usage', None)
        if usage:
            logger.info(f"OpenAI tokens: prompt={usage.prompt_tokens}, completion={usage.completion_tokens}, total={usage.total_tokens}")
        
        # Extract content from response
        content = response.choices[0].message.content
        
        # Log the raw response content
        logger.info(f"Raw response from OpenAI: {content}")
        
        # Parse JSON
        try:
            enriched_data = json.loads(content)
            logger.info(f"Successfully parsed JSON response")
            logger.info(f"Enriched job data: {json.dumps(enriched_data)}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received from OpenAI: {e}")
            logger.error(f"Raw response (failed to parse): {content}")
            raise ValueError(f"Failed to parse JSON from OpenAI response: {e}")
        
        # Validate the response has the required fields
        for key in job_data.keys():
            if key not in enriched_data:
                logger.error(f"Missing key in response: {key}")
                logger.error(f"Original data had keys: {list(job_data.keys())}")
                logger.error(f"Response data has keys: {list(enriched_data.keys())}")
                raise ValueError(f"OpenAI response missing required key: {key}")
        
        # Return parsed data
        return enriched_data
        
    except Exception as e:
        logger.error(f"Error processing job enrichment with OpenAI: {str(e)}", exc_info=True)
        raise