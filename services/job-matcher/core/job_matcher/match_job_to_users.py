import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from config.log_config import setup_logging
from core.job_matcher.types import Job, UserProfile
from utils.supabase.client import (
    fetch_job_by_id, 
    get_users_by_role,
    get_user_specialties,
    check_match_exists,
    store_match_result,
    create_supabase_client,
    update_user_matching_status
)
from models.job_matcher.healthcare_matching import compute_healthcare_match_score

logger = setup_logging()

def match_job_to_users_async(job_id: str, overwrite_existing: bool = False, environment: str = None):
    """
    Asynchronously match a job to HCP users based on medical specialties.
    Only runs detailed matching if specialties match.
    
    Args:
        job_id: The ID of the job to match
        overwrite_existing: Whether to overwrite existing matches
        environment: Explicit environment (development, staging, production)
    """
    logger.info("Starting async job matching process", job_id=job_id)
    
    try:
        # Fetch job data
        job_data = fetch_job_by_id(job_id, environment=environment)
        job = Job.from_dict(job_data)
        
        if not job.medical_specialty_rosetta_id:
            logger.warning("Job has no medical specialty, skipping", job_id=job_id)
            return
        
        logger.info("Processing job", 
                   job_id=job_id,
                   title=job.title,
                   specialty=job.medical_specialty_rosetta_id)
        
        # Get all HCP users
        hcp_users = get_users_by_role("hcp", environment=environment)
        logger.info(f"Found {len(hcp_users)} HCP users to process")
        
        matches_found = 0
        
        for user_data in hcp_users:
            try:
                user_id = user_data.get("user_id")
                if not user_id:
                    continue
                
                # Check if match already exists
                if not overwrite_existing and check_match_exists(user_id, job_id, environment=environment):
                    logger.debug("Match already exists, skipping", 
                               user_id=user_id, job_id=job_id)
                    continue
                
                # Get user specialties
                user_specialties = get_user_specialties(user_id, environment=environment)
                
                # Check specialty match (hard requirement)
                specialty_match = False
                for specialty in user_specialties:
                    if specialty.get("id_rosetta") == job.medical_specialty_rosetta_id:
                        specialty_match = True
                        break
                
                if not specialty_match:
                    logger.debug("No specialty match, skipping detailed analysis",
                               user_id=user_id,
                               job_specialty=job.medical_specialty_rosetta_id)
                    continue
                
                # Specialty matches - proceed with detailed matching
                logger.info("Specialty match found, running detailed analysis",
                          user_id=user_id,
                          job_id=job_id)
                
                # Get resume text
                resume_text = get_resume_text_for_user(user_id, environment=environment)
                if not resume_text:
                    logger.warning("No resume text available", user_id=user_id)
                    continue
                
                # Run detailed AI matching
                match_result = compute_healthcare_match_score(
                    resume_text=resume_text,
                    job_description=job.description
                )
                
                if match_result:
                    score = float(match_result.get("overall_match_percentage", 0)) / 100.0
                    
                    if score > 0.5:
                            # Store the match
                        store_match_result(
                            user_id=user_id,
                            job_id=job_id,
                            score=score,
                            details=match_result,
                            environment=environment
                        )
                        matches_found += 1
                        
                        logger.info("Match found and stored",
                                    user_id=user_id,
                                    job_id=job_id,
                                    score=score)
                
            except Exception as e:
                logger.error("Error processing user",
                           user_id=user_data.get("user_id"),
                           error=str(e))
                continue
        
        logger.info("Job matching completed",
                   job_id=job_id,
                   total_users=len(hcp_users),
                   matches_found=matches_found)
        
    except Exception as e:
        logger.error("Error in job matching process", 
                    job_id=job_id, 
                    error=str(e),
                    exc_info=True)

def get_user_profile_data(user_id: str, environment: str = None) -> Optional[Dict[str, Any]]:
    """
    Get complete user profile data as a structured dictionary.
    """
    try:
        client = create_supabase_client(environment=environment)
        user_data = {}
        
        # Get user profile
        profile_response = client.table("user_profile").select("*").eq("user_id", user_id).single().execute()
        if profile_response.data:
            user_data["profile"] = profile_response.data
        else:
            logger.warning("No profile found for user", user_id=user_id)
            return None
        
        # Get experience
        try:
            exp_response = client.table("user_experience").select("*").eq(
                "user_id", user_id
            ).order("start_date", desc=True).execute()
            user_data["experience"] = exp_response.data or []
        except Exception as e:
            logger.debug("Could not fetch user_experience", error=str(e))
            user_data["experience"] = []
        
        # Get education
        try:
            edu_response = client.table("user_education").select("*").eq(
                "user_id", user_id
            ).order("end_year", desc=True).execute()
            user_data["education"] = edu_response.data or []
        except Exception as e:
            logger.debug("Could not fetch user_education", error=str(e))
            user_data["education"] = []
        
        # Get specialties
        user_data["specialties"] = get_user_specialties(user_id, environment=environment)
        
        # Try to get certifications if table exists
        try:
            cert_response = client.table("user_certifications").select("*").eq(
                "user_id", user_id
            ).execute()
            user_data["certifications"] = cert_response.data or []
        except Exception:
            # Table might not exist
            user_data["certifications"] = []
        
        # Try to get publications if table exists
        try:
            pub_response = client.table("user_publications").select("*").eq(
                "user_id", user_id
            ).execute()
            user_data["publications"] = pub_response.data or []
        except Exception:
            user_data["publications"] = []
        
        # Try to get languages if table exists
        try:
            lang_response = client.table("user_languages").select("*").eq(
                "user_id", user_id
            ).execute()
            user_data["languages"] = lang_response.data or []
        except Exception:
            user_data["languages"] = []
        
        return user_data
        
    except Exception as e:
        logger.error("Error fetching user profile data", user_id=user_id, error=str(e))
        return None

