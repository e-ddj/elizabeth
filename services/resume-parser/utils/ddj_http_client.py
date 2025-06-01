from typing import Optional, Any, TypedDict
import os
import requests
from requests.exceptions import RequestException


class Response(TypedDict, total=False):
    success: Optional[bool]
    data: Optional[Any]
    error: Optional[str]


def post_request(endpoint: str, data: Optional[Any] = None) -> Response:
    """
    Makes a POST request to the specified endpoint with JSON data.

    Args:
        endpoint (str): The endpoint path to send the POST request to.
        data (dict, optional): The JSON data to send in the request body. Defaults to an empty dict.

    Returns:
        Response: A dictionary containing the status, data, or error information.
    """
    base_url = os.getenv("AI_SERVICES_HOST")

    # Handle the case where the environment variable is missing
    if not base_url:
        return {
            "success": False,
            "error": "API base URL is not set in the environment variable 'AI_SERVICES_HOST'.",
        }

    url = f"{base_url}{endpoint}"
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, headers=headers, json=data or {})
        response.raise_for_status()  # Raise an error for 4XX/5XX responses
        return {"success": True, "data": response.json()}

    except ValueError as e:
        # Handle any ValueError if it occurs within the try block
        return {"success": False, "error": f"ValueError occurred: {str(e)}"}

    except RequestException as e:
        # Return error information for request failures
        return {"success": False, "error": f"RequestException occurred: {str(e)}"}
