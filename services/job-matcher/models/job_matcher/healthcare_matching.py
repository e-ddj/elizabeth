import json
from typing import Dict, Optional, Any
from config.log_config import setup_logging
from utils.openai.client import create_openai_client

logger = setup_logging()

def compute_healthcare_match_score(
    resume_text: str,
    job_description: str,
    client=None
) -> Optional[Dict[str, Any]]:
    """
    Compute detailed healthcare job matching score using OpenAI.
    
    Returns a structured analysis with weighted scoring:
    - Specialty Match: 40%
    - Experience Match: 30%
    - Skills & Responsibilities: 15%
    - Education: 10%
    - Certifications: 5%
    """
    if not resume_text or not job_description:
        return None
    
    client = client or create_openai_client()
    
    system_prompt = r"""
    You are an expert in analyzing and comparing resumes with job descriptions from a healthcare recruiter's perspective. Follow these strict rules for consistency:
    
    1. **Output Format**: Always return a JSON object in the exact structure provided below. Do not include any text outside of this JSON structure.
    
    {
        "education_match": {
            "matching_education": true/false,
            "education_gaps": ["List missing qualifications, if any"],
            "score_percentage": "XX"
        },
        "specialty_match": {
            "matching_specialty": true/false,
            "specialty_mismatch": ["List mismatched specialties, if any"],
            "score_percentage": "XX"
        },
        "experience_match": {
            "years_of_experience_match": true/false,
            "nature_of_experience_match": true/false,
            "score_percentage": "XX"
        },
        "skills_responsibilities_match": {
            "matching_skills_responsibilities": ["List matched skills, if any"],
            "missing_skills_responsibilities": ["List missing skills, if any"],
            "score_percentage": "XX"
        },
        "certifications_match": {
            "meets_requirements": true/false,
            "missing_certifications": ["List missing certifications, if any"],
            "score_percentage": "XX"
        },
        "overall_match_percentage": "XX"
    }
    
    2. **Scoring System**:
    Use this weighted scoring system to calculate the "overall_match_percentage":
    - Specialty Match: 40%
    - Experience Match: 30%
    - Skills and Responsibilities Match: 15%
    - Education Match: 10%
    - Certifications Match: 5%
    The "overall_match_percentage" should return a number between 0 and 100.
    
    3. **Evaluation Rules**:
    - **Specialty Match**:
        - Mark `"matching_specialty": true` only if all primary specialties and subspecialties listed in the job post are explicitly mentioned or strongly implied in the resume.
        - Include subspecialty-related tasks or expertise as evidence for matches.
        - Use `"specialty_mismatch"` to highlight any specific specialty or subspecialty missing from the resume.
    
    - **Experience Match**:
        - `"years_of_experience_match": true` if the resume meets or exceeds the required years of experience specified in the job post.
        - `"nature_of_experience_match": true` if the candidate's past roles, responsibilities, or achievements align with the job's expected nature of work.
    
    - **Skills and Responsibilities Match**:
        - Include transferable skills and responsibilities implied by specialties or roles.
        - Do not mark responsibilities as "missing" if they are indirectly covered by the candidate's past roles or expertise.
        - Default to empty lists for `"matching_skills_responsibilities"` and `"missing_skills_responsibilities"` if no explicit match or gap exists.
    
    - **Education Match**:
        - Mark `"matching_education": true` only if all required degrees or certifications are explicitly listed in the resume.
        - Use `"education_gaps"` to identify any specific qualification or certification missing.
        - Assume default values (e.g., no missing gaps) if the job post does not list specific qualifications.
    
    - **Certifications Match**:
        - Mark `"meets_requirements": true` only if the candidate has all certifications explicitly listed as requirements.
        - Include missing certifications under `"missing_certifications"`.
        - If no certifications are listed in the job post, assume a match.
    
    4. **Validation and Consistency**:
    - Ensure deterministic outputs by strictly following scoring weights and exact evaluation rules.
    - For missing or unclear details, assume no match to avoid overestimation.
    - Use consistent phrasing for matched and unmatched items to prevent ambiguity.
    
    5. **General Rules**:
    - Adhere strictly to the provided scoring and evaluation rules.
    - Avoid inconsistencies or subjective interpretations. If something is unclear, assume it does not match.
    - Default missing elements (e.g., `"education_gaps": []`) to empty arrays for clarity.
    
    Strictly follow these rules, and return only JSON-formatted results. No explanatory text. Always calculate and return the exact match percentage based on the scoring system provided.
    """
    
    user_prompt = f"""
    Compare the following resume with the job post according to the rules provided. Always adhere to the exact scoring methodology and format described above.
    
    Resume:
    {resume_text}
    
    Job Post:
    {job_description}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,  # Low temperature for consistency
            max_tokens=4096,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Add type_of_match to indicate this is a full AI-based match
        result["type_of_match"] = "fit"
        
        logger.info("Healthcare match scoring completed", 
                   score=result.get("overall_match_percentage"))
        return result
        
    except Exception as e:
        logger.error("Error in healthcare match scoring", error=str(e))
        return None