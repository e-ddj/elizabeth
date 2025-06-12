import os
from typing import List, Any
from supabase import create_client as create_supabase_client, Client
from config.log_config import get_logger
from shared.utils.environment import get_environment_config

logger = get_logger()

def create_client(options) -> Client:
    """
    Creates a Supabase client using environment variables.
    
    Args:
        options (dict): Options dictionary, with 'admin' key to determine if we use service role key.
        
    Returns:
        Client: Supabase client instance
        
    Raises:
        ValueError: If required environment variables are missing
        Exception: For other connection issues
    """
    # Get environment-specific Supabase configuration
    config = get_environment_config()
    url: str = config['url']
    
    if options.get("admin"):
        key: str = config['key']
        key_type = "service role key"
    else:
        # For public/anon key, still use environment variable (not environment-specific yet)
        key: str = os.getenv("SUPABASE_PUBLIC_ANON_KEY")
        key_type = "anon key"

    # Log key presence/absence without exposing the actual keys
    logger.info(f"Creating Supabase client for {config['environment']} environment with {'admin' if options.get('admin') else 'public'} permissions")
    
    # Validate environment variables
    if not url:
        error_msg = "SUPABASE_URL environment variable is not set"
        logger.error(error_msg)
        raise ValueError(error_msg)
        
    if not key:
        error_msg = f"Supabase {key_type} is not set in environment variables"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Create the Supabase client
    try:
        logger.info(f"Connecting to Supabase at URL: {url[:8]}...{url[-4:] if len(url) > 8 else ''}")
        supabase_client = create_supabase_client(supabase_url=url, supabase_key=key)
        logger.info("Supabase client created successfully")
        
        # Verify connection by performing a simple operation
        try:
            # Just fetch a small amount of data to test the connection
            supabase_client.table("user_profile").select("id").limit(1).execute()
            logger.info("Supabase connection verified - successful test query")
        except Exception as e:
            logger.warning(f"Created client but test query failed: {e}", exc_info=True)
            # Don't raise here, as the client might still be usable for other operations
        
        return supabase_client

    except Exception as e:
        error_msg = f"Failed to create Supabase client: {e}"
        logger.error(error_msg, exc_info=True)
        raise Exception(error_msg)


def users_per_role(client: Client, role: str) -> List[Any]:
    """
    Retrieves users with a specific role from Supabase auth.
    
    Args:
        client: Supabase client
        role: Role to filter users by
        
    Returns:
        List of user objects with the specified role
    """
    try:
        logger.info(f"Fetching users with role: {role}")
        users = client.auth.admin.list_users()
        user_per_role = [
            user
            for user in users
            if user.user_metadata.get("role") == role and user.confirmed_at is not None
        ]
        logger.info(f"Found {len(user_per_role)} users with role '{role}'")
        return user_per_role

    except Exception as e:
        logger.error(f"Error fetching users with role '{role}': {e}", exc_info=True)
        raise
