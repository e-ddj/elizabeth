"""
Supabase client creation utility.
"""

import os
from typing import Optional, Dict, Any
import logging
from supabase import create_client as sb_create_client, Client

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
    # Get Supabase URL and key from environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_PRIVATE_SERVICE_ROLE_KEY")
    
    if not supabase_url:
        error_msg = "SUPABASE_URL environment variable is not set"
        logger.error(error_msg)
        raise ValueError(error_msg)
        
    if not supabase_key:
        error_msg = "SUPABASE_PRIVATE_SERVICE_ROLE_KEY environment variable is not set"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.debug("Creating Supabase client")
    
    # Create and return Supabase client
    options = options or {}
    
    # Remove the 'admin' key if it exists, as it's not supported by the Supabase Python client
    if options and 'admin' in options:
        logger.debug("Removing unsupported 'admin' option from Supabase client options")
        options.pop('admin')
    
    client = sb_create_client(supabase_url, supabase_key, **options)
    
    logger.debug("Supabase client created successfully")
    return client 