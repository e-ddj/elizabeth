from supabase import Client
from typing import Optional
from utils.supabase.client import create_client


def exists_candidate_job_pair(
    client: Optional[Client],
    candidate_id: str,
    job_id: int,
) -> Optional[bool]:
    """
    Check if a candidate-job pair exists in the 'match' table.

    Args:
        client (Client): The Supabase client instance.
        candidate_id (str): The UUID of the candidate.
        job_id (int): The ID of the job.

    Returns:
        Optional[bool]: True if the pair exists, False if it does not, or None in case of an error.
    """
    client = client or create_client(options={"admin": True})

    try:
        # Query the 'match' table for the candidate-job pair
        response = (
            client.table("match")
            .select("id")
            .eq("candidate_id", candidate_id)
            .eq("job_id", job_id)
            .execute()
        )

        # Return True if the pair exists, otherwise False
        return len(response.data or []) > 0

    except Exception as e:
        print(f"Error checking candidate-job pair: {str(e)}")
        return None
