"""
Wallet management and transaction execution for Fragment API

This module provides wallet operations for TON blockchain including:
- Multiple wallet version support (V3R1, V3R2, V4R2, V5R1/W5)
- Balance checking via TonAPI
- Transaction signing and sending
- Direct TON transfers with optional memo
"""

import logging
import base64
from typing import Optional, Tuple, Any, Type
from .exceptions import WalletError, InsufficientBalanceError, TransactionError, InvalidWalletVersionError
from .models import WalletBalance, TransferResult
from .utils import nano_to_ton, ton_to_nano

logger = logging.getLogger(__name__)


class WalletManager:
    """
    Manages TON wallet operations including balance checking and transaction signing
    
    Supports multiple wallet versions:
    - V3R1: Legacy wallet version
    - V3R2: Legacy wallet version  
    - V4R2: Most common wallet version (default)
    - V5R1/W5: Latest wallet version
    
    Attributes:
        wallet_mnemonic: List of mnemonic words for wallet
        wallet_api_key: TonAPI key for blockchain interactions
        wallet_version: Normalized wallet version string
    """

    TRANSFER_FEE_NANO = "1000000"
    TRANSFER_FEE_TON = 0.05
    
    SUPPORTED_VERSIONS = {
        'V3R1': 'V3R1',
        'V3R2': 'V3R2', 
        'V4R2': 'V4R2',
        'V5R1': 'V5R1',
        'W5': 'V5R1',
    }
    
    DEFAULT_VERSION = 'V4R2'

    def __init__(self, wallet_mnemonic: str, wallet_api_key: str, wallet_version: str = DEFAULT_VERSION):
        """
        Initialize wallet manager with mnemonic and API credentials
        
        Args:
            wallet_mnemonic: Space-separated mnemonic phrase or list of words
            wallet_api_key: TonAPI key for blockchain interactions
            wallet_version: Wallet version string (V3R1, V3R2, V4R2, V5R1, W5)
                           Case-insensitive, defaults to V4R2
        
        Raises:
            WalletError: If mnemonic or API key is missing
            InvalidWalletVersionError: If wallet version is not supported
        
        Example:
            >>> manager = WalletManager(
            ...     wallet_mnemonic="word1 word2 ... word24",
            ...     wallet_api_key="your-tonapi-key",
            ...     wallet_version="V4R2"
            ... )
        """
        if not wallet_mnemonic or not wallet_api_key:
            raise WalletError("Wallet mnemonic and API key are required")
        
        self.wallet_mnemonic = wallet_mnemonic.split() if isinstance(wallet_mnemonic, str) else wallet_mnemonic
        self.wallet_api_key = wallet_api_key
        self.wallet_version = self._validate_and_normalize_version(wallet_version)

    def _validate_and_normalize_version(self, version: str) -> str:
        """
        Validate and normalize wallet version string
        
        Converts version to uppercase and maps aliases (W5 -> V5R1).
        
        Args:
            version: Wallet version string (case-insensitive)
        
        Returns:
            Normalized version string (e.g., 'V4R2', 'V5R1')
        
        Raises:
            InvalidWalletVersionError: If version is not supported
        
        Example:
            >>> manager._validate_and_normalize_version('w5')
            'V5R1'
            >>> manager._validate_and_normalize_version('v4r2')
            'V4R2'
        """
        if not version or not isinstance(version, str):
            raise InvalidWalletVersionError(str(version))
        
        normalized = version.upper().strip()
        
        if normalized not in self.SUPPORTED_VERSIONS:
            raise InvalidWalletVersionError(version)
        
        return self.SUPPORTED_VERSIONS[normalized]

    def _get_wallet_class(self) -> Type:
        """
        Get the appropriate wallet class based on configured version
        
        Dynamically imports and returns the correct wallet class
        from tonutils.wallet based on self.wallet_version.
        
        Returns:
            Wallet class (WalletV3R1, WalletV3R2, WalletV4R2, or WalletV5R1)
        
        Raises:
            WalletError: If wallet class import fails
        
        Example:
            >>> cls = manager._get_wallet_class()
            >>> cls.__name__
            'WalletV4R2'
        """
        try:
            if self.wallet_version == 'V3R1':
                from tonutils.wallet import WalletV3R1
                return WalletV3R1
            elif self.wallet_version == 'V3R2':
                from tonutils.wallet import WalletV3R2
                return WalletV3R2
            elif self.wallet_version == 'V4R2':
                from tonutils.wallet import WalletV4R2
                return WalletV4R2
            elif self.wallet_version == 'V5R1':
                from tonutils.wallet import WalletV5R1
                return WalletV5R1
            else:
                raise WalletError(f"Unknown wallet version: {self.wallet_version}")
        except ImportError as e:
            raise WalletError(f"Failed to import wallet class for {self.wallet_version}: {e}")

    def _create_wallet(self, client: Any) -> Any:
        """
        Create wallet instance from mnemonic using appropriate version
        
        Args:
            client: TonapiClient instance for blockchain interaction
        
        Returns:
            Wallet instance of the configured version
        
        Raises:
            WalletError: If wallet creation fails
        
        Example:
            >>> wallet = manager._create_wallet(client)
            >>> wallet.address.to_str()
            'EQ...'
        """
        try:
            wallet_class = self._get_wallet_class()
            wallet_tuple = wallet_class.from_mnemonic(client, self.wallet_mnemonic)
            
            if isinstance(wallet_tuple, tuple):
                return wallet_tuple[0]
            return wallet_tuple
        except Exception as e:
            raise WalletError(f"Failed to create wallet: {e}")

    async def get_balance(self) -> WalletBalance:
        """
        Get current wallet balance from blockchain
        
        Fetches wallet balance using TonAPI. Creates wallet instance
        to derive address, then queries balance via HTTP API.
        
        Returns:
            WalletBalance with balance_nano, balance_ton, address, and is_ready
        
        Raises:
            WalletError: If balance retrieval fails
        
        Example:
            >>> balance = await manager.get_balance()
            >>> print(f"Balance: {balance.balance_ton} TON")
            Balance: 1.5 TON
        """
        try:
            from tonutils.client import TonapiClient
            import httpx
            
            client = TonapiClient(api_key=self.wallet_api_key, is_testnet=False)
            wallet = self._create_wallet(client)
            address = wallet.address.to_str(is_user_friendly=True)
            
            async with httpx.AsyncClient() as http_client:
                response = await http_client.get(
                    f"https://tonapi.io/v2/accounts/{address}",
                    headers={"Authorization": f"Bearer {self.wallet_api_key}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    balance_nano = data.get("balance", "0")
                else:
                    balance_nano = "0"
            
            balance_ton = nano_to_ton(str(balance_nano))
            
            return WalletBalance(
                balance_nano=str(balance_nano),
                balance_ton=balance_ton,
                address=address,
                is_ready=True
            )
        except WalletError:
            raise
        except Exception as e:
            logger.error(f"Balance retrieval error: {e}")
            raise WalletError(f"Failed to get wallet balance: {e}")

    def get_balance_sync(self) -> WalletBalance:
        """
        Synchronous wrapper for get_balance()
        
        Creates new event loop to run async get_balance method.
        
        Returns:
            WalletBalance with current wallet state
        
        Raises:
            WalletError: If balance retrieval fails
        
        Example:
            >>> balance = manager.get_balance_sync()
            >>> print(f"Balance: {balance.balance_ton} TON")
        """
        import asyncio
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            balance = loop.run_until_complete(self.get_balance())
            loop.close()
            return balance
        except Exception as e:
            raise WalletError(f"Failed to get wallet balance: {e}")

    async def send_transaction(self, dest_address: str, amount_nano: str, raw_boc: str) -> str:
        """
        Send transaction with BOC payload to destination address
        
        Used for Fragment API purchases (stars, premium, TON topup).
        Validates balance before sending.
        
        Args:
            dest_address: Destination wallet address
            amount_nano: Amount to send in nanotons
            raw_boc: Base64-encoded BOC payload from Fragment API
        
        Returns:
            Transaction hash string
        
        Raises:
            InsufficientBalanceError: If wallet has insufficient funds
            TransactionError: If transaction fails
        
        Example:
            >>> tx_hash = await manager.send_transaction(
            ...     dest_address="EQ...",
            ...     amount_nano="1000000000",
            ...     raw_boc="te6cc..."
            ... )
        """
        try:
            from tonutils.client import TonapiClient
            from pytoniq_core import Cell
            
            client = TonapiClient(api_key=self.wallet_api_key, is_testnet=False)
            wallet = self._create_wallet(client)
            
            current_balance = await self.get_balance()
            total_required = int(amount_nano) + int(self.TRANSFER_FEE_NANO)
            
            if int(current_balance.balance_nano) < total_required:
                required_ton = nano_to_ton(str(total_required))
                raise InsufficientBalanceError(
                    f"Insufficient balance. Required: {required_ton:.6f} TON, "
                    f"Available: {current_balance.balance_ton:.6f} TON"
                )
            
            amount_ton = nano_to_ton(amount_nano)
            
            missing_padding = len(raw_boc) % 4
            if missing_padding != 0:
                raw_boc = raw_boc + '=' * (4 - missing_padding)
            
            boc_bytes = base64.b64decode(raw_boc)
            cell = Cell.one_from_boc(boc_bytes)
            
            tx_hash = await wallet.transfer(
                destination=dest_address,
                amount=amount_ton,
                body=cell
            )
            
            logger.info(f"Transaction sent: {tx_hash}")
            return tx_hash
        
        except InsufficientBalanceError:
            raise
        except WalletError:
            raise
        except Exception as e:
            logger.error(f"Transaction error: {e}")
            raise TransactionError(f"Transaction failed: {e}")

    def send_transaction_sync(self, dest_address: str, amount_nano: str, raw_boc: str) -> str:
        """
        Synchronous wrapper for send_transaction()
        
        Args:
            dest_address: Destination wallet address
            amount_nano: Amount in nanotons
            raw_boc: Base64-encoded BOC payload
        
        Returns:
            Transaction hash string
        
        Raises:
            InsufficientBalanceError: If insufficient funds
            TransactionError: If transaction fails
        """
        import asyncio
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            tx_hash = loop.run_until_complete(
                self.send_transaction(dest_address, amount_nano, raw_boc)
            )
            loop.close()
            return tx_hash
        except (TransactionError, InsufficientBalanceError, WalletError):
            raise
        except Exception as e:
            raise TransactionError(f"Failed to send transaction: {e}")

    async def transfer_ton(self, to_address: str, amount_ton: float, memo: Optional[str] = None) -> TransferResult:
        """
        Transfer TON directly to another wallet address
        
        Performs simple TON transfer with optional text memo.
        Validates address and balance before sending.
        
        Args:
            to_address: Destination wallet address
            amount_ton: Amount to transfer in TON
            memo: Optional text message to include with transfer
        
        Returns:
            TransferResult with transaction details and status
        
        Raises:
            WalletError: If address is invalid or amount <= 0
            InsufficientBalanceError: If insufficient funds
            TransactionError: If transfer fails
        
        Example:
            >>> result = await manager.transfer_ton(
            ...     to_address="EQ...",
            ...     amount_ton=1.5,
            ...     memo="Payment for services"
            ... )
            >>> print(f"TX: {result.transaction_hash}")
        """
        try:
            from tonutils.client import TonapiClient
            from pytoniq_core import begin_cell
            
            if not to_address or not isinstance(to_address, str):
                raise WalletError("Invalid destination address")
            
            if amount_ton <= 0:
                raise WalletError("Amount must be greater than 0")
            
            client = TonapiClient(api_key=self.wallet_api_key, is_testnet=False)
            wallet = self._create_wallet(client)
            sender_address = wallet.address.to_str(is_user_friendly=True)
            
            current_balance = await self.get_balance()
            required = amount_ton + self.TRANSFER_FEE_TON
            
            if current_balance.balance_ton < required:
                raise InsufficientBalanceError(
                    f"Insufficient balance. Required: ~{required:.4f} TON (including fee), "
                    f"Available: {current_balance.balance_ton:.4f} TON"
                )
            
            body = None
            if memo:
                body = (
                    begin_cell()
                    .store_uint(0, 32)
                    .store_snake_string(memo)
                    .end_cell()
                )
            
            tx_hash = await wallet.transfer(
                destination=to_address,
                amount=amount_ton,
                body=body
            )
            
            logger.info(f"TON transfer sent: {tx_hash}")
            
            return TransferResult(
                success=True,
                transaction_hash=tx_hash,
                from_address=sender_address,
                to_address=to_address,
                amount_ton=amount_ton,
                balance_before=current_balance.balance_ton,
                memo=memo
            )
        
        except InsufficientBalanceError:
            raise
        except WalletError:
            raise
        except Exception as e:
            logger.error(f"TON transfer error: {e}")
            raise TransactionError(f"TON transfer failed: {e}")

    def transfer_ton_sync(self, to_address: str, amount_ton: float, memo: Optional[str] = None) -> TransferResult:
        """
        Synchronous wrapper for transfer_ton()
        
        Args:
            to_address: Destination wallet address
            amount_ton: Amount to transfer in TON
            memo: Optional text message
        
        Returns:
            TransferResult with transaction status
        
        Raises:
            WalletError: If validation fails
            InsufficientBalanceError: If insufficient funds
            TransactionError: If transfer fails
        """
        import asyncio
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.transfer_ton(to_address, amount_ton, memo)
            )
            loop.close()
            return result
        except (TransactionError, InsufficientBalanceError, WalletError):
            raise
        except Exception as e:
            raise TransactionError(f"Failed to transfer TON: {e}")
    
    def get_wallet_info(self) -> dict:
        """
        Get information about configured wallet
        
        Returns:
            Dictionary with wallet version and supported versions info
        
        Example:
            >>> info = manager.get_wallet_info()
            >>> print(f"Version: {info['version']}")
            Version: V4R2
        """
        return {
            'version': self.wallet_version,
            'supported_versions': list(self.SUPPORTED_VERSIONS.keys()),
            'version_mapping': self.SUPPORTED_VERSIONS.copy()
        }
