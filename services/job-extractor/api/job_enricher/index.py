from flask import Blueprint
from api.job_enricher.enrich_standalone import job_enricher_api

# Register the main route
job_enricher_api_root = Blueprint("job_enricher_api_root", __name__)

# Import all the sub-routes
job_enricher_api_root.register_blueprint(job_enricher_api)