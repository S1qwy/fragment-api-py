from enum import Enum
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
import json
import os

class FragmentErrorType(Enum):
    AUTH_KEY_EXPIRED = "AUTH_KEY_EXPIRED"
    INVALID_WALLET_TYPE = "INVALID_WALLET_TYPE"
    INVALID_ORDER_PRODUCT_TYPE = "INVALID_ORDER_PRODUCT_TYPE"
    ORDER_ALREADY_PROCESSED = "ORDER_ALREADY_PROCESSED"
    ORDER_ALREADY_PROCESSING = "ORDER_ALREADY_PROCESSING"
    INVALID_ORDER_COST = "INVALID_ORDER_COST"
    INVALID_PREMIUM_DURATION = "INVALID_PREMIUM_DURATION"
    INSUFFICIENT_BALANCE = "INSUFFICIENT_BALANCE"
    ORDER_EXPIRED = "ORDER_EXPIRED"
    INVALID_USERNAME_FORMAT = "INVALID_USERNAME_FORMAT"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    AUTH_KEY_NOT_FOUND = "AUTH_KEY_NOT_FOUND"
    ORDER_NOT_FOUND = "ORDER_NOT_FOUND"
    MISSING_FRAGMENT_COOKIES = "MISSING_FRAGMENT_COOKIES"
    MISSING_SEED = "MISSING_SEED"
    INVALID_SEED_FORMAT = "INVALID_SEED_FORMAT"
    INVALID_FRAGMENT_COOKIES = "INVALID_FRAGMENT_COOKIES"
    USER_ALREADY_HAS_PREMIUM = "USER_ALREADY_HAS_PREMIUM"
    SEARCH_ERROR = "SEARCH_ERROR"
    BALANCE_CHECK_ERROR = "BALANCE_CHECK_ERROR"
    TRANSFER_FAILED = "TRANSFER_FAILED"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"

@dataclass
class FragmentAPIError(Exception):
    error_type: FragmentErrorType
    message: str
    status_code: int
    details: Optional[Dict[str, Any]] = None

    def __str__(self):
        return f"[{self.status_code}] {self.error_type.value}: {self.message}"

@dataclass
class FragmentSession:
    auth_key: str
    fragment_cookies: str
    wallet_type: str = "v4r2"
    last_balance: Optional[float] = None

    def save_to_file(self, filename: str = "fragment_session.json"):
        with open(filename, 'w') as f:
            json.dump(asdict(self), f)

    @classmethod
    def load_from_file(cls, filename: str = "fragment_session.json"):
        if not os.path.exists(filename):
            return None
        
        with open(filename, 'r') as f:
            data = json.load(f)
            return cls(**data)
