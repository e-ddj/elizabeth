from flask import Blueprint

job_matcher_bp = Blueprint("job_matcher", __name__)

# Import routes
from . import match