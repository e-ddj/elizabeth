import os
from supabase import create_client, Client
from config.log_config import setup_logging
from typing import List, Optional
from uuid import UUID
from shared.utils.environment import get_environment_config

logger = setup_logging()

def create_supabase_client(environment: str = None) -> Client:
    """Create and return a Supabase client instance."""
    config = get_environment_config(environment=environment)
    url = config['url']
    key = config['key']
    
    if not url or not key:
        raise ValueError(f"Supabase credentials not found for {config['environment']} environment")
    
    logger.info(f"Creating Supabase client for {config['environment']} environment")
    return create_client(url, key)

def fetch_job_by_id(job_id: str, environment: str = None) -> dict:
    """Fetch job data from Supabase by ID."""
    try:
        client = create_supabase_client(environment=environment)
        
        # Fetch job from the job table (singular)
        response = client.table("job").select("*").eq("id", job_id).single().execute()
        
        if not response.data:
            raise ValueError(f"Job with ID {job_id} not found")
        
        logger.info("Job fetched successfully", job_id=job_id)
        return response.data
        
    except Exception as e:
        logger.error("Error fetching job", job_id=job_id, error=str(e))
        raise

def fetch_all_user_profiles(environment: str = None) -> list[dict]:
    """Fetch all active user profiles from Supabase."""
    try:
        client = create_supabase_client(environment=environment)
        
        # Fetch all user profiles
        # Note: user_profile table, not user_profiles
        response = client.table("user_profile").select("*").execute()
        
        user_profiles = response.data
        
        # For each user, fetch their specialties from user_specialty table
        for profile in user_profiles:
            user_id = profile.get("user_id")
            if user_id:
                # Fetch specialties through user_specialty join table
                specialty_response = client.table("user_specialty").select(
                    "medical_specialty_rosetta(id,id_rosetta,name)"
                ).eq("user_id", user_id).execute()
                
                # Extract the specialty data
                specialties = []
                for spec in specialty_response.data:
                    if spec.get("medical_specialty_rosetta"):
                        specialties.append(spec["medical_specialty_rosetta"])
                
                profile["specialties"] = specialties
        
        logger.info("User profiles fetched with specialties", count=len(user_profiles))
        return user_profiles
        
    except Exception as e:
        logger.error("Error fetching user profiles", error=str(e))
        raise

def job_exists(job_id: str, environment: str = None) -> bool:
    """Check if a job exists in the database."""
    try:
        client = create_supabase_client(environment=environment)
        response = client.table("job").select("id").eq("id", job_id).execute()
        return len(response.data) > 0
    except Exception as e:
        logger.error("Error checking job existence", job_id=job_id, error=str(e))
        return False

def get_users_by_role(role: str = "hcp", environment: str = None) -> List[dict]:
    """Get all users with a specific role."""
    try:
        client = create_supabase_client(environment=environment)
        # This assumes there's a way to filter users by role
        # Adjust based on your actual schema
        response = client.table("user_profile").select("*").execute()
        # You might need to join with auth.users or filter differently
        return response.data
    except Exception as e:
        logger.error("Error fetching users by role", role=role, error=str(e))
        return []

def get_user_specialties(user_id: str, environment: str = None) -> List[dict]:
    """Get user's medical specialties."""
    try:
        client = create_supabase_client(environment=environment)
        response = client.table("user_specialty").select(
            "medical_specialty_rosetta(id,id_rosetta,name)"
        ).eq("user_id", user_id).execute()
        
        specialties = []
        for spec in response.data:
            if spec.get("medical_specialty_rosetta"):
                specialties.append(spec["medical_specialty_rosetta"])
        return specialties
    except Exception as e:
        logger.error("Error fetching user specialties", user_id=user_id, error=str(e))
        return []

def check_match_exists(user_id: str, job_id: str, environment: str = None) -> bool:
    """Check if a match already exists between user and job."""
    try:
        client = create_supabase_client(environment=environment)
        response = client.table("match").select("id").eq(
            "candidate_id", user_id
        ).eq("job_id", job_id).execute()
        return len(response.data) > 0
    except Exception as e:
        logger.error("Error checking match existence", error=str(e))
        return False

def store_match_result(user_id: str, job_id: str, score: float, details: dict, environment: str = None) -> None:
    """Store a single match result in Supabase."""
    try:
        from datetime import datetime
        client = create_supabase_client(environment=environment)
        
        # Prepare match record matching your schema
        match_record = {
            "candidate_id": user_id,
            "job_id": int(job_id),
            "score": float(score),
            "details": details,  # JSON details from AI matching
            "origin": "internal",  # Mark as internally generated match
            "updated_at": datetime.now().isoformat()
        }
        
        # Upsert to handle updates
        client.table("match").upsert(match_record).execute()
        logger.info("Match result stored", user_id=user_id, job_id=job_id, score=score, origin="internal")
        
    except Exception as e:
        logger.error("Error storing match result", user_id=user_id, job_id=job_id, error=str(e))
        # Don't raise - this is optional functionality

def fetch_jobs_by_specialty(specialty_id: str, environment: str = None) -> List[dict]:
    """Fetch all jobs that match a specific medical specialty."""
    try:
        client = create_supabase_client(environment=environment)
        response = client.table("job").select("*").eq("medical_specialty_rosetta_id", specialty_id).execute()
        return response.data
    except Exception as e:
        logger.error("Error fetching jobs by specialty", specialty_id=specialty_id, error=str(e))
        return []

def user_exists(user_id: str, environment: str = None) -> bool:
    """Check if a user exists in the database."""
    try:
        client = create_supabase_client(environment=environment)
        response = client.table("user_profile").select("user_id").eq("user_id", user_id).execute()
        return len(response.data) > 0
    except Exception as e:
        logger.error("Error checking user existence", user_id=user_id, error=str(e))
        return False

def update_user_matching_status(user_id: str, status: str, environment: str = None) -> bool:
    """Update the matching_status field for a user in user_profile table."""
    try:
        client = create_supabase_client(environment=environment)
        response = client.table("user_profile").update({
            "matching_status": status
        }).eq("user_id", user_id).execute()
        
        if response.data:
            logger.info("User matching status updated", user_id=user_id, status=status)
            return True
        return False
    except Exception as e:
        logger.error("Error updating user matching status", user_id=user_id, status=status, error=str(e))
        return False