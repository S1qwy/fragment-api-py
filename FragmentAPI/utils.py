"""
Utility functions for Fragment API library
"""

from typing import Dict
import hmac
import hashlib
import logging

logger = logging.getLogger(__name__)


def parse_cookies(cookie_string: str) -> Dict[str, str]:
    """
    Parse cookie string from HTTP headers into dictionary format
    
    The cookie string should be extracted from the 'Cookie' header when
    making authenticated requests to Fragment API. Format should be:
    'key1=value1; key2=value2; key3=value3'
    
    Args:
        cookie_string: Cookie string in 'key1=value1; key2=value2' format
    
    Returns:
        Dictionary with cookie keys and values ready for HTTP requests
    
    Raises:
        ValueError: If cookie string is empty, invalid format, or contains no valid cookies
    
    Example:
        >>> cookies = "stel_ssid=abc123; stel_dt=-180; stel_token=xyz789"
        >>> parsed = parse_cookies(cookies)
        >>> parsed['stel_ssid']
        'abc123'
    """
    if not cookie_string or not isinstance(cookie_string, str):
        raise ValueError("Cookie string must be non-empty string")
    
    cookie_dict = {}
    for cookie in cookie_string.split(';'):
        cookie = cookie.strip()
        if '=' in cookie:
            key, value = cookie.split('=', 1)
            cookie_dict[key.strip()] = value.strip()
    
    if not cookie_dict:
        raise ValueError("No valid cookies found in provided string")
    
    return cookie_dict


def validate_username(username: str) -> bool:
    """
    Validate Telegram username format according to Telegram rules
    
    Telegram usernames must be:
    - Between 5 and 32 characters
    - Contain only alphanumeric characters and underscores
    - Start with a letter (enforced by Telegram frontend, not API)
    
    Args:
        username: Username to validate (with or without @ prefix)
    
    Returns:
        True if username format is valid, False otherwise
    
    Example:
        >>> validate_username('john_doe')
        True
        >>> validate_username('@john_doe')
        True
        >>> validate_username('john')
        False
    """
    if not username or not isinstance(username, str):
        return False
    
    username = username.lstrip('@')
    
    if len(username) < 5 or len(username) > 32:
        return False
    
    if not username.replace('_', '').isalnum():
        return False
    
    return True


def validate_amount(amount: int, min_val: int = 1, max_val: int = 999999) -> bool:
    """
    Validate numeric amount within acceptable range
    
    This function checks if the provided amount is a valid number
    and falls within the specified minimum and maximum values.
    
    Args:
        amount: Amount to validate (int or float)
        min_val: Minimum allowed value (inclusive)
        max_val: Maximum allowed value (inclusive)
    
    Returns:
        True if amount is valid, False otherwise
    
    Example:
        >>> validate_amount(100, 1, 1000)
        True
        >>> validate_amount(0, 1, 1000)
        False
        >>> validate_amount(2000, 1, 1000)
        False
    """
    if not isinstance(amount, (int, float)):
        return False
    
    if amount < min_val or amount > max_val:
        return False
    
    return True


def nano_to_ton(nano: str) -> float:
    """
    Convert nanotons to TON
    
    1 TON = 1,000,000,000 nanotons (nano)
    
    Args:
        nano: Amount in nanotons as string
    
    Returns:
        Amount in TON as float
    
    Example:
        >>> nano_to_ton("1000000000")
        1.0
        >>> nano_to_ton("2500000000")
        2.5
    """
    try:
        nano_int = int(str(nano).replace(',', ''))
        return nano_int / 1e9
    except (ValueError, AttributeError):
        return 0.0


def ton_to_nano(ton: float) -> str:
    """
    Convert TON to nanotons
    
    Args:
        ton: Amount in TON
    
    Returns:
        Amount in nanotons as string
    
    Example:
        >>> ton_to_nano(1.0)
        '1000000000'
        >>> ton_to_nano(2.5)
        '2500000000'
    """
    nano = int(ton * 1e9)
    return str(nano)


def get_default_headers() -> Dict[str, str]:
    """
    Get default HTTP headers for Fragment API requests
    
    These headers mimic a real browser request to Fragment.com
    and are required for successful authentication.
    
    Returns:
        Dictionary with default HTTP headers
    
    Example:
        >>> headers = get_default_headers()
        >>> headers['origin']
        'https://fragment.com'
    """
    return {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://fragment.com',
        'referer': 'https://fragment.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest'
    }