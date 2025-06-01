import json
from flask import Blueprint, abort, jsonify, request, make_response
from models.job_extractor.enrich_job import enrich_job_field
from config.log_config import get_logger
from api.cors_middleware import cors_middleware

logger = get_logger()
job_enricher_api = Blueprint("job_enricher", __name__)


def enrich_job_data(job_data):
    """Enriches all supported fields in the job data"""
    logger.info("Enriching all supported job fields (standalone implementation)")
    
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


def enrich_field(job_data, field_name):
    """Enriches a specific field in the job data"""
    logger.info(f"Enriching job field: {field_name} (standalone implementation)")
    
    if field_name not in job_data:
        raise ValueError(f"Invalid field name: {field_name}. Field not found in job data.")
    
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


@job_enricher_api.route("/enrich-field", methods=["POST", "OPTIONS"])
@cors_middleware
def job_field_enricher_endpoint():
    """
    Endpoint to enrich a specific field in job data.

    Expects a JSON payload with the following structure:
    {
        "job_data": {
            # Full job data dictionary
        },
        "field_name": "string"  # Name of the field to enrich
    }

    Returns:
        JSON response containing the updated job data with the enriched field.
    """
    # OPTIONS requests are now handled globally in the main app
        
    logger.info("Received request to /enrich-field endpoint")
    
    request_data = request.get_json()
    logger.info(f"Request data received for field enrichment")

    if not request_data:
        logger.error("Invalid JSON payload - no data received")
        abort(400, description="Invalid JSON payload.")

    job_data = request_data.get("job_data")
    field_name = request_data.get("field_name")
    
    logger.info(f"Field to enrich: {field_name}")

    if not job_data:
        logger.error("job_data parameter is missing in request")
        abort(400, description="job_data parameter is required")
        
    if not field_name:
        logger.error("field_name parameter is missing in request")
        abort(400, description="field_name parameter is required")

    try:
        logger.info(f"Attempting to enrich field: {field_name}")
        # Enrich the specified field
        updated_job_data = enrich_field(job_data=job_data, field_name=field_name)
        logger.info(f"Field enrichment successful for: {field_name}")
    except ValueError as val_error:
        error_msg = str(val_error)
        logger.error(f"Value error: {error_msg}")
        abort(400, description=error_msg)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error enriching job field: {error_msg}", exc_info=True)
        abort(
            500, description=f"An unexpected error occurred while enriching the job field: {error_msg}"
        )

    # Prepare the response data
    try:
        logger.info("Field enriched successfully, returning response")
        # CORS headers are now added globally in the after_request handler
        return jsonify(updated_job_data), 200
    except Exception as e:
        logger.error(f"Error serializing response: {e}", exc_info=True)
        abort(500, description=f"Error serializing response: {str(e)}")


@job_enricher_api.route("/enrich", methods=["GET", "POST", "OPTIONS"])
@cors_middleware
def job_enricher_endpoint():
    """
    Endpoint to enrich all supported fields in job data.

    Expects a JSON payload with the following structure:
    {
        "job_data": {
            # Full job data dictionary
        }
    }

    Returns:
        JSON response containing the updated job data with all enriched fields.
    """
    # OPTIONS requests are now handled globally in the main app
        
    logger.info("Received request to /enrich endpoint")
    
    request_data = request.get_json()
    logger.info(f"Request data received for full job enrichment")

    if not request_data:
        logger.error("Invalid JSON payload - no data received")
        abort(400, description="Invalid JSON payload.")

    job_data = request_data.get("job_data")
    
    if not job_data:
        logger.error("job_data parameter is missing in request")
        abort(400, description="job_data parameter is required")

    try:
        logger.info(f"Attempting to enrich all supported fields")
        
        # Use the local function to enrich all fields
        job_data = enrich_job_data(job_data)
        
        logger.info(f"All fields enrichment completed")
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error enriching job data: {error_msg}", exc_info=True)
        abort(
            500, description=f"An unexpected error occurred while enriching the job data: {error_msg}"
        )

    # Prepare the response data
    try:
        logger.info("All fields enriched successfully, returning response")
        return jsonify(job_data), 200
    except Exception as e:
        logger.error(f"Error serializing response: {e}", exc_info=True)
        abort(500, description=f"Error serializing response: {str(e)}")