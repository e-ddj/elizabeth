import json
import os
from pathlib import Path
from flask import Blueprint, abort, jsonify, request
from core.job_extractor.extract_job_data import extract_job_data, extract_job_data_from_file
from config.log_config import get_logger

# Import Supabase utilities
try:
    from utils.supabase.client import create_client
    from utils.supabase.bucket import download_file
    _HAS_SUPABASE = True
except ImportError:
    _HAS_SUPABASE = False

logger = get_logger()
job_extractor_api = Blueprint("job_extractor", __name__)


@job_extractor_api.route("/extract", methods=["POST"])
def job_extractor_endpoint():
    """
    Endpoint to extract structured data from job posting HTML/text.

    Expects a JSON payload with the following structure:
    {
        "job_url": "https://example.com/job-posting"
    }

    Returns:
        JSON response containing the extracted job data in structured format.
    """
    logger.info("Received request to /extract endpoint")
    
    request_data = request.get_json()
    logger.info(f"Request data: {request_data}")

    if not request_data:
        logger.error("Invalid JSON payload - no data received")
        abort(400, description="Invalid JSON payload.")

    job_url = request_data.get("job_url")
    logger.info(f"Job URL from request: {job_url}")

    if not job_url:
        logger.error("job_url parameter is missing in request")
        abort(400, description="job_url parameter is required")

    try:
        logger.info(f"Attempting to extract job data from URL: {job_url}")
        # Extract job data from the provided URL
        job_data = extract_job_data(job_url=job_url)
        logger.info("Job data extraction successful")
    except ValueError as val_error:
        error_msg = str(val_error)
        logger.error(f"Value error: {error_msg}")
        
        # Provide more user-friendly error messages for common cases
        if "Access forbidden" in error_msg:
            abort(403, description="Unable to access this job posting. The website may be blocking automated access. Please try a different job posting URL or contact support if this persists.")
        elif "Invalid URL format" in error_msg:
            abort(400, description="Please provide a valid URL starting with http:// or https://")
        else:
            abort(400, description=error_msg)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error processing job posting: {error_msg}", exc_info=True)
        abort(
            500, description=f"An unexpected error occurred while processing the job posting: {error_msg}"
        )

    # Prepare the response data
    try:
        logger.info("Job data extracted successfully, returning response")
        return jsonify(job_data), 200
    except Exception as e:
        logger.error(f"Error serializing response: {e}", exc_info=True)
        abort(500, description=f"Error serializing response: {str(e)}")


@job_extractor_api.route("/extract-from-file", methods=["POST", "OPTIONS"])
def job_extractor_file_endpoint():
    """
    Endpoint to extract structured data from a job document uploaded to Supabase.
    
    Expects a JSON payload with:
    {
        "file_path": "path/to/file/in/supabase/storage",
        "bucket_name": "optional_bucket_name"
    }
    
    Returns:
        JSON response containing the extracted job data in structured format.
    """
    logger.info("Received request to /extract-from-file endpoint")
    
    if not _HAS_SUPABASE:
        logger.error("Supabase utilities not available - cannot process file upload")
        abort(500, description="File upload processing is not available. The server is missing required dependencies.")
    
    request_data = request.get_json()
    logger.info(f"Request data: {request_data}")

    if not request_data:
        logger.error("Invalid JSON payload - no data received")
        abort(400, description="Invalid JSON payload.")

    file_path = request_data.get("file_path")
    logger.info(f"File path from request: {file_path}")

    if not file_path:
        logger.error("file_path parameter is missing in request")
        abort(400, description="file_path parameter is required")

    try:
        # Verify environment variables
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_PRIVATE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not supabase_key:
            logger.error("Supabase environment variables not set")
            abort(500, description="Server configuration error: Supabase credentials not found")
        
        # Initialize Supabase client
        supabase = create_client()
        logger.info("Supabase client created successfully")
        
        # Download file from Supabase
        # If bucket_name is provided in the request, use it, otherwise let download_file use the default
        blob = download_file(supabase, file_path)
        if blob is None:
            logger.error(f"File not found in Supabase: {file_path}")
            abort(404, description=f"File not found: {file_path}")
        
        file_bytes = blob.getvalue()
        file_extension = Path(file_path).suffix.lower()
        logger.info(f"Downloaded file from Supabase, size: {len(file_bytes)} bytes, extension: {file_extension}")
        
        # Extract job data from the file
        logger.info(f"Attempting to extract job data from file: {file_path}")
        job_data = extract_job_data_from_file(file_bytes=file_bytes, file_extension=file_extension)
        logger.info("Job data extraction from file successful")
        
    except ValueError as val_error:
        error_msg = str(val_error)
        logger.error(f"Value error: {error_msg}")
        
        # Provide user-friendly error messages
        if "Unsupported file format" in error_msg:
            abort(400, description=f"Unsupported file format. Please upload a PDF, DOCX, or TXT file.")
        elif "Failed to extract text" in error_msg:
            abort(400, description="Unable to extract text from the file. The file may be corrupted or password-protected.")
        else:
            abort(400, description=error_msg)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error processing job file: {error_msg}", exc_info=True)
        abort(
            500, description=f"An unexpected error occurred while processing the job file: {error_msg}"
        )

    # Prepare the response data
    try:
        logger.info("Job data extracted successfully from file, returning response")
        return jsonify(job_data), 200
    except Exception as e:
        logger.error(f"Error serializing response: {e}", exc_info=True)
        abort(500, description=f"Error serializing response: {str(e)}")