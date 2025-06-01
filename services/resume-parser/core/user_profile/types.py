import datetime
from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID


@dataclass
class Benefit:
    id: int
    name: str


@dataclass
class MedicalSpecialty:
    id: int
    id_rosetta: str
    name: str
    created_at: datetime


@dataclass
class UserExperience:
    position: Optional[str] = None
    specialty: Optional[str] = None
    rosetta_id: Optional[int] = None
    organization: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    start_date: Optional[datetime.date] = None
    end_date: Optional[datetime.date] = None


@dataclass
class UserEducation:
    degree: Optional[str] = None
    organization: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None


@dataclass
class UserProfile:
    first_name: str
    last_name: str
    # email: str
    title: Optional[str] = None
    position: Optional[str] = None
    citizenships: Optional[List[str]] = None
    street: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    about_me: Optional[str] = None
    specialties: Optional[List[MedicalSpecialty]] = None
    extracted_resume: Optional[str] = None
    verified: bool = False


@dataclass
class UserPublications:
    publication_title: Optional[str] = None
    journal: Optional[str] = None
    publishing_date: Optional[str] = None


@dataclass
class UserLanguages:
    language: Optional[str] = None


@dataclass
class UserCertifications:
    certifications: Optional[str] = None
    cert_issuer: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    issue_date: Optional[str] = None


@dataclass
class UserCriteria:
    locations: List[str]
    location_insights: List[str]
    max_yearly_salary: Optional[int] = None
    min_yearly_salary: Optional[int] = None
    salary_currency: Optional[str] = None
    full_time: Optional[bool] = None
    night_shift: Optional[bool] = None
    part_time: Optional[bool] = None
    benefits: Optional[List[Benefit]] = None
    specialties: Optional[List[MedicalSpecialty]] = None


@dataclass
class UserData:
    profile: UserProfile
    user_id: Optional[UUID] = None
    publications: Optional[List[UserPublications]] = None
    languages: Optional[List[UserLanguages]] = None
    certifications: Optional[List[UserCertifications]] = None
    educations: Optional[List[UserEducation]] = None
    experiences: Optional[List[UserExperience]] = None
    criteria: Optional[UserCriteria] = None
