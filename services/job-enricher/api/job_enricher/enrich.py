import json
from flask import Blueprint, abort, jsonify, request
from core.job_enricher.enrich_job_data import enrich_job_data, enrich_field
from config.log_config import get_logger

logger = get_logger()
job_enricher_api = Blueprint("job_enricher", __name__)


@job_enricher_api.route("/enrich", methods=["POST"])
def job_enricher_endpoint():
    """
    Endpoint to enrich job posting data to make it more appealing for candidates.

    Expects a JSON payload with job data in a specific structure.

    Returns:
        JSON response containing the enriched job data.
    """
    logger.info("Received request to /enrich endpoint")
    
    request_data = request.get_json()
    # Log the full request data for debugging
    logger.info(f"Request data received: {json.dumps(request_data)}")

    if not request_data:
        logger.error("Invalid JSON payload - no data received")
        abort(400, description="Invalid JSON payload.")

    # Check if the essential fields exist in the request data
    required_fields = ["title", "summary", "responsibilities", "qualifications"]
    for field in required_fields:
        if field not in request_data:
            logger.error(f"Required field '{field}' is missing in request")
            abort(400, description=f"Required field '{field}' is missing")

    try:
        logger.info("Attempting to enrich job data")
        # Enrich job data
        enriched_data = enrich_job_data(request_data)
        
        # Log the enriched data for debugging
        logger.info(f"Enriched data received from enrichment service: {json.dumps(enriched_data)}")
        
        # Validate the response has required fields
        if not enriched_data:
            logger.error("Enriched data is empty or None")
            abort(500, description="Enrichment service returned empty data")
            
        # Verify that all required fields are in the response
        for field in required_fields:
            if field not in enriched_data:
                logger.error(f"Required field '{field}' is missing in enriched data")
                abort(500, description=f"Required field '{field}' is missing in enriched data")
                
        logger.info("Job data enrichment successful and validated")
    except ValueError as val_error:
        error_msg = str(val_error)
        logger.error(f"Value error: {error_msg}")
        abort(400, description=error_msg)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error enriching job data: {error_msg}", exc_info=True)
        abort(
            500, description=f"An unexpected error occurred while enriching job data: {error_msg}"
        )

    # Prepare the response data
    try:
        logger.info("Job data enriched successfully, returning response")
        response = jsonify(enriched_data)
        logger.info(f"Response status: 200, Content-Type: {response.content_type}, Length: {response.content_length}")
        return response, 200
    except Exception as e:
        logger.error(f"Error serializing response: {e}", exc_info=True)
        abort(500, description=f"Error serializing response: {str(e)}")


@job_enricher_api.route("/enrich-field", methods=["POST"])
def enrich_field_endpoint():
    """
    Endpoint to enrich a specific field of job posting data.

    Expects a JSON payload with field data and context.
    Example request:
    {
        "field": "title",
        "value": "Software Engineer",
        "context": {
            "company": "TechCorp", 
            "industry": "Technology"
        }
    }

    Returns:
        JSON response containing the enriched field value.
    """
    logger.info("Received request to /enrich-field endpoint")
    
    request_data = request.get_json()
    # Log the full request data for debugging
    logger.info(f"Request data received: {json.dumps(request_data)}")

    if not request_data:
        logger.error("Invalid JSON payload - no data received")
        abort(400, description="Invalid JSON payload.")

    # Check if the essential fields exist in the request data
    required_fields = ["field", "value"]
    for field in required_fields:
        if field not in request_data:
            logger.error(f"Required field '{field}' is missing in request")
            abort(400, description=f"Required field '{field}' is missing")

    field_name = request_data.get("field")
    field_value = request_data.get("value")
    context = request_data.get("context", {})

    try:
        logger.info(f"Attempting to enrich field: {field_name}")
        # Enrich specific field
        enriched_value = enrich_field(field_name, field_value, context)
        
        # Log the enriched value for debugging
        logger.info(f"Enriched value received from enrichment service: {enriched_value}")
        
        # Validate the response
        if enriched_value is None:
            logger.error("Enriched value is None")
            abort(500, description="Enrichment service returned None value")
            
        logger.info(f"Field enrichment successful: {field_name}")
    except ValueError as val_error:
        error_msg = str(val_error)
        logger.error(f"Value error: {error_msg}")
        abort(400, description=error_msg)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error enriching field: {error_msg}", exc_info=True)
        abort(
            500, description=f"An unexpected error occurred while enriching field: {error_msg}"
        )

    # Prepare the response data
    try:
        response = {
            "field": field_name,
            "original": field_value,
            "enriched": enriched_value
        }
        logger.info(f"Response data: {json.dumps(response)}")
        logger.info(f"Field enrichment successful, returning response for {field_name}")
        return jsonify(response), 200
    except Exception as e:
        logger.error(f"Error serializing response: {e}", exc_info=True)
        abort(500, description=f"Error serializing response: {str(e)}")