from datetime import datetime

from core.user_profile.types import Benefit, MedicalSpecialty, UserCriteria


def get_user_criteria(supabase_client, user_id: str) -> UserCriteria:
    # Query user_criteria
    criteria_response = (
        supabase_client.table("user_criteria")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )
    if not criteria_response.data:
        raise Exception(
            f"Error fetching user criteria: {criteria_response.get('error')}"
        )

    criteria_data = criteria_response.data[0]

    # Query user_specialty
    specialties_response = (
        supabase_client.table("user_specialty")
        .select("""
            medical_specialty_rosetta (
                id, id_rosetta, name, created_at
            )
        """)
        .eq("user_id", user_id)  # Make sure the filter is on the correct field
        .execute()
    )

    specialties_data = specialties_response.data or []
    specialties = [
        MedicalSpecialty(
            id=specialty["medical_specialty_rosetta"]["id"],
            id_rosetta=specialty["medical_specialty_rosetta"]["id_rosetta"],
            name=specialty["medical_specialty_rosetta"]["name"],
            created_at=datetime.fromisoformat(
                specialty["medical_specialty_rosetta"]["created_at"]
            ),
        )
        for specialty in specialties_data
    ]

    # Query user_desired_benefits
    benefits_response = (
        supabase_client.table("user_desired_benefits")
        .select("""
            job_benefit (id, name)
        """)
        .eq("user_id", user_id)
        .execute()
    )
    benefits_data = benefits_response.data or []
    benefits = [
        Benefit(id=benefit["job_benefit"]["id"], name=benefit["job_benefit"]["name"])
        for benefit in benefits_data
    ]

    # Build UserCriteria instance
    return UserCriteria(
        locations=criteria_data["locations"],
        location_insights=criteria_data["location_insights"],
        max_yearly_salary=criteria_data.get("max_yearly_salary"),
        min_yearly_salary=criteria_data.get("min_yearly_salary"),
        salary_currency=criteria_data.get("salary_currency"),
        full_time=criteria_data.get("full_time"),
        night_shift=criteria_data.get("night_shift"),
        part_time=criteria_data.get("part_time"),
        benefits=benefits,
        specialties=specialties,
    )
