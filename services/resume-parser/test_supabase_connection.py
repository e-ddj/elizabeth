#!/usr/bin/env python3
"""
Utility script to test Supabase connectivity and bucket access.
Run with: python test_supabase_connection.py
"""

import logging
import os
import sys
from dotenv import load_dotenv

# Configure basic logging
logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d - %(message)s",
    stream=sys.stdout,
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file if present
load_dotenv()

# Check required environment variables
required_vars = [
    "SUPABASE_URL",
    "SUPABASE_PRIVATE_SERVICE_ROLE_KEY",
    "SUPABASE_PUBLIC_ANON_KEY"
]

for var in required_vars:
    value = os.getenv(var)
    if not value:
        logger.error(f"Environment variable {var} is not set")
    else:
        # Show a masked version of the value for security
        masked = value[:5] + "..." + value[-4:] if len(value) > 9 else "***"
        logger.info(f"Environment variable {var} is set: {masked}")

# Test Supabase connection
try:
    from utils.supabase.client import create_client
    logger.info("Attempting to create Supabase client with admin permissions")
    supabase = create_client(options={"admin": True})
    logger.info("Supabase client created successfully")
    
    # Try to list buckets
    try:
        logger.info("Attempting to list storage buckets")
        buckets = supabase.storage.list_buckets()
        bucket_names = [bucket.name for bucket in buckets]
        logger.info(f"Successfully listed storage buckets: {bucket_names}")
    except Exception as e:
        logger.error(f"Failed to list storage buckets: {e}", exc_info=True)
    
    # Try a simple database query
    try:
        logger.info("Attempting a test database query")
        # Use any table that should exist in your database
        test_query = supabase.table("user_profile").select("count").limit(1).execute()
        logger.info(f"Successfully executed test query, row count: {len(test_query.data)}")
    except Exception as e:
        logger.error(f"Failed to execute test database query: {e}", exc_info=True)
        
except Exception as e:
    logger.error(f"Failed to create Supabase client: {e}", exc_info=True)

logger.info("Supabase connection test complete") 