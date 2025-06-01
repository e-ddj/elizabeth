from datetime import datetime
from typing import Optional
from supabase import Client
from utils.supabase.client import create_client
from core.jobs.types import ScrapingLog


def insert_scraping_log(
    log: ScrapingLog,
    client: Optional[Client] = None,
) -> Optional[ScrapingLog]:
    client = client or create_client(options={"admin": True})
    response = (
        client.table("scraping_logs")
        .insert(
            {
                "scraper_name": log.scraper_name,
                "success": log.success,
                "nb_affected_rows": log.nb_affected_rows,
                "operation_type": log.operation_type,
                "target_entity": log.target_entity,
                "error": log.error,
            }
        )
        .execute()
    )
    return response


def get_last_successful_date_for_scraper(
    scraper_name: str,
    client: Optional[Client] = None,
) -> Optional[datetime]:
    client = client or create_client(options={"admin": True})
    response = (
        client.table("scraping_logs")
        .select("created_at")
        .eq("scraper_name", scraper_name)
        .eq("success", True)
        .order("created_at", desc=True)  # Sort by created_at in descending order
        .limit(1)  # Limit to the most recent row
        .execute()
    )

    if not response.data:
        return None

    # Extract the 'created_at' value from the first row
    date = response.data[0]["created_at"]
    return datetime.fromisoformat(date)
