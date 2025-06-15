import io
import logging
from typing import Optional
from supabase import Client
from config.log_config import get_logger

logger = get_logger()
# Note: This constant should match the value in the frontend code
SUPABASE_USER_FILE_BUCKET = "user_files"

# Alternative buckets where resumes might be stored
SUPABASE_RESUMES_BUCKET = "resumes"


def download_file(client: Client, file_path: str) -> Optional[io.BytesIO]:
    """
    Attempts to download a file from Supabase storage, trying multiple buckets if needed.
    The file_path can be in three formats:
    1. "environment/bucket/path" - Environment prefix with bucket and path
    2. "bucket/path" - Explicit bucket and path
    3. "path" - Uses default bucket (SUPABASE_USER_FILE_BUCKET)
    
    Returns a BytesIO object if successful, or None if there's an error.
    """
    # Parse the file path to determine bucket and path
    parts = file_path.split('/')
    
    # Check if the first part is an environment name
    environments = ["development", "staging", "production"]
    known_buckets = ["user_files", "resumes", "public", "avatars", "user-files"]
    
    if len(parts) >= 2 and parts[0] in environments:
        # Format: "environment/..." - skip the environment part
        logger.info(f"Detected environment prefix in path: {parts[0]}")
        
        # Remove the environment part and reparse
        remaining_parts = parts[1:]
        
        if len(remaining_parts) >= 2 and remaining_parts[0] in known_buckets:
            # Format: "environment/bucket/path"
            bucket_id = remaining_parts[0]
            path = '/'.join(remaining_parts[1:])
            logger.info(f"Parsed path with environment and bucket: env={parts[0]}, bucket={bucket_id}, path={path}")
        else:
            # Format: "environment/path" - use default bucket
            bucket_id = SUPABASE_USER_FILE_BUCKET
            path = '/'.join(remaining_parts)
            logger.info(f"Parsed path with environment only: env={parts[0]}, bucket={bucket_id}, path={path}")
    elif len(parts) >= 2 and parts[0] in known_buckets:
        # Format: "bucket/path"
        bucket_id = parts[0]
        path = '/'.join(parts[1:])
        logger.info(f"Parsed path with explicit bucket: bucket={bucket_id}, path={path}")
    else:
        # Format: just "path" - assume default bucket
        bucket_id = SUPABASE_USER_FILE_BUCKET
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
                # If the bucket doesn't exist, try the resumes bucket as fallback
                if bucket_id != SUPABASE_RESUMES_BUCKET and SUPABASE_RESUMES_BUCKET in bucket_names:
                    logger.warning(f"Falling back to '{SUPABASE_RESUMES_BUCKET}' bucket")
                    bucket_id = SUPABASE_RESUMES_BUCKET
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
        fallback_bucket = SUPABASE_RESUMES_BUCKET if bucket_id != SUPABASE_RESUMES_BUCKET else SUPABASE_USER_FILE_BUCKET
        
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
