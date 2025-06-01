"""
Core functionality for enriching job data to make it more appealing for candidates.
"""

import json
import logging
from typing import Dict, Any
import copy

from models.job_enricher.model import process_job_enrichment
from config.log_config import get_logger

logger = get_logger()

def enrich_job_data(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich job data by using AI to make it more appealing for candidates.
    
    Args:
        job_data: Original job data dictionary
        
    Returns:
        Dictionary containing the enriched job data
        
    Raises:
        ValueError: If the job data is invalid
    """
    logger.info("Starting job data enrichment")
    logger.info(f"Original job data keys: {list(job_data.keys())}")
    
    # Validate job data structure
    if not isinstance(job_data, dict):
        error_msg = "Job data must be a dictionary"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Create a copy of the original job data to preserve it
    validated_job_data = copy.deepcopy(job_data)
    
    try:
        # Log what we're sending to the model
        logger.info(f"Sending job data to model with keys: {list(validated_job_data.keys())}")
        
        # Process the job data through the AI model for enrichment
        enriched_job_data = process_job_enrichment(validated_job_data)
        
        # Validate the response
        if not enriched_job_data:
            error_msg = "Failed to enrich job data - no data returned from model"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Log what we received from the model
        logger.info(f"Received enriched data from model with keys: {list(enriched_job_data.keys())}")
            
        # Ensure all original keys are present in the enriched data
        for key in validated_job_data.keys():
            if key not in enriched_job_data:
                error_msg = f"Enriched data is missing required key: {key}"
                logger.error(error_msg)
                logger.error(f"Original keys: {list(validated_job_data.keys())}")
                logger.error(f"Enriched keys: {list(enriched_job_data.keys())}")
                raise ValueError(error_msg)
        
        logger.info("Successfully enriched job data")
        return enriched_job_data
        
    except Exception as e:
        error_msg = f"Error processing job enrichment: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise

def enrich_field(field_name: str, field_value: str, context: Dict[str, Any] = None) -> str:
    """
    Enrich a specific field of job data using AI to make it more appealing for candidates.
    
    Args:
        field_name: Name of the field to enrich (e.g., 'title', 'summary')
        field_value: Original value of the field
        context: Optional dictionary containing context information (e.g., company, industry)
        
    Returns:
        Enriched field value as a string
        
    Raises:
        ValueError: If the field data is invalid
    """
    logger.info(f"Starting enrichment for field: {field_name}")
    logger.info(f"Original field value: {field_value}")
    if context:
        logger.info(f"Context provided with keys: {list(context.keys())}")
    
    if not isinstance(field_value, str):
        error_msg = f"Field value for {field_name} must be a string"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    if context is None:
        context = {}
    
    try:
        # Create a minimal job data structure with just the field to enrich
        job_data = {
            field_name: field_value,
            **context
        }
        
        logger.info(f"Sending data to model with keys: {list(job_data.keys())}")
        
        # Process the field through the AI model for enrichment
        enriched_data = process_job_enrichment(job_data)
        
        # Validate the response
        if not enriched_data:
            error_msg = f"Failed to enrich field {field_name} - no data returned from model"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info(f"Received enriched data from model with keys: {list(enriched_data.keys())}")
            
        if field_name not in enriched_data:
            error_msg = f"Failed to enrich field {field_name} - field not found in model response"
            logger.error(error_msg)
            logger.error(f"Response keys: {list(enriched_data.keys())}")
            raise ValueError(error_msg)
        
        enriched_value = enriched_data[field_name]
        
        # Validate the enriched value
        if enriched_value is None:
            error_msg = f"Enriched value for field {field_name} is None"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not isinstance(enriched_value, str):
            error_msg = f"Enriched value for field {field_name} must be a string, got {type(enriched_value)}"
            logger.error(error_msg)
            logger.error(f"Actual value: {enriched_value}")
            raise ValueError(error_msg)
            
        logger.info(f"Successfully enriched field: {field_name}")
        logger.info(f"Enriched value: {enriched_value}")
        return enriched_value
        
    except Exception as e:
        error_msg = f"Error processing field enrichment: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise