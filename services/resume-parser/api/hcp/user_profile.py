import json
from flask import Blueprint, abort, jsonify, request
from core.user_profile.extract_profile_from_resume import extract_profile_from_resume
from utils.json_serializer import json_serializer
from config.log_config import get_logger

logger = get_logger()
hcp_user_profile_api = Blueprint("hcp_user_profile", __name__)


@hcp_user_profile_api.route("/user-profile", methods=["POST"])
def hcp_user_profile_endpoint():
    """
    Endpoint to extract user profile information from a resume PDF.

    Expects a JSON payload with the following structure:
    {
        "file_path": "path/to/your/file.pdf"
    }

    Returns:
        JSON response containing both the extracted CV text and profile dictionary.
    """
    logger.info("Received request to /user-profile endpoint")
    
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
        logger.info(f"Attempting to extract profile from resume at path: {file_path}")
        # Extract both resume_text and profile_dict from the resume
        resume_text, profile_dict = extract_profile_from_resume(file_path=file_path)
        logger.info("Profile extraction successful")
    except FileNotFoundError as fnf_error:
        error_msg = str(fnf_error)
        logger.error(f"File not found: {error_msg}")
        abort(404, description=error_msg)
    except ValueError as val_error:
        error_msg = str(val_error)
        logger.error(f"Value error: {error_msg}")
        abort(400, description=error_msg)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error processing resume: {error_msg}", exc_info=True)
        abort(
            500, description=f"An unexpected error occurred while processing the resume: {error_msg}"
        )

    # Prepare the response data
    try:
        profile_dict = json.loads(json.dumps(profile_dict, default=json_serializer))
        logger.info("Profile serialized successfully, returning response")
        return jsonify(profile_dict), 200
    except Exception as e:
        logger.error(f"Error serializing response: {e}", exc_info=True)
        abort(500, description=f"Error serializing response: {str(e)}")
