import io
from typing import List, Optional, Tuple

from supabase import Client

from utils.supabase.bucket import SUPABASE_USER_FILE_BUCKET, download_file
from utils.supabase.client import create_client


def retrieve_file_from_path(
    client: Client,
    file_path: str,
) -> Optional[io.BytesIO]:
    """
    Retrieves a file from a specified path in Supabase storage.

    Args:
        client (Client): The Supabase client instance.
        file_path (str): The path to the file in the Supabase storage bucket.

    Returns:
        Optional[io.BytesIO]: A BytesIO object containing the file content, or None if the file couldn't be downloaded.

    Raises:
        FileNotFoundError: If the file cannot be found or downloaded.
        ConnectionError: If there is a connection issue with Supabase.
        Exception: For any unexpected errors that occur.
    """
    try:
        client = client or create_client(options={"admin": True})

        # remove bucket path if necessary
        file_path = file_path.replace(f"{SUPABASE_USER_FILE_BUCKET}/", "")

        # Download file
        file: Optional[io.BytesIO] = download_file(
            client=client,
            file_path=file_path,
        )

        if not file:
            raise FileNotFoundError(
                f"File at path {file_path} not found or could not be downloaded."
            )

        return file

    except ConnectionError as e:
        raise ConnectionError(f"Failed to connect to Supabase: {str(e)}")
    except FileNotFoundError as e:
        raise e  # Propagate the FileNotFoundError
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {str(e)}")


def retrieve_user_files(
    client: Client,
    user_id: str,
    file_type: Optional[str] = None,
    storage_id: Optional[str] = None,
) -> List[Tuple[io.BytesIO, str]]:
    """
    Retrieves user files based on the given user_id and optional filters for file_type and storage_id.

    Args:
        client (Client): The Supabase client instance.
        user_id (str): The ID of the user whose files are to be retrieved.
        file_type (Optional[str]): The file type filter (e.g., "CV", "Resume"). Defaults to None.
        storage_id (Optional[str]): The storage ID filter. Defaults to None.

    Returns:
        List[Tuple[io.BytesIO, str]]: A list of tuples where each contains a file's content (BytesIO) and its path (str).

    Raises:
        ConnectionError: If there is a connection issue with Supabase.
        Exception: For any unexpected errors that occur.
    """
    try:
        client = client or create_client(options={"admin": True})
        query = client.table("user_file").select("*").eq("user_id", user_id)

        if file_type:
            query = query.eq("file_type", file_type)

        if storage_id:
            query = query.eq("storage_id", storage_id)

        result = query.execute()

        files = []
        for row in result.data:
            file_path = row["url"]
            file: Optional[io.BytesIO] = retrieve_file_from_path(
                client=client,
                file_path=file_path,
            )
            if file:
                files.append((file, file_path))  # Append as (file content, file path)

        return files
    except ConnectionError as e:
        raise ConnectionError(f"Failed to connect to Supabase: {str(e)}")
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {str(e)}")
