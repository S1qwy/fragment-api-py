"""
Wallet management and transaction execution for Fragment API
"""

import logging
import base64
from typing import Optional
from .exceptions import WalletError, InsufficientBalanceError, TransactionError
from .models import WalletBalance
from .utils import nano_to_ton, ton_to_nano

logger = logging.getLogger(__name__)


class WalletManager:
    """
    Manages TON wallet operations including balance checking and transaction signing
    """

    TRANSFER_FEE_NANO = "1000000"

    def __init__(self, wallet_mnemonic: str, wallet_api_key: str):
        """
        Initialize wallet manager
        
        Args:
            wallet_mnemonic: 24-word mnemonic phrase
            wallet_api_key: API key from tonconsole.com
        
        Raises:
            WalletError: If wallet initialization fails
        """
        if not wallet_mnemonic or not wallet_api_key:
            raise WalletError("Wallet mnemonic and API key are required")
        
        self.wallet_mnemonic = wallet_mnemonic.split() if isinstance(wallet_mnemonic, str) else wallet_mnemonic
        self.wallet_api_key = wallet_api_key

    async def get_balance(self) -> WalletBalance:
        """
        Get current wallet balance from blockchain (async version)
        
        Returns:
            WalletBalance object with balance information
        
        Raises:
            WalletError: If balance retrieval fails
        """
        try:
            from tonutils.client import TonapiClient
            from tonutils.wallet import WalletV4R2
            import httpx
            
            client = TonapiClient(api_key=self.wallet_api_key, is_testnet=False)
            
            # from_mnemonic возвращает кортеж (wallet, mnemonics)
            wallet_tuple = WalletV4R2.from_mnemonic(client, self.wallet_mnemonic)
            
            # Извлекаем сам wallet из кортежа
            if isinstance(wallet_tuple, tuple):
                wallet = wallet_tuple[0]
            else:
                wallet = wallet_tuple
            
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
        except Exception as e:
            logger.error(f"Balance retrieval error: {e}")
            raise WalletError(f"Failed to get wallet balance: {e}")

    def get_balance_sync(self) -> WalletBalance:
        """
        Get current wallet balance synchronously
        
        Returns:
            WalletBalance object with current balance
        
        Raises:
            WalletError: If balance retrieval fails
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
        Send and sign transaction on TON blockchain (async version)
        
        Args:
            dest_address: Destination blockchain address
            amount_nano: Transaction amount in nanotons
            raw_boc: Serialized transaction body as base64 string
        
        Returns:
            Transaction hash for tracking on blockchain
        
        Raises:
            TransactionError: If transaction fails
            InsufficientBalanceError: If wallet has insufficient balance
        """
        try:
            from tonutils.client import TonapiClient
            from tonutils.wallet import WalletV4R2
            from pytoniq_core import Cell
            
            client = TonapiClient(api_key=self.wallet_api_key, is_testnet=False)
            
            # from_mnemonic возвращает кортеж (wallet, mnemonics)
            wallet_tuple = WalletV4R2.from_mnemonic(client, self.wallet_mnemonic)
            
            if isinstance(wallet_tuple, tuple):
                wallet = wallet_tuple[0]
            else:
                wallet = wallet_tuple
            
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
        except Exception as e:
            logger.error(f"Transaction error: {e}")
            raise TransactionError(f"Transaction failed: {e}")

    def send_transaction_sync(self, dest_address: str, amount_nano: str, raw_boc: str) -> str:
        """
        Send and sign transaction synchronously
        
        Args:
            dest_address: Destination blockchain address
            amount_nano: Amount in nanotons
            raw_boc: Serialized transaction body
        
        Returns:
            Transaction hash
        
        Raises:
            TransactionError: If transaction fails
            InsufficientBalanceError: If insufficient balance
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
        except (TransactionError, InsufficientBalanceError):
            raise
        except Exception as e:
            raise TransactionError(f"Failed to send transaction: {e}")