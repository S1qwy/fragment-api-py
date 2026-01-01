# Fragment API Python Library

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://img.shields.io/badge/pypi-v3.0.2-blue.svg)](https://pypi.org/project/fragment-api-py/)

**[Русская версия](README_RU.md)**

Professional Python library for Fragment.com API with full Telegram payment support. Send Telegram Stars, Premium subscriptions and TON cryptocurrency with automatic wallet balance checking and error handling.

## Features

- ✅ **Async and Sync Interfaces** - Use async/await or traditional blocking calls
- ✅ **3 Products** - Telegram Stars, Premium subscriptions, and TON top-ups
- ✅ **Recipient Lookup** - Get user information and avatar before sending payment
- ✅ **Automatic Balance Checking** - Validate wallet balance before initiating transaction
- ✅ **WalletV4R2 Support** - Direct interaction with TON blockchain
- ✅ **Comprehensive Error Handling** - Specific exceptions for different error scenarios
- ✅ **Type Hints** - Full type annotations for IDE autocompletion
- ✅ **Detailed Logging** - Track API interactions and errors
- ✅ **Retry Logic** - Automatic retry on network failures
- ✅ **Sender Visibility Control** - Optional anonymous or visible payments

## Installation

### Via pip

```bash
pip install fragment-api-py
```

### From source

```bash
git clone https://github.com/S1qwy/fragment-api-py.git
cd fragment-api-py
pip install -e .
```

## Quick Start

### Synchronous Example

```python
from FragmentAPI import SyncFragmentAPI

api = SyncFragmentAPI(
    cookies="stel_ssid=value; stel_token=value; ...",
    hash_value="your_hash",
    wallet_mnemonic="abandon ability able abandon abandon abandon abandon abandon abandon abandon abandon about",
    wallet_api_key="YOUR_TONCONSOLE_API_KEY"
)

# Get recipient info with avatar
user = api.get_recipient_stars('username')
print(f"Name: {user.name}")
print(f"Avatar: {user.avatar}")

# Send Telegram Stars (anonymously)
result = api.buy_stars('username', 100)
if result.success:
    print(f"✓ Transaction: {result.transaction_hash}")
else:
    print(f"✗ Error: {result.error}")

# Send with visible sender
result = api.buy_stars('username', 100, show_sender=True)

api.close()
```

### Asynchronous Example

```python
import asyncio
from FragmentAPI import AsyncFragmentAPI

async def main():
    api = AsyncFragmentAPI(
        cookies="stel_ssid=value; stel_token=value; ...",
        hash_value="your_hash",
        wallet_mnemonic="abandon ability able abandon abandon abandon abandon abandon abandon abandon abandon about",
        wallet_api_key="YOUR_TONCONSOLE_API_KEY"
    )
    
    # Get recipient info
    user = await api.get_recipient_stars('username')
    print(f"Name: {user.name}")
    
    # Send Stars (anonymously)
    result = await api.buy_stars('username', 100)
    if result.success:
        print(f"✓ TX: {result.transaction_hash}")
    
    # Send with visible sender
    result = await api.buy_stars('username', 100, show_sender=True)
    
    await api.close()

asyncio.run(main())
```

## Setup and Configuration

### Step 1: Get Fragment Cookies

