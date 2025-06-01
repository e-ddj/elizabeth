import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.log_config import setup_logging

logger = setup_logging()

# Create Flask app
app = Flask(__name__)
CORS(app)

# Register blueprints
from api.job_matcher.index import job_matcher_bp
app.register_blueprint(job_matcher_bp, url_prefix="/api/job-matcher")

@app.route("/")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "job-matcher"}

@app.route("/health")
def health():
    """Health check endpoint for load balancer"""
    return {"status": "healthy", "service": "job-matcher"}, 200

@app.route("/metrics")
def metrics():
    """Metrics endpoint for Prometheus monitoring"""
    return "# TYPE job_matcher_health gauge\njob_matcher_health 1\n", 200, {'Content-Type': 'text/plain'}

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5001))
    logger.info(f"Starting Job Matcher Service on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
