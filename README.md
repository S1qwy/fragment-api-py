# Fragment API Python Library - Complete Documentation

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://img.shields.io/badge/pypi-v3.2.0-blue.svg)](https://pypi.org/project/fragment-api-py/)

**Professional Python library for Fragment.com API with comprehensive support for multiple TON wallet versions, Telegram payments, and direct cryptocurrency transfers.**

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Wallet Version Support](#wallet-version-support)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Setup Guide](#setup-guide)
- [API Reference](#api-reference)
- [Exception Handling](#exception-handling)
- [Data Models](#data-models)
- [Advanced Usage](#advanced-usage)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Overview

Fragment API Python Library is a professional-grade solution for integrating Telegram payments into Python applications. It provides both asynchronous and synchronous interfaces for sending Telegram Stars, Premium subscriptions, and direct TON transfers with full blockchain integration.

**Current Version:** 3.2.0

---

## Key Features

### Core Capabilities

- ✅ **Dual Interface** - Both async/await and synchronous blocking interfaces
- ✅ **Three Payment Products** - Telegram Stars, Premium subscriptions, TON top-ups
- ✅ **Direct TON Transfers** - Send cryptocurrency to any address with optional memo
- ✅ **Recipient Lookup** - Fetch user information and avatars before payment
- ✅ **Automatic Balance Validation** - Prevent failed transactions with pre-flight checks
- ✅ **Comprehensive Error Handling** - Specific exceptions for each error scenario
- ✅ **Full Type Hints** - IDE autocompletion and static type checking support

### Advanced Features

- 🔐 **Multiple Wallet Versions** - V3R1, V3R2, V4R2, V5R1/W5 (NEW in 3.2.0)
- 🔄 **Automatic Retry Logic** - Network error recovery with exponential backoff
- 📝 **Detailed Logging** - Track all API interactions and debug issues
- 👁️ **Sender Visibility Control** - Anonymous or visible payments
- ⚡ **High Performance** - Concurrent async operations for batch processing
- 🛡️ **Input Validation** - Username and amount validation utilities
- 🔌 **Context Manager Support** - Automatic resource cleanup

---

## Wallet Version Support

### NEW in Version 3.2.0: Multi-Wallet Support

The library now supports **5 different TON wallet versions** with automatic version handling:

| Version | Name | Status | Use Case |
|---------|------|--------|----------|
| **V3R1** | WalletV3R1 | Legacy | Older wallets, compatibility |
| **V3R2** | WalletV3R2 | Legacy | Older wallets, compatibility |
| **V4R2** | WalletV4R2 | **Recommended** | Standard, most compatible |
| **V5R1** | WalletV5R1 | Latest | New wallets, modern features |
| **W5** | Alias for V5R1 | Latest | Alternative naming for V5R1 |

### Wallet Version Selection

The wallet version determines how transactions are signed and sent. Most modern TON wallets use **V4R2** or **V5R1**.

**Auto-detection and normalization:**
```python
# All of these will work and be normalized to V4R2
api = SyncFragmentAPI(..., wallet_version="v4r2")
api = SyncFragmentAPI(..., wallet_version="V4R2")
api = SyncFragmentAPI(..., wallet_version="V4r2")  # Case-insensitive

# W5 is automatically mapped to V5R1
api = SyncFragmentAPI(..., wallet_version="w5")      # → V5R1
api = SyncFragmentAPI(..., wallet_version="W5")      # → V5R1
api = SyncFragmentAPI(..., wallet_version="v5r1")    # → V5R1
```

### Determining Your Wallet Version

**Option 1: Check in Tonkeeper/MyTonWallet**

1. Open your TON wallet app
2. Go to Settings → About/Wallet Info
3. Look for "Wallet Type" or "Contract Version"
4. Common values: "Wallet V4R2", "Wallet V5R1", "W5"

**Option 2: Derive from Address Format**

- **V4R2 addresses:** Start with `EQA...` or `0QA...`
- **V5R1 addresses:** Start with `EQA...` or `0QA...` (same format)
- **V3R1/V3R2:** Older format, less common

**Option 3: Check Seed Phrase Origin**

- **Tonkeeper:** Uses V4R2 by default
- **MyTonWallet:** Uses V4R2 by default
- **TonHub:** Uses V5R1
- **TON Wallet:** Uses V4R2 by default

### Migration Between Versions

If you're upgrading your wallet or need to switch versions:

```python
# Old wallet with V3R2
api_old = SyncFragmentAPI(
    cookies=cookies,
    hash_value=hash_value,
    wallet_mnemonic=mnemonic_old,
    wallet_api_key=api_key,
    wallet_version="V3R2"  # Legacy version
)

# New wallet with V4R2
api_new = SyncFragmentAPI(
    cookies=cookies,
    hash_value=hash_value,
    wallet_mnemonic=mnemonic_new,
    wallet_api_key=api_key,
    wallet_version="V4R2"  # Modern version
)

# If upgrading to V5R1
api_latest = SyncFragmentAPI(
    cookies=cookies,
    hash_value=hash_value,
    wallet_mnemonic=mnemonic_new,
    wallet_api_key=api_key,
    wallet_version="V5R1"  # Latest version
)
```

### Wallet Version Compatibility

**Transaction Compatibility:**
- All versions can receive TON from any other version
- All versions can send TON to any address
- Version differences are transparent to users

**Recommended Approach:**
1. Use **V4R2** for maximum compatibility (default)
2. Use **V5R1** for latest TON features
3. Use **V3R1/V3R2** only if maintaining legacy systems

**Check Supported Versions:**
```python
from FragmentAPI import WalletManager

manager = WalletManager(mnemonic, api_key, "V4R2")
info = manager.get_wallet_info()

print(f"Current Version: {info['version']}")
print(f"Supported Versions: {info['supported_versions']}")
print(f"Version Mapping: {info['version_mapping']}")
```

Output:
```
Current Version: V4R2
Supported Versions: ['V4R2', 'V5R1', 'W5', 'V3R2', 'V3R1']
Version Mapping: {
    'V4R2': 'V4R2',
    'V5R1': 'V5R1',
    'W5': 'V5R1',
    'V3R2': 'V3R2',
    'V3R1': 'V3R1'
}
```

### Wallet Version Errors

Invalid wallet version will raise `InvalidWalletVersionError`:

```python
from FragmentAPI import InvalidWalletVersionError

try:
    api = SyncFragmentAPI(
        cookies=cookies,
        hash_value=hash_value,
        wallet_mnemonic=mnemonic,
        wallet_api_key=api_key,
        wallet_version="V2R1"  # Invalid version
    )
except InvalidWalletVersionError as e:
    print(f"Error: {e}")
    # Output:
    # Invalid wallet version: 'V2R1'
    # Supported wallet versions:
    #   - V4R2: WalletV4R2 - Most common wallet version
    #   - V5R1: WalletV5R1 - Latest wallet version (also known as W5)
    #   - W5: WalletV5R1 - Alias for V5R1
    #   - V3R2: WalletV3R2 - Legacy wallet version
    #   - V3R1: WalletV3R1 - Legacy wallet version
```

---

## Installation

### Via pip (Recommended)

```bash
pip install fragment-api-py
```

### From source with git

```bash
git clone https://github.com/S1qwy/fragment-api-py.git
cd fragment-api-py
pip install -e .
```

### Development installation

```bash
git clone https://github.com/S1qwy/fragment-api-py.git
cd fragment-api-py
pip install -e ".[dev]"
```

### Verify installation

```python
from FragmentAPI import AsyncFragmentAPI, SyncFragmentAPI, __version__

print(f"Fragment API version: {__version__}")
print(f"Async client: {AsyncFragmentAPI}")
print(f"Sync client: {SyncFragmentAPI}")
```

### Dependencies

The library automatically installs all required dependencies:

```
requests >= 2.28.0      # HTTP requests
aiohttp >= 3.8.0        # Async HTTP
tonutils >= 0.3.0       # TON blockchain interaction
pytoniq-core >= 0.1.0   # TON message encoding
httpx >= 0.23.0         # Async HTTP client
```

---

## Quick Start

### Synchronous Usage (Blocking)

```python
from FragmentAPI import SyncFragmentAPI

# Initialize with default wallet version (V4R2)
api = SyncFragmentAPI(
    cookies="stel_ssid=value; stel_token=value; stel_dt=value; stel_ton_token=value",
    hash_value="your_hash_from_network_tab",
    wallet_mnemonic="word1 word2 ... word24",
    wallet_api_key="your_tonapi_key"
)

# Get user info
user = api.get_recipient_stars('jane_doe')
print(f"User: {user.name}")
print(f"Avatar: {user.avatar}")

# Send Telegram Stars (anonymous)
result = api.buy_stars('jane_doe', 100)
if result.success:
    print(f"✓ Stars sent! TX: {result.transaction_hash}")
else:
    print(f"✗ Error: {result.error}")

# Send with visible sender
result = api.buy_stars('jane_doe', 100, show_sender=True)

# Direct TON transfer
transfer = api.transfer_ton("recipient.t.me", 0.5, "Payment for services")
if transfer.success:
    print(f"✓ Transfer: {transfer.transaction_hash}")

# Get wallet balance
balance = api.get_wallet_balance()
print(f"Balance: {balance['balance_ton']} TON")

# Clean up
api.close()
```

### Asynchronous Usage (Async/Await)

```python
import asyncio
from FragmentAPI import AsyncFragmentAPI

async def main():
    api = AsyncFragmentAPI(
        cookies="stel_ssid=value; stel_token=value; stel_dt=value; stel_ton_token=value",
        hash_value="your_hash_from_network_tab",
        wallet_mnemonic="word1 word2 ... word24",
        wallet_api_key="your_tonapi_key"
    )
    
    # Get user info
    user = await api.get_recipient_stars('jane_doe')
    print(f"User: {user.name}")
    
    # Send Stars anonymously
    result = await api.buy_stars('jane_doe', 100)
    if result.success:
        print(f"✓ TX: {result.transaction_hash}")
    
    # Send with visible sender
    result = await api.buy_stars('jane_doe', 100, show_sender=True)
    
    # Direct TON transfer
    transfer = await api.transfer_ton("recipient.t.me", 0.5, "Payment")
    
    # Get balance
    balance = await api.get_wallet_balance()
    print(f"Balance: {balance['balance_ton']} TON")
    
    # Clean up
    await api.close()

asyncio.run(main())
```

### Using Context Managers

```python
# Synchronous with context manager
with SyncFragmentAPI(cookies, hash_value, mnemonic, api_key) as api:
    result = api.buy_stars('username', 100)
    balance = api.get_wallet_balance()
    # Automatically closes on exit

# Asynchronous with context manager
async with AsyncFragmentAPI(cookies, hash_value, mnemonic, api_key) as api:
    result = await api.buy_stars('username', 100)
    balance = await api.get_wallet_balance()
    # Automatically closes on exit
```

### Custom Wallet Version

```python
from FragmentAPI import SyncFragmentAPI

# Use V5R1 (latest wallet version)
api = SyncFragmentAPI(
    cookies=cookies,
    hash_value=hash_value,
    wallet_mnemonic=mnemonic,
    wallet_api_key=api_key,
    wallet_version="V5R1"  # Specify version explicitly
)

# Use legacy V3R2
api_legacy = SyncFragmentAPI(
    cookies=cookies,
    hash_value=hash_value,
    wallet_mnemonic=mnemonic,
    wallet_api_key=api_key,
    wallet_version="V3R2"  # Use legacy version
)

# W5 is automatically mapped to V5R1
api_w5 = SyncFragmentAPI(
    cookies=cookies,
    hash_value=hash_value,
    wallet_mnemonic=mnemonic,
    wallet_api_key=api_key,
    wallet_version="W5"  # Works as V5R1
)
```

---

## Setup Guide

### Step 1: Extract Fragment Cookies

1. Visit [fragment.com](https://fragment.com) in your browser
2. Press `F12` to open Developer Tools
3. Navigate to `Application` tab → `Cookies` → `fragment.com`
4. Copy these cookies:

| Cookie Name | Purpose |
|-------------|---------|
| `stel_ssid` | Session ID |
| `stel_token` | Authentication token |
| `stel_dt` | Timezone offset |
| `stel_ton_token` | TON-specific token |

5. Combine into single string:
```
stel_ssid=abc123def456; stel_token=xyz789uvw012; stel_dt=-180; stel_ton_token=qrs345tuv678
```

### Step 2: Get Hash Value

1. Keep DevTools open, go to `Network` tab
2. Refresh fragment.com page
3. Look for requests to `fragment.com/api`
4. Click on any API request
5. In the `Query String Parameters` section, copy the `hash` value

### Step 3: Prepare TON Wallet

#### Option A: Export from Tonkeeper

1. Open Tonkeeper app
2. Go to Settings → Wallet Settings
3. Tap "View Recovery Phrase"
4. Copy the 24-word mnemonic phrase
5. Wallet version defaults to **V4R2**

#### Option B: Export from MyTonWallet

1. Go to [mytonwallet.io](https://www.mytonwallet.io)
2. Open existing wallet
3. Settings → Backup Seed/Wallet
4. Copy the 24 words
5. Wallet version defaults to **V4R2**

#### Option C: Export from TonHub

1. Open TonHub app
2. Settings → Seed Phrase
3. Copy the 24 words
4. **Note:** TonHub uses **V5R1** wallet version

#### Option D: Check Your Wallet Version

Most wallets display version info:

```python
from FragmentAPI import SyncFragmentAPI

api = SyncFragmentAPI(
    cookies=cookies,
    hash_value=hash_value,
    wallet_mnemonic=mnemonic,
    wallet_api_key=api_key,
    wallet_version="V4R2"  # Default, try this first
)

balance_info = api.get_wallet_balance()
print(f"Wallet Version: {balance_info['wallet_version']}")
# Output: V4R2
```

**If your wallet is newer, try V5R1:**
```python
api = SyncFragmentAPI(
    ...
    wallet_version="V5R1"  # For newer wallets
)
```

### Step 4: Get TonAPI Key

1. Visit [tonconsole.com](https://tonconsole.com)
2. Sign in with your account (or create one)
3. Create a new project
4. Go to project settings
5. Copy the **API Key**
6. Keep this key secure

### Step 5: Set Up Environment Variables

Create `.env` file in your project root:

```bash
# .env
FRAGMENT_COOKIES="stel_ssid=abc123; stel_token=xyz789; stel_dt=-180; stel_ton_token=uvw012"
FRAGMENT_HASH="abc123def456ghi789jkl012mno345"
WALLET_MNEMONIC="abandon ability able abandon abandon abandon abandon abandon abandon abandon abandon about"
WALLET_API_KEY="AHQSQGXHKZZSJQWPYXYZABCDEFGHIJK"
WALLET_VERSION="V4R2"
FRAGMENT_TIMEOUT="15"
```

Add to `.gitignore`:
```
.env
.env.local
*.pem
private_key*
wallet_seed*
```

### Step 6: Use in Your Application

```python
import os
from dotenv import load_dotenv
from FragmentAPI import SyncFragmentAPI

# Load environment variables
load_dotenv()

# Initialize client
api = SyncFragmentAPI(
    cookies=os.getenv('FRAGMENT_COOKIES'),
    hash_value=os.getenv('FRAGMENT_HASH'),
    wallet_mnemonic=os.getenv('WALLET_MNEMONIC'),
    wallet_api_key=os.getenv('WALLET_API_KEY'),
    wallet_version=os.getenv('WALLET_VERSION', 'V4R2'),  # Defaults to V4R2
    timeout=int(os.getenv('FRAGMENT_TIMEOUT', 15))
)

# Use the client
result = api.buy_stars('username', 100)
print(result)

api.close()
```

---

## API Reference

### Recipient Information Methods

#### `get_recipient_stars(username: str) → UserInfo`

Retrieve recipient information for Telegram Stars transfer.

**Parameters:**
- `username` (str): Target username, with or without `@` prefix (5-32 characters)

**Returns:** `UserInfo` object containing:
- `name` (str): User's display name
- `recipient` (str): Blockchain recipient address
- `avatar` (str): Avatar URL or base64-encoded image data
- `found` (bool): Whether user was successfully found

**Raises:**
- `UserNotFoundError`: User doesn't exist on Telegram
- `NetworkError`: API request failed
- `AuthenticationError`: Session expired or invalid credentials

**Example:**
```python
# Synchronous
user = api.get_recipient_stars('jane_doe')
print(f"Name: {user.name}")
print(f"Recipient: {user.recipient}")
print(f"Avatar: {user.avatar[:50]}...")  # First 50 chars

# Asynchronous
user = await api.get_recipient_stars('jane_doe')
```

#### `get_recipient_premium(username: str) → UserInfo`

Retrieve recipient information for Premium subscription gift.

**Parameters:**
- `username` (str): Target username

**Returns:** `UserInfo` object

**Raises:**
- `UserNotFoundError`: User doesn't exist, already has Premium, or cannot receive gift
- `NetworkError`: API request failed
- `AuthenticationError`: Session expired

**Example:**
```python
user = api.get_recipient_premium('jane_doe')
if user.found:
    print(f"Can gift Premium to: {user.name}")
else:
    print("User not eligible for Premium gift")
```

#### `get_recipient_ton(username: str) → UserInfo`

Retrieve recipient information for TON Ads top-up.

**Parameters:**
- `username` (str): Target username or channel name

**Returns:** `UserInfo` object

**Raises:**
- `UserNotFoundError`: User/channel doesn't exist
- `NetworkError`: API request failed
- `AuthenticationError`: Session expired

**Example:**
```python
user = api.get_recipient_ton('ad_manager_bot')
print(f"Address: {user.recipient}")
```

---

### Payment Methods

#### `buy_stars(username: str, quantity: int, show_sender: bool = False) → PurchaseResult`

Send Telegram Stars to a user.

**Parameters:**
- `username` (str): Recipient's username (5-32 characters)
- `quantity` (int): Number of stars to send (1-999999)
- `show_sender` (bool, optional): Whether to show sender. Default: `False` (anonymous)

**Returns:** `PurchaseResult` containing:
- `success` (bool): Transaction success status
- `transaction_hash` (str|None): Blockchain transaction hash if successful
- `error` (str|None): Error message if failed
- `user` (UserInfo|None): Recipient information
- `balance_checked` (bool): Whether balance was validated
- `required_amount` (float|None): Total TON required (including fees)

**Raises:**
- `UserNotFoundError`: User doesn't exist
- `InvalidAmountError`: Quantity out of valid range (1-999999)
- `InsufficientBalanceError`: Wallet lacks sufficient balance
- `AuthenticationError`: Session expired
- `PaymentInitiationError`: Cannot initiate payment
- `TransactionError`: Transaction execution failed

**Example - Synchronous:**
```python
# Anonymous stars (default)
result = api.buy_stars('jane_doe', 100)

if result.success:
    print(f"✓ Stars sent successfully!")
    print(f"Transaction: {result.transaction_hash}")
    print(f"Recipient: {result.user.name}")
    print(f"Total cost: {result.required_amount} TON")
    print(f"Balance verified: {result.balance_checked}")
else:
    print(f"✗ Error: {result.error}")

# Stars with visible sender
result = api.buy_stars('jane_doe', 100, show_sender=True)
if result.success:
    print(f"✓ Stars sent (sender visible)")
```

**Example - Asynchronous:**
```python
result = await api.buy_stars('jane_doe', 100)

if result.success:
    print(f"✓ TX: {result.transaction_hash}")
else:
    print(f"✗ Error: {result.error}")

# With visible sender
result = await api.buy_stars('jane_doe', 100, show_sender=True)
```

**Example - Batch Processing:**
```python
users = [
    ('user1', 10, False),   # (username, quantity, show_sender)
    ('user2', 20, True),
    ('user3', 15, False)
]

for username, quantity, show_sender in users:
    result = api.buy_stars(username, quantity, show_sender=show_sender)
    
    if result.success:
        visibility = "visible" if show_sender else "anonymous"
        print(f"✓ {username} ({visibility}): {result.transaction_hash}")
    else:
        print(f"✗ {username}: {result.error}")
```

#### `gift_premium(username: str, months: int = 3, show_sender: bool = False) → PurchaseResult`

Gift a Telegram Premium subscription to a user.

**Parameters:**
- `username` (str): Recipient's username
- `months` (int): Subscription duration. Valid values: 3, 6, 12. Default: `3`
- `show_sender` (bool, optional): Whether to show sender. Default: `False` (anonymous)

**Returns:** `PurchaseResult` object

**Raises:**
- `UserNotFoundError`: User doesn't exist, already has Premium, or cannot receive gift
- `InvalidAmountError`: Months not in [3, 6, 12]
- `InsufficientBalanceError`: Wallet lacks sufficient balance
- `AuthenticationError`: Session expired
- `PaymentInitiationError`: Cannot initiate payment
- `TransactionError`: Transaction execution failed

**Example - Synchronous:**
```python
# Gift 3 months anonymously (default)
result = api.gift_premium('jane_doe')

if result.success:
    print(f"✓ Premium gifted for 3 months!")
    print(f"Transaction: {result.transaction_hash}")
else:
    print(f"✗ Error: {result.error}")

# Gift 6 months with visible sender
result = api.gift_premium('jane_doe', months=6, show_sender=True)

if result.success:
    print(f"✓ Premium gifted (6 months, sender visible)")
    print(f"Cost: {result.required_amount} TON")
else:
    print(f"✗ Error: {result.error}")

# Gift 12 months anonymously
result = api.gift_premium('jane_doe', months=12)
```

**Example - Asynchronous:**
```python
# 3 months (default)
result = await api.gift_premium('jane_doe')

# 6 months with visible sender
result = await api.gift_premium('jane_doe', months=6, show_sender=True)

# 12 months anonymously
result = await api.gift_premium('jane_doe', months=12)
```

**Example - Error Handling:**
```python
try:
    result = api.gift_premium('jane_doe', months=6, show_sender=True)
    
    if result.success:
        print(f"✓ Success: {result.transaction_hash}")
    else:
        print(f"✗ Failed: {result.error}")
        
except UserNotFoundError as e:
    print(f"User issue: {e}")
    # User doesn't exist, already has Premium, or cannot receive gift
    
except InvalidAmountError as e:
    print(f"Duration issue: {e}")
    # months parameter is not 3, 6, or 12
    
except InsufficientBalanceError as e:
    print(f"Balance issue: {e}")
    # Wallet doesn't have enough TON
```

#### `topup_ton(username: str, amount: int, show_sender: bool = False) → PurchaseResult`

Top up TON balance for Telegram Ads account.

**Parameters:**
- `username` (str): Target username or ads account
- `amount` (int): Amount of TON to transfer (1-999999)
- `show_sender` (bool, optional): Whether to show sender. Default: `False` (anonymous)

**Returns:** `PurchaseResult` object

**Raises:**
- `UserNotFoundError`: User/account doesn't exist
- `InvalidAmountError`: Amount out of valid range (1-999999)
- `InsufficientBalanceError`: Wallet lacks sufficient balance
- `AuthenticationError`: Session expired
- `PaymentInitiationError`: Cannot initiate payment
- `TransactionError`: Transaction execution failed

**Example - Synchronous:**
```python
# Top-up 10 TON anonymously
result = api.topup_ton('ad_account', 10)

if result.success:
    print(f"✓ Topped up 10 TON")
    print(f"Transaction: {result.transaction_hash}")
else:
    print(f"✗ Error: {result.error}")

# Top-up 50 TON with visible sender
result = api.topup_ton('ad_account', 50, show_sender=True)

if result.success:
    print(f"✓ Top-up sent (sender visible)")
    print(f"Cost: {result.required_amount} TON")
```

**Example - Asynchronous:**
```python
result = await api.topup_ton('ad_account', 10)

if result.success:
    print(f"✓ TX: {result.transaction_hash}")
    print(f"Amount: {result.required_amount} TON")
else:
    print(f"✗ Error: {result.error}")
```

#### `transfer_ton(to_address: str, amount_ton: float, memo: str = None) → TransferResult`

Send TON directly to any wallet address or Telegram username.

**Parameters:**
- `to_address` (str): Destination address (TON address or `username.t.me` format)
- `amount_ton` (float): Amount to transfer in TON
- `memo` (str, optional): Text comment/memo for the transaction

**Returns:** `TransferResult` containing:
- `success` (bool): Transfer success status
- `transaction_hash` (str|None): Blockchain transaction hash
- `from_address` (str|None): Sender's wallet address
- `to_address` (str|None): Recipient's address
- `amount_ton` (float|None): Amount sent in TON
- `balance_before` (float|None): Wallet balance before transfer
- `memo` (str|None): Memo included in transaction
- `error` (str|None): Error message if failed

**Raises:**
- `WalletError`: Invalid address or amount
- `InsufficientBalanceError`: Wallet lacks sufficient balance
- `TransactionError`: Transaction execution failed
- `NetworkError`: Network request failed

**Example - To Username:**
```python
# Transfer to Telegram username with memo
result = api.transfer_ton('jane_doe.t.me', 0.5, 'Payment for services')

if result.success:
    print(f"✓ Transfer successful!")
    print(f"From: {result.from_address}")
    print(f"To: {result.to_address}")
    print(f"Amount: {result.amount_ton} TON")
    print(f"Memo: {result.memo}")
    print(f"Hash: {result.transaction_hash}")
else:
    print(f"✗ Error: {result.error}")
```

**Example - To TON Address:**
```python
# Transfer to blockchain address
address = "EQDrjaLahLkMB-hMCmkzOyBuHJ139ZUYmPHu6RRBKnbRELWt"

result = api.transfer_ton(address, 1.0, "blockchain payment")

if result.success:
    print(f"✓ Hash: {result.transaction_hash}")
else:
    print(f"✗ Error: {result.error}")
```

**Example - Without Memo:**
```python
result = api.transfer_ton('recipient.t.me', 0.01)

if result.success:
    print(f"✓ Transferred {result.amount_ton} TON")
```

**Example - Asynchronous:**
```python
result = await api.transfer_ton('jane_doe.t.me', 0.5, 'async payment')

if result.success:
    print(f"✓ TX: {result.transaction_hash}")
    print(f"Amount: {result.amount_ton} TON")
    print(f"Memo: {result.memo}")
else:
    print(f"✗ Error: {result.error}")
```

---

### Wallet Methods

#### `get_wallet_balance() → Dict[str, Any]` (Synchronous)

Get current wallet balance and information.

**Returns:** Dictionary with:
- `balance_ton` (float): Balance in TON
- `balance_nano` (str): Balance in nanotons (1 TON = 1e9 nanotons)
- `address` (str): Blockchain wallet address
- `is_ready` (bool): Wallet readiness status
- `wallet_version` (str): Current wallet version (V3R1, V3R2, V4R2, V5R1)

**Raises:**
- `WalletError`: Failed to retrieve balance

**Example:**
```python
balance_info = api.get_wallet_balance()

print(f"Balance: {balance_info['balance_ton']} TON")
print(f"Balance (nano): {balance_info['balance_nano']} nanotons")
print(f"Address: {balance_info['address']}")
print(f"Ready: {balance_info['is_ready']}")
print(f"Wallet Version: {balance_info['wallet_version']}")

# Output:
# Balance: 5.123456 TON
# Balance (nano): 5123456000 nanotons
# Address: EQDrjaLahLkMB-hMCmkzOyBuHJ139ZUYmPHu6RRBKnbRELWt
# Ready: True
# Wallet Version: V4R2
```

#### `async get_wallet_balance() → Dict[str, Any]` (Asynchronous)

Asynchronous version of wallet balance retrieval.

**Returns:** Same dictionary as synchronous version

**Example:**
```python
balance_info = await api.get_wallet_balance()

print(f"Balance: {balance_info['balance_ton']} TON")
print(f"Address: {balance_info['address']}")
print(f"Version: {balance_info['wallet_version']}")
```

---

## Exception Handling

### Exception Hierarchy

```
FragmentAPIException (base exception)
├── AuthenticationError
│   └── Raised when session expires or credentials invalid
├── UserNotFoundError
│   └── Raised when user/recipient not found
├── InvalidAmountError
│   └── Raised when quantity/amount is invalid
├── InsufficientBalanceError
│   └── Raised when wallet balance insufficient
├── PaymentInitiationError
│   └── Raised when payment cannot be initiated
├── TransactionError
│   └── Raised when transaction execution fails
├── NetworkError
│   └── Raised when network request fails
├── RateLimitError
│   └── Raised when rate limit exceeded
└── WalletError
    └── Raised when wallet operation fails
        └── InvalidWalletVersionError
            └── Raised when wallet version not supported
```

### Comprehensive Exception Handling

```python
from FragmentAPI import (
    FragmentAPIException,
    AuthenticationError,
    UserNotFoundError,
    InvalidAmountError,
    InsufficientBalanceError,
    PaymentInitiationError,
    TransactionError,
    NetworkError,
    RateLimitError,
    WalletError,
    InvalidWalletVersionError
)

try:
    result = api.buy_stars('username', 100, show_sender=True)
    
    if not result.success:
        print(f"Transaction failed: {result.error}")
        
except AuthenticationError as e:
    print(f"❌ Authentication Failed")
    print(f"   Error: {e}")
    print(f"   Action: Update your cookies from fragment.com")
    print(f"   Steps: DevTools → Application → Cookies")
    
except UserNotFoundError as e:
    print(f"❌ User Not Found")
    print(f"   Error: {e}")
    print(f"   Action: Check username validity")
    print(f"   Requirement: 5-32 characters, only letters/numbers/_")
    
except InvalidAmountError as e:
    print(f"❌ Invalid Amount")
    print(f"   Error: {e}")
    print(f"   For Stars: 1-999999")
    print(f"   For Premium: 3, 6, or 12 months")
    print(f"   For TON topup: 1-999999")
    
except InsufficientBalanceError as e:
    print(f"❌ Insufficient Balance")
    print(f"   Error: {e}")
    print(f"   Action: Deposit more TON to your wallet")
    balance = api.get_wallet_balance()
    print(f"   Current balance: {balance['balance_ton']} TON")
    print(f"   Address: {balance['address']}")
    
except PaymentInitiationError as e:
    print(f"❌ Payment Initiation Failed")
    print(f"   Error: {e}")
    print(f"   Action: Try again, may be temporary issue")
    
except TransactionError as e:
    print(f"❌ Transaction Failed")
    print(f"   Error: {e}")
    print(f"   Action: Check balance and wallet status")
    
except NetworkError as e:
    print(f"❌ Network Error")
    print(f"   Error: {e}")
    print(f"   Action: Check internet connection, retry")
    
except RateLimitError as e:
    print(f"❌ Rate Limit Exceeded")
    print(f"   Error: {e}")
    print(f"   Action: Wait 60 seconds before retrying")
    import time
    time.sleep(60)
    # Retry operation
    
except InvalidWalletVersionError as e:
    print(f"❌ Invalid Wallet Version")
    print(f"   Error: {e}")
    print(f"   Supported: V3R1, V3R2, V4R2, V5R1, W5")
    print(f"   Recommended: V4R2 (default)")
    
except WalletError as e:
    print(f"❌ Wallet Error")
    print(f"   Error: {e}")
    print(f"   Action: Check wallet setup, API key, mnemonic")
    
except FragmentAPIException as e:
    print(f"❌ General API Error")
    print(f"   Error: {e}")
    print(f"   Action: Check credentials and connection")
```

### Exception-Specific Recovery

```python
def safe_buy_stars(api, username, quantity):
    """Send stars with specific error recovery"""
    
    try:
        result = api.buy_stars(username, quantity)
        
        if result.success:
            return {
                'success': True,
                'tx_hash': result.transaction_hash,
                'recipient': result.user.name
            }
        else:
            return {
                'success': False,
                'error': result.error,
                'recovery': 'Check logs above'
            }
            
    except UserNotFoundError:
        return {
            'success': False,
            'error': f'User {username} not found',
            'recovery': 'Check username spelling and existence'
        }
        
    except InvalidAmountError:
        return {
            'success': False,
            'error': f'Invalid quantity: {quantity}',
            'recovery': f'Use value between 1-999999'
        }
        
    except InsufficientBalanceError as e:
        balance = api.get_wallet_balance()
        return {
            'success': False,
            'error': str(e),
            'recovery': f'Add TON to: {balance["address"]}',
            'current_balance': balance['balance_ton']
        }
        
    except AuthenticationError:
        return {
            'success': False,
            'error': 'Session expired',
            'recovery': 'Extract new cookies from fragment.com'
        }
        
    except TransactionError as e:
        return {
            'success': False,
            'error': str(e),
            'recovery': 'Try again, wallet may be processing'
        }
        
    except NetworkError:
        return {
            'success': False,
            'error': 'Network connection error',
            'recovery': 'Check internet, retry with exponential backoff'
        }

# Usage
result = safe_buy_stars(api, 'jane_doe', 100)
if not result['success']:
    print(f"Error: {result['error']}")
    print(f"Recovery: {result['recovery']}")
else:
    print(f"Success: {result['tx_hash']}")
```

---

## Data Models

### UserInfo

Data class for user information retrieved from Fragment API.

```python
from dataclasses import dataclass

@dataclass
class UserInfo:
    name: str           # User's display name
    recipient: str      # Blockchain recipient address
    found: bool         # Whether user exists
    avatar: str = ""    # Avatar URL or base64 data
```

**Example:**
```python
user = api.get_recipient_stars('jane_doe')

print(f"Name: {user.name}")
print(f"Recipient: {user.recipient}")
print(f"Found: {user.found}")
print(f"Avatar: {user.avatar[:100]}...")

# Output:
# Name: Jane Doe
# Recipient: EQA1b4_TYf...
# Found: True
# Avatar: https://t.me/i/u/123456...
```

### PurchaseResult

Data class for payment transaction results.

```python
@dataclass
class PurchaseResult:
    success: bool                    # Transaction success
    transaction_hash: Optional[str]  # Blockchain TX hash
    error: Optional[str]             # Error message if failed
    user: Optional[UserInfo]         # Recipient info
    balance_checked: bool            # Balance was validated
    required_amount: Optional[float] # Total TON required
```

**Example:**
```python
result = api.buy_stars('jane_doe', 100, show_sender=True)

if result.success:
    print(f"Status: Success")
    print(f"Hash: {result.transaction_hash}")
    print(f"Recipient: {result.user.name}")
    print(f"Amount: {result.required_amount} TON")
    print(f"Balance checked: {result.balance_checked}")
else:
    print(f"Status: Failed")
    print(f"Error: {result.error}")

# Output:
# Status: Success
# Hash: EQA1b4_TYf...
# Recipient: Jane Doe
# Amount: 0.012345 TON
# Balance checked: True
```

### TransferResult

Data class for direct TON transfer results.

```python
@dataclass
class TransferResult:
    success: bool                    # Transfer success
    transaction_hash: Optional[str]  # Blockchain TX hash
    from_address: Optional[str]      # Sender address
    to_address: Optional[str]        # Recipient address
    amount_ton: Optional[float]      # Amount in TON
    balance_before: Optional[float]  # Balance before transfer
    memo: Optional[str]              # Transaction memo
    error: Optional[str]             # Error message if failed
```

**Example:**
```python
result = api.transfer_ton('jane_doe.t.me', 0.5, 'payment for services')

if result.success:
    print(f"Status: Success")
    print(f"From: {result.from_address}")
    print(f"To: {result.to_address}")
    print(f"Amount: {result.amount_ton} TON")
    print(f"Memo: {result.memo}")
    print(f"Hash: {result.transaction_hash}")
    print(f"Balance before: {result.balance_before} TON")
else:
    print(f"Status: Failed")
    print(f"Error: {result.error}")

# Output:
# Status: Success
# From: EQDrjaLah...
# To: EQA1b4_TYf...
# Amount: 0.5 TON
# Memo: payment for services
# Hash: EQA1b4_TYf...
# Balance before: 5.123456 TON
```

### WalletBalance

Data class for wallet balance information.

```python
@dataclass
class WalletBalance:
    balance_nano: str    # Balance in nanotons
    balance_ton: float   # Balance in TON
    address: str         # Blockchain address
    is_ready: bool       # Wallet ready status
    
    def has_sufficient_balance(self, required_nano: str, fee_nano: str = "1000000") -> bool:
        """Check if balance is sufficient"""
```

**Example:**
```python
from FragmentAPI import WalletManager

manager = WalletManager(mnemonic, api_key, "V4R2")
balance = manager.get_balance_sync()

print(f"Balance: {balance.balance_ton} TON")
print(f"Nano: {balance.balance_nano} nanotons")
print(f"Address: {balance.address}")
print(f"Ready: {balance.is_ready}")

# Check if sufficient for transaction
if balance.has_sufficient_balance("100000000", "1000000"):  # 0.1 TON + 0.001 fee
    print("✓ Sufficient balance for transaction")
else:
    print("✗ Insufficient balance")

# Output:
# Balance: 5.123456 TON
# Nano: 5123456000 nanotons
# Address: EQDrjaLah...
# Ready: True
# ✓ Sufficient balance for transaction
```

---

## Advanced Usage

### Batch Operations with Error Handling

```python
from FragmentAPI import SyncFragmentAPI, UserNotFoundError, InsufficientBalanceError

def batch_send_stars(api, recipients):
    """Send stars to multiple recipients"""
    results = []
    
    for username, quantity in recipients:
        try:
            print(f"Sending {quantity} stars to {username}...", end=" ")
            result = api.buy_stars(username, quantity, show_sender=False)
            
            if result.success:
                print(f"✓ {result.transaction_hash[:20]}...")
                results.append({
                    'status': 'success',
                    'username': username,
                    'quantity': quantity,
                    'tx_hash': result.transaction_hash
                })
            else:
                print(f"✗ {result.error}")
                results.append({
                    'status': 'failed',
                    'username': username,
                    'quantity': quantity,
                    'error': result.error
                })
                
        except InsufficientBalanceError as e:
            print(f"✗ INSUFFICIENT BALANCE")
            balance = api.get_wallet_balance()
            print(f"   Current: {balance['balance_ton']} TON")
            print(f"   Address: {balance['address']}")
            break  # Stop processing
            
        except UserNotFoundError as e:
            print(f"✗ USER NOT FOUND")
            results.append({
                'status': 'user_not_found',
                'username': username,
                'error': str(e)
            })
            
        except Exception as e:
            print(f"✗ ERROR: {type(e).__name__}")
            results.append({
                'status': 'error',
                'username': username,
                'error': str(e)
            })
    
    return results

# Usage
api = SyncFragmentAPI(cookies, hash_value, mnemonic, api_key)

recipients = [
    ('user1', 10),
    ('user2', 20),
    ('user3', 15),
    ('invalid_user', 5),
    ('user4', 100)
]

results = batch_send_stars(api, recipients)

# Summary
successful = [r for r in results if r['status'] == 'success']
failed = [r for r in results if r['status'] == 'failed']
not_found = [r for r in results if r['status'] == 'user_not_found']

print(f"\n=== SUMMARY ===")
print(f"✓ Successful: {len(successful)}")
print(f"✗ Failed: {len(failed)}")
print(f"✗ Not found: {len(not_found)}")

api.close()
```

### Async Concurrent Operations

```python
import asyncio
from FragmentAPI import AsyncFragmentAPI

async def send_batch_concurrent(api, recipients):
    """Send stars to multiple recipients concurrently"""
    tasks = [
        api.buy_stars(username, quantity, show_sender=False)
        for username, quantity in recipients
    ]
    
    # Execute all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return results

async def main():
    api = AsyncFragmentAPI(cookies, hash_value, mnemonic, api_key)
    
    recipients = [
        ('user1', 10),
        ('user2', 20),
        ('user3', 15),
        ('user4', 25),
        ('user5', 30)
    ]
    
    print("Sending stars to 5 users concurrently...")
    results = await send_batch_concurrent(api, recipients)
    
    for (username, quantity), result in zip(recipients, results):
        if isinstance(result, Exception):
            print(f"✗ {username}: {type(result).__name__}")
        elif result.success:
            print(f"✓ {username}: {result.transaction_hash[:20]}...")
        else:
            print(f"✗ {username}: {result.error}")
    
    await api.close()

asyncio.run(main())
```

### Scheduled Payments

```python
import asyncio
import time
from datetime import datetime, timedelta
from FragmentAPI import AsyncFragmentAPI

async def scheduled_payment(api, schedule):
    """Execute payments on schedule"""
    
    for task in schedule:
        username = task['username']
        quantity = task['quantity']
        delay_minutes = task['delay_minutes']
        
        # Wait until scheduled time
        wait_seconds = delay_minutes * 60
        print(f"Scheduled: {username} → {quantity} stars in {delay_minutes} minutes")
        await asyncio.sleep(wait_seconds)
        
        # Execute payment
        print(f"Executing: {username}...", end=" ")
        result = await api.buy_stars(username, quantity)
        
        if result.success:
            print(f"✓ {result.transaction_hash[:20]}...")
        else:
            print(f"✗ {result.error}")

async def main():
    api = AsyncFragmentAPI(cookies, hash_value, mnemonic, api_key)
    
    # Schedule: Send stars at specific intervals
    schedule = [
        {'username': 'user1', 'quantity': 10, 'delay_minutes': 1},
        {'username': 'user2', 'quantity': 20, 'delay_minutes': 2},
        {'username': 'user3', 'quantity': 15, 'delay_minutes': 3}
    ]
    
    await scheduled_payment(api, schedule)
    await api.close()

asyncio.run(main())
```

### Multi-Wallet Management

```python
from FragmentAPI import SyncFragmentAPI

def manage_multiple_wallets():
    """Manage multiple wallets with different versions"""
    
    wallets = {
        'v4r2': {
            'mnemonic': 'mnemonic_for_v4r2_wallet',
            'api_key': 'api_key_1',
            'version': 'V4R2'
        },
        'v5r1': {
            'mnemonic': 'mnemonic_for_v5r1_wallet',
            'api_key': 'api_key_2',
            'version': 'V5R1'
        },
        'v3r2': {
            'mnemonic': 'mnemonic_for_v3r2_wallet',
            'api_key': 'api_key_3',
            'version': 'V3R2'
        }
    }
    
    # Initialize APIs for each wallet
    apis = {}
    for name, config in wallets.items():
        apis[name] = SyncFragmentAPI(
            cookies=cookies,
            hash_value=hash_value,
            wallet_mnemonic=config['mnemonic'],
            wallet_api_key=config['api_key'],
            wallet_version=config['version']
        )
    
    # Check balances
    for name, api in apis.items():
        balance = api.get_wallet_balance()
        print(f"{name}: {balance['balance_ton']} TON (Version: {balance['wallet_version']})")
    
    # Output:
    # v4r2: 5.123456 TON (Version: V4R2)
    # v5r1: 3.654321 TON (Version: V5R1)
    # v3r2: 2.111111 TON (Version: V3R2)
    
    # Send from different wallets
    result_v4 = apis['v4r2'].buy_stars('user1', 100)
    result_v5 = apis['v5r1'].buy_stars('user2', 50)
    result_v3 = apis['v3r2'].buy_stars('user3', 25)
    
    # Clean up
    for api in apis.values():
        api.close()

manage_multiple_wallets()
```

### Payment Validation System

```python
from FragmentAPI import SyncFragmentAPI, UserNotFoundError, InvalidAmountError
from FragmentAPI.utils import validate_username, validate_amount

class PaymentValidator:
    """Comprehensive payment validation"""
    
    def __init__(self, api):
        self.api = api
    
    def validate_stars_payment(self, username, quantity, show_sender=False):
        """Validate stars payment before sending"""
        
        errors = []
        
        # Validate username
        if not validate_username(username):
            errors.append(f"Invalid username: {username}")
            errors.append("  - Must be 5-32 characters")
            errors.append("  - Only letters, numbers, underscores")
            return {'valid': False, 'errors': errors}
        
        # Validate quantity
        if not validate_amount(quantity, 1, 999999):
            errors.append(f"Invalid quantity: {quantity}")
            errors.append("  - Must be between 1-999999")
            return {'valid': False, 'errors': errors}
        
        # Check user exists
        try:
            user = self.api.get_recipient_stars(username)
        except UserNotFoundError as e:
            errors.append(f"User not found: {e}")
            return {'valid': False, 'errors': errors}
        
        # Check wallet balance
        try:
            balance = self.api.get_wallet_balance()
            # Rough estimate: ~0.00001 TON per star + 0.001 TON fee
            estimated_cost = (quantity * 0.00001) + 0.001
            
            if float(balance['balance_ton']) < estimated_cost:
                errors.append(f"Insufficient balance")
                errors.append(f"  - Required: ~{estimated_cost:.6f} TON")
                errors.append(f"  - Available: {balance['balance_ton']} TON")
                errors.append(f"  - Address: {balance['address']}")
                return {'valid': False, 'errors': errors}
        except Exception as e:
            errors.append(f"Balance check failed: {e}")
            return {'valid': False, 'errors': errors}
        
        return {
            'valid': True,
            'user': user,
            'estimated_cost': estimated_cost,
            'balance': float(balance['balance_ton'])
        }

# Usage
validator = PaymentValidator(api)

result = validator.validate_stars_payment('jane_doe', 100, show_sender=True)

if result['valid']:
    print("✓ Payment validation passed")
    print(f"  User: {result['user'].name}")
    print(f"  Estimated cost: {result['estimated_cost']:.6f} TON")
    print(f"  Wallet balance: {result['balance']} TON")
    
    # Proceed with payment
    payment_result = api.buy_stars('jane_doe', 100, show_sender=True)
else:
    print("✗ Payment validation failed")
    for error in result['errors']:
        print(f"  {error}")
```

---

## Best Practices

### 1. Error Handling

**Always handle exceptions explicitly:**

```python
from FragmentAPI import (
    UserNotFoundError,
    InsufficientBalanceError,
    AuthenticationError,
    TransactionError
)

def safe_payment(api, username, quantity):
    """Best practice error handling"""
    
    try:
        result = api.buy_stars(username, quantity)
        
        if result.success:
            return {'status': 'success', 'tx': result.transaction_hash}
        else:
            return {'status': 'failed', 'error': result.error}
            
    except UserNotFoundError as e:
        print(f"User validation failed: {e}")
        return {'status': 'invalid_user', 'error': str(e)}
        
    except InsufficientBalanceError as e:
        print(f"Balance insufficient: {e}")
        balance = api.get_wallet_balance()
        return {
            'status': 'insufficient_balance',
            'error': str(e),
            'current_balance': balance['balance_ton'],
            'address': balance['address']
        }
        
    except AuthenticationError as e:
        print(f"Session expired: {e}")
        return {'status': 'auth_failed', 'error': 'Update cookies'}
        
    except TransactionError as e:
        print(f"Transaction failed: {e}")
        return {'status': 'tx_error', 'error': str(e)}
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {'status': 'unknown_error', 'error': str(e)}
```

### 2. Resource Management

**Always close connections properly:**

```python
# ✗ DON'T - Leaves resources open
api = SyncFragmentAPI(cookies, hash_value, mnemonic, api_key)
result = api.buy_stars('username', 100)

# ✓ DO - Closes automatically
with SyncFragmentAPI(cookies, hash_value, mnemonic, api_key) as api:
    result = api.buy_stars('username', 100)

# ✓ DO - Explicit close
api = SyncFragmentAPI(cookies, hash_value, mnemonic, api_key)
try:
    result = api.buy_stars('username', 100)
finally:
    api.close()

# ✓ DO - Async context manager
async with AsyncFragmentAPI(cookies, hash_value, mnemonic, api_key) as api:
    result = await api.buy_stars('username', 100)
```

### 3. Security

**Never hardcode credentials:**

```python
import os
from dotenv import load_dotenv

# ✗ DON'T
api = SyncFragmentAPI(
    cookies="stel_ssid=abc123",
    hash_value="xyz789",
    wallet_mnemonic="word word word...",
    wallet_api_key="secret_key"
)

# ✓ DO
load_dotenv()

api = SyncFragmentAPI(
    cookies=os.getenv('FRAGMENT_COOKIES'),
    hash_value=os.getenv('FRAGMENT_HASH'),
    wallet_mnemonic=os.getenv('WALLET_MNEMONIC'),
    wallet_api_key=os.getenv('WALLET_API_KEY')
)
```

### 4. Input Validation

**Validate before sending:**

```python
from FragmentAPI.utils import validate_username, validate_amount

def send_payment(api, username, quantity):
    """Send with validation"""
    
    # Validate inputs
    if not validate_username(username):
        raise ValueError(f"Invalid username: {username}")
    
    if not validate_amount(quantity, 1, 999999):
        raise ValueError(f"Invalid quantity: {quantity}")
    
    # Proceed
    return api.buy_stars(username, quantity)
```

### 5. Logging

**Enable detailed logging:**

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fragment_api.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('FragmentAPI')
logger.setLevel(logging.DEBUG)

# Now all API calls will be logged
api = SyncFragmentAPI(cookies, hash_value, mnemonic, api_key)
result = api.buy_stars('username', 100)
# All details logged to file and console
```

### 6. Timeouts

**Set appropriate timeouts:**

```python
# Short timeout for quick operations (default)
api_fast = SyncFragmentAPI(
    cookies, hash_value, mnemonic, api_key,
    timeout=15  # 15 seconds
)

# Long timeout for slow networks
api_slow = SyncFragmentAPI(
    cookies, hash_value, mnemonic, api_key,
    timeout=30  # 30 seconds
)
```

### 7. Retry Logic

**Implement exponential backoff:**

```python
import time
from FragmentAPI import NetworkError

def send_with_retry(api, username, quantity, max_retries=3):
    """Send with automatic retry"""
    
    for attempt in range(max_retries):
        try:
            return api.buy_stars(username, quantity)
            
        except NetworkError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential: 1, 2, 4 seconds
                print(f"Retry in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
```

### 8. Batch Operations

**Process large batches safely:**

```python
def batch_send_with_delays(api, recipients, delay_seconds=2):
    """Send to multiple users with delays"""
    
    results = []
    
    for username, quantity in recipients:
        try:
            result = api.buy_stars(username, quantity)
            results.append({
                'username': username,
                'success': result.success,
                'tx': result.transaction_hash if result.success else None
            })
        except Exception as e:
            results.append({
                'username': username,
                'success': False,
                'error': str(e)
            })
        
        # Delay between requests to avoid rate limiting
        time.sleep(delay_seconds)
    
    return results
```

---

## Troubleshooting

### Issue: "Session expired" Error

**Symptom:**
```
AuthenticationError: Session expired: please update cookies
```

**Causes:**
- Cookies have expired (typically after 1-2 weeks)
- Wrong cookies copied
- Missing cookie values

**Solutions:**

1. **Refresh cookies:**
   - Open fragment.com in browser
   - Press F12 → Application → Cookies
   - Copy all cookies again
   - Update your `.env` file

2. **Verify all cookies:**
   ```python
   # Should have all these:
   # stel_ssid, stel_token, stel_dt, stel_ton_token
   
   cookies = "stel_ssid=ABC; stel_token=XYZ; stel_dt=-180; stel_ton_token=UVW"
   ```

3. **Check cookie format:**
   ```python
   from FragmentAPI.utils import parse_cookies
   
   try:
       parsed = parse_cookies(cookies)
       print(f"Cookies parsed: {list(parsed.keys())}")
   except ValueError as e:
       print(f"Invalid format: {e}")
   ```

### Issue: "User not found" Error

**Symptom:**
```
UserNotFoundError: User username not found: no Telegram users found
```

**Causes:**
- Username doesn't exist
- Username too short (< 5 characters)
- Invalid characters in username
- User account deleted

**Solutions:**

1. **Verify username exists:**
   - Search user in Telegram
   - Check exact spelling
   - Verify they have public username

2. **Validate username format:**
   ```python
   from FragmentAPI.utils import validate_username
   
   username = 'jane_doe'
   if validate_username(username):
       print("✓ Valid format")
   else:
       print("✗ Invalid format")
       print("  - Must be 5-32 characters")
       print("  - Only letters, numbers, underscores")
   ```

3. **Test with known user:**
   ```python
   # Try with a known public account
   user = api.get_recipient_stars('telegram')  # Official Telegram account
   print(f"✓ Found: {user.name}")
   ```

### Issue: "Insufficient balance" Error

**Symptom:**
```
InsufficientBalanceError: Insufficient balance. Required: X.XX TON, Available: Y.YY TON
```

**Causes:**
- Wallet balance too low
- Need TON for transaction fees
- Didn't account for network fees

**Solutions:**

1. **Check balance:**
   ```python
   balance_info = api.get_wallet_balance()
   print(f"Balance: {balance_info['balance_ton']} TON")
   print(f"Address: {balance_info['address']}")
   ```

2. **Deposit TON:**
   - Send TON to your wallet address from exchange/another wallet
   - Wait for blockchain confirmation (30-60 seconds)
   - Check balance again

3. **Account for fees:**
   ```python
   # Estimate cost: amount + 0.001 TON fee
   estimated_cost = 0.1 + 0.001  # 0.101 TON minimum
   
   balance = api.get_wallet_balance()
   if float(balance['balance_ton']) >= estimated_cost:
       print("✓ Sufficient balance")
   else:
       print(f"✗ Need at least {estimated_cost} TON")
   ```

### Issue: "Invalid hash" or "Hash expired"

**Symptom:**
```
NetworkError: Request failed
```

**Causes:**
- Hash value is wrong
- Hash has expired
- Hash copied from wrong request

**Solutions:**

1. **Re-copy hash:**
   - Open fragment.com
   - Press F12 → Network tab
   - Refresh page
   - Look for request to `fragment.com/api`
   - Copy `hash` parameter from Query String

2. **Verify hash format:**
   ```python
   # Hash should be alphanumeric string, ~30+ characters
   hash_value = "abc123def456ghi789jkl012mno345"
   
   if len(hash_value) > 20 and hash_value.isalnum():
       print("✓ Hash looks valid")
   else:
       print("✗ Hash format invalid")
   ```

3. **Check request URL:**
   - Right-click API request in Network tab
   - "Copy as cURL"
   - Verify hash in URL

### Issue: "Invalid wallet version"

**Symptom:**
```
InvalidWalletVersionError: Invalid wallet version: 'V2R1'
Supported wallet versions:
  - V4R2: WalletV4R2 - Most common wallet version
  - V5R1: WalletV5R1 - Latest wallet version (also known as W5)
  - ...
```

**Causes:**
- Typo in wallet version
- Using unsupported version
- Wrong version format

**Solutions:**

1. **Use correct version:**
   ```python
   # ✗ Wrong
   api = SyncFragmentAPI(..., wallet_version="V2R1")

   # ✓ Correct
   api = SyncFragmentAPI(..., wallet_version="V4R2")
   ```

2. **Determine your wallet version:**
   - Check wallet app settings
   - Default is usually V4R2
   - V5R1 for newer wallets
   - V3R1/V3R2 for legacy wallets

3. **Supported versions:**
   ```python
   # All valid versions
   "V3R1"  # Legacy
   "V3R2"  # Legacy
   "V4R2"  # Recommended (default)
   "V5R1"  # Latest
   "W5"    # Alias for V5R1 (TonHub)
   ```

### Issue: "Invalid quantity" or "Invalid amount"

**Symptom:**
```
InvalidAmountError: Invalid quantity: 0
```

**Causes:**
- Amount less than 1
- Amount greater than 999999
- Invalid type (string instead of int)

**Solutions:**

1. **Validate before sending:**
   ```python
   from FragmentAPI.utils import validate_amount
   
   # Check validity
   if validate_amount(100, 1, 999999):
       print("✓ Valid quantity")
   else:
       print("✗ Invalid quantity")
   ```

2. **Use correct ranges:**
   ```python
   # Stars: 1-999999
   result = api.buy_stars('username', 100)  # ✓
   result = api.buy_stars('username', 0)    # ✗ Too low
   result = api.buy_stars('username', 1000000)  # ✗ Too high
   
   # Premium: 3, 6, or 12 months only
   result = api.gift_premium('username', 3)   # ✓
   result = api.gift_premium('username', 6)   # ✓
   result = api.gift_premium('username', 12)  # ✓
   result = api.gift_premium('username', 5)   # ✗ Invalid
   
   # TON topup: 1-999999
   result = api.topup_ton('channel', 10)      # ✓
   result = api.topup_ton('channel', 0)       # ✗ Too low
   ```

### Issue: "Cannot gift Premium" Error

**Symptom:**
```
UserNotFoundError: Premium recipient {username} already subscribed to Premium
```

or

```
UserNotFoundError: Premium recipient {username}: cannot gift premium to this user
```

**Causes:**
- User already has Premium subscription
- User has Premium gift active
- User account restricted
- Bot account (cannot gift to bots)

**Solutions:**

1. **Check user eligibility:**
   ```python
   try:
       user = api.get_recipient_premium('username')
       if user.found:
           print("✓ User can receive Premium")
   except UserNotFoundError as e:
       print(f"✗ User not eligible: {e}")
   ```

2. **Verify in Telegram:**
   - Open user's profile
   - Check if they have Premium badge (⭐)
   - If they do, cannot gift

3. **Alternative:** Send Telegram Stars instead
   ```python
   # If cannot gift Premium, send Stars
   result = api.buy_stars('username', 100)
   ```

### Issue: Network Timeouts

**Symptom:**
```
NetworkError: Request timeout after maximum retries
```

**Causes:**
- Slow internet connection
- Fragment.com server slow
- Default timeout too short

**Solutions:**

1. **Increase timeout:**
   ```python
   api = SyncFragmentAPI(
       cookies, hash_value, mnemonic, api_key,
       timeout=30  # Increase from default 15
   )
   ```

2. **Check connection:**
   ```bash
   # Test connectivity
   ping fragment.com
   ```

3. **Retry with backoff:**
   ```python
   import time
   from FragmentAPI import NetworkError
   
   def send_with_retry(api, username, quantity, max_retries=3):
       for attempt in range(max_retries):
           try:
               return api.buy_stars(username, quantity)
           except NetworkError:
               if attempt < max_retries - 1:
                   wait = 2 ** attempt
                   print(f"Timeout, retrying in {wait}s...")
                   time.sleep(wait)
               else:
                   raise
   ```

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## License

Licensed under MIT License - see [LICENSE](LICENSE) file.

---

## Support

For issues and questions:

- 📌 Check [existing issues](https://github.com/S1qwy/fragment-api-py/issues)
- 🐛 Report bugs with error message and steps to reproduce
- 💡 Suggest features with use cases
- 📖 Share documentation improvements

---

## Disclaimer

⚠️ **IMPORTANT:**

- This library is **NOT affiliated** with Fragment.com, Telegram, or TON Foundation
- **Use at your own risk** - author not responsible for losses
- Keep credentials secure and private
- Test with small amounts first
- Comply with all applicable laws and regulations

---

## Changelog

### Version 3.2.0 (Current)
- ✅ **Multi-wallet version support** (V3R1, V3R2, V4R2, V5R1, W5)
- ✅ WalletManager improvements
- ✅ Enhanced error messages
- ✅ Complete documentation rewrite
- ✅ Improved validation utilities

### Version 3.1.0
- ✅ Async/sync interfaces
- ✅ Direct TON transfers
- ✅ Balance checking
- ✅ Error handling

### Version 3.0.0
- ✅ Initial release
- ✅ Stars, Premium, TON support
- ✅ Basic error handling

---

**Made with ❤️ by S1qwy**
