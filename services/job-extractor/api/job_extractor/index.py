from flask import Blueprint
from api.job_extractor.extract import job_extractor_api

# register the main route
job_extractor_api_root = Blueprint("job_extractor_api_root", __name__)

# import all the sub-routes
job_extractor_api_root.register_blueprint(job_extractor_api)