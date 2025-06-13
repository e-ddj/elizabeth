import threading
from flask import jsonify, request
from api.job_matcher.index import job_matcher_bp
from config.log_config import setup_logging
from core.job_matcher.match_job_to_users import match_job_to_users_async, match_user_to_jobs_async
from utils.supabase.client import job_exists, user_exists

logger = setup_logging()

@job_matcher_bp.route("/match", methods=["POST"])
def match_job():
    """
    Match a job to user profiles with HCP role.
    
    Expected payload:
    {
        "job_id": "uuid-string",
        "overwrite_existing_matches": false (optional)
    }
    
    Returns immediately:
    {
        "status": "accepted",
        "job_id": "uuid-string",
        "message": "Job matching process started"
    }
    """
    try:
        # Get job ID from request
        data = request.get_json()
        if not data or "job_id" not in data:
            return jsonify({"error": "job_id is required"}), 400
        
        job_id = data["job_id"]
        overwrite = data.get("overwrite_existing_matches", False)
        
        logger.info("Received job match request", job_id=job_id)
        
        # Get environment from header
        environment = request.headers.get('X-Environment', '').lower()
        if environment not in ['development', 'staging', 'production']:
            environment = None  # Use default
        
        # Check if job exists
        if not job_exists(job_id, environment=environment):
            return jsonify({"error": f"Job with ID {job_id} not found"}), 404
        
        # Start async matching process with explicit environment
        thread = threading.Thread(
            target=match_job_to_users_async,
            args=(job_id, overwrite, environment),
            daemon=True
        )
        thread.start()
        
        # Return success immediately
        return jsonify({
            "status": "accepted",
            "job_id": job_id,
            "message": "Job matching process started successfully"
        }), 202
        
    except Exception as e:
        logger.error("Error starting job match", error=str(e), exc_info=True)
        return jsonify({"error": "Failed to start job matching", "details": str(e)}), 500

@job_matcher_bp.route("/match-user", methods=["POST"])
def match_user():
    """
    Match a user to all available jobs based on their medical specialties.
    
    Expected payload:
    {
        "user_id": "uuid-string",
        "overwrite_existing_matches": false (optional)
    }
    
    Returns immediately:
    {
        "status": "accepted",
        "user_id": "uuid-string",
        "message": "User matching process started"
    }
    """
    try:
        # Get user ID from request
        data = request.get_json()
        if not data or "user_id" not in data:
            return jsonify({"error": "user_id is required"}), 400
        
        user_id = data["user_id"]
        overwrite = data.get("overwrite_existing_matches", False)
        
        logger.info("Received user match request", user_id=user_id)
        
        # Get environment from header
        environment = request.headers.get('X-Environment', '').lower()
        if environment not in ['development', 'staging', 'production']:
            environment = None  # Use default
        
        # Check if user exists
        if not user_exists(user_id, environment=environment):
            return jsonify({"error": f"User with ID {user_id} not found"}), 404
        
        # Start async matching process with explicit environment
        thread = threading.Thread(
            target=match_user_to_jobs_async,
            args=(user_id, overwrite, environment),
            daemon=True
        )
        thread.start()
        
        # Return success immediately
        return jsonify({
            "status": "accepted",
            "user_id": user_id,
            "message": "User matching process started successfully"
        }), 202
        
    except Exception as e:
        logger.error("Error starting user match", error=str(e), exc_info=True)
        return jsonify({"error": "Failed to start user matching", "details": str(e)}), 500