def get_resume_text_for_user(user_id: str, environment: str = None) -> Optional[str]:
    """
    Get resume text for a user from various sources.
    
    Priority:
    1. extracted_resume field in user_profile
    2. Reconstruct from user data tables
    """
    try:
        # Get all user data
        user_data = get_user_profile_data(user_id, environment=environment)
        if not user_data:
            return None
        
        profile = user_data.get("profile", {})
        
        # First check if we have extracted_resume
        if profile.get("extracted_resume"):
            return profile["extracted_resume"]
        
        # Otherwise, build a comprehensive resume from all data
        resume_parts = []
        
        # Personal Information
        resume_parts.append("=== PERSONAL INFORMATION ===")
        if profile.get("first_name") or profile.get("last_name"):
            name = f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip()
            resume_parts.append(f"Name: {name}")
        
        if profile.get("title"):
            resume_parts.append(f"Title: {profile['title']}")
        
        if profile.get("position"):
            resume_parts.append(f"Current Position: {profile['position']}")
        
        if profile.get("city") or profile.get("country"):
            location = f"{profile.get('city', '')}, {profile.get('country', '')}".strip(", ")
            resume_parts.append(f"Location: {location}")
        
        if profile.get("phone"):
            resume_parts.append(f"Phone: {profile['phone']}")
        
        # About/Summary
        if profile.get("about_me"):
            resume_parts.append(f"\n=== PROFESSIONAL SUMMARY ===\n{profile['about_me']}")
        
        # Medical Specialties
        if user_data.get("specialties"):
            resume_parts.append("\n=== MEDICAL SPECIALTIES ===")
            for spec in user_data["specialties"]:
                resume_parts.append(f"- {spec.get('name', 'Specialty')} (Code: {spec.get('id_rosetta', 'N/A')})")
        
        # Experience
        if user_data.get("experience"):
            resume_parts.append("\n=== PROFESSIONAL EXPERIENCE ===")
            for exp in user_data["experience"]:
                exp_parts = []
                exp_parts.append(f"\n{exp.get('position', 'Position')} at {exp.get('organization', 'Organization')}")
                
                # Date range
                if exp.get('start_date'):
                    end_date = exp.get('end_date', 'Present')
                    exp_parts.append(f"Duration: {exp['start_date']} - {end_date}")
                
                # Location
                if exp.get('city') or exp.get('country'):
                    exp_location = f"{exp.get('city', '')}, {exp.get('country', '')}".strip(", ")
                    exp_parts.append(f"Location: {exp_location}")
                
                # Specialty for this role
                if exp.get('specialty'):
                    exp_parts.append(f"Specialty: {exp['specialty']}")
                
                # Add any description or responsibilities if available
                if exp.get('description'):
                    exp_parts.append(f"Description: {exp['description']}")
                
                resume_parts.extend(exp_parts)
        
        # Education
        if user_data.get("education"):
            resume_parts.append("\n=== EDUCATION ===")
            for edu in user_data["education"]:
                edu_text = f"\n{edu.get('degree', 'Degree')} from {edu.get('organization', 'Institution')}"
                if edu.get('start_year'):
                    edu_text += f" ({edu['start_year']} - {edu.get('end_year', 'N/A')})"
                if edu.get('city') or edu.get('country'):
                    edu_location = f"{edu.get('city', '')}, {edu.get('country', '')}".strip(", ")
                    edu_text += f"\nLocation: {edu_location}"
                resume_parts.append(edu_text)
        
        # Certifications
        if user_data.get("certifications"):
            resume_parts.append("\n=== CERTIFICATIONS ===")
            for cert in user_data["certifications"]:
                cert_text = f"\n- {cert.get('certifications', cert.get('name', 'Certification'))}"
                if cert.get('cert_issuer') or cert.get('issuer'):
                    cert_text += f" by {cert.get('cert_issuer', cert.get('issuer'))}"
                if cert.get('issue_date'):
                    cert_text += f" (Issued: {cert['issue_date']})"
                if cert.get('country'):
                    cert_text += f" - {cert['country']}"
                resume_parts.append(cert_text)
        
        # Publications
        if user_data.get("publications"):
            resume_parts.append("\n=== PUBLICATIONS ===")
            for pub in user_data["publications"]:
                pub_text = f"\n- {pub.get('publication_title', pub.get('title', 'Publication'))}"
                if pub.get('journal'):
                    pub_text += f" in {pub['journal']}"
                if pub.get('publishing_date'):
                    pub_text += f" ({pub['publishing_date']})"
                resume_parts.append(pub_text)
        
        # Languages
        if user_data.get("languages"):
            resume_parts.append("\n=== LANGUAGES ===")
            for lang in user_data["languages"]:
                lang_text = lang.get('language', lang.get('name', 'Language'))
                if lang.get('proficiency'):
                    lang_text += f" - {lang['proficiency']}"
                resume_parts.append(f"- {lang_text}")
        
        # Additional fields from profile
        if profile.get("citizenships"):
            resume_parts.append(f"\n=== CITIZENSHIP ===\n{', '.join(profile['citizenships'])}")
        
        # Create the final resume text
        resume_text = "\n".join(resume_parts)
        
        # Also create a JSON representation for better AI processing
        json_representation = json.dumps(user_data, indent=2, default=str)
        
        # Combine both for comprehensive context
        final_text = f"{resume_text}\n\n=== STRUCTURED DATA (JSON) ===\n{json_representation}"
        
        return final_text if resume_parts else None
        
    except Exception as e:
        logger.error("Error building resume text", user_id=user_id, error=str(e))
        return None

