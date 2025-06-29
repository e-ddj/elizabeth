"""
Supabase client creation utility.
"""

import os
from typing import Optional, Dict, Any
import logging
from supabase import create_client as sb_create_client, Client
from shared.utils.environment import get_environment_config

logger = logging.getLogger(__name__)

def create_client(options: Optional[Dict[str, Any]] = None) -> Client:
    """
    Create and return a Supabase client.
    
    Args:
        options: Additional options for the Supabase client
        
    Returns:
        Supabase client
        
    Raises:
        ValueError: If required environment variables are not set
    """
    # Get environment-specific Supabase configuration
    config = get_environment_config()
    supabase_url = config['url']
    supabase_key = config['key']
    
    if not supabase_url:
        error_msg = f"Supabase URL not found for {config['environment']} environment"
        logger.error(error_msg)
        raise ValueError(error_msg)
        
    if not supabase_key:
        error_msg = f"Supabase key not found for {config['environment']} environment"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"Creating Supabase client for {config['environment']} environment")
    
    # Create and return Supabase client
    options = options or {}
    
    # Remove the 'admin' key if it exists, as it's not supported by the Supabase Python client
    if options and 'admin' in options:
        logger.debug("Removing unsupported 'admin' option from Supabase client options")
        options.pop('admin')
    
    client = sb_create_client(supabase_url, supabase_key, **options)
    
    logger.debug("Supabase client created successfully")
    return client 