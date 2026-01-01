# Fragment API Python Library

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://img.shields.io/badge/pypi-v3.0.2-blue.svg)](https://pypi.org/project/fragment-api-py/)

**[Русская версия](README_ru.md)**

A professional Python library for the Fragment.com API with comprehensive support for Telegram payments. Send Telegram Stars, Premium subscriptions, and TON cryptocurrency with automatic wallet validation and error handling.

## Features

- ✅ **Async & Sync Interfaces** - Use either async/await or traditional blocking calls
- ✅ **3 Payment Methods** - Telegram Stars, Premium subscriptions, and TON transfers
- ✅ **Recipient Lookup** - Get user info and avatar URLs before sending payments
- ✅ **Automatic Balance Validation** - Check wallet balance before initiating transactions
- ✅ **WalletV4R2 Support** - Direct blockchain interaction with TON wallets
- ✅ **Comprehensive Error Handling** - Specific exceptions for different error scenarios
- ✅ **Type Hints** - Full type annotations for IDE autocomplete
- ✅ **Detailed Logging** - Track API interactions and errors
- ✅ **Retry Logic** - Automatic retry on network failures

## Installation

### Via pip

```bash
pip install fragment-api-py
```

### From Source

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

# Send Telegram Stars
result = api.buy_stars('username', 100)
if result.success:
    print(f"✓ Transaction: {result.transaction_hash}")
else:
    print(f"✗ Error: {result.error}")

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
    
    # Send Stars
    result = await api.buy_stars('username', 100)
    if result.success:
        print(f"✓ TX: {result.transaction_hash}")
    
    await api.close()

asyncio.run(main())
```

## Setup & Configuration

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
3. Look for the request and copy the `hash` parameter from query string

### Step 3: Setup TON Wallet

1. Get a 24-word seed phrase from:
   - [Tonkeeper](https://tonkeeper.com/)
   - [MyTonWallet](https://www.mytonwallet.io/)
   - Any other TON wallet

2. Fund the wallet with TON for transactions

### Step 4: Get TON API Key

1. Go to [tonconsole.com](https://tonconsole.com)
2. Create a new project
3. Generate API key from project settings

### Step 5: Store Credentials Securely

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

### Recipient Methods

#### `get_recipient_stars(username: str) → UserInfo`

Get recipient information for Telegram Stars transfer.

**Parameters:**
- `username` (str): Target username (with or without @ prefix)

**Returns:** `UserInfo` object with:
- `name` - User's display name
- `recipient` - Blockchain address
- `avatar` - Avatar URL or base64 encoded image
- `found` - Boolean flag

**Raises:**
- `UserNotFoundError` - User doesn't exist
- `NetworkError` - API request failed
- `AuthenticationError` - Session expired

**Example:**
```python
user = api.get_recipient_stars('john_doe')
print(f"Name: {user.name}")
print(f"Address: {user.recipient}")
print(f"Avatar: {user.avatar}")
```

#### `get_recipient_premium(username: str) → UserInfo`

Get recipient information for Premium gift.

**Example:**
```python
user = api.get_recipient_premium('jane_doe')
if user.found:
    print(f"Can gift Premium to: {user.name}")
else:
    print("User not found or already has Premium")
```

#### `get_recipient_ton(username: str) → UserInfo`

Get recipient information for Ads account top-up.

### Payment Methods

#### `buy_stars(username: str, quantity: int) → PurchaseResult`

Send Telegram Stars to user.

**Parameters:**
- `username` (str): Target username
- `quantity` (int): Number of stars (1-999999)

**Returns:** `PurchaseResult` with:
- `success` (bool) - Transaction success status
- `transaction_hash` (str) - Blockchain TX hash
- `error` (str) - Error message if failed
- `user` (UserInfo) - Recipient information
- `balance_checked` (bool) - Whether balance was validated
- `required_amount` (float) - Total required TON (amount + fee)

**Example:**
```python
result = api.buy_stars('username', 100)

if result.success:
    print(f"✓ Stars sent successfully!")
    print(f"Transaction: {result.transaction_hash}")
    print(f"Balance checked: {result.balance_checked}")
else:
    print(f"✗ Error: {result.error}")
```

#### `gift_premium(username: str, months: int = 3) → PurchaseResult`

Gift Premium subscription.

**Parameters:**
- `username` (str): Target username
- `months` (int): Duration (3, 6, or 12 months)

**Returns:** `PurchaseResult`

**Example:**
```python
result = api.gift_premium('username', 6)

if result.success:
    print(f"✓ Premium gifted for 6 months!")
else:
    print(f"✗ {result.error}")
```

#### `topup_ton(username: str, amount: int) → PurchaseResult`

Top up Telegram Ads account with TON.

**Parameters:**
- `username` (str): Target username
- `amount` (int): TON amount (1-999999)

**Returns:** `PurchaseResult`

**Example:**
```python
result = api.topup_ton('ads_account', 10)

if result.success:
    print(f"✓ Topped up with 10 TON")
else:
    print(f"✗ {result.error}")
```

### Wallet Methods

#### `get_wallet_balance() → Dict[str, Any]`

Get current wallet balance and address.

**Returns:** Dictionary with:
- `balance_ton` (float) - Balance in TON
- `balance_nano` (str) - Balance in nanotons
- `address` (str) - Wallet blockchain address
- `is_ready` (bool) - Wallet readiness status

**Example:**
```python
balance_info = api.get_wallet_balance()
print(f"Balance: {balance_info['balance_ton']} TON")
print(f"Address: {balance_info['address']}")
```

## Exception Handling

The library provides specific exceptions for different error scenarios:

```python
from FragmentAPI import (
    UserNotFoundError,
    InvalidAmountError,
    InsufficientBalanceError,
    AuthenticationError,
    NetworkError,
    TransactionError
)

