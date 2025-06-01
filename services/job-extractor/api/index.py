from flask import Flask, jsonify, request
from flask_cors import CORS
from config.log_config import configure_logging, get_logger
from api.job_extractor.index import job_extractor_api_root
import logging
import sys

# Configure logging with explicit stdout handler
configure_logging()
logger = get_logger()

# Add an explicit StreamHandler to ensure logs go to stdout
root_logger = logging.getLogger()
has_stdout_handler = any(
    isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout
    for handler in root_logger.handlers
)

if not has_stdout_handler:
    stdout_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d - %(message)s')
    stdout_handler.setFormatter(formatter)
    root_logger.addHandler(stdout_handler)
    logger.info("Added explicit stdout handler for logging")

# register main Flask app
logger.info("Registering Flask App")
app = Flask(__name__)

# Enable CORS for all routes with detailed configuration
# In production, replace "*" with specific allowed origins
cors_config = {
    "origins": "*",  # Allow all origins (update for production)
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": [
        "Content-Type", "Authorization", "X-Requested-With", "Accept",
        "Origin", "Access-Control-Request-Method", "Access-Control-Request-Headers",
        "Access-Control-Allow-Methods", "Access-Control-Allow-Origin", 
        "Access-Control-Allow-Headers", "Access-Control-Allow-Credentials"
    ],
    "expose_headers": ["Content-Type", "Authorization"],
    "supports_credentials": False,  # Set to False when using origins: "*"
    "max_age": 86400  # 24 hours
}
CORS(app, resources={r"/*": cors_config})
logger.info("CORS enabled globally with detailed configuration")

# register job extractor API blueprint
app.register_blueprint(job_extractor_api_root, url_prefix="/api/job-extractor")
logger.info("Job extractor API blueprint registered successfully")



# Simple handler for OPTIONS requests
@app.before_request
def handle_options():
    if request.method == 'OPTIONS':
        logger.info(f"Handling OPTIONS request for path: {request.path}")
        # Log request headers for debugging CORS issues
        logger.debug(f"Request headers: {dict(request.headers)}")
        response = app.make_default_options_response()
        return response

@app.route("/")
def home():
    logger.info("Home endpoint accessed")
    return "Job Extractor Microservice API"
    
@app.route("/cors-test", methods=["GET", "POST", "OPTIONS"])
def cors_test():
    """Endpoint to test CORS configuration"""
    if request.method == "OPTIONS":
        # Return a response for the preflight request
        logger.info("Received OPTIONS request for CORS test")
        return "", 200
    
    logger.info(f"Received {request.method} request for CORS test")
    return jsonify({"message": "CORS test successful"}), 200

# Test endpoint for CORS
@app.route("/api/test-cors", methods=["GET", "POST", "OPTIONS"])
def test_cors():
    if request.method == "OPTIONS":
        return ""
    return jsonify({"message": "CORS is working!"})
@app.route("/health")
def health():
    """Health check endpoint for load balancer"""
    return {"status": "healthy", "service": "job-extractor"}, 200

@app.route("/metrics")
def metrics():
    """Metrics endpoint for Prometheus monitoring"""
    return "# TYPE job_extractor_health gauge\njob_extractor_health 1\n", 200, {'Content-Type': 'text/plain'}

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)
