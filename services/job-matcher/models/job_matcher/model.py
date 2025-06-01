import os
import json
from typing import Tuple, List
from config.log_config import setup_logging
from core.job_matcher.types import Job, UserProfile
from utils.openai.client import create_openai_client

logger = setup_logging()

def get_ai_match_score(job: Job, user: UserProfile) -> Tuple[float, List[str]]:
    """
    Use AI to evaluate job-user match quality.
    
    Args:
        job: Job to match
        user: User profile to evaluate
        
    Returns:
        Tuple of (score between 0-1, list of reasons)
    """
    try:
        client = create_openai_client()
        model = os.getenv("OPENAI_MATCHER_MODEL", "gpt-4o-mini")
        
        # Prepare job summary
        job_summary = {
            "title": job.title,
            "description": job.description,
            "requirements": job.requirements,
            "skills": job.skills,
            "experience_years": job.experience_years,
            "location": job.location,
            "company": job.company,
            "department": job.department
        }
        
        # Prepare user summary
        user_summary = {
            "name": user.name,
            "skills": user.skills,
            "total_experience_years": user.total_experience_years,
            "current_location": user.current_location,
            "desired_locations": user.desired_locations,
            "recent_experience": user.experience[:3] if user.experience else [],
            "education": user.education[:2] if user.education else [],
            "job_preferences": user.job_preferences
        }
        
        prompt = create_matching_prompt(job_summary, user_summary)
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        score = float(result.get("match_score", 0))
        reasons = result.get("match_reasons", [])
        
        logger.info("AI matching completed", 
                   job_title=job.title,
                   user_name=user.name,
                   ai_score=score)
        
        return score, reasons
        
    except Exception as e:
        logger.error("Error in AI matching", error=str(e))
        # Return neutral score on error
        return 0.5, ["AI analysis unavailable"]

def create_matching_prompt(job_summary: dict, user_summary: dict) -> str:
    """Create prompt for AI matching evaluation."""
    return f"""Evaluate how well this candidate matches the job opening.

JOB OPENING:
{json.dumps(job_summary, indent=2)}

CANDIDATE PROFILE:
{json.dumps(user_summary, indent=2)}

Analyze the match considering:
1. Skill alignment and technical competencies
2. Experience relevance and career progression
3. Location compatibility
4. Role and company fit
5. Potential for growth and success

Provide a JSON response with:
- match_score: float between 0.0 (no match) and 1.0 (perfect match)
- match_reasons: list of 2-4 specific reasons explaining the match quality
- Focus on concrete factors from the data provided
"""

SYSTEM_PROMPT = """You are an expert job matching AI assistant. Your role is to evaluate how well a candidate's profile matches a job opening based on skills, experience, location preferences, and overall fit.

Provide objective, data-driven assessments focusing on:
- Direct skill matches and transferable skills
- Relevant experience and career trajectory
- Geographic preferences and constraints
- Cultural and role fit indicators

Return structured JSON responses with match scores and specific reasons.
Be fair and unbiased in your assessments, considering both strengths and potential gaps."""