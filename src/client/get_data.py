import requests
from typing import Optional, Dict, Any, Union

from src.client.Auth import Auth


def gd_requests(
    auth: Auth,
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, str]] = None,
    body: Optional[Union[str, Dict[str, Any]]] = None,
    debug_api: bool = False,
) -> requests.Response:
    """Wrapper around requests.request that handles authentication and common parameters.

    Args:
        method (str): HTTP method (GET, POST, etc.)
        url (str): The URL to make the request to
        auth (Dict[str, str]): Authentication credentials
        headers (Optional[Dict[str, str]]): Request headers
        params (Optional[Dict[str, str]]): Query parameters
        body (Optional[Union[str, Dict[str, Any]]]): Request body

    Returns:
        requests.Response: The response from the request
    """
    # Merge auth headers with provided headers

    headers = {**headers, **auth.generate_auth_headers()}
    # Prepare request data
    data = body if isinstance(body, str) else None
    json_data = body if isinstance(body, dict) else None

    if debug_api:
        print(f"🚀 Making {method} request to {url}")
        print(f"Headers: {headers}")
        print(f"Params: {params}")
        print(f"Data: {data}")
        print(f"JSON: {json_data}")

    return requests.request(
        method=method,
        url=url,
        headers=headers,
        params=params,
        data=data,
        json=json_data,
    )


def normalize_json_to_python(json_str: str) -> str:
    """Convert JSON-style boolean and null values to Python syntax (True, False, None).

    Args:
        json_str (str): JSON string that might contain 'true', 'false', or 'null'

    Returns:
        str: String with Python-style boolean and None values
    """
    if not json_str:
        return json_str

    # Replace JSON booleans with Python booleans
    # Use word boundaries to ensure we only replace complete words
    result = json_str
    result = result.replace("true", "True")
    result = result.replace("false", "False")
    result = result.replace("null", "None")

    return result
