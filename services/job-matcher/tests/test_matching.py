import pytest
from core.job_matcher.types import Job, UserProfile, MatchingCriteria
from core.job_matcher.match_job_to_users import (
    match_skills, match_experience, match_location, 
    match_salary, calculate_base_score, match_user_to_job
)

def test_match_skills():
    """Test skill matching logic."""
    required = ["Python", "Django", "PostgreSQL"]
    user_skills = ["python", "DJANGO", "MySQL", "PostgreSQL"]
    
    matches = match_skills(required, user_skills)
    assert len(matches) == 3
    assert "Python" in matches
    assert "Django" in matches
    assert "PostgreSQL" in matches

def test_match_skills_partial():
    """Test partial skill matching."""
    required = ["React", "TypeScript", "Node.js"]
    user_skills = ["React", "JavaScript"]
    
    matches = match_skills(required, user_skills)
    assert len(matches) == 1
    assert "React" in matches

def test_match_experience():
    """Test experience matching with tolerance."""
    # Exact match
    assert match_experience(5, 5.0, 2) == True
    
    # Within tolerance
    assert match_experience(5, 4.0, 2) == True
    assert match_experience(5, 3.0, 2) == True
    
    # Outside tolerance
    assert match_experience(5, 2.0, 2) == False
    
    # No requirement
    assert match_experience(None, 10.0, 2) == True
    assert match_experience(5, None, 2) == True

def test_match_location():
    """Test location matching logic."""
    # Current location match
    assert match_location("New York", "New York, NY", []) == True
    
    # Desired location match
    assert match_location("San Francisco", "Boston", ["San Francisco", "Seattle"]) == True
    
    # No match
    assert match_location("Chicago", "Miami", ["Los Angeles", "Austin"]) == False
    
    # No job location (remote)
    assert match_location(None, "Anywhere", []) == True

def test_match_salary():
    """Test salary matching logic."""
    # Within range
    job_range = {"min": 80000, "max": 120000}
    assert match_salary(job_range, 100000) == True
    assert match_salary(job_range, 80000) == True
    assert match_salary(job_range, 120000) == True
    
    # With 10% flexibility
    assert match_salary(job_range, 72000) == True  # 80k * 0.9
    assert match_salary(job_range, 132000) == True  # 120k * 1.1
    
    # Outside range
    assert match_salary(job_range, 60000) == False
    assert match_salary(job_range, 150000) == False
    
    # No data
    assert match_salary({}, 100000) == True
    assert match_salary(job_range, None) == True

def test_calculate_base_score():
    """Test base score calculation."""
    # Perfect match
    score = calculate_base_score(
        skill_match_ratio=1.0,
        experience_match=True,
        location_match=True,
        salary_match=True
    )
    assert score == 1.0
    
    # Partial match
    score = calculate_base_score(
        skill_match_ratio=0.5,
        experience_match=True,
        location_match=False,
        salary_match=True
    )
    assert 0.5 < score < 0.8
    
    # Poor match
    score = calculate_base_score(
        skill_match_ratio=0.2,
        experience_match=False,
        location_match=False,
        salary_match=False
    )
    assert score < 0.5

def test_match_user_to_job():
    """Test complete user-job matching."""
    job = Job(
        id="job-123",
        title="Senior Python Developer",
        description="Build scalable web applications",
        requirements=["5+ years experience", "Strong Python skills"],
        skills=["Python", "Django", "PostgreSQL", "Docker"],
        experience_years=5,
        location="New York",
        salary_range={"min": 120000, "max": 180000},
        company="Tech Corp",
        department="Engineering",
        job_type="full-time"
    )
    
    user = UserProfile(
        id="user-456",
        name="Jane Doe",
        email="jane@example.com",
        skills=["Python", "Django", "MySQL", "Docker", "AWS"],
        experience=[
            {"title": "Python Developer", "years": 3},
            {"title": "Senior Developer", "years": 2}
        ],
        education=[{"degree": "BS Computer Science"}],
        total_experience_years=5,
        current_location="New York, NY",
        desired_locations=["New York", "Remote"],
        desired_salary=150000,
        job_preferences={"remote": True, "full_time": True}
    )
    
    criteria = MatchingCriteria(ai_matching_enabled=False)  # Disable AI for testing
    
    result = match_user_to_job(job, user, criteria)
    
    assert result is not None
    assert result.user_id == "user-456"
    assert result.match_score > 0.7  # Good match
    assert len(result.skill_matches) >= 3
    assert result.experience_match == True
    assert result.location_match == True
    assert result.salary_match == True

def test_match_user_below_threshold():
    """Test user that doesn't meet minimum threshold."""
    job = Job(
        id="job-123",
        title="Senior React Developer",
        description="Frontend development",
        requirements=["React expert"],
        skills=["React", "TypeScript", "Next.js", "GraphQL"],
        experience_years=5,
        location="San Francisco",
        salary_range={"min": 150000, "max": 200000},
        company="Tech Corp",
        department="Engineering",
        job_type="full-time"
    )
    
    user = UserProfile(
        id="user-789",
        name="John Smith",
        email="john@example.com",
        skills=["Python", "Django", "Flask"],  # No matching skills
        experience=[{"title": "Backend Developer", "years": 2}],
        education=[],
        total_experience_years=2,
        current_location="Miami, FL",
        desired_locations=["Miami"],
        desired_salary=80000,
        job_preferences={}
    )
    
    criteria = MatchingCriteria(
        min_skill_match_ratio=0.3,
        ai_matching_enabled=False
    )
    
    result = match_user_to_job(job, user, criteria)
    assert result is None  # Below skill threshold