1. Open [fragment.com](https://fragment.com) in your browser
2. Press `F12` to open DevTools
3. Go to `Application` tab → `Cookies`
4. Copy the following cookies:
   - `stel_ssid`
   - `stel_token`
   - `stel_dt`
   - `stel_ton_token`

5. Combine them: `stel_ssid=value; stel_token=value; stel_dt=value; stel_ton_token=value`

### Step 2: Get Hash Value

1. Open DevTools → `Network` tab
2. Make any request to fragment.com/api
3. View the request and copy the `hash` parameter from the query string

### Step 3: Set Up TON Wallet

1. Get 24-word seed phrase from:
   - [Tonkeeper](https://tonkeeper.com/)
   - [MyTonWallet](https://www.mytonwallet.io/)
   - Any other TON wallet

2. Top up wallet with TON for transactions

### Step 4: Get TON API Key

1. Go to [tonconsole.com](https://tonconsole.com)
2. Create a new project
3. Generate API key from project settings

### Step 5: Store Credentials Safely

```bash
# .env file
export FRAGMENT_COOKIES="stel_ssid=...; stel_token=..."
export FRAGMENT_HASH="your_hash_here"
export WALLET_MNEMONIC="abandon ability able ... about"
export WALLET_API_KEY="AHQSQGXHKZZS..."
```

```python
import os
from FragmentAPI import SyncFragmentAPI

api = SyncFragmentAPI(
    cookies=os.getenv('FRAGMENT_COOKIES'),
    hash_value=os.getenv('FRAGMENT_HASH'),
    wallet_mnemonic=os.getenv('WALLET_MNEMONIC'),
    wallet_api_key=os.getenv('WALLET_API_KEY')
)
```

## API Reference

### Recipient Information Methods

#### `get_recipient_stars(username: str) → UserInfo`

Get recipient information for sending Telegram Stars.

**Parameters:**
- `username` (str): Target username (with or without @)

**Returns:** `UserInfo` object with:
- `name` (str) - User display name
- `recipient` (str) - Blockchain address
- `avatar` (str) - Avatar URL or base64 encoded image
- `found` (bool) - Whether user was found

**Raises:**
- `UserNotFoundError` - User not found
- `NetworkError` - API request error
- `AuthenticationError` - Session expired

**Example:**
```python
user = api.get_recipient_stars('jane_doe')
print(f"Name: {user.name}")
print(f"Address: {user.recipient}")
print(f"Avatar: {user.avatar}")
```

#### `get_recipient_premium(username: str) → UserInfo`

Get recipient information for gifting Premium.

**Parameters:**
- `username` (str): Target username

**Returns:** `UserInfo` object

**Raises:**
- `UserNotFoundError` - User not found, already has Premium, or cannot receive gift
- `NetworkError` - API request error
- `AuthenticationError` - Session expired

**Example:**
```python
user = api.get_recipient_premium('jane_doe')
if user.found:
    print(f"Can gift Premium: {user.name}")
else:
    print("User not found or already has Premium")
```

#### `get_recipient_ton(username: str) → UserInfo`

Get recipient information for TON top-up.

**Parameters:**
- `username` (str): Target username

**Returns:** `UserInfo` object

**Raises:**
- `UserNotFoundError` - User not found
- `NetworkError` - API request error
- `AuthenticationError` - Session expired

**Example:**
```python
user = api.get_recipient_ton('jane_doe')
print(f"Name: {user.name}")
```

### Payment Methods

#### `buy_stars(username: str, quantity: int, show_sender: bool = False) → PurchaseResult`

Send Telegram Stars to a user.

**Parameters:**
- `username` (str): Target username (5-32 characters)
- `quantity` (int): Number of stars to send (1-999999)
- `show_sender` (bool, optional): Show sender information. Default: `False` (anonymous)

**Returns:** `PurchaseResult` with:
- `success` (bool) - Whether transaction was successful
- `transaction_hash` (str | None) - Blockchain TX hash if successful
- `error` (str | None) - Error message if unsuccessful
- `user` (UserInfo | None) - Recipient information
- `balance_checked` (bool) - Whether balance was validated before transaction
- `required_amount` (float | None) - Total required TON (amount + fee)

**Raises:**
- `UserNotFoundError` - User doesn't exist
- `InvalidAmountError` - Quantity out of valid range
- `InsufficientBalanceError` - Not enough funds in wallet
- `AuthenticationError` - Session expired
- `NetworkError` - Network request error

**Examples:**

```python
# Send anonymously (default)
result = api.buy_stars('username', 100)

if result.success:
    print(f"✓ Stars sent successfully!")
    print(f"Transaction: {result.transaction_hash}")
    print(f"Recipient: {result.user.name}")
    print(f"Required amount: {result.required_amount} TON")
else:
    print(f"✗ Error: {result.error}")
```

```python
# Send with visible sender
result = api.buy_stars('username', 100, show_sender=True)

if result.success:
    print(f"✓ Stars sent (sender visible)")
    print(f"Transaction: {result.transaction_hash}")
else:
    print(f"✗ Error: {result.error}")
```

```python
# Async version
result = await api.buy_stars('username', 100, show_sender=True)
```

#### `gift_premium(username: str, months: int = 3, show_sender: bool = False) → PurchaseResult`

Gift Premium subscription to a user.

**Parameters:**
- `username` (str): Target username
- `months` (int): Subscription duration. Valid values: 3, 6, or 12. Default: `3`
- `show_sender` (bool, optional): Show sender information. Default: `False` (anonymous)

**Returns:** `PurchaseResult`

**Raises:**
- `UserNotFoundError` - User not found, already has Premium, or cannot receive gift
- `InvalidAmountError` - Months not in [3, 6, 12]
- `InsufficientBalanceError` - Not enough funds in wallet
- `AuthenticationError` - Session expired
- `NetworkError` - Network request error

**Examples:**

```python
# Anonymous Premium gift (3 months default)
result = api.gift_premium('username')

if result.success:
    print(f"✓ Premium gifted for 3 months!")
    print(f"Transaction: {result.transaction_hash}")
else:
    print(f"✗ Error: {result.error}")
```

```python
# Gift for 6 months with visible sender
result = api.gift_premium('username', months=6, show_sender=True)

if result.success:
    print(f"✓ Premium gifted for 6 months (sender visible)")
else:
    print(f"✗ Error: {result.error}")
```

```python
# Gift for 12 months (anonymously)
result = api.gift_premium('username', months=12)
```

```python
# Async version
result = await api.gift_premium('username', months=6, show_sender=True)
```

#### `topup_ton(username: str, amount: int, show_sender: bool = False) → PurchaseResult`

Top up Telegram account with TON cryptocurrency.

**Parameters:**
- `username` (str): Target username
- `amount` (int): Amount of TON to send (1-999999)
- `show_sender` (bool, optional): Show sender information. Default: `False` (anonymous)

**Returns:** `PurchaseResult`

**Raises:**
- `UserNotFoundError` - User doesn't exist
- `InvalidAmountError` - Amount out of valid range
- `InsufficientBalanceError` - Not enough funds in wallet
- `AuthenticationError` - Session expired
- `NetworkError` - Network request error

**Examples:**

```python
# Anonymous top-up
result = api.topup_ton('jane_doe', 10)

if result.success:
    print(f"✓ Topped up 10 TON")
    print(f"Transaction: {result.transaction_hash}")
else:
    print(f"✗ Error: {result.error}")
```

```python
# Top-up with visible sender
result = api.topup_ton('jane_doe', 10, show_sender=True)

if result.success:
    print(f"✓ Top-up sent (sender visible)")
else:
    print(f"✗ Error: {result.error}")
```

```python
# Async version
result = await api.topup_ton('jane_doe', 10, show_sender=True)
```

### Wallet Methods

#### `get_wallet_balance() → Dict[str, Any]`

Get current wallet balance and address (synchronous).

**Returns:** Dictionary with:
- `balance_ton` (float) - Balance in TON
- `balance_nano` (str) - Balance in nanotons
- `address` (str) - Blockchain wallet address
- `is_ready` (bool) - Wallet readiness status

**Raises:**
- `WalletError` - Error getting balance

**Example:**
```python
balance_info = api.get_wallet_balance()
print(f"Balance: {balance_info['balance_ton']} TON")
print(f"Address: {balance_info['address']}")
print(f"Ready: {balance_info['is_ready']}")
```

#### `async get_wallet_balance() → Dict[str, Any]` (Async version)

Get current wallet balance and address (asynchronous).

**Returns:** Dictionary with:
- `balance_ton` (float) - Balance in TON
- `balance_nano` (str) - Balance in nanotons
- `address` (str) - Blockchain wallet address
- `is_ready` (bool) - Wallet readiness status

**Raises:**
- `WalletError` - Error getting balance

**Example:**
```python
balance_info = await api.get_wallet_balance()
print(f"Balance: {balance_info['balance_ton']} TON")
```

## Exception Handling

The library provides specific exceptions for different error scenarios:

```python
from FragmentAPI import (
    FragmentAPIException,
    UserNotFoundError,
    InvalidAmountError,
    InsufficientBalanceError,
    AuthenticationError,
    NetworkError,
    TransactionError,
    RateLimitError,
    WalletError,
    PaymentInitiationError
)

try:
    result = api.buy_stars('username', 100, show_sender=True)
    if not result.success:
        print(f"Transaction failed: {result.error}")
        
except UserNotFoundError as e:
    print(f"User not found: {e}")
    
except InvalidAmountError as e:
    print(f"Invalid amount: {e}")
    
except InsufficientBalanceError as e:
    print(f"Low wallet balance: {e}")
    print("Please top up your wallet")
    
except AuthenticationError as e:
    print(f"Authentication error: {e}")
    print("Update your cookies from fragment.com")
    
except NetworkError as e:
    print(f"Network error: {e}")
    
except TransactionError as e:
    print(f"Transaction error: {e}")
    
except PaymentInitiationError as e:
    print(f"Cannot initiate payment: {e}")
    
except RateLimitError as e:
    print(f"Rate limit exceeded: {e}")
    print("Wait before retrying")
    
except WalletError as e:
    print(f"Wallet error: {e}")
    
except FragmentAPIException as e:
    print(f"API error: {e}")
```

### Exception Hierarchy

```
FragmentAPIException (base)
├── AuthenticationError
├── UserNotFoundError
├── InvalidAmountError
├── InsufficientBalanceError
├── PaymentInitiationError
├── TransactionError
├── NetworkError
├── RateLimitError
└── WalletError
```

## Data Models

### UserInfo

```python
@dataclass
class UserInfo:
    name: str           # User display name
    recipient: str      # Blockchain address
    found: bool         # Whether user was found
    avatar: str = ""    # Avatar URL or base64 encoded image
```

**Example:**
```python
user = api.get_recipient_stars('jane_doe')
print(f"Name: {user.name}")
print(f"Recipient: {user.recipient}")
print(f"Avatar: {user.avatar}")
print(f"Found: {user.found}")
```

### PurchaseResult

```python
@dataclass
class PurchaseResult:
    success: bool                    # Whether transaction was successful
    transaction_hash: Optional[str]  # Blockchain TX hash
    error: Optional[str]            # Error message if unsuccessful
    user: Optional[UserInfo]        # Recipient information
    balance_checked: bool           # Whether balance was validated
    required_amount: Optional[float] # Total required TON
```

**Example:**
```python
result = api.buy_stars('username', 100, show_sender=True)

if result.success:
    print(f"✓ Success: {result.transaction_hash}")
    print(f"Recipient: {result.user.name}")
    print(f"Required: {result.required_amount} TON")
    print(f"Balance checked: {result.balance_checked}")
else:
    print(f"✗ Error: {result.error}")
```

### WalletBalance

```python
@dataclass
class WalletBalance:
    balance_nano: str    # Balance in nanotons
    balance_ton: float   # Balance in TON
    address: str         # Blockchain address
    is_ready: bool       # Wallet readiness status
```

## Context Manager Usage

### Synchronous

```python
with SyncFragmentAPI(cookies, hash_value, mnemonic, api_key) as api:
    result = api.buy_stars('username', 50)
    result = api.gift_premium('username', 6, show_sender=True)
    # Connection closes automatically
```

### Asynchronous

```python
async with AsyncFragmentAPI(cookies, hash_value, mnemonic, api_key) as api:
    result = await api.buy_stars('username', 50)
    result = await api.gift_premium('username', 6, show_sender=True)
    # Connection closes automatically
```

## Advanced Usage

### Bulk Operations

```python
api = SyncFragmentAPI(cookies, hash_value, mnemonic, api_key)

recipients = [
    ('user1', 10, False),
    ('user2', 20, True),
    ('user3', 15, False)
]

for username, quantity, show_sender in recipients:
    try:
        result = api.buy_stars(username, quantity, show_sender=show_sender)
        if result.success:
            visibility = "visible" if show_sender else "anonymous"
            print(f"✓ {username} ({visibility}): {result.transaction_hash}")
        else:
            print(f"✗ {username}: {result.error}")
    except Exception as e:
        print(f"✗ {username}: {type(e).__name__}: {e}")

api.close()
```

### Async Parallel Operations

```python
import asyncio
from FragmentAPI import AsyncFragmentAPI

async def send_stars_batch(api, users):
    """Send stars to multiple users concurrently"""
    tasks = [
        api.buy_stars(user['username'], user['quantity'], show_sender=user.get('show_sender', False))
        for user in users
    ]
    results = await asyncio.gather(*tasks)
    return results

async def main():
    api = AsyncFragmentAPI(cookies, hash_value, mnemonic, api_key)
    
    users = [
        {'username': 'user1', 'quantity': 10, 'show_sender': True},
        {'username': 'user2', 'quantity': 20, 'show_sender': False},
        {'username': 'user3', 'quantity': 15, 'show_sender': True}
    ]
    
    results = await send_stars_batch(api, users)
    
    for user, result in zip(users, results):
        if result.success:
            visibility = "visible" if user.get('show_sender') else "anonymous"
            print(f"✓ {user['username']} ({visibility}): {result.transaction_hash}")
        else:
            print(f"✗ {user['username']}: {result.error}")
    
    await api.close()

asyncio.run(main())
```

### Pre-Payment Validation

```python
api = SyncFragmentAPI(cookies, hash_value, mnemonic, api_key)

username = 'jane_doe'
quantity = 100
show_sender = True

# Check recipient exists
try:
    user = api.get_recipient_stars(username)
    print(f"✓ User found: {user.name}")
    if user.avatar:
        print(f"✓ Avatar: {user.avatar[:50]}...")
except UserNotFoundError as e:
    print(f"✗ User not found: {e}")
    exit(1)

# Check wallet balance
try:
    balance = api.get_wallet_balance()
    print(f"✓ Wallet balance: {balance['balance_ton']} TON")
    print(f"✓ Address: {balance['address']}")
except WalletError as e:
    print(f"✗ Wallet error: {e}")
    exit(1)

# Verify sufficient balance
estimated_fee = 0.001
estimated_total = quantity * 0.00001 + estimated_fee  # Rough estimate
if float(balance['balance_ton']) < estimated_total:
    print(f"✗ Insufficient funds")
    print(f"  Required: ~{estimated_total} TON")
    print(f"  Available: {balance['balance_ton']} TON")
    exit(1)

# Send payment with visible sender
print(f"\nSending {quantity} stars to {username} (sender visible)...")
result = api.buy_stars(username, quantity, show_sender=show_sender)

if result.success:
    print(f"✓ Success!")
    print(f"  Transaction: {result.transaction_hash}")
    print(f"  Recipient: {result.user.name}")
    print(f"  Required: {result.required_amount} TON")
    print(f"  Balance checked: {result.balance_checked}")
else:
    print(f"✗ Error: {result.error}")

api.close()
```

### Premium Gift with Validation

```python
api = SyncFragmentAPI(cookies, hash_value, mnemonic, api_key)

username = 'jane_doe'
months = 6

# Check if user can receive Premium
try:
    user = api.get_recipient_premium(username)
    print(f"✓ Can gift Premium: {user.name}")
except UserNotFoundError as e:
    print(f"✗ Cannot gift: {e}")
    exit(1)

# Check balance
balance_info = api.get_wallet_balance()
print(f"Wallet balance: {balance_info['balance_ton']} TON")

# Send Premium gift (anonymously)
print(f"\nGifting {months}-month Premium to {username}...")
result = api.gift_premium(username, months=months)

if result.success:
    print(f"✓ Premium gifted!")
    print(f"  Months: {months}")
    print(f"  Recipient: {result.user.name}")
    print(f"  Transaction: {result.transaction_hash}")
else:
    print(f"✗ Error: {result.error}")

api.close()
```

### Sender Visibility Examples

```python
api = SyncFragmentAPI(cookies, hash_value, mnemonic, api_key)

# Send anonymously (default behavior)
result1 = api.buy_stars('user1', 100)
# Recipient won't know who sent it

# Send with visible sender
result2 = api.buy_stars('user2', 100, show_sender=True)
# Recipient will see your account

# Gift Premium anonymously
result3 = api.gift_premium('user3', 6)
# Recipient won't know who gifted it

# Gift Premium visibly
result4 = api.gift_premium('user4', 6, show_sender=True)
# Recipient will see your account in gift info

# Top-up TON anonymously
result5 = api.topup_ton('ads_account1', 10)
# Account owner won't see the sender

# Top-up TON visibly
result6 = api.topup_ton('ads_account2', 10, show_sender=True)
# Account owner will see your account

api.close()
```

## Requirements

- Python 3.7+
- `requests >= 2.28.0`
- `aiohttp >= 3.8.0`
- `tonutils >= 0.3.0`
- `pytoniq-core >= 0.1.0`
- `httpx >= 0.23.0`

## Installation with Dependencies

```bash
pip install fragment-api-py
```

All dependencies will be installed automatically.

## Environment Variables

```bash
# Required
FRAGMENT_COOKIES="stel_ssid=...; stel_token=..."
FRAGMENT_HASH="abc123def456"
WALLET_MNEMONIC="abandon ability able ... about"
WALLET_API_KEY="AHQSQGXHKZZS..."

# Optional
FRAGMENT_TIMEOUT=15  # Request timeout in seconds
```

## Logging

Enable debug logging to view API interactions:

```python
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Enable debug for Fragment API
logger = logging.getLogger('fragment_api')
logger.setLevel(logging.DEBUG)

# Now all API calls will be logged
api = SyncFragmentAPI(cookies, hash_value, mnemonic, api_key)
result = api.buy_stars('username', 100, show_sender=True)
```

**Example log output:**
```
2024-01-15 10:30:45,123 - FragmentAPI - DEBUG - Making request to Fragment API
2024-01-15 10:30:45,456 - FragmentAPI - DEBUG - User found: jane_doe
2024-01-15 10:30:45,789 - FragmentAPI - DEBUG - Wallet balance: 5.123456 TON
2024-01-15 10:30:46,123 - FragmentAPI - INFO - Transaction sent: EQA...
2024-01-15 10:30:46,456 - FragmentAPI - DEBUG - Transaction successful
```

## Rate Limiting

The library implements automatic retry logic with exponential backoff:

- **Max retries:** 3
- **Timeout:** 15 seconds (configurable)
- **Automatic retry on:**
  - Network timeout
  - Connection errors
  - Temporary server issues

**Example with custom timeout:**
```python
api = SyncFragmentAPI(
    cookies=cookies,
    hash_value=hash_value,
    wallet_mnemonic=mnemonic,
    wallet_api_key=api_key,
    timeout=30  # 30 second timeout
)
```

## Common Issues and Solutions

### "Session expired"
**Issue:** `AuthenticationError: Session expired: please update cookies`

**Solutions:**
- Update your cookies from fragment.com
- Make sure you copied ALL required cookies (stel_ssid, stel_token, stel_dt, stel_ton_token)
- Cookies expire over time, refresh them regularly

```python
# Update cookies
api = SyncFragmentAPI(
    cookies="FRESH_COOKIES_HERE",  # Update with fresh cookies
    hash_value=hash_value,
    wallet_mnemonic=mnemonic,
    wallet_api_key=api_key
)
```

### "User not found"
**Issue:** `UserNotFoundError: User not found`

**Solutions:**
- Verify the user exists in Telegram
- Username must be 5-32 characters
- Only letters, numbers, and underscores allowed
- Remove @ if included

```python
from FragmentAPI.utils import validate_username

# Check username validity
if not validate_username('jane_doe'):
    print("Invalid username format")

# Usage
user = api.get_recipient_stars('jane_doe')  # ✓ Correct
user = api.get_recipient_stars('john')      # ✗ Too short
user = api.get_recipient_stars('@jane_doe') # ✓ Works (@ removed)
```

### "Insufficient balance"
**Issue:** `InsufficientBalanceError: Insufficient balance`

**Solutions:**
- Check wallet balance before sending
- Ensure wallet has TON for transactions
- Account for fees (~0.001 TON)
- Library automatically validates balance

```python
# Check balance
balance_info = api.get_wallet_balance()
print(f"Available: {balance_info['balance_ton']} TON")

# Try to send (will raise InsufficientBalanceError)
try:
    result = api.buy_stars('username', 100)
except InsufficientBalanceError as e:
    print(f"Error: {e}")
    # Top up your wallet
```

### "Invalid hash"
**Issue:** `NetworkError: Request failed`

**Solutions:**
- Re-copy hash from DevTools Network tab
- Ensure hash is from fragment.com/api request
- Hash can expire, refresh it

```python
# Steps to get hash:
# 1. Open fragment.com in browser
# 2. Press F12 to open DevTools
# 3. Go to Network tab
# 4. Make any API request
# 5. Copy 'hash' parameter from query string

api = SyncFragmentAPI(
    cookies=cookies,
    hash_value="CORRECT_HASH_HERE",  # Update hash
    wallet_mnemonic=mnemonic,
    wallet_api_key=api_key
)
```

### "Invalid quantity/amount"
**Issue:** `InvalidAmountError: Invalid quantity`

**Solutions:**
- Quantity must be between 1 and 999999
- Premium months must be 3, 6, or 12
- TON amount must be between 1 and 999999

```python
from FragmentAPI.utils import validate_amount

# Check amount validity
validate_amount(100, 1, 999999)  # ✓ True
validate_amount(0, 1, 999999)    # ✗ False (too low)
validate_amount(1000000, 1, 999999)  # ✗ False (too high)

# Usage
result = api.buy_stars('username', 100)      # ✓ Valid
result = api.buy_stars('username', 0)        # ✗ Invalid
result = api.gift_premium('username', 3)     # ✓ Valid
result = api.gift_premium('username', 5)     # ✗ Invalid (must be 3, 6, or 12)
```

## Security Best Practices

### 1. Never hardcode credentials

```python
# ❌ WRONG - Never do this!
api = SyncFragmentAPI(
    cookies="stel_ssid=abc123; stel_token=xyz789",
    hash_value="your_actual_hash_here"
)

# ✅ CORRECT - Use environment variables
import os
from dotenv import load_dotenv

load_dotenv()

api = SyncFragmentAPI(
    cookies=os.getenv('FRAGMENT_COOKIES'),
    hash_value=os.getenv('FRAGMENT_HASH'),
    wallet_mnemonic=os.getenv('WALLET_MNEMONIC'),
    wallet_api_key=os.getenv('WALLET_API_KEY')
)
```

### 2. Use .env file (add to .gitignore)

```bash
# .env file
FRAGMENT_COOKIES="stel_ssid=...; stel_token=..."
FRAGMENT_HASH="your_hash_here"
WALLET_MNEMONIC="abandon ability able ... about"
WALLET_API_KEY="AHQSQGXHKZZS..."
```

```bash
# .gitignore
.env
.env.local
*.pyc
__pycache__/
```

### 3. Validate user input

```python
from FragmentAPI.utils import validate_username, validate_amount
from FragmentAPI import UserNotFoundError, InvalidAmountError

def safe_send_stars(api, username, quantity):
    """Safely send stars with validation"""
    
    # Validate username
    if not validate_username(username):
        raise UserNotFoundError(f"Invalid username: {username}")
    
    # Validate quantity
    if not validate_amount(quantity, 1, 999999):
        raise InvalidAmountError(f"Invalid quantity: {quantity}")
    
    # Send
    return api.buy_stars(username, quantity)

# Usage
try:
    result = safe_send_stars(api, 'jane_doe', 100)
except UserNotFoundError as e:
    print(f"Invalid username: {e}")
except InvalidAmountError as e:
    print(f"Invalid quantity: {e}")
```

### 4. Handle exceptions properly

```python
import logging

logger = logging.getLogger(__name__)

def send_payment_safely(api, username, quantity, show_sender=False):
    """Send payment with full error handling"""
    
    try:
        result = api.buy_stars(username, quantity, show_sender=show_sender)
        
        if result.success:
            logger.info(f"Payment successful: {result.transaction_hash}")
            return result
        else:
            logger.error(f"Payment failed: {result.error}")
            return result
            
    except UserNotFoundError as e:
        logger.error(f"User not found: {e}")
        return None
        
    except InsufficientBalanceError as e:
        logger.error(f"Insufficient funds: {e}")
        return None
        
    except AuthenticationError as e:
        logger.error(f"Authentication error: {e}")
        logger.info("Please update your cookies from fragment.com")
        return None
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        # Don't expose sensitive data to users
        return None

# Usage
result = send_payment_safely(api, 'username', 100, show_sender=True)
```

### 5. Use timeout to prevent hanging

```python
# Set request timeout to prevent indefinite waiting
api = SyncFragmentAPI(
    cookies=cookies,
    hash_value=hash_value,
    wallet_mnemonic=mnemonic,
    wallet_api_key=api_key,
    timeout=15  # 15 second timeout
)
```

### 6. Rate limiting and delays

```python
import time
from FragmentAPI import RateLimitError

def send_with_delays(api, users, delay_seconds=2):
    """Send stars to multiple users with delays"""
    
    for username, quantity in users:
        try:
            result = api.buy_stars(username, quantity)
            
            if result.success:
                print(f"✓ {username}: {result.transaction_hash}")
            else:
                print(f"✗ {username}: {result.error}")
                
        except RateLimitError as e:
            print(f"Rate limit exceeded, waiting 60 seconds...")
            time.sleep(60)
            # Retry
            result = api.buy_stars(username, quantity)
            
        except Exception as e:
            print(f"✗ {username}: {type(e).__name__}")
        
        # Wait before next request
        time.sleep(delay_seconds)

# Usage
users = [('user1', 10), ('user2', 20), ('user3', 15)]
send_with_delays(api, users, delay_seconds=2)
```

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## Disclaimer

⚠️ **Important:**

This library is **NOT affiliated** with Fragment.com or Telegram. Use at your own risk. The author is not responsible for any losses or damages related to using this library.

## Support

For issues, questions, or feature requests:

1. Check existing [GitHub Issues](https://github.com/S1qwy/fragment-api-py/issues)
2. Create a new issue with:
   - Clear description
   - Error message (without credentials)
   - Steps to reproduce
   - Environment information
