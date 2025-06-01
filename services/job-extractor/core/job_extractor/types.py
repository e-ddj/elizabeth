from typing import List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class SalaryRange:
    min: Optional[float]
    max: Optional[float]
    currency: str
    display: str


@dataclass
class JobData:
    id: int
    title: str
    summary: str
    department: str
    location: str
    job_type: str
    status: str
    posted_at: str
    salary_range: Optional[SalaryRange]
    responsibilities: List[str]
    qualifications: List[str]
    perks: List[str]
    benefits_data: List[int]
    specialty: str
    organization: str
    country: str
    is_remote: bool
    visa_sponsorship: bool
    full_time: bool
    part_time: bool
    night_shift: bool