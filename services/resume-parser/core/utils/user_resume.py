import io
from typing import List, Optional

from supabase import Client
from core.utils.user_file import retrieve_file_from_path, retrieve_user_files
from utils.files.doc_converters import extract_text_from_document, extract_text_from_pdf
from utils.supabase.client import create_client


def retrieve_resume_file(
    client: Optional[Client],
    file_path: str,
) -> Optional[io.BytesIO]:
    """
    Retrieves the resume file from the specified path.

    Args:
        client (Client): The Supabase client instance.
        file_path (str): The path to the resume file in Supabase storage.

    Returns:
        Optional[io.BytesIO]: A BytesIO object containing the resume file content, or None if the file cannot be found.
    """
    client = client or create_client(options={"admin": True})
    return retrieve_file_from_path(
        client=client,
        file_path=file_path,
    )


def retrieve_resume_as_text(
    client: Optional[Client],
    file_path: str,
) -> Optional[str]:
    """
    Retrieves the resume file from the specified path and extracts text from it.

    Args:
        file_path (str): The path to the resume file in Supabase storage.

    Returns:
        Optional[str]: The extracted text from the resume, or None if text extraction fails.

    Raises:
        ValueError: If the text extraction fails due to corrupt or unsupported file formats.
        FileNotFoundError: If the file cannot be found.
        Exception: For any unexpected errors during file retrieval or text extraction.
    """
    try:
        client = client or create_client(options={"admin": True})

        # Download file
        file = retrieve_resume_file(file_path=file_path, client=client)

        # Extract text
        resume_text = extract_text_from_pdf(file)

        if not resume_text:
            raise ValueError(
                "Failed to extract text from the CV. The file may be corrupt or in an unsupported format."
            )

        return resume_text

    except ValueError as e:
        raise e  # Propagate the ValueError for extraction issues
    except FileNotFoundError as e:
        raise e  # Propagate the FileNotFoundError for file retrieval issues
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {str(e)}")
    finally:
        # Ensure that the file object is closed after use, to free up resources
        if file:
            if isinstance(file, io.BytesIO):
                file.close()


def retrieve_user_resume_text(
    client: Client,
    user_id: str,
) -> Optional[str]:
    """
    Retrieves and extracts text from a user's resume file.

    Args:
        client (Client): The Supabase client instance.
        user_id (str): The ID of the user whose resume is to be retrieved.

    Returns:
        Optional[str]: The extracted text from the user's resume.

    Raises:
        Exception: For any unexpected errors that occur during the retrieval and text extraction process.
    """
    client = client or create_client(options={"admin": True})

    files: List[io.BytesIO] = retrieve_user_files(
        client=client,
        user_id=user_id,
        file_type="CV",
    )

    if not files:
        raise FileNotFoundError(f"No resume found for user {user_id}.")

    # TODO maybe get the most recent one
    resume, resume_path = files[0]

    try:
        resume_text, _ = extract_text_from_document(file=resume, file_path=resume_path)
        return resume_text
    except Exception as e:
        raise Exception(f"Failed to extract text from resume: {str(e)}")
    finally:
        # Ensure the file object is closed after use
        if isinstance(resume, io.BytesIO):
            resume.close()
