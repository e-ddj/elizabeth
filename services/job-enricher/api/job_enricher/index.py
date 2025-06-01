from flask import Blueprint
from api.job_enricher.enrich import job_enricher_api

# register the main route
job_enricher_api_root = Blueprint("job_enricher_api_root", __name__)

# import all the sub-routes
job_enricher_api_root.register_blueprint(job_enricher_api)