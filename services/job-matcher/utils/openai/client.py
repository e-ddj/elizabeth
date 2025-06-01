import os
from openai import OpenAI
from config.log_config import setup_logging

logger = setup_logging()

def create_openai_client() -> OpenAI:
    """Create and return an OpenAI client instance."""
    api_key = os.getenv("OPENAI_API_KEY")
    org_id = os.getenv("OPENAI_ORG_ID")
    project_id = os.getenv("OPENAI_PROJECT_ID")
    
    if not api_key:
        raise ValueError("OPENAI_API_KEY must be set")
    
    client_kwargs = {"api_key": api_key}
    
    if org_id:
        client_kwargs["organization"] = org_id
    
    if project_id:
        client_kwargs["project"] = project_id
    
    return OpenAI(**client_kwargs)