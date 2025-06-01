"""
AI model for enriching specific job data fields with enhanced quality content.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Union

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

# System prompt for job field enrichment
SYSTEM_PROMPT = """
You are a specialized job data enhancement assistant. You will be given a specific field from a job posting 
along with its current value and context from other fields. Your task is to enrich and improve the field's 
content without altering its core meaning.

For each field type, follow these specific guidelines:

1. summary: Create a comprehensive, well-structured summary that highlights the key aspects of the role,
   the organization, and what makes this position unique. Aim for 3-5 sentences that would attract qualified candidates.

2. responsibilities: Expand and clarify the responsibilities list. Ensure each item is specific, 
   action-oriented, and provides clear insight into what the role entails.

3. qualifications: Enhance the qualifications list to be more specific and detailed. Include both the 
   technical skills and soft skills required for the role.

4. perks: Elaborate on the perks and benefits in a more engaging way that highlights their value to 
   potential candidates.

For all enhancements:
- Maintain professional language appropriate for job descriptions
- Keep the same overall structure (format lists as lists, etc.)
- Do not invent false information - only elaborate based on existing data
- If a field is empty or minimal, use context from other fields to create appropriate content
- Return only the enhanced content for the specific field, nothing else
"""

def enrich_job_field(field_name: str, field_value: Any, context: Dict[str, Any]) -> Any:
    """
    Enrich a specific field from job data using OpenAI to improve its quality and detail.
    
    Args:
        field_name: Name of the field to enrich
        field_value: Current value of the field
        context: The complete job data dictionary for context
        
    Returns:
        Enriched field value of the same type as the input
    """
    # Only process supported field types
    supported_fields = ['summary', 'responsibilities', 'qualifications', 'perks']
    
    if field_name not in supported_fields:
        logger.warning(f"Field enrichment not supported for: {field_name}")
        return field_value
    
    logger.info(f"Enriching job field: {field_name}")
    
    try:
        client = create_openai_client()
        
        # Get model name from environment or use default
        model_name = os.getenv("OPENAI_JOB_ENRICHMENT_MODEL", "gpt-4o-mini")
        logger.info(f"Using OpenAI model: {model_name}")
        
        # Prepare context and current field value
        context_for_model = {k: v for k, v in context.items() if k != field_name}
        
        # Prepare message for AI
        user_message = f"""
Field name: {field_name}
Current value: {json.dumps(field_value)}

Context (other fields from the job posting):
{json.dumps(context_for_model, indent=2)}

Please enrich and improve the content for the field "{field_name}".
"""
        
        # Make API call to OpenAI
        response = client.chat.completions.create(
            model=model_name,
            temperature=0.7,  # Allow for some creativity
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ]
        )
        
        # Extract content from response
        result = response.choices[0].message.content
        
        # Process the result based on field type
        if field_name in ['responsibilities', 'qualifications', 'perks'] and isinstance(field_value, list):
            # For list fields, split the result into a list and clean up items
            enriched_items = [item.strip() for item in result.split('\n') if item.strip()]
            # Remove any bullet points or numbering that might have been added
            enriched_items = [item.lstrip('•-* 0123456789.') for item in enriched_items]
            # Remove duplicates while preserving order
            seen = set()
            enriched_value = [item for item in enriched_items if not (item in seen or seen.add(item))]
        else:
            # For text fields, use the result directly
            enriched_value = result.strip()
        
        logger.info(f"Successfully enriched field: {field_name}")
        return enriched_value
        
    except Exception as e:
        logger.error(f"Error enriching job field with OpenAI: {str(e)}", exc_info=True)
        # Return original value on error
        return field_value