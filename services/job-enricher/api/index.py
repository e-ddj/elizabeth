from flask import Flask
from flask_cors import CORS
from config.log_config import configure_logging, get_logger
from api.job_enricher.index import job_enricher_api_root
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

# Enable CORS with support for credentials
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000", "supports_credentials": True}})
logger.info("CORS enabled for API endpoints with credentials support")

# register job enricher API blueprint
app.register_blueprint(job_enricher_api_root, url_prefix="/api/job-enricher")

logger.info("Job enricher API blueprint registered successfully")

@app.route("/")
def home():
    logger.info("Home endpoint accessed")
    return "Job Enricher Microservice API"
@app.route("/health")
def health():
    """Health check endpoint for load balancer"""
    return {"status": "healthy", "service": "job-enricher"}, 200

@app.route("/metrics")
def metrics():
    """Metrics endpoint for Prometheus monitoring"""
    return "# TYPE job_enricher_health gauge\njob_enricher_health 1\n", 200, {'Content-Type': 'text/plain'}

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)
