from typing import List, Optional
from supabase import Client
from utils.supabase.client import create_client
from core.jobs.types import Job, JobStatus
from core.user_profile.types import MedicalSpecialty


def get_jobs(
    client: Optional[Client],
    job_ids: Optional[List[int]] = None,
) -> List[Job]:
    """
    Fetch job records from the "job" table in Supabase.

    Args:
        client (Client): The Supabase client instance used to connect to the database.
        job_ids (Optional[List[int]]): A list of job IDs to fetch. If None, fetch all live jobs.

    Returns:
        Union[Dict[str, Any], str]: The result of the query as a dictionary on success,
                                    or an error message string if the query fails.

    Raises:
        ValueError: If the client instance is not provided.
    """
    client = client or create_client(options={"admin": True})

    try:
        # Base query to fetch jobs
        query = (
            client.table("job")
            .select(
                "id",
                "created_at",
                "title",
                "medical_specialty_rosetta_id",
                "description",
                "url",
                # "description_reworked",
                # "description_condensed",
                "min_yearly_salary",
                "max_yearly_salary",
                # "contract_length_in_years",
                # "previous_experience_in_years",
                # "night_shift",
                # "part_time",
                # "full_time",
            )
            .eq("status", "Live")
        )

        # Add condition if specific job IDs are provided
        if job_ids:
            query = query.in_("id", job_ids or [])

        # Execute the query
        response = query.execute()

        return response.data or []

    except Exception as e:
        # General error handling
        return f"An unexpected error occurred: {str(e)}"


def filter_jobs_for_specialties(
    jobs: List[Job], specialties: Optional[List[MedicalSpecialty]]
) -> Optional[List[Job]]:
    """
    Filters a list of Job objects based on the provided list of MedicalSpecialty objects.

    :param jobs: A list of Job objects to filter.
    :param specialties: An optional list of MedicalSpecialty objects to filter against.
    :return: A filtered list of Job objects if specialties are provided, or None if specialties is None.
    """
    if not specialties:
        return None  # Return None if no specialties are provided.

    # Extract the id_rosetta values from the specialties
    specialty_rosetta_ids = {specialty.get("id_rosetta") for specialty in specialties}

    # Filter jobs based on whether their medical_specialty_rosetta_id matches any id_rosetta
    filtered_jobs = [
        job
        for job in jobs
        if job.get("medical_specialty_rosetta_id") in specialty_rosetta_ids
    ]

    return filtered_jobs


def update_job_status(client: Client, job_id: int, status: JobStatus):
    client = client or create_client(options={"admin": True})
    response = (
        client.table("job").update({"status": status.value}).eq("id", job_id).execute()
    )
    return response


def insert_new_job(client: Client, job: Job):
    client = client or create_client(options={"admin": True})
    response = (
        client.table("job")
        .insert(
            {
                "title": job.title,
                "description": job.description,
                "description_reworked": job.description_reworked,
                "description_condensed": job.description_condensed,
                "location": job.location,
                "country": job.country,
                "organization": job.organization,
                "medical_specialty_rosetta_id": job.medical_specialty_rosetta_id,
                "min_yearly_salary": job.min_yearly_salary,
                "max_yearly_salary": job.max_yearly_salary,
                "salary_currency": job.salary_currency,
                "status": job.status,
                "recruiter_id": job.recruiter_id,
                "posted_at": job.posted_at,
                "url": job.url,
            }
        )
        .execute()
    )
    return response
