"""
Core functionality for enriching job data fields.
"""

import logging
from typing import Dict, Any, Optional, List

from models.job_extractor.enrich_job import enrich_job_field
from config.log_config import get_logger

logger = get_logger()

def enrich_job_data(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich multiple fields in the job data using AI enhancement.
    
    Args:
        job_data: The extracted job data dictionary
        
    Returns:
        Dictionary containing the updated job data with enriched fields
        
    Raises:
        ValueError: If the enrichment fails
    """
    logger.info("Enriching all supported job fields")
    
    try:
        # Define fields to enrich
        fields_to_enrich = ['summary', 'responsibilities', 'qualifications', 'perks']
        
        # Enrich each field
        for field_name in fields_to_enrich:
            if field_name in job_data:
                try:
                    # Get the original field value
                    original_value = job_data[field_name]
                    
                    # Call the enrichment model
                    enriched_value = enrich_job_field(
                        field_name=field_name,
                        field_value=original_value,
                        context=job_data
                    )
                    
                    # Update the job data with the enriched value
                    job_data[field_name] = enriched_value
                    logger.info(f"Successfully enriched field: {field_name}")
                except Exception as field_error:
                    logger.error(f"Error enriching field {field_name}: {str(field_error)}")
                    # Continue with other fields even if one fails
        
        logger.info("All fields enrichment completed")
        return job_data
        
    except Exception as e:
        error_msg = f"Error enriching job data: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise ValueError(error_msg)


def enrich_field(job_data: Dict[str, Any], field_name: str) -> Dict[str, Any]:
    """
    Enrich a specific field in the job data using AI enhancement.
    
    Args:
        job_data: The extracted job data dictionary
        field_name: The name of the field to enrich
        
    Returns:
        Dictionary containing the updated job data with enriched field
        
    Raises:
        ValueError: If the field name is invalid or enrichment fails
    """
    logger.info(f"Enriching job field: {field_name}")
    
    if field_name not in job_data:
        error_msg = f"Invalid field name: {field_name}. Field not found in job data."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    try:
        # Get the original field value
        original_value = job_data[field_name]
        
        # Call the enrichment model
        enriched_value = enrich_job_field(
            field_name=field_name,
            field_value=original_value,
            context=job_data
        )
        
        # Update the job data with the enriched value
        job_data[field_name] = enriched_value
        
        logger.info(f"Successfully enriched field: {field_name}")
        return job_data
        
    except Exception as e:
        error_msg = f"Error enriching job field {field_name}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise ValueError(error_msg)