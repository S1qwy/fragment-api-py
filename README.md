# FragmentAPI Python Client

[![PyPI version](https://badge.fury.io/py/fragment-api-py.svg)](https://badge.fury.io/py/fragment-api-py)
[![Python versions](https://img.shields.io/pypi/pyversions/fragment-api-py.svg)](https://pypi.org/project/fragment-api-py/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python client library for interacting with the Fragment API, designed to manage authentication, session handling, and Telegram-related transactions such as buying Telegram Stars, gifting Telegram Premium, and topping up TON.

## Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [Usage](#usage)
  - [Initialization](#initialization)
  - [Authentication](#authentication)
  - [Session Management](#session-management)
  - [API Methods](#api-methods)
  - [Error Handling](#error-handling)
- [Examples](#examples)
- [Contributing](#contributing)
- [License](#license)

## Overview
The `FragmentAPI` class provides a convenient interface to interact with the Fragment API (`https://fragment.s1qwy.ru`). It supports:
- Authentication with wallet mnemonic, cookies, and hash value.
- Session management (save, load, delete sessions).
- Retrieving wallet balance.
- Performing Telegram transactions (buying Stars, gifting Premium, topping up TON).
- Querying user information for Stars and Premium transactions.
- Checking API health status.

The client uses the `requests` library for HTTP communication and includes verbose response logging for debugging purposes, printing the full server response (status code, headers, and body) for every API request.

## Installation
Install the package directly from PyPI using pip:

```bash
pip install fragment-api-py
```

### Requirements
- Python 3.6 or higher
- `requests` library (automatically installed as a dependency)

To verify the installation, run:
```bash
pip show fragment-api-py
```

For development, clone the repository (if available) and install in editable mode:
```bash
git clone https://github.com/your-username/fragment-api-py.git
cd fragment-api-py
pip install -e .
```

## Usage

### Initialization
Import and create an instance of the `FragmentAPI` class, optionally specifying the base URL.

```python
from fragment_api_py import FragmentAPI  # Adjust import based on package structure

# Initialize with default base URL
api = FragmentAPI()

# Or specify a custom base URL
api = FragmentAPI(base_url="https://custom-fragment-api.com")
```

### Authentication
Authenticate with the API using a wallet mnemonic, cookies, and hash value. The full server response (status code, headers, body) is printed for transparency.

```python
result = api.create_auth(
    wallet_mnemonic="your mnemonic phrase",
    cookies="your session cookies",
    hash_value="your hash value"
)
print(result)  # Contains auth_key if successful
```

### Session Management
- **Save Session**: Saves the authentication key to a file (default: `fragment_session.json`).
  ```python
  api.save_session()  # Default filename
  api.save_session("custom_session.json")  # Custom filename
  ```
- **Load Session**: Loads a previously saved session.
  ```python
  api.load_session()  # Default filename
  api.load_session("custom_session.json")  # Custom filename
  ```
- **Delete Session**: Removes the saved session file and clears the auth key.
  ```python
  api.delete_session()
  api.delete_session("custom_session.json")  # Custom filename
  ```
- **Check Valid Session**: Verifies if an active session exists.
  ```python
  if api.has_valid_session():
      print("Valid session available")
  ```

### API Methods
All methods requiring authentication (`get_balance`, `buy_stars`, `gift_premium`, `topup_ton`, `get_user_stars`, `get_user_premium`) raise a `ValueError` if no `auth_key` is set. Every API request prints the full server response, including status code, headers, and body (JSON if parseable, otherwise raw text).

- **`get_balance()`**: Retrieves the wallet balance.
  ```python
  balance = api.get_balance()
  # Example response: {"ok": true, "balance": 100.50, "currency": "TON"}
  ```

- **`buy_stars(username, quantity=None)`**: Buys Telegram Stars for a user (username with @ prefix).
  ```python
  result = api.buy_stars("@username", quantity=100)
  ```

- **`gift_premium(username, months=None)`**: Gifts Telegram Premium to a user.
  ```python
  result = api.gift_premium("@username", months=3)
  ```

- **`topup_ton(username, amount)`**: Tops up TON balance for a user.
  ```python
  result = api.topup_ton("@username", amount=10)
  ```

- **`get_user_stars(username)`**: Queries user information for Telegram Stars transactions.
  ```python
  result = api.get_user_stars("@username")
  ```

- **`get_user_premium(username)`**: Queries user information for Telegram Premium transactions.
  ```python
  result = api.get_user_premium("@username")
  ```

- **`health_check()`**: Checks the API's health status (no authentication required).
  ```python
  status = api.health_check()
  # Example response: {"status": "healthy", "timestamp": "2025-09-12T00:00:00Z"}
  ```

- **`close()`**: Closes the HTTP session and clears the auth key.
  ```python
  api.close()
  ```

### Error Handling
- **Authentication Errors**: Methods requiring authentication raise `ValueError` if `auth_key` is not set.
- **HTTP Errors**: Failed requests (e.g., 400, 401, 500) raise `requests.exceptions.HTTPError`. Before raising, the client prints:
  - Error message
  - Full response details (status code, headers, body)
- **Network Errors**: Issues like connection failures raise `requests.exceptions.RequestException` with details printed.
- **Session Errors**: File I/O errors in session management (e.g., saving/loading sessions) print error messages and return `False`.
- **Verbose Output**: Every API request outputs details in the following format:
  ```
  --- API Request: POST https://fragment.s1qwy.ru/create_auth ---
  Status Code: 200
  Headers: {'Content-Type': 'application/json', ...}
  Response Body: {
    "ok": true,
    "auth_key": "abc123"
  }
  --- End of Response ---
  ```

Example error output:
```
HTTP Error occurred: 401 Client Error: Unauthorized for url: https://fragment.s1qwy.ru/balance/abc123
Response details:
--- API Request: GET https://fragment.s1qwy.ru/balance/abc123 ---
Status Code: 401
Headers: {'Content-Type': 'application/json', ...}
Response Body: {
  "ok": false,
  "error": "Invalid authentication key"
}
--- End of Response ---
```

Wrap API calls in try-except blocks for robust error handling:
```python
try:
    balance = api.get_balance()
except ValueError as e:
    print(f"Auth error: {e}")
except requests.exceptions.HTTPError as e:
    print(f"HTTP error: {e}")
except requests.exceptions.RequestException as e:
    print(f"Request error: {e}")
```

## Examples
### Authenticate and Check Balance
```python
from fragment_api_py import FragmentAPI

api = FragmentAPI()
try:
    api.create_auth("mnemonic", "cookies", "hash")  # Prints response
    if api.has_valid_session():
        balance = api.get_balance()  # Prints response
        print(f"Balance: {balance.get('balance', 0)}")
except Exception as e:
    print(f"Error: {e}")
finally:
    api.close()
```

### Load Session and Buy Stars
```python
from fragment_api_py import FragmentAPI

api = FragmentAPI()
try:
    if api.load_session():
        result = api.buy_stars("@example_user", quantity=50)  # Prints response
        print(f"Transaction result: {result}")
    else:
        print("No valid session found")
except Exception as e:
    print(f"Error: {e}")
finally:
    api.close()
```

For additional examples, check the `examples/` directory in the source code (if provided) or the project's GitHub repository.

## Contributing
Contributions are welcome! To contribute:
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

Report bugs or suggest features via the project's GitHub issue tracker.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

For more information, visit the project on [PyPI](https://pypi.org/project/fragment-api-py/).