try:
    result = api.buy_stars('username', 100)
    if not result.success:
        print(f"Transaction failed: {result.error}")
        
except UserNotFoundError as e:
    print(f"User not found: {e}")
    
except InvalidAmountError as e:
    print(f"Invalid amount: {e}")
    
except InsufficientBalanceError as e:
    print(f"Low wallet balance: {e}")
    
except AuthenticationError as e:
    print(f"Auth failed: {e}")
    print("Update your cookies")
    
except NetworkError as e:
    print(f"Network error: {e}")
    
except TransactionError as e:
    print(f"Transaction failed: {e}")
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

## Context Manager Usage

### Synchronous

```python
with SyncFragmentAPI(cookies, hash_value, mnemonic, api_key) as api:
    result = api.buy_stars('username', 50)
    # Connection closed automatically
```

### Asynchronous

```python
async with AsyncFragmentAPI(cookies, hash_value, mnemonic, api_key) as api:
    result = await api.buy_stars('username', 50)
    # Connection closed automatically
```

## Advanced Usage

### Batch Operations

```python
api = SyncFragmentAPI(cookies, hash_value, mnemonic, api_key)

recipients = ['user1', 'user2', 'user3']

for username in recipients:
    try:
        result = api.buy_stars(username, 10)
        if result.success:
            print(f"✓ {username}: {result.transaction_hash}")
        else:
            print(f"✗ {username}: {result.error}")
    except Exception as e:
        print(f"✗ {username}: {type(e).__name__}: {e}")

api.close()
```

### Async Concurrent Operations

```python
import asyncio
from FragmentAPI import AsyncFragmentAPI

async def send_stars_batch(api, users):
    tasks = [api.buy_stars(user, 10) for user in users]
    results = await asyncio.gather(*tasks)
    return results

async def main():
    api = AsyncFragmentAPI(cookies, hash_value, mnemonic, api_key)
    
    users = ['user1', 'user2', 'user3']
    results = await send_stars_batch(api, users)
    
    for user, result in zip(users, results):
        if result.success:
            print(f"✓ {user}: {result.transaction_hash}")
        else:
            print(f"✗ {user}: {result.error}")
    
    await api.close()

asyncio.run(main())
```

### Pre-check Before Payment

```python
api = SyncFragmentAPI(cookies, hash_value, mnemonic, api_key)

username = 'john_doe'

# Check recipient exists
try:
    user = api.get_recipient_stars(username)
    print(f"✓ User found: {user.name}")
    print(f"Avatar: {user.avatar}")
except UserNotFoundError as e:
    print(f"✗ User not found: {e}")
    exit(1)

# Check wallet balance
balance = api.get_wallet_balance()
print(f"Wallet balance: {balance['balance_ton']} TON")

if float(balance['balance_ton']) < 0.1:
    print("✗ Insufficient balance")
    exit(1)

# Send payment
result = api.buy_stars(username, 100)
if result.success:
    print(f"✓ Success: {result.transaction_hash}")
else:
    print(f"✗ Error: {result.error}")

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

Enable debug logging to see API interactions:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('fragment_api')
logger.setLevel(logging.DEBUG)

# Now all API calls will be logged
api = SyncFragmentAPI(cookies, hash_value, mnemonic, api_key)
```

## Rate Limiting

The library implements automatic retry logic with exponential backoff:

- Maximum retries: 3
- Timeout: 15 seconds (configurable)
- Automatic retry on:
  - Network timeouts
  - Connection errors
  - Temporary server issues

## Common Issues

### "Session expired"
- Update your cookies from fragment.com
- Ensure you're copying ALL required cookies

### "User not found"
- Verify username exists on Telegram
- Username must be 5-32 characters
- Only alphanumeric and underscore allowed

### "Insufficient balance"
- Check wallet balance: `api.get_wallet_balance()`
- Ensure wallet is funded with TON
- Account for transaction fee (~0.001 TON)

### "Invalid hash"
- Recopy hash from DevTools Network tab
- Ensure hash is from fragment.com/api request

## Security Best Practices

1. **Never hardcode credentials**
   ```python
   # ❌ Bad
   api = SyncFragmentAPI(
       cookies="stel_ssid=...",
       hash_value="..."
   )
   
   # ✅ Good
   api = SyncFragmentAPI(
       cookies=os.getenv('FRAGMENT_COOKIES'),
       hash_value=os.getenv('FRAGMENT_HASH')
   )
   ```

2. **Use environment variables**
   ```bash
   # .env file (add to .gitignore)
   FRAGMENT_COOKIES="..."
   WALLET_MNEMONIC="..."
   ```

3. **Validate user input**
   ```python
   from FragmentAPI.utils import validate_username, validate_amount
   
   if not validate_username(username):
       raise ValueError("Invalid username")
   
   if not validate_amount(quantity, 1, 999999):
       raise ValueError("Invalid quantity")
   ```

4. **Handle exceptions properly**
   ```python
   try:
       result = api.buy_stars(username, quantity)
   except Exception as e:
       logger.error(f"Payment failed: {e}")
       # Don't expose sensitive data
   ```

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This library is not affiliated with Fragment.com or Telegram. Use at your own risk. The authors are not responsible for any losses or damages resulting from the use of this library.
