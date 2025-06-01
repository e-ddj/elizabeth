from flask import Blueprint
from api.hcp.user_profile import hcp_user_profile_api

# register the main route
hcp_api_root = Blueprint("hcp_api_root", __name__)

# import all the sub-routes
hcp_api_root.register_blueprint(hcp_user_profile_api)
