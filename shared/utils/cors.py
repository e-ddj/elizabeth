from flask import make_response, request
from flask_cors import CORS
import os

def configure_cors(app):
    """Configure CORS for the Flask app with production-ready settings"""
    
    # Get allowed origins from environment variable
    allowed_origins = os.getenv('CORS_ALLOWED_ORIGINS', '*').split(',')
    
    # In production, you should specify exact origins instead of '*'
    # Example: CORS_ALLOWED_ORIGINS=https://app.example.com,https://www.example.com
    
    cors_config = {
        "origins": allowed_origins,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": [
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "Accept",
            "Origin",
            "Access-Control-Request-Method",
            "Access-Control-Request-Headers"
        ],
        "expose_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True,
        "max_age": 86400  # 24 hours
    }
    
    CORS(app, resources={r"/*": cors_config})
    
    # Also handle OPTIONS requests explicitly
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = make_response()
            response.headers.add("Access-Control-Allow-Origin", request.headers.get("Origin", "*"))
            response.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
            response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
            response.headers.add("Access-Control-Max-Age", "86400")
            response.headers.add("Access-Control-Allow-Credentials", "true")
            return response
    
    return app