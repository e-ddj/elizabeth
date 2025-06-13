import os
import contextvars
from flask import request, has_request_context
import logging

logger = logging.getLogger(__name__)

# Context variable for environment - automatically propagates to child threads
env_context = contextvars.ContextVar('environment', default='production')

def get_environment_config():
    """
    Determine environment based on X-Environment header or context variable.
    Supports: development, staging, production
    Uses context variables to propagate environment to background threads.
    
    Returns:
        dict: Configuration with 'url', 'key', and 'environment'
    """
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
    
    # Try context variable first (works in background threads)
    env = env_context.get()
    if env != 'production':  # Already set to non-default
        logger.debug(f"Using environment from context: {env}")
        return configs.get(env, configs['production'])
    
    # Set from request header if we have request context (main thread)
    if has_request_context():
        header_env = request.headers.get('X-Environment', '').lower()
        valid_envs = ['development', 'staging', 'production']
        
        if header_env and header_env in valid_envs:
            env = header_env
            env_context.set(env)  # Set context for background threads
            logger.info(f"Set environment from header: {env}")
        else:
            # Use default from env var
            env = os.getenv('DEFAULT_ENVIRONMENT', 'production').lower()
            if env in valid_envs:
                env_context.set(env)
                logger.info(f"Set environment from DEFAULT_ENVIRONMENT: {env}")
            else:
                env = 'production'
    else:
        # No request context (likely background thread), use fallback
        env = os.getenv('DEFAULT_ENVIRONMENT', 'production').lower()
        valid_envs = ['development', 'staging', 'production']
        if env not in valid_envs:
            env = 'production'
        logger.debug(f"No request context, using environment: {env}")
    
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