def match_user_to_jobs_async(user_id: str, overwrite_existing: bool = False, environment: str = None):
    """
    Asynchronously match a user to all available jobs based on medical specialties.
    Only runs detailed matching if specialties match.
    
    Args:
        user_id: The ID of the user to match
        overwrite_existing: Whether to overwrite existing matches
        environment: Explicit environment (development, staging, production)
    """
    logger.info("Starting async user-to-jobs matching process", user_id=user_id)
    
    # Update user's matching status to 'processing' at the start
    update_user_matching_status(user_id, "processing", environment=environment)
    
    try:
        # Get user specialties
        user_specialties = get_user_specialties(user_id, environment=environment)
        
        if not user_specialties:
            logger.warning("User has no medical specialties, skipping", user_id=user_id)
            return
        
        logger.info("Processing user", 
                   user_id=user_id,
                   specialties=[s.get("name") for s in user_specialties])
        
        # Get user's resume text once (to avoid multiple fetches)
        resume_text = get_resume_text_for_user(user_id, environment=environment)
        if not resume_text:
            logger.warning("No resume text available for user", user_id=user_id)
            return
        
        matches_found = 0
        jobs_processed = 0
        
        # For each user specialty, find matching jobs
        for specialty in user_specialties:
            specialty_id = specialty.get("id_rosetta")
            if not specialty_id:
                continue
            
            # Fetch all jobs with this specialty
            from utils.supabase.client import fetch_jobs_by_specialty
            matching_jobs = fetch_jobs_by_specialty(specialty_id, environment=environment)
            
            logger.info(f"Found {len(matching_jobs)} jobs for specialty",
                       specialty=specialty.get("name"),
                       specialty_id=specialty_id)
            
            for job_data in matching_jobs:
                try:
                    job_id = str(job_data.get("id"))
                    if not job_id:
                        continue
                    
                    jobs_processed += 1
                    
                    # Check if match already exists
                    if not overwrite_existing and check_match_exists(user_id, job_id, environment=environment):
                        logger.debug("Match already exists, skipping", 
                                   user_id=user_id, job_id=job_id)
                        continue
                    
                    # Create Job object
                    job = Job.from_dict(job_data)
                    
                    # Run detailed AI matching
                    logger.info("Running detailed analysis for job match",
                              user_id=user_id,
                              job_id=job_id,
                              job_title=job.title)
                    
                    match_result = compute_healthcare_match_score(
                        resume_text=resume_text,
                        job_description=job.description
                    )
                    
                    if match_result:
                        score = float(match_result.get("overall_match_percentage", 0)) / 100.0
                        
                        # Store the match
                        store_match_result(
                            user_id=user_id,
                            job_id=job_id,
                            score=score,
                            details=match_result,
                            environment=environment
                        )
                        matches_found += 1
                        
                        logger.info("Match found and stored",
                                    user_id=user_id,
                                    job_id=job_id,
                                    score=score)
                    
                except Exception as e:
                    logger.error("Error processing job for user",
                               user_id=user_id,
                               job_id=job_data.get("id"),
                               error=str(e))
                    continue
        
        logger.info("User-to-jobs matching completed",
                   user_id=user_id,
                   jobs_processed=jobs_processed,
                   matches_found=matches_found)
        
        # Update user's matching status to 'finished'
        update_user_matching_status(user_id, "finished", environment=environment)
        
    except Exception as e:
        logger.error("Error in user-to-jobs matching process", 
                    user_id=user_id, 
                    error=str(e),
                    exc_info=True)
        
        # Even on error, update the status to indicate the process is finished
        update_user_matching_status(user_id, "finished", environment=environment)