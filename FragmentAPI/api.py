from typing import Optional, Dict, Any
from .models import FragmentSession, FragmentAPIError
from .utils import make_request, handle_api_error
from .exceptions import FragmentAuthError, FragmentOrderError, FragmentPaymentError
import os

class FragmentAPI:
    def __init__(self, api_url: str = "https://fragment-api.net"):
        if not isinstance(api_url, str) or not api_url.startswith(('http://', 'https://')):
            api_url = f'https://{api_url}'
        self.api_url = api_url.rstrip('/') + '/'
        self.session = None
        
    def _make_request(self, method: str, endpoint: str, 
                    params: Optional[dict] = None, 
                    json_data: Optional[dict] = None) -> Dict[str, Any]:
        return make_request(self.api_url, method, endpoint, params, json_data)
        
    def save_session(self, filename: str = "fragment_session.json"):
        if self.session:
            self.session.save_to_file(filename)

    def load_session(self, filename: str = "fragment_session.json"):
        self.session = FragmentSession.load_from_file(filename)
        return self.session

    def auth(self) -> 'FragmentAuth':
        return FragmentAuth(self)
        
    def general(self) -> 'FragmentGeneral':
        return FragmentGeneral(self)
        
    def premium(self) -> 'FragmentPremium':
        return FragmentPremium(self)
        
    def stars(self) -> 'FragmentStars':
        return FragmentStars(self)
        
    def ton(self) -> 'FragmentTON':
        return FragmentTON(self)

class FragmentAuth:
    def __init__(self, api: FragmentAPI):
        self.api = api
        
    def create_auth_key(self, fragment_cookies: str, seed: str) -> FragmentSession:
        data = {
            "fragment_cookies": fragment_cookies,
            "seed": seed
        }
        
        try:
            response = self.api._make_request("POST", "/v2/auth", json_data=data)
            
            if not response.get("success"):
                raise FragmentAuthError(
                    FragmentErrorType.INVALID_FRAGMENT_COOKIES,
                    "Failed to create auth key",
                    400,
                    response
                )
            
            # Создаем и сохраняем сессию
            self.api.session = FragmentSession(
                auth_key=response["auth_key"],
                fragment_cookies=fragment_cookies
            )
            
            return self.api.session
            
        except FragmentAPIError as e:
            if "Invalid fragment_cookies" in str(e):
                e = FragmentAuthError(
                    FragmentErrorType.INVALID_FRAGMENT_COOKIES,
                    str(e),
                    e.status_code,
                    e.details
                )
            raise e

class FragmentGeneral:
    def __init__(self, api: FragmentAPI):
        self.api = api
    
    def ping(self) -> dict:
        return self.api._make_request("GET", "/v2/ping")
    
    def get_balance(self, auth_key: Optional[str] = None) -> dict:
        """
        Получить баланс кошелька
        """
        if auth_key is None:
            if not self.api.session or not self.api.session.auth_key:
                raise FragmentAuthError(
                    FragmentErrorType.AUTH_KEY_NOT_FOUND,
                    "No auth key provided and no active session",
                    401
                )
            auth_key = self.api.session.auth_key
            wallet_type = self.api.session.wallet_type
        else:
            wallet_type = "v4r2"
        
        params = {
            "auth_key": auth_key,
            "wallet_type": wallet_type
        }
        
        response = self.api._make_request("GET", "/v2/getBalance", params=params)
        
        # Обновляем баланс в сессии
        if self.api.session and response.get("success"):
            self.api.session.last_balance = response.get("balance")
            
        return response
    
    def get_user_info(self, username: str, auth_key: Optional[str] = None) -> dict:
        if auth_key is None:
            if not self.api.session or not self.api.session.auth_key:
                raise FragmentAuthError(
                    FragmentErrorType.AUTH_KEY_NOT_FOUND,
                    "No auth key provided and no active session",
                    401
                )
            auth_key = self.api.session.auth_key
        
        params = {
            "username": username,
            "auth_key": auth_key
        }
        return self.api._make_request("GET", "/v2/getUserInfo", params=params)
    
    def get_orders(self, auth_key: Optional[str] = None, limit: int = 10, offset: int = 0) -> dict:
        if auth_key is None:
            if not self.api.session or not self.api.session.auth_key:
                raise FragmentAuthError(
                    FragmentErrorType.AUTH_KEY_NOT_FOUND,
                    "No auth key provided and no active session",
                    401
                )
            auth_key = self.api.session.auth_key
        
        params = {
            "auth_key": auth_key,
            "limit": limit,
            "offset": offset
        }
        return self.api._make_request("GET", "/v2/getOrders", params=params)

