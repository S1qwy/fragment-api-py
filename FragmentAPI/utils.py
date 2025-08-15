from urllib.parse import urljoin
from typing import Dict, Optional, Any
import requests
from .models import FragmentAPIError, FragmentErrorType

def make_request(api_url: str, method: str, endpoint: str, 
               params: Optional[dict] = None, 
               json_data: Optional[dict] = None) -> Dict[str, Any]:
    url = urljoin(api_url, endpoint.lstrip('/'))
    
    try:
        response = requests.request(
            method, 
            url, 
            params=params, 
            json=json_data,
            timeout=30
        )
        
        if not response.ok:
            handle_api_error(response)
            
        return response.json()
        
    except requests.exceptions.RequestException as e:
        raise FragmentAPIError(
            FragmentErrorType.INTERNAL_SERVER_ERROR,
            f"Network error: {str(e)}",
            500
        ) from e

def handle_api_error(response: requests.Response):
    try:
        error_data = response.json()
        error_code = error_data.get("error_code")
        message = error_data.get("message", "Unknown error")
        
        try:
            error_type = FragmentErrorType(error_code)
        except ValueError:
            error_type = FragmentErrorType.INTERNAL_SERVER_ERROR
        
        raise FragmentAPIError(
            error_type,
            message,
            response.status_code,
            error_data
        )
        
    except ValueError:
        raise FragmentAPIError(
            FragmentErrorType.INTERNAL_SERVER_ERROR,
            f"HTTP {response.status_code}: {response.text}",
            response.status_code
        )
