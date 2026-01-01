from typing import Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class UserInfo:
    """
    Represents user information found on Fragment
    """
    name: str
    recipient: str
    found: bool
    avatar: str = ""

    def __repr__(self) -> str:
        return f"UserInfo(name={self.name}, recipient={self.recipient}, avatar={self.avatar})"


@dataclass
class TransactionMessage:
    """
    Represents a single transaction message with blockchain details
    """
    address: str
    amount: str
    payload: str

    def __repr__(self) -> str:
        return f"TransactionMessage(address={self.address}, amount={self.amount})"


@dataclass
class TransactionData:
    """
    Represents complete transaction data with all messages
    """
    messages: list
    req_id: Optional[str] = None

    def get_first_message(self) -> TransactionMessage:
        """
        Get the first message from transaction messages list
        
        Returns:
            TransactionMessage object with blockchain details
            
        Raises:
            ValueError: If no messages in transaction
        """
        if not self.messages:
            raise ValueError("No messages in transaction")
        msg = self.messages[0]
        return TransactionMessage(
            address=msg.get('address'),
            amount=msg.get('amount'),
            payload=msg.get('payload')
        )

    def __repr__(self) -> str:
        return f"TransactionData(messages_count={len(self.messages)})"


@dataclass
class WalletBalance:
    """
    Represents wallet balance information
    """
    balance_nano: str
    balance_ton: float
    address: str
    is_ready: bool

    def has_sufficient_balance(self, required_nano: str, fee_nano: str = "1000000") -> bool:
        """
        Check if wallet has sufficient balance for transaction
        
        Args:
            required_nano: Required amount in nanotons
            fee_nano: Transaction fee in nanotons (default 1 TON = 1,000,000,000 nano)
        
        Returns:
            True if balance is sufficient, False otherwise
        """
        total_required = int(required_nano) + int(fee_nano)
        current_balance = int(self.balance_nano)
        return current_balance >= total_required

    def __repr__(self) -> str:
        return f"WalletBalance(balance={self.balance_ton:.6f} TON, ready={self.is_ready})"


@dataclass
class PurchaseResult:
    """
    Represents the result of a purchase operation
    """
    success: bool
    transaction_hash: Optional[str] = None
    error: Optional[str] = None
    user: Optional[UserInfo] = None
    balance_checked: bool = False
    required_amount: Optional[float] = None

    def __repr__(self) -> str:
        status = "SUCCESS" if self.success else "FAILED"
        return f"PurchaseResult({status}, tx_hash={self.transaction_hash})"