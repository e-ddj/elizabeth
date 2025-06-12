import os
from flask import request
import logging

logger = logging.getLogger(__name__)

def get_environment_config():
    """
    Determine environment based on X-Environment header or default.
    Supports: development, staging, production
    
    Returns:
        dict: Configuration with 'url', 'key', and 'environment'
    """
    # Check request header first
    env = None
    if request:
        env = request.headers.get('X-Environment', '').lower()
    
    # Fallback to default environment
    valid_envs = ['development', 'staging', 'production']
    if not env or env not in valid_envs:
        env = os.getenv('DEFAULT_ENVIRONMENT', 'production').lower()
    
    logger.info(f"Using environment: {env}")
    
    # Environment-specific configurations
    configs = {
        'development': {
            'url': os.getenv('SUPABASE_URL_DEV', 'http://host.docker.internal:54321'),
            'key': os.getenv('SUPABASE_PRIVATE_SERVICE_ROLE_KEY_DEV'),
            'environment': 'development'
        },
        'staging': {
            'url': os.getenv('SUPABASE_URL_STAGING'),
            'key': os.getenv('SUPABASE_PRIVATE_SERVICE_ROLE_KEY_STAGING'),
            'environment': 'staging'
        },
        'production': {
            'url': os.getenv('SUPABASE_URL_PROD', os.getenv('SUPABASE_URL')),
            'key': os.getenv('SUPABASE_PRIVATE_SERVICE_ROLE_KEY_PROD', 
                           os.getenv('SUPABASE_PRIVATE_SERVICE_ROLE_KEY')),
            'environment': 'production'
        }
    }
    
    return configs.get(env, configs['production'])

def is_development():
    """Check if running in development mode"""
    config = get_environment_config()
    return config['environment'] == 'development'

def is_staging():
    """Check if running in staging mode"""
    config = get_environment_config()
    return config['environment'] == 'staging'

def is_production():
    """Check if running in production mode"""
    config = get_environment_config()
    return config['environment'] == 'production'