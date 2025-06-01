from typing import List
from supabase import Client
from core.user_profile.types import UserData, UserEducation, UserExperience, UserProfile
from core.utils.user_experience import (
    get_user_educations_for_user,
    get_user_experience_for_user,
)
from core.utils.user_resume import retrieve_user_resume_text
from utils.supabase.client import create_client
from datetime import date
from typing import Optional


def get_user_profile_with_specialties(
    user_id: str, client: Optional[Client] = None
) -> UserProfile | None:
    client = client or create_client(options={"admin": True})

    # Combined query to fetch user profile along with specialties
    response = (
        client.table("user_profile")
        .select("*, specialties:medical_specialty_rosetta(id,id_rosetta,name)")
        .eq("user_id", user_id)
        .execute()
    )

    user_profiles = response.data
    if not user_profiles or len(user_profiles) == 0:
        return None

    # Extracting single user profile
    user_profile = user_profiles[0]

    return user_profile


def get_resume_text(user: UserData) -> str | None:
    # try first to get the resume from the column in user_profile
    resume_text = user.profile.get("extracted_resume", None)

    # if not set, try to retrieve the resume from the file bucket
    if not resume_text:
        resume_text = retrieve_user_resume_text(user_id=user.user_id, client=None)

    # if also not in bucket, probably the user did the onboarding manually
    # so rebuild a string from the various database tables
    if not resume_text:
        resume_text = build_resume_text_from_database(user_id=user.user_id, client=None)

    return resume_text


# when no resume stored in user_profile and no resume uploaded
# then rebuild a resume from all the entries in the database
def build_resume_text_from_database(
    user_id: str, client: Optional[Client] = None
) -> str:
    client = client or create_client(options={"admin": True})

    def format_date_range(start: Optional[date], end: Optional[date]) -> str:
        """Formats a date range, handling missing values gracefully."""
        if start and end:
            return f"{start} – {end}"
        elif start:
            return f"Since {start}"
        elif end:
            return f"Until {end}"
        return "N/A"

    # Retrieve data
    profile: Optional[UserProfile] = get_user_profile_with_specialties(
        client=client, user_id=user_id
    )
    experiences: List[UserExperience] = get_user_experience_for_user(
        client=client, user_id=user_id
    )
    educations: List[UserEducation] = get_user_educations_for_user(
        client=client, user_id=user_id
    )

    # Build Profile Section
    profile_string = ""
    if profile:
        profile_string = (
            f"{profile.get('first_name', '')} {profile.get('last_name', '')}\n"
        )
        if profile.get("title"):
            profile_string += f"{profile.get('title')}\n"
        if profile.get("position"):
            profile_string += f"Current Position: {profile.get('position')}\n"
        if profile.get("citizenships"):
            profile_string += (
                f"Citizenship: {', '.join(profile.get('citizenships', []))}\n"
            )
        if profile.get("city") or profile.get("country"):
            profile_string += (
                f"Location: {profile.get('city', '')}, {profile.get('country', '')}\n"
            )
        if profile.get("about_me"):
            profile_string += f"\nAbout Me:\n{profile.get('about_me')}\n"
        if profile.get("specialties"):
            profile_string += f"\nSpecialties:\n{', '.join([spe['name'] for spe in profile.get('specialties')])}\n"

    # Build Experience Section
    experiences_string = ""
    if experiences:
        experiences_string = "Work Experience:\n"
        for exp in experiences:
            experiences_string += f"- {exp.get('position', 'Unknown Position')} at {exp.get('organization', 'Unknown Organization')}"
            if exp.get("city") or exp.get("country"):
                experiences_string += (
                    f" ({exp.get('city', '')}, {exp.get('country', '')})"
                )
            experiences_string += f"\n  {format_date_range(exp.get('start_date', 'N/A'), exp.get('end_date', 'N/A'))}\n"

    # Build Education Section
    educations_string = ""
    if educations:
        educations_string = "Education:\n"
        for edu in educations:
            educations_string += f"- {edu.get('degree', 'Unknown Degree')} from {edu.get('organization', 'Unknown Institution')}"
            if edu.get("city") or edu.get("country"):
                educations_string += (
                    f" ({edu.get('city', '')}, {edu.get('country', '')})"
                )
            educations_string += (
                f"\n  {edu.get('start_year', 'N/A')} – {edu.get('end_year', 'N/A')}\n"
            )

    # Combine all sections
    final_string = "\n".join(
        filter(None, [profile_string, experiences_string, educations_string])
    )

    return final_string
