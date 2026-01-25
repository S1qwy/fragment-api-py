"""
Synchronous Fragment API client for Telegram payments

Provides synchronous interface for:
- Purchasing Telegram Stars
- Gifting Telegram Premium subscriptions
- Topping up TON for Telegram Ads
- Direct TON transfers
"""

import logging
import re
from typing import Dict, Any, Optional
from .core import FragmentAPICore
from .wallet import WalletManager
from .exceptions import (
    UserNotFoundError, InvalidAmountError, PaymentInitiationError,
    TransactionError, NetworkError, FragmentAPIException,
    InsufficientBalanceError, AuthenticationError, WalletError, InvalidWalletVersionError
)
from .models import UserInfo, PurchaseResult, TransferResult
from .utils import validate_username, validate_amount, nano_to_ton

logger = logging.getLogger(__name__)


class SyncFragmentAPI(FragmentAPICore):
    """
    Synchronous client for Fragment.com API with TON wallet integration
    
    Provides blocking synchronous interface for all Fragment API operations.
    Inherits from FragmentAPICore for HTTP request handling.
    Supports multiple wallet versions.
    
    Attributes:
        wallet: WalletManager instance for blockchain operations
    
    Example:
        >>> with SyncFragmentAPI(
        ...     cookies="...",
        ...     hash_value="...",
        ...     wallet_mnemonic="...",
        ...     wallet_api_key="...",
        ...     wallet_version="V4R2"
        ... ) as api:
        ...     result = api.buy_stars("username", 100)
    """
    
    TRANSFER_FEE_TON = 0.001

    def __init__(self, cookies: str, hash_value: str, wallet_mnemonic: str, 
                 wallet_api_key: str, wallet_version: str = "V4R2",
                 timeout: int = 15):
        """
        Initialize synchronous Fragment API client
        
        Args:
            cookies: Cookie string from authenticated Fragment session
            hash_value: Hash value for API authentication
            wallet_mnemonic: Space-separated mnemonic phrase for TON wallet
            wallet_api_key: TonAPI key for blockchain interactions
            wallet_version: Wallet version (V3R1, V3R2, V4R2, V5R1, W5)
                           Case-insensitive, defaults to V4R2
            timeout: Request timeout in seconds
        
        Raises:
            AuthenticationError: If credentials are invalid
            InvalidWalletVersionError: If wallet version is not supported
        
        Example:
            >>> api = SyncFragmentAPI(
            ...     cookies="stel_ssid=...; stel_token=...",
            ...     hash_value="abc123",
            ...     wallet_mnemonic="word1 word2 ... word24",
            ...     wallet_api_key="your-api-key",
            ...     wallet_version="V4R2"
            ... )
        """
        super().__init__(cookies, hash_value, timeout)
        self.wallet = WalletManager(wallet_mnemonic, wallet_api_key, wallet_version)

    @staticmethod
    def _extract_avatar_url(photo_html: str) -> str:
        """
        Extract avatar URL from HTML photo element
        
        Args:
            photo_html: HTML string containing img tag
        
        Returns:
            Extracted URL or empty string if not found
        """
        if not photo_html:
            return ""
        
        match = re.search(r'src=["\']([^"\']+)["\']', photo_html)
        if match:
            src_value = match.group(1)
            if src_value.startswith('data:image'):
                return src_value
            return src_value
        
        return ""

    def _check_user(self, username: str, method: str) -> UserInfo:
        """
        Check if user exists and get recipient info
        
        Args:
            username: Telegram username to check
            method: API method for user search
        
        Returns:
            UserInfo with user details
        
        Raises:
            UserNotFoundError: If user not found
            NetworkError: If request fails
            AuthenticationError: If session expired
        """
        if not validate_username(username):
            raise UserNotFoundError(f"Invalid username format: {username}")
        
        try:
            result = self._make_request({
                'query': username,
                'method': method,
                'quantity': '' if 'Stars' in method else '3'
            })
        except Exception as e:
            raise NetworkError(f"Failed to check user: {e}")
        
        if 'error' in result:
            error_msg = result.get('error', 'Unknown error')
            if isinstance(error_msg, dict):
                error_msg = error_msg.get('error', 'Unknown error')
            
            if error_msg == 'No Telegram users found.':
                raise UserNotFoundError(f"User {username} not found: no Telegram users found")
            elif error_msg == 'Session expired':
                raise AuthenticationError("Session expired: please update cookies")
            else:
                raise UserNotFoundError(f"User {username} not found: {error_msg}")
        
        found_data = result.get('found', {})
        if not found_data or not found_data.get('recipient'):
            raise UserNotFoundError(f"User {username} not found")
        
        photo_html = found_data.get('photo', '')
        avatar = self._extract_avatar_url(photo_html)
        
        return UserInfo(
            name=found_data.get('name', username),
            recipient=found_data.get('recipient'),
            found=True,
            avatar=avatar
        )

    def get_recipient_stars(self, username: str) -> UserInfo:
        """
        Get recipient info for Telegram Stars purchase
        
        Args:
            username: Telegram username
        
        Returns:
            UserInfo with recipient details
        
        Raises:
            UserNotFoundError: If user not found
            AuthenticationError: If session expired
        """
        if not validate_username(username):
            raise UserNotFoundError(f"Invalid username format: {username}")
        
        try:
            result = self._make_request({
                'query': username,
                'method': 'searchStarsRecipient',
                'quantity': ''
            })
        except Exception as e:
            raise NetworkError(f"Failed to get stars recipient: {e}")
        
        if 'error' in result:
            error_msg = result.get('error', 'Unknown error')
            if isinstance(error_msg, dict):
                error_msg = error_msg.get('error', 'Unknown error')
            
            if error_msg == 'No Telegram users found.':
                raise UserNotFoundError(f"Stars recipient {username} not found: no Telegram users found")
            elif error_msg == 'Session expired':
                raise AuthenticationError("Session expired: please update cookies")
            else:
                raise UserNotFoundError(f"Stars recipient {username} not found: {error_msg}")
        
        found_data = result.get('found', {})
        if not found_data or not found_data.get('recipient'):
            raise UserNotFoundError(f"Stars recipient {username} not found")
        
        photo_html = found_data.get('photo', '')
        avatar = self._extract_avatar_url(photo_html)
        
        return UserInfo(
            name=found_data.get('name', username),
            recipient=found_data.get('recipient'),
            found=True,
            avatar=avatar
        )

    def get_recipient_premium(self, username: str) -> UserInfo:
        """
        Get recipient info for Telegram Premium gift
        
        Args:
            username: Telegram username
        
        Returns:
            UserInfo with recipient details
        
        Raises:
            UserNotFoundError: If user not found or already has Premium
            AuthenticationError: If session expired
        """
        if not validate_username(username):
            raise UserNotFoundError(f"Invalid username format: {username}")
        
        try:
            result = self._make_request({
                'query': username,
                'method': 'searchPremiumGiftRecipient',
                'months': '3'
            })
        except Exception as e:
            raise NetworkError(f"Failed to get premium recipient: {e}")
        
        if 'error' in result:
            error_msg = result.get('error', 'Unknown error')
            if isinstance(error_msg, dict):
                error_msg = error_msg.get('error', 'Unknown error')
            
            if error_msg == 'No Telegram users found.':
                raise UserNotFoundError(f"Premium recipient {username} not found: no Telegram users found")
            elif error_msg == 'Session expired':
                raise AuthenticationError("Session expired: please update cookies")
            elif "This account is already subscribed to Telegram Premium" in error_msg:
                raise UserNotFoundError(f"Premium recipient {username} already subscribed to Premium")
            elif "can't gift" in error_msg:
                raise UserNotFoundError(f"Premium recipient {username}: cannot gift premium to this user")
            else:
                raise UserNotFoundError(f"Premium recipient {username} not found: {error_msg}")
        
        found_data = result.get('found', {})
        if not found_data or not found_data.get('recipient'):
            raise UserNotFoundError(f"Premium recipient {username} not found")
        
        photo_html = found_data.get('photo', '')
        avatar = self._extract_avatar_url(photo_html)
        
        return UserInfo(
            name=found_data.get('name', username),
            recipient=found_data.get('recipient'),
            found=True,
            avatar=avatar
        )

    def get_recipient_ton(self, username: str) -> UserInfo:
        """
        Get recipient info for TON Ads topup
        
        Args:
            username: Telegram username/channel
        
        Returns:
            UserInfo with recipient details
        
        Raises:
            UserNotFoundError: If user not found
            AuthenticationError: If session expired
        """
        if not validate_username(username):
            raise UserNotFoundError(f"Invalid username format: {username}")
        
        try:
            result = self._make_request({
                'query': username,
                'method': 'searchAdsTopupRecipient'
            })
        except Exception as e:
            raise NetworkError(f"Failed to get TON recipient: {e}")
        
        if 'error' in result:
            error_msg = result.get('error', 'Unknown error')
            if isinstance(error_msg, dict):
                error_msg = error_msg.get('error', 'Unknown error')
            
            if error_msg == 'No Telegram users found.':
                raise UserNotFoundError(f"TON recipient {username} not found: no Telegram users found")
            elif error_msg == 'Session expired':
                raise AuthenticationError("Session expired: please update cookies")
            else:
                raise UserNotFoundError(f"TON recipient {username} not found: {error_msg}")
        
        found_data = result.get('found', {})
        if not found_data or not found_data.get('recipient'):
            raise UserNotFoundError(f"TON recipient {username} not found")
        
        photo_html = found_data.get('photo', '')
        avatar = self._extract_avatar_url(photo_html)
        
        return UserInfo(
            name=found_data.get('name', username),
            recipient=found_data.get('recipient'),
            found=True,
            avatar=avatar
        )

    def buy_stars(self, username: str, quantity: int, show_sender: bool = False) -> PurchaseResult:
        """
        Purchase Telegram Stars for a user
        
        Args:
            username: Recipient's Telegram username
            quantity: Number of stars to purchase (1-999999)
            show_sender: Whether to show sender info to recipient
        
        Returns:
            PurchaseResult with transaction status and details
        
        Example:
            >>> result = api.buy_stars("username", 100)
            >>> if result.success:
            ...     print(f"TX: {result.transaction_hash}")
        """
        if not validate_amount(quantity, 1, 999999):
            raise InvalidAmountError(f"Invalid quantity: {quantity}")
        
        try:
            user = self._check_user(username, 'searchStarsRecipient')
            
            init = self._make_request({
                'recipient': user.recipient,
                'quantity': quantity,
                'method': 'initBuyStarsRequest'
            })
            
            if 'error' in init:
                raise PaymentInitiationError(init.get('error'))
            
            req_id = init.get('req_id')
            buy_response = self._make_request({
                'transaction': '1',
                'id': req_id,
                'show_sender': '1' if show_sender else '0',
                'method': 'getBuyStarsLink'
            })
            
            if 'error' in buy_response:
                raise TransactionError(buy_response.get('error'))
            
            transaction = buy_response.get('transaction', {})
            messages = transaction.get('messages', [{}])
            
            dest_address = messages[0].get('address')
            amount_nano = messages[0].get('amount')
            raw_boc = messages[0].get('payload')
            
            wallet_balance = self.wallet.get_balance_sync()
            required_amount = nano_to_ton(amount_nano)
            total_with_fee = required_amount + self.TRANSFER_FEE_TON
            
            if not wallet_balance.has_sufficient_balance(amount_nano):
                raise InsufficientBalanceError(
                    f"Insufficient balance. Required: {total_with_fee:.6f} TON, "
                    f"Available: {wallet_balance.balance_ton:.6f} TON"
                )
            
            tx_hash = self.wallet.send_transaction_sync(dest_address, amount_nano, raw_boc)
            
            return PurchaseResult(
                success=True,
                transaction_hash=tx_hash,
                user=user,
                balance_checked=True,
                required_amount=total_with_fee
            )
        
        except (UserNotFoundError, InvalidAmountError, InsufficientBalanceError,
                PaymentInitiationError, TransactionError) as e:
            return PurchaseResult(
                success=False,
                error=str(e),
                user=None,
                balance_checked=False
            )
        except Exception as e:
            logger.error(f"Error buying stars: {e}")
            return PurchaseResult(
                success=False,
                error=str(e),
                user=None,
                balance_checked=False
            )

    def gift_premium(self, username: str, months: int = 3, show_sender: bool = False) -> PurchaseResult:
        """
        Gift Telegram Premium subscription to a user
        
        Args:
            username: Recipient's Telegram username
            months: Subscription duration (3, 6, or 12 months)
            show_sender: Whether to show sender info to recipient
        
        Returns:
            PurchaseResult with transaction status and details
        
        Raises:
            InvalidAmountError: If months is not 3, 6, or 12
        
        Example:
            >>> result = api.gift_premium("username", months=3)
            >>> if result.success:
            ...     print(f"Premium gifted! TX: {result.transaction_hash}")
        """
        if months not in [3, 6, 12]:
            raise InvalidAmountError(f"Invalid months: {months}. Must be 3, 6, or 12")
        
        try:
            user = self._check_user(username, 'searchPremiumGiftRecipient')
            
            init = self._make_request({
                'recipient': user.recipient,
                'months': months,
                'method': 'initGiftPremiumRequest'
            })
            
            if 'error' in init:
                raise PaymentInitiationError(init.get('error'))
            
            req_id = init.get('req_id')
            buy_response = self._make_request({
                'transaction': '1',
                'id': req_id,
                'show_sender': '1' if show_sender else '0',
                'method': 'getGiftPremiumLink'
            })
            
            if 'error' in buy_response:
                raise TransactionError(buy_response.get('error'))
            
            transaction = buy_response.get('transaction', {})
            messages = transaction.get('messages', [{}])
            
            dest_address = messages[0].get('address')
            amount_nano = messages[0].get('amount')
            raw_boc = messages[0].get('payload')
            
            wallet_balance = self.wallet.get_balance_sync()
            required_amount = nano_to_ton(amount_nano)
            total_with_fee = required_amount + self.TRANSFER_FEE_TON
            
            if not wallet_balance.has_sufficient_balance(amount_nano):
                raise InsufficientBalanceError(
                    f"Insufficient balance. Required: {total_with_fee:.6f} TON, "
                    f"Available: {wallet_balance.balance_ton:.6f} TON"
                )
            
            tx_hash = self.wallet.send_transaction_sync(dest_address, amount_nano, raw_boc)
            
            return PurchaseResult(
                success=True,
                transaction_hash=tx_hash,
                user=user,
                balance_checked=True,
                required_amount=total_with_fee
            )
        
        except (UserNotFoundError, InvalidAmountError, InsufficientBalanceError,
                PaymentInitiationError, TransactionError) as e:
            return PurchaseResult(
                success=False,
                error=str(e),
                user=None,
                balance_checked=False
            )
        except Exception as e:
            logger.error(f"Error gifting premium: {e}")
            return PurchaseResult(
                success=False,
                error=str(e),
                user=None,
                balance_checked=False
            )

    def topup_ton(self, username: str, amount: int, show_sender: bool = False) -> PurchaseResult:
        """
        Top up TON for Telegram Ads
        
        Args:
            username: Recipient's Telegram username/channel
            amount: Amount in TON to top up (1-999999)
            show_sender: Whether to show sender info
        
        Returns:
            PurchaseResult with transaction status and details
        
        Example:
            >>> result = api.topup_ton("channel_name", 10)
            >>> if result.success:
            ...     print(f"Topped up! TX: {result.transaction_hash}")
        """
        if not validate_amount(amount, 1, 999999):
            raise InvalidAmountError(f"Invalid amount: {amount}")
        
        try:
            user = self._check_user(username, 'searchAdsTopupRecipient')
            
            init = self._make_request({
                'recipient': user.recipient,
                'amount': str(amount),
                'method': 'initAdsTopupRequest'
            })
            
            if 'error' in init:
                raise PaymentInitiationError(init.get('error'))
            
            req_id = init.get('req_id')
            buy_response = self._make_request({
                'transaction': '1',
                'id': req_id,
                'show_sender': '1' if show_sender else '0',
                'method': 'getAdsTopupLink'
            })
            
            if 'error' in buy_response:
                raise TransactionError(buy_response.get('error'))
            
            transaction = buy_response.get('transaction', {})
            messages = transaction.get('messages', [{}])
            
            dest_address = messages[0].get('address')
            amount_nano = messages[0].get('amount')
            raw_boc = messages[0].get('payload')
            
            wallet_balance = self.wallet.get_balance_sync()
            required_amount = nano_to_ton(amount_nano)
            total_with_fee = required_amount + self.TRANSFER_FEE_TON
            
            if not wallet_balance.has_sufficient_balance(amount_nano):
                raise InsufficientBalanceError(
                    f"Insufficient balance. Required: {total_with_fee:.6f} TON, "
                    f"Available: {wallet_balance.balance_ton:.6f} TON"
                )
            
            tx_hash = self.wallet.send_transaction_sync(dest_address, amount_nano, raw_boc)
            
            return PurchaseResult(
                success=True,
                transaction_hash=tx_hash,
                user=user,
                balance_checked=True,
                required_amount=total_with_fee
            )
        
        except (UserNotFoundError, InvalidAmountError, InsufficientBalanceError,
                PaymentInitiationError, TransactionError) as e:
            return PurchaseResult(
                success=False,
                error=str(e),
                user=None,
                balance_checked=False
            )
        except Exception as e:
            logger.error(f"Error topping up TON: {e}")
            return PurchaseResult(
                success=False,
                error=str(e),
                user=None,
                balance_checked=False
            )

    def transfer_ton(self, to_address: str, amount_ton: float, memo: Optional[str] = None) -> TransferResult:
        """
        Transfer TON directly to another wallet
        
        Args:
            to_address: Destination wallet address
            amount_ton: Amount to transfer in TON
            memo: Optional text message for transfer
        
        Returns:
            TransferResult with transaction status and details
        
        Example:
            >>> result = api.transfer_ton("EQ...", 1.5, memo="Payment")
            >>> if result.success:
            ...     print(f"Sent! TX: {result.transaction_hash}")
        """
        try:
            return self.wallet.transfer_ton_sync(to_address, amount_ton, memo)
        except (InsufficientBalanceError, WalletError, TransactionError) as e:
            return TransferResult(
                success=False,
                error=str(e),
                to_address=to_address,
                amount_ton=amount_ton,
                memo=memo
            )
        except Exception as e:
            logger.error(f"Error transferring TON: {e}")
            return TransferResult(
                success=False,
                error=str(e),
                to_address=to_address,
                amount_ton=amount_ton,
                memo=memo
            )

    def get_wallet_balance(self) -> Dict[str, Any]:
        """
        Get current wallet balance and info
        
        Returns:
            Dictionary with balance_ton, balance_nano, address,
            is_ready, and wallet_version
        
        Example:
            >>> balance = api.get_wallet_balance()
            >>> print(f"Balance: {balance['balance_ton']} TON")
        """
        try:
            balance = self.wallet.get_balance_sync()
            return {
                'balance_ton': balance.balance_ton,
                'balance_nano': balance.balance_nano,
                'address': balance.address,
                'is_ready': balance.is_ready,
                'wallet_version': self.wallet.wallet_version
            }
        except Exception as e:
            logger.error(f"Failed to get wallet balance: {e}")
            raise
