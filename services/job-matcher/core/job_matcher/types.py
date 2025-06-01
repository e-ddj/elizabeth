from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Job:
    """Represents a job posting."""
    id: str
    title: str
    description: str
    requirements: List[str]  # Will extract from description if not available
    skills: List[str]  # Will extract from description if not available
    experience_years: Optional[int]
    location: Optional[str]
    salary_range: Optional[Dict[str, float]]
    company: str
    department: Optional[str]
    job_type: Optional[str]  # full-time, part-time, contract, etc.
    country: Optional[str]
    contract_type: Optional[str]
    is_remote: bool
    medical_specialty_rosetta_id: Optional[str]
    
    @classmethod
    def from_dict(cls, data: dict) -> "Job":
        """Create Job instance from dictionary."""
        # Parse salary range from min/max fields
        salary_range = None
        if data.get("min_yearly_salary") or data.get("max_yearly_salary"):
            salary_range = {
                "min": float(data.get("min_yearly_salary", 0)) if data.get("min_yearly_salary") else 0,
                "max": float(data.get("max_yearly_salary", 0)) if data.get("max_yearly_salary") else float("inf"),
                "currency": data.get("salary_currency", "USD")
            }
        
        # Determine job type from boolean fields
        job_type = "full-time"
        if data.get("part_time") == "true":
            job_type = "part-time"
        elif data.get("contract_type"):
            job_type = data.get("contract_type")
        
        # Extract requirements and skills from description if not explicitly provided
        # In a real implementation, you might want to use NLP here
        requirements = data.get("requirements", [])
        skills = data.get("skills", [])
        
        # If no explicit requirements/skills, we could extract them from description
        # For now, we'll leave them empty and let the AI matcher handle it
        
        return cls(
            id=str(data["id"]),
            title=data.get("title", ""),
            description=data.get("description", ""),
            requirements=requirements,
            skills=skills,
            experience_years=data.get("previous_experience_in_years"),
            location=data.get("location"),
            salary_range=salary_range,
            company=data.get("organization", ""),
            department=data.get("department"),
            job_type=job_type,
            country=data.get("country"),
            contract_type=data.get("contract_type"),
            is_remote=data.get("is_remote") == "true",
            medical_specialty_rosetta_id=data.get("medical_specialty_rosetta_id")
        )

@dataclass
class UserProfile:
    """Represents a user's professional profile."""
    user_id: str
    first_name: str
    last_name: str
    email: Optional[str]
    title: Optional[str]
    position: Optional[str]
    city: Optional[str]
    country: Optional[str]
    about_me: Optional[str]
    specialties: List[Dict[str, Any]]  # Medical specialties
    skills: List[str]  # Extracted from profile/resume
    experience: List[Dict[str, Any]]  # Will need to fetch separately
    education: List[Dict[str, Any]]  # Will need to fetch separately
    total_experience_years: Optional[float]
    desired_locations: Optional[List[str]]  # From user_criteria
    min_yearly_salary: Optional[int]  # From user_criteria
    max_yearly_salary: Optional[int]  # From user_criteria
    salary_currency: Optional[str]
    job_preferences: Optional[Dict[str, Any]]  # From user_criteria
    
    @property
    def name(self) -> str:
        """Get full name."""
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def current_location(self) -> Optional[str]:
        """Get current location."""
        if self.city and self.country:
            return f"{self.city}, {self.country}"
        return self.city or self.country
    
    @classmethod
    def from_dict(cls, data: dict) -> "UserProfile":
        """Create UserProfile instance from dictionary."""
        # Extract specialties
        specialties = data.get("specialties", [])
        
        # Extract skills from various sources
        skills = []
        # Could extract from title, position, specialties, etc.
        if data.get("title"):
            skills.append(data["title"])
        for specialty in specialties:
            if specialty.get("name"):
                skills.append(specialty["name"])
        
        # Note: In a real implementation, you'd fetch experience and education
        # from related tables. For now, we'll use empty lists
        experience = []
        education = []
        
        # Calculate total experience (would need actual experience data)
        total_experience_years = None
        
        # Extract preferences from user_criteria if available
        # In the actual implementation, this would come from a join
        job_preferences = {
            "full_time": data.get("full_time"),
            "part_time": data.get("part_time"),
            "night_shift": data.get("night_shift")
        }
        
        return cls(
            user_id=data.get("user_id", data.get("id", "")),
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            email=data.get("email"),
            title=data.get("title"),
            position=data.get("position"),
            city=data.get("city"),
            country=data.get("country"),
            about_me=data.get("about_me"),
            specialties=specialties,
            skills=skills,
            experience=experience,
            education=education,
            total_experience_years=total_experience_years,
            desired_locations=[data.get("city")] if data.get("city") else [],
            min_yearly_salary=data.get("min_yearly_salary"),
            max_yearly_salary=data.get("max_yearly_salary"),
            salary_currency=data.get("salary_currency", "USD"),
            job_preferences=job_preferences
        )

@dataclass
class MatchResult:
    """Represents a job-user match result."""
    user_id: str
    user_name: str
    user_email: str
    match_score: float  # 0.0 to 1.0
    match_reasons: List[str]
    skill_matches: List[str]
    experience_match: bool
    location_match: bool
    salary_match: bool
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "user_email": self.user_email,
            "match_score": self.match_score,
            "match_reasons": self.match_reasons,
            "skill_matches": self.skill_matches,
            "experience_match": self.experience_match,
            "location_match": self.location_match,
            "salary_match": self.salary_match
        }

@dataclass
class MatchingCriteria:
    """Criteria for matching jobs to users."""
    min_skill_match_ratio: float = 0.3
    experience_tolerance_years: int = 2
    location_matching_enabled: bool = True
    salary_matching_enabled: bool = True
    ai_matching_enabled: bool = True
    max_results: int = 10
    min_score_threshold: float = 0.5