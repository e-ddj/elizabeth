from typing import List, Optional
from supabase import Client

from core.user_profile.types import UserEducation, UserExperience
from utils.supabase.client import create_client


def get_user_experience_for_user(
    user_id: str, client: Optional[Client] = None
) -> List[UserExperience]:
    client = client or create_client(options={"admin": True})

    # Combined query to fetch user profile along with specialties
    response = (
        client.table("user_experience").select("*").eq("user_id", user_id).execute()
    )

    experiences = response.data
    if not experiences or len(experiences) == 0:
        return []

    return experiences


def get_user_educations_for_user(
    user_id: str, client: Optional[Client] = None
) -> List[UserEducation]:
    client = client or create_client(options={"admin": True})

    # Combined query to fetch user profile along with specialties
    response = (
        client.table("user_education").select("*").eq("user_id", user_id).execute()
    )

    educations = response.data
    if not educations or len(educations) == 0:
        return []

    return educations
