"""
Supabase storage bucket utilities.
"""

import io
import logging
from typing import Optional
from supabase import Client
from config.log_config import get_logger

logger = get_logger()
# Note: This constant should match the value in the frontend code
SUPABASE_JOB_FILES_BUCKET = "jobs"

# Alternative buckets where job files might be stored
SUPABASE_USER_FILES_BUCKET = "user_files"


def download_file(client: Client, file_path: str) -> Optional[io.BytesIO]:
    """
    Attempts to download a file from Supabase storage, trying multiple buckets if needed.
    The file_path can be in two formats:
    1. "bucket/path" - Explicit bucket and path
    2. "path" - Uses default bucket (SUPABASE_JOB_FILES_BUCKET)
    
    Returns a BytesIO object if successful, or None if there's an error.
    """
    # Parse the file path to determine bucket and path
    parts = file_path.split('/', 1)
    
    if len(parts) > 1 and parts[0] in ["jobs", "user_files", "public", "job-files"]:
        # Format: "bucket/path"
        bucket_id = parts[0]
        path = parts[1]
        logger.info(f"Parsed path with explicit bucket: bucket={bucket_id}, path={path}")
    else:
        # Format: just "path" - assume default bucket
        bucket_id = SUPABASE_JOB_FILES_BUCKET
        path = file_path
        logger.info(f"Using default bucket: bucket={bucket_id}, path={path}")

    # 1) Check if the bucket exists (and that we have permissions to list buckets)
    try:
        logger.info("Listing Supabase buckets")
        buckets = client.storage.list_buckets()
        bucket_names = [bucket.name for bucket in buckets]
        logger.info(f"Available buckets: {bucket_names}")

        if bucket_id not in bucket_names:
            # Check if a differently-named but equivalent bucket exists
            alternative_name = bucket_id.replace("_", "-")
            logger.warning(f"Bucket '{bucket_id}' not found, checking for '{alternative_name}'")
            
            if alternative_name in bucket_names:
                bucket_id = alternative_name
                logger.info(f"Using alternative bucket name: {bucket_id}")
            else:
                # If the bucket doesn't exist, try the user_files bucket as fallback
                if bucket_id != SUPABASE_USER_FILES_BUCKET and SUPABASE_USER_FILES_BUCKET in bucket_names:
                    logger.warning(f"Falling back to '{SUPABASE_USER_FILES_BUCKET}' bucket")
                    bucket_id = SUPABASE_USER_FILES_BUCKET
                else:
                    error_msg = f"Bucket '{bucket_id}' does not exist or you do not have permission to access it."
                    logger.error(error_msg)
                    return None
    except Exception as e:
        error_msg = f"Error retrieving list of buckets (permissions/credentials issue?): {e}"
        logger.error(error_msg, exc_info=True)
        return None

    # 2) Try downloading from the selected bucket
    response = None
    try:
        logger.info(f"Attempting to download file from bucket '{bucket_id}': {path}")
        response = client.storage.from_(bucket_id).download(path)

        if not response:
            error_msg = f"Supabase Bucket: No valid response returned for '{path}' in bucket '{bucket_id}'."
            logger.error(error_msg)
            return None

        logger.info(f"Successfully downloaded file from bucket '{bucket_id}': {path}, size: {len(response)} bytes")
        return io.BytesIO(response)

    except Exception as primary_error:
        # If the download failed, try the other bucket as a fallback
        fallback_bucket = SUPABASE_USER_FILES_BUCKET if bucket_id != SUPABASE_USER_FILES_BUCKET else SUPABASE_JOB_FILES_BUCKET
        
        if fallback_bucket in bucket_names:
            try:
                logger.warning(f"Primary download failed. Trying fallback bucket '{fallback_bucket}': {path}")
                response = client.storage.from_(fallback_bucket).download(path)
                
                if response:
                    logger.info(f"Successfully downloaded file from fallback bucket '{fallback_bucket}': {path}, size: {len(response)} bytes")
                    return io.BytesIO(response)
            except Exception as fallback_error:
                logger.error(f"Fallback download also failed: {fallback_error}")
                
        # If we reached here, all download attempts failed
        error_msg = f"Failed to download file '{path}' from any bucket: {primary_error}"
        logger.error(error_msg, exc_info=True)
        return None

def list_files(supabase: Client, path: str = "", bucket_name: str = "jobs") -> list:
    """
    List files in a Supabase storage bucket.
    
    Args:
        supabase: Supabase client
        path: Path in the bucket to list files from
        bucket_name: Name of the bucket (default: "jobs")
        
    Returns:
        List of files in the specified path
    """
    try:
        logger.info(f"Listing files in {bucket_name}/{path}")
        response = supabase.storage.from_(bucket_name).list(path)
        logger.info(f"Found {len(response)} files in {bucket_name}/{path}")
        return response
    except Exception as e:
        logger.error(f"Error listing files in Supabase bucket: {str(e)}", exc_info=True)
        return [] 