class FragmentPremium:
    def __init__(self, api: FragmentAPI):
        self.api = api
        
    def create_premium_order(self, username: str, duration: int, 
                           auth_key: Optional[str] = None,
                           show_sender: bool = False) -> dict:
        if auth_key is None:
            if not self.api.session or not self.api.session.auth_key:
                raise FragmentAuthError(
                    FragmentErrorType.AUTH_KEY_NOT_FOUND,
                    "No auth key provided and no active session",
                    401
                )
            auth_key = self.api.session.auth_key
        
        data = {
            "username": username,
            "duration": duration,
            "auth_key": auth_key,
            "show_sender": show_sender
        }
        return self.api._make_request("POST", "/v2/buyPremium/create", json_data=data)
    
    def pay_premium_order(self, order_uuid: str, cost: float,
                         auth_key: Optional[str] = None,
                         wallet_type: Optional[str] = None) -> dict:
        if auth_key is None:
            if not self.api.session or not self.api.session.auth_key:
                raise FragmentAuthError(
                    FragmentErrorType.AUTH_KEY_NOT_FOUND,
                    "No auth key provided and no active session",
                    401
                )
            auth_key = self.api.session.auth_key
            wallet_type = self.api.session.wallet_type
        
        data = {
            "order_uuid": order_uuid,
            "auth_key": auth_key,
            "cost": cost,
            "wallet_type": wallet_type or "v4r2"
        }
        return self.api._make_request("POST", "/v2/buyPremium/pay", json_data=data)
    
    def check_premium_order(self, uuid: str) -> dict:
        params = {"uuid": uuid}
        return self.api._make_request("GET", "/v2/buyPremium/check", params=params)

class FragmentStars:
    def __init__(self, api: FragmentAPI):
        self.api = api
        
    def create_stars_order(self, username: str, amount: int, 
                         auth_key: Optional[str] = None,
                         show_sender: bool = True) -> dict:
        if auth_key is None:
            if not self.api.session or not self.api.session.auth_key:
                raise FragmentAuthError(
                    FragmentErrorType.AUTH_KEY_NOT_FOUND,
                    "No auth key provided and no active session",
                    401
                )
            auth_key = self.api.session.auth_key
        
        data = {
            "username": username,
            "amount": amount,
            "auth_key": auth_key,
            "show_sender": show_sender
        }
        return self.api._make_request("POST", "/v2/buyStars/create", json_data=data)
    
    def pay_stars_order(self, order_uuid: str, cost: float,
                       auth_key: Optional[str] = None,
                       wallet_type: Optional[str] = None) -> dict:
        if auth_key is None:
            if not self.api.session or not self.api.session.auth_key:
                raise FragmentAuthError(
                    FragmentErrorType.AUTH_KEY_NOT_FOUND,
                    "No auth key provided and no active session",
                    401
                )
            auth_key = self.api.session.auth_key
            wallet_type = self.api.session.wallet_type
        
        data = {
            "order_uuid": order_uuid,
            "auth_key": auth_key,
            "cost": cost,
            "wallet_type": wallet_type or "v4r2"
        }
        return self.api._make_request("POST", "/v2/buyStars/pay", json_data=data)
    
    def check_stars_order(self, uuid: str) -> dict:
        params = {"uuid": uuid}
        return self.api._make_request("GET", "/v2/buyStars/check", params=params)

class FragmentTON:
    def __init__(self, api: FragmentAPI):
        self.api = api
        
    def create_ton_order(self, username: str, amount: int,
                       auth_key: Optional[str] = None,
                       show_sender: bool = True) -> dict:
        if auth_key is None:
            if not self.api.session or not self.api.session.auth_key:
                raise FragmentAuthError(
                    FragmentErrorType.AUTH_KEY_NOT_FOUND,
                    "No auth key provided and no active session",
                    401
                )
            auth_key = self.api.session.auth_key
        
        data = {
            "username": username,
            "amount": amount,
            "auth_key": auth_key,
            "show_sender": show_sender
        }
        return self.api._make_request("POST", "/v2/buyTon/create", json_data=data)
    
    def pay_ton_order(self, order_uuid: str, cost: float,
                     auth_key: Optional[str] = None,
                     wallet_type: Optional[str] = None) -> dict:
        if auth_key is None:
            if not self.api.session or not self.api.session.auth_key:
                raise FragmentAuthError(
                    FragmentErrorType.AUTH_KEY_NOT_FOUND,
                    "No auth key provided and no active session",
                    401
                )
            auth_key = self.api.session.auth_key
            wallet_type = self.api.session.wallet_type
        
        data = {
            "order_uuid": order_uuid,
            "auth_key": auth_key,
            "cost": cost,
            "wallet_type": wallet_type or "v4r2"
        }
        return self.api._make_request("POST", "/v2/buyTon/pay", json_data=data)
    
    def check_ton_order(self, uuid: str) -> dict:
        params = {"uuid": uuid}
        return self.api._make_request("GET", "/v2/buyTon/check", params=params)
