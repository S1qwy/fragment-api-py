"""
Core Fragment API client implementation with request handling
"""

import requests
import logging
from typing import Dict, Any
from .exceptions import (
    AuthenticationError, NetworkError, FragmentAPIException
)
from .utils import parse_cookies, get_default_headers

logger = logging.getLogger(__name__)


class FragmentAPICore:
    """
    Core Fragment API client handling HTTP requests and authentication
    
    This class manages low-level HTTP communication with Fragment.com API,
    including session management, retry logic, and error handling.
    """

    BASE_URL = "https://fragment.com/api"
    DEFAULT_TIMEOUT = 15
    MAX_RETRIES = 3

    def __init__(self, cookies: str, hash_value: str, timeout: int = DEFAULT_TIMEOUT):
        """
        Initialize Fragment API core client
        
        Args:
            cookies: Cookie string from authenticated Fragment session in format:
                    'stel_ssid=value; stel_dt=value; stel_token=value'
                    Extract from browser DevTools -> Application -> Cookies
            hash_value: Hash value for API authentication
            timeout: Request timeout in seconds (default 15)
        
        Raises:
            AuthenticationError: If cookies or hash are invalid/empty
        
        Example:
            >>> core = FragmentAPICore(
            ...     cookies="stel_ssid=abc; stel_token=xyz",
            ...     hash_value="abc123def456"
            ... )
        """
        if not cookies or not hash_value:
            raise AuthenticationError("Cookies and hash value are required")
        
        try:
            self.cookies_dict = parse_cookies(cookies)
        except ValueError as e:
            raise AuthenticationError(f"Invalid cookies format: {e}")
        
        self.hash_value = hash_value
        self.timeout = timeout
        self.session = requests.Session()
        self._setup_session()

    def _setup_session(self) -> None:
        """
        Configure session with default headers and cookies
        
        Sets up persistent session with proper headers and authentication
        cookies for all subsequent requests to Fragment API.
        """
        self.session.headers.update(get_default_headers())
        self.session.cookies.update(self.cookies_dict)

    def _make_request(self, data: Dict[str, Any], retry_count: int = 0) -> Dict[str, Any]:
        """
        Make HTTP POST request to Fragment API with automatic retry logic
        
        This method handles network errors gracefully by automatically
        retrying failed requests up to MAX_RETRIES times with exponential backoff.
        
        Args:
            data: Request payload data dictionary
            retry_count: Current retry attempt number (used internally)
        
        Returns:
            Parsed JSON response as dictionary
        
        Raises:
            NetworkError: If request fails after all retries
            FragmentAPIException: If API returns invalid response
        
        Example:
            >>> response = core._make_request({
            ...     'method': 'searchStarsRecipient',
            ...     'query': 'username'
            ... })
        """
        params = {'hash': self.hash_value}
        
        try:
            response = self.session.post(
                self.BASE_URL,
                params=params,
                data=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.Timeout:
            if retry_count < self.MAX_RETRIES:
                logger.warning(f"Request timeout, retrying... (attempt {retry_count + 1})")
                return self._make_request(data, retry_count + 1)
            raise NetworkError("Request timeout after maximum retries")
        
        except requests.exceptions.ConnectionError as e:
            if retry_count < self.MAX_RETRIES:
                logger.warning(f"Connection error, retrying... (attempt {retry_count + 1})")
                return self._make_request(data, retry_count + 1)
            raise NetworkError(f"Connection failed: {e}")
        
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Request failed: {e}")
        
        except ValueError as e:
            raise FragmentAPIException(f"Invalid JSON response: {e}")

    def close(self) -> None:
        """
        Close session and cleanup resources
        
        Should be called when done with the client to release connections.
        """
        self.session.close()

    def __enter__(self):
        """
        Context manager entry for 'with' statement usage
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit for automatic cleanup
        """
        self.close()