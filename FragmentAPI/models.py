from typing import Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class UserInfo:
    name: str
    recipient: str
    found: bool
    avatar: str = ""

    def __repr__(self) -> str:
        return f"UserInfo(name={self.name}, recipient={self.recipient}, avatar={self.avatar})"


@dataclass
class TransactionMessage:
    address: str
    amount: str
    payload: str

    def __repr__(self) -> str:
        return f"TransactionMessage(address={self.address}, amount={self.amount})"


@dataclass
class TransactionData:
    messages: list
    req_id: Optional[str] = None

    def get_first_message(self) -> TransactionMessage:
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
    balance_nano: str
    balance_ton: float
    address: str
    is_ready: bool

    def has_sufficient_balance(self, required_nano: str, fee_nano: str = "1000000") -> bool:
        total_required = int(required_nano) + int(fee_nano)
        current_balance = int(self.balance_nano)
        return current_balance >= total_required

    def __repr__(self) -> str:
        return f"WalletBalance(balance={self.balance_ton:.6f} TON, ready={self.is_ready})"


@dataclass
class PurchaseResult:
    success: bool
    transaction_hash: Optional[str] = None
    error: Optional[str] = None
    user: Optional[UserInfo] = None
    balance_checked: bool = False
    required_amount: Optional[float] = None

    def __repr__(self) -> str:
        status = "SUCCESS" if self.success else "FAILED"
        return f"PurchaseResult({status}, tx_hash={self.transaction_hash})"


@dataclass
class TransferResult:
    success: bool
    transaction_hash: Optional[str] = None
    from_address: Optional[str] = None
    to_address: Optional[str] = None
    amount_ton: Optional[float] = None
    balance_before: Optional[float] = None
    memo: Optional[str] = None
    error: Optional[str] = None

    def __repr__(self) -> str:
        status = "SUCCESS" if self.success else "FAILED"
        memo_str = f", memo={self.memo}" if self.memo else ""
        return f"TransferResult({status}, amount={self.amount_ton} TON{memo_str}, tx_hash={self.transaction_hash})"
