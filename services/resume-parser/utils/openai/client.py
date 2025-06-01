import os
from openai import OpenAI


def create_client() -> OpenAI:
    org_id = os.getenv("OPENAI_ORG_ID")
    if not org_id:
        raise ValueError("OPENAI_ORG_ID must be provided.")

    project_id = os.getenv("OPENAI_PROJECT_ID")
    if not project_id:
        raise ValueError("OPENAI_PROJECT_ID must be provided.")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY must be provided.")

    client = OpenAI(
        organization=org_id,
        project=project_id,
        api_key=api_key,
    )
    return client
