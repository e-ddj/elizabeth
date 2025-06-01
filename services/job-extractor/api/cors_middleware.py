from functools import wraps
from flask import request, make_response, current_app

def add_cors_headers(response):
    """Add CORS headers to the response"""
    response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    # Include all common headers and custom headers that might be sent from the frontend
    response.headers['Access-Control-Allow-Headers'] = (
        'Content-Type, Authorization, X-Requested-With, Accept, '
        'Origin, Access-Control-Request-Method, Access-Control-Request-Headers, '
        'Access-Control-Allow-Methods, Access-Control-Allow-Origin, '
        'Access-Control-Allow-Headers, Access-Control-Allow-Credentials'
    )
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    # Add Access-Control-Max-Age to cache preflight requests
    response.headers['Access-Control-Max-Age'] = '86400'  # 24 hours
    return response

def cors_middleware(f):
    """CORS middleware for Flask routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'OPTIONS':
            response = make_response()
            add_cors_headers(response)
            return response
        
        response = make_response(f(*args, **kwargs))
        add_cors_headers(response)
        return response
    
    return decorated_function