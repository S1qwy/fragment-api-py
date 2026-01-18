# Fragment API Python Library

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://img.shields.io/badge/pypi-v3.0.2-blue.svg)](https://pypi.org/project/fragment-api-py/)

**[English Version](README.md)**

Профессиональная Python библиотека для API Fragment.com с полной поддержкой платежей Telegram. Отправляйте Telegram Stars, подписку Premium и криптовалюту TON с автоматической проверкой баланса кошелька и обработкой ошибок.

## Возможности

- ✅ **Асинхронный и синхронный интерфейсы** - Используйте async/await или традиционные блокирующие вызовы
- ✅ **3 товара** - Telegram Stars, подписки Premium и пополнение TON
- ✅ **Прямые TON переводы** - Отправляйте TON на любой адрес или username с поддержкой memo
- ✅ **Поиск получателя** - Получите информацию о пользователе и аватар перед отправкой платежа
- ✅ **Автоматическая проверка баланса** - Проверка баланса кошелька перед инициацией транзакции
- ✅ **Поддержка WalletV4R2** - Прямое взаимодействие с блокчейном TON
- ✅ **Комплексная обработка ошибок** - Специфичные исключения для разных сценариев ошибок
- ✅ **Type Hints** - Полные аннотации типов для автодополнения IDE
- ✅ **Детальное логирование** - Отслеживание API взаимодействий и ошибок
- ✅ **Логика повторов** - Автоматический повтор при сетевых сбоях
- ✅ **Контроль видимости отправителя** - Опциональные анонимные или указанные платежи

## Установка

### Через pip

```bash
pip install fragment-api-py
```

### Из исходников

```bash
git clone https://github.com/S1qwy/fragment-api-py.git
cd fragment-api-py
pip install -e .
```

## Быстрый старт

### Синхронный пример

```python
from FragmentAPI import SyncFragmentAPI

api = SyncFragmentAPI(
    cookies="stel_ssid=значение; stel_token=значение; ...",
    hash_value="ваш_хеш",
    wallet_mnemonic="abandon ability able abandon abandon abandon abandon abandon abandon abandon abandon about",
    wallet_api_key="ВАШ_TONCONSOLE_API_KEY"
)

# Получить информацию о получателе с аватаром
user = api.get_recipient_stars('username')
print(f"Имя: {user.name}")
print(f"Аватар: {user.avatar}")

# Отправить Telegram Stars (анонимно)
result = api.buy_stars('username', 100)
if result.success:
    print(f"✓ Транзакция: {result.transaction_hash}")
else:
    print(f"✗ Ошибка: {result.error}")

# Отправить с видимым отправителем
result = api.buy_stars('username', 100, show_sender=True)

# Прямой перевод TON
transfer = api.transfer_ton("recipient.t.me", 0.5, "Оплата за услуги")
if transfer.success:
    print(f"✓ Перевод: {transfer.transaction_hash}")

api.close()
```

### Асинхронный пример

```python
import asyncio
from FragmentAPI import AsyncFragmentAPI

async def main():
    api = AsyncFragmentAPI(
        cookies="stel_ssid=значение; stel_token=значение; ...",
        hash_value="ваш_хеш",
        wallet_mnemonic="abandon ability able abandon abandon abandon abandon abandon abandon abandon abandon about",
        wallet_api_key="ВАШ_TONCONSOLE_API_KEY"
    )
    
    # Получить информацию о получателе
    user = await api.get_recipient_stars('username')
    print(f"Имя: {user.name}")
    
    # Отправить Stars (анонимно)
    result = await api.buy_stars('username', 100)
    if result.success:
        print(f"✓ TX: {result.transaction_hash}")
    
    # Отправить с видимым отправителем
    result = await api.buy_stars('username', 100, show_sender=True)
    
    # Прямой перевод TON
    transfer = await api.transfer_ton("recipient.t.me", 0.5, "Оплата")
    if transfer.success:
        print(f"✓ Перевод: {transfer.transaction_hash}")
    
    await api.close()

asyncio.run(main())
```

## Настройка и конфигурация

### Шаг 1: Получите cookies Fragment

1. Откройте [fragment.com](https://fragment.com) в браузере
2. Нажмите `F12` чтобы открыть DevTools
3. Перейдите на вкладку `Application` → `Cookies`
4. Скопируйте следующие cookies:
   - `stel_ssid`
   - `stel_token`
   - `stel_dt`
   - `stel_ton_token`

5. Объедините их: `stel_ssid=значение; stel_token=значение; stel_dt=значение; stel_ton_token=значение`

### Шаг 2: Получите значение Hash

1. Откройте DevTools → вкладка `Network`
2. Сделайте любой запрос к fragment.com/api
3. Посмотрите запрос и скопируйте параметр `hash` из строки запроса

### Шаг 3: Настройте TON кошелек

1. Получите seed фразу из 24 слов из:
   - [Tonkeeper](https://tonkeeper.com/)
   - [MyTonWallet](https://www.mytonwallet.io/)
   - Любого другого TON кошелька

2. Пополните кошелек TON для транзакций

### Шаг 4: Получите TON API ключ

1. Перейдите на [tonconsole.com](https://tonconsole.com)
2. Создайте новый проект
3. Сгенерируйте API ключ из параметров проекта

### Шаг 5: Сохраните учетные данные безопасно

```bash
# .env файл
export FRAGMENT_COOKIES="stel_ssid=...; stel_token=..."
export FRAGMENT_HASH="ваш_хеш_здесь"
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

## Справочник API

### Методы получения информации о получателе

#### `get_recipient_stars(username: str) → UserInfo`

Получить информацию о получателе для отправки Telegram Stars.

**Параметры:**
- `username` (str): Целевое имя пользователя (с @ или без)

**Возвращает:** объект `UserInfo` с:
- `name` (str) - Отображаемое имя пользователя
- `recipient` (str) - Адрес блокчейна
- `avatar` (str) - URL аватара или base64 закодированное изображение
- `found` (bool) - Флаг успешного поиска

**Вызывает исключения:**
- `UserNotFoundError` - Пользователь не найден
- `NetworkError` - Ошибка API запроса
- `AuthenticationError` - Сеанс истек

**Пример:**
```python
user = api.get_recipient_stars('jane_doe')
print(f"Имя: {user.name}")
print(f"Адрес: {user.recipient}")
print(f"Аватар: {user.avatar}")
```

#### `get_recipient_premium(username: str) → UserInfo`

Получить информацию о получателе для подарка Premium.

**Параметры:**
- `username` (str): Целевое имя пользователя

**Возвращает:** объект `UserInfo`

**Вызывает исключения:**
- `UserNotFoundError` - Пользователь не найден, уже имеет Premium или не может получить подарок
- `NetworkError` - Ошибка API запроса
- `AuthenticationError` - Сеанс истек

**Пример:**
```python
user = api.get_recipient_premium('jane_doe')
if user.found:
    print(f"Можно подарить Premium: {user.name}")
else:
    print("Пользователь не найден или уже имеет Premium")
```

#### `get_recipient_ton(username: str) → UserInfo`

Получить информацию о получателе для пополнения баланса TON в Telegram.

**Параметры:**
- `username` (str): Целевое имя пользователя

**Возвращает:** объект `UserInfo`

**Вызывает исключения:**
- `UserNotFoundError` - Пользователь не найден
- `NetworkError` - Ошибка API запроса
- `AuthenticationError` - Сеанс истек

**Пример:**
```python
user = api.get_recipient_ton('jane_doe')
print(f"Имя: {user.name}")
```

### Методы платежей

#### `buy_stars(username: str, quantity: int, show_sender: bool = False) → PurchaseResult`

Отправить Telegram Stars пользователю.

**Параметры:**
- `username` (str): Целевое имя пользователя (5-32 символов)
- `quantity` (int): Количество звезд для отправки (1-999999)
- `show_sender` (bool, опционально): Показывать ли информацию об отправителе. По умолчанию: `False` (анонимно)

**Возвращает:** `PurchaseResult` с:
- `success` (bool) - Статус успешности транзакции
- `transaction_hash` (str | None) - Хеш TX блокчейна если успешно
- `error` (str | None) - Сообщение об ошибке если не успешно
- `user` (UserInfo | None) - Информация о получателе
- `balance_checked` (bool) - Была ли проверена проверка баланса перед транзакцией
- `required_amount` (float | None) - Общее требуемое количество TON (сумма + комиссия)

**Вызывает исключения:**
- `UserNotFoundError` - Пользователь не существует
- `InvalidAmountError` - Количество вне допустимого диапазона
- `InsufficientBalanceError` - Недостаточно средств в кошельке
- `AuthenticationError` - Сеанс истек
- `NetworkError` - Ошибка сетевого запроса

**Примеры:**

```python
# Анонимная отправка (по умолчанию)
result = api.buy_stars('username', 100)

if result.success:
    print(f"✓ Звезды отправлены успешно!")
    print(f"Транзакция: {result.transaction_hash}")
    print(f"Получатель: {result.user.name}")
    print(f"Требуемая сумма: {result.required_amount} TON")
else:
    print(f"✗ Ошибка: {result.error}")
```

```python
# Отправить с видимым отправителем
result = api.buy_stars('username', 100, show_sender=True)

if result.success:
    print(f"✓ Звезды отправлены (отправитель видим)")
    print(f"Транзакция: {result.transaction_hash}")
else:
    print(f"✗ Ошибка: {result.error}")
```

```python
# Асинхронная версия
result = await api.buy_stars('username', 100, show_sender=True)
```

#### `gift_premium(username: str, months: int = 3, show_sender: bool = False) → PurchaseResult`

Подарить подписку Premium пользователю.

**Параметры:**
- `username` (str): Целевое имя пользователя
- `months` (int): Продолжительность подписки. Допустимые значения: 3, 6 или 12. По умолчанию: `3`
- `show_sender` (bool, опционально): Показывать ли информацию об отправителе. По умолчанию: `False` (анонимно)

**Возвращает:** `PurchaseResult`

**Вызывает исключения:**
- `UserNotFoundError` - Пользователь не существует, уже имеет Premium или не может получить подарок
- `InvalidAmountError` - Месяцы не в [3, 6, 12]
- `InsufficientBalanceError` - Недостаточно средств в кошельке
- `AuthenticationError` - Сеанс истек
- `NetworkError` - Ошибка сетевого запроса

**Примеры:**

```python
# Анонимный подарок Premium (3 месяца по умолчанию)
result = api.gift_premium('username')

if result.success:
    print(f"✓ Premium подарен на 3 месяца!")
    print(f"Транзакция: {result.transaction_hash}")
else:
    print(f"✗ Ошибка: {result.error}")
```

```python
# Подарить на 6 месяцев с видимым отправителем
result = api.gift_premium('username', months=6, show_sender=True)

if result.success:
    print(f"✓ Premium подарен на 6 месяцев (отправитель видим)")
else:
    print(f"✗ Ошибка: {result.error}")
```

```python
# Подарить на 12 месяцев (анонимно)
result = api.gift_premium('username', months=12)
```

```python
# Асинхронная версия
result = await api.gift_premium('username', months=6, show_sender=True)
```

#### `topup_ton(username: str, amount: int, show_sender: bool = False) → PurchaseResult`

Пополнить аккаунт Telegram криптовалютой TON.

**Параметры:**
- `username` (str): Целевое имя пользователя
- `amount` (int): Количество TON для отправки (1-999999)
- `show_sender` (bool, опционально): Показывать ли информацию об отправителе. По умолчанию: `False` (анонимно)

**Возвращает:** `PurchaseResult`

**Вызывает исключения:**
- `UserNotFoundError` - Пользователь не существует
- `InvalidAmountError` - Сумма вне допустимого диапазона
- `InsufficientBalanceError` - Недостаточно средств в кошельке
- `AuthenticationError` - Сеанс истек
- `NetworkError` - Ошибка сетевого запроса

**Примеры:**

```python
# Анонимное пополнение
result = api.topup_ton('jane_doe', 10)

if result.success:
    print(f"✓ Пополнено на 10 TON")
    print(f"Транзакция: {result.transaction_hash}")
else:
    print(f"✗ Ошибка: {result.error}")
```

```python
# Пополнение с видимым отправителем
result = api.topup_ton('jane_doe', 10, show_sender=True)

if result.success:
    print(f"✓ Пополнение отправлено (отправитель видим)")
else:
    print(f"✗ Ошибка: {result.error}")
```

```python
# Асинхронная версия
result = await api.topup_ton('jane_doe', 10, show_sender=True)
```

#### `transfer_ton(to_address: str, amount: float, memo: str = None) → TransferResult`

Отправить TON напрямую на любой адрес или Telegram username.

**Параметры:**
- `to_address` (str): Адрес назначения (TON адрес или username вида `user.t.me`)
- `amount` (float): Количество TON для отправки
- `memo` (str, опционально): Комментарий/memo для транзакции

**Возвращает:** `TransferResult` с:
- `success` (bool) - Статус успешности перевода
- `transaction_hash` (str | None) - Хеш TX блокчейна если успешно
- `memo` (str | None) - Memo включенный в транзакцию
- `error` (str | None) - Сообщение об ошибке если не успешно

**Вызывает исключения:**
- `InvalidAmountError` - Сумма невалидна
- `InsufficientBalanceError` - Недостаточно средств в кошельке
- `WalletError` - Ошибка операции кошелька
- `NetworkError` - Ошибка сетевого запроса

**Примеры:**

```python
# Перевод на username (формат t.me)
result = api.transfer_ton("username.t.me", 0.5, "Оплата за услуги")

if result.success:
    print(f"✓ Перевод успешен!")
    print(f"Хеш: {result.transaction_hash}")
    print(f"Memo: {result.memo}")
else:
    print(f"✗ Ошибка: {result.error}")
```

```python
# Перевод на TON адрес
result = api.transfer_ton("EQDrjaLahLkMB-hMCmkzOyBuHJ139ZUYmPHu6RRBKnbRELWt", 1.0)

if result.success:
    print(f"✓ Хеш: {result.transaction_hash}")
else:
    print(f"✗ Ошибка: {result.error}")
```

```python
# Перевод без memo
result = api.transfer_ton("username.t.me", 0.01)
```

```python
# Асинхронная версия
result = await api.transfer_ton("username.t.me", 0.5, "async платеж")

if result.success:
    print(f"✓ Хеш: {result.transaction_hash}")
    print(f"Memo: {result.memo}")
```

### Методы кошелька

#### `get_wallet_balance() → Dict[str, Any]`

Получить текущий баланс кошелька и адрес (синхронный).

**Возвращает:** Словарь с:
- `balance_ton` (float) - Баланс в TON
- `balance_nano` (str) - Баланс в нанотонах
- `address` (str) - Адрес кошелька в блокчейне
- `is_ready` (bool) - Статус готовности кошелька

**Вызывает исключения:**
- `WalletError` - Ошибка при получении баланса

**Пример:**
```python
balance_info = api.get_wallet_balance()
print(f"Баланс: {balance_info['balance_ton']} TON")
print(f"Адрес: {balance_info['address']}")
print(f"Готов: {balance_info['is_ready']}")
```

#### `async get_wallet_balance() → Dict[str, Any]` (Асинхронная версия)

Получить текущий баланс кошелька и адрес (асинхронный).

**Возвращает:** Словарь с:
- `balance_ton` (float) - Баланс в TON
- `balance_nano` (str) - Баланс в нанотонах
- `address` (str) - Адрес кошелька в блокчейне
- `is_ready` (bool) - Статус готовности кошелька

**Вызывает исключения:**
- `WalletError` - Ошибка при получении баланса

**Пример:**
```python
balance_info = await api.get_wallet_balance()
print(f"Баланс: {balance_info['balance_ton']} TON")
```

## Обработка исключений

Библиотека предоставляет специфичные исключения для разных сценариев ошибок:

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
        print(f"Транзакция не прошла: {result.error}")
        
except UserNotFoundError as e:
    print(f"Пользователь не найден: {e}")
    
except InvalidAmountError as e:
    print(f"Неверная сумма: {e}")
    
except InsufficientBalanceError as e:
    print(f"Низкий баланс кошелька: {e}")
    print("Пожалуйста, пополните кошелек")
    
except AuthenticationError as e:
    print(f"Ошибка аутентификации: {e}")
    print("Обновите ваши cookies с fragment.com")
    
except NetworkError as e:
    print(f"Ошибка сети: {e}")
    
except TransactionError as e:
    print(f"Ошибка транзакции: {e}")
    
except PaymentInitiationError as e:
    print(f"Не удается инициировать платеж: {e}")
    
except RateLimitError as e:
    print(f"Превышен лимит запросов: {e}")
    print("Подождите перед повторной попыткой")
    
except WalletError as e:
    print(f"Ошибка кошелька: {e}")
    
except FragmentAPIException as e:
    print(f"Ошибка API: {e}")
```

### Иерархия исключений

```
FragmentAPIException (базовое)
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

## Модели данных

### UserInfo

```python
@dataclass
class UserInfo:
    name: str           # Отображаемое имя пользователя
    recipient: str      # Адрес блокчейна
    found: bool         # Был ли пользователь найден
    avatar: str = ""    # URL аватара или base64 закодированное изображение
```

**Пример:**
```python
user = api.get_recipient_stars('jane_doe')
print(f"Имя: {user.name}")
print(f"Получатель: {user.recipient}")
print(f"Аватар: {user.avatar}")
print(f"Найден: {user.found}")
```

### PurchaseResult

```python
@dataclass
class PurchaseResult:
    success: bool                    # Была ли транзакция успешной
    transaction_hash: Optional[str]  # Хеш TX блокчейна
    error: Optional[str]            # Сообщение об ошибке если не успешно
    user: Optional[UserInfo]        # Информация о получателе
    balance_checked: bool           # Была ли проверена баланс
    required_amount: Optional[float] # Общее требуемое количество TON
```

**Пример:**
```python
result = api.buy_stars('username', 100, show_sender=True)

if result.success:
    print(f"✓ Успешно: {result.transaction_hash}")
    print(f"Получатель: {result.user.name}")
    print(f"Требуется: {result.required_amount} TON")
    print(f"Баланс проверен: {result.balance_checked}")
else:
    print(f"✗ Ошибка: {result.error}")
```

### TransferResult

```python
@dataclass
class TransferResult:
    success: bool                    # Был ли перевод успешным
    transaction_hash: Optional[str]  # Хеш TX блокчейна
    memo: Optional[str]              # Memo/комментарий включенный в транзакцию
    error: Optional[str]             # Сообщение об ошибке если не успешно
```

**Пример:**
```python
result = api.transfer_ton("username.t.me", 0.5, "оплата за услуги")

if result.success:
    print(f"✓ Успешно: {result.transaction_hash}")
    print(f"Memo: {result.memo}")
else:
    print(f"✗ Ошибка: {result.error}")
```

### WalletBalance

```python
@dataclass
class WalletBalance:
    balance_nano: str    # Баланс в нанотонах
    balance_ton: float   # Баланс в TON
    address: str         # Адрес блокчейна
    is_ready: bool       # Статус готовности кошелька
```

## Использование Context Manager

### Синхронный

```python
with SyncFragmentAPI(cookies, hash_value, mnemonic, api_key) as api:
    result = api.buy_stars('username', 50)
    result = api.gift_premium('username', 6, show_sender=True)
    transfer = api.transfer_ton("recipient.t.me", 0.1, "тест")
    # Соединение закроется автоматически
```

### Асинхронный

```python
async with AsyncFragmentAPI(cookies, hash_value, mnemonic, api_key) as api:
    result = await api.buy_stars('username', 50)
    result = await api.gift_premium('username', 6, show_sender=True)
    transfer = await api.transfer_ton("recipient.t.me", 0.1, "тест")
    # Соединение закроется автоматически
```

## Продвинутое использование

### Массовые операции

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
            visibility = "видим" if show_sender else "аноним"
            print(f"✓ {username} ({visibility}): {result.transaction_hash}")
        else:
            print(f"✗ {username}: {result.error}")
    except Exception as e:
        print(f"✗ {username}: {type(e).__name__}: {e}")

api.close()
```

### Асинхронные параллельные операции

```python
import asyncio
from FragmentAPI import AsyncFragmentAPI

async def send_stars_batch(api, users):
    """Отправить звезды нескольким пользователям одновременно"""
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
            visibility = "видим" if user.get('show_sender') else "аноним"
            print(f"✓ {user['username']} ({visibility}): {result.transaction_hash}")
        else:
            print(f"✗ {user['username']}: {result.error}")
    
    await api.close()

asyncio.run(main())
```

### Прямой перевод TON

```python
import asyncio
from FragmentAPI import AsyncFragmentAPI, SyncFragmentAPI

# Синхронный пример
api = SyncFragmentAPI(cookies, hash_value, mnemonic, api_key)

# Сначала проверить баланс
balance = api.get_wallet_balance()
print(f"Баланс: {balance['balance_ton']} TON")
print(f"Адрес: {balance['address']}")

# Перевод на username с memo
result = api.transfer_ton("username.t.me", 0.01, "тестовый платеж")

if result.success:
    print(f"✓ Успех! Хеш: {result.transaction_hash}")
    print(f"Memo: {result.memo}")
else:
    print(f"✗ Ошибка: {result.error}")

api.close()

# Асинхронный пример
async def transfer_async():
    api = AsyncFragmentAPI(cookies, hash_value, mnemonic, api_key)
    
    balance = await api.get_wallet_balance()
    print(f"Баланс: {balance['balance_ton']} TON")
    print(f"Адрес: {balance['address']}")
    
    # Перевод на TON адрес
    result = await api.transfer_ton(
        "EQDrjaLahLkMB-hMCmkzOyBuHJ139ZUYmPHu6RRBKnbRELWt",
        0.5,
        "async платеж"
    )
    
    if result.success:
        print(f"✓ Успех! Хеш: {result.transaction_hash}")
        print(f"Memo: {result.memo}")
    else:
        print(f"✗ Ошибка: {result.error}")
    
    await api.close()

asyncio.run(transfer_async())
```

### Предварительная проверка перед платежом

```python
api = SyncFragmentAPI(cookies, hash_value, mnemonic, api_key)

username = 'jane_doe'
quantity = 100
show_sender = True

# Проверить что получатель существует
try:
    user = api.get_recipient_stars(username)
    print(f"✓ Пользователь найден: {user.name}")
    if user.avatar:
        print(f"✓ Аватар: {user.avatar[:50]}...")
except UserNotFoundError as e:
    print(f"✗ Пользователь не найден: {e}")
    exit(1)

# Проверить баланс кошелька
try:
    balance = api.get_wallet_balance()
    print(f"✓ Баланс кошелька: {balance['balance_ton']} TON")
    print(f"✓ Адрес: {balance['address']}")
except WalletError as e:
    print(f"✗ Ошибка кошелька: {e}")
    exit(1)

# Проверить достаточность баланса
estimated_fee = 0.001
estimated_total = quantity * 0.00001 + estimated_fee  # Примерная оценка
if float(balance['balance_ton']) < estimated_total:
    print(f"✗ Недостаточно средств")
    print(f"  Требуется: ~{estimated_total} TON")
    print(f"  Доступно: {balance['balance_ton']} TON")
    exit(1)

# Отправить платеж с видимым отправителем
print(f"\nОтправляю {quantity} звезд пользователю {username} (отправитель видим)...")
result = api.buy_stars(username, quantity, show_sender=show_sender)

if result.success:
    print(f"✓ Успешно!")
    print(f"  Транзакция: {result.transaction_hash}")
    print(f"  Получатель: {result.user.name}")
    print(f"  Требуется: {result.required_amount} TON")
    print(f"  Баланс проверен: {result.balance_checked}")
else:
    print(f"✗ Ошибка: {result.error}")

api.close()
```

### Подарок Premium с проверкой

```python
api = SyncFragmentAPI(cookies, hash_value, mnemonic, api_key)

username = 'jane_doe'
months = 6

# Проверить что получатель может получить Premium
try:
    user = api.get_recipient_premium(username)
    print(f"✓ Можно подарить Premium: {user.name}")
except UserNotFoundError as e:
    print(f"✗ Не удается подарить: {e}")
    exit(1)

# Проверить баланс
balance_info = api.get_wallet_balance()
print(f"Баланс кошелька: {balance_info['balance_ton']} TON")

# Отправить подарок Premium (анонимно)
print(f"\nДарю {months}-месячный Premium пользователю {username}...")
result = api.gift_premium(username, months=months)

if result.success:
    print(f"✓ Premium подарен!")
    print(f"  Месяцев: {months}")
    print(f"  Получатель: {result.user.name}")
    print(f"  Транзакция: {result.transaction_hash}")
else:
    print(f"✗ Ошибка: {result.error}")

api.close()
```

### Примеры видимости отправителя

```python
api = SyncFragmentAPI(cookies, hash_value, mnemonic, api_key)

# Отправить анонимно (поведение по умолчанию)
result1 = api.buy_stars('user1', 100)
# Получатель не узнает кто отправил

# Отправить с видимым отправителем
result2 = api.buy_stars('user2', 100, show_sender=True)
# Получатель увидит ваш аккаунт

# Подарок Premium анонимно
result3 = api.gift_premium('user3', 6)
# Получатель не узнает кто подарил

# Подарок Premium видимо
result4 = api.gift_premium('user4', 6, show_sender=True)
# Получатель увидит ваш аккаунт в информации о подарке

# Пополнение TON анонимно
result5 = api.topup_ton('ads_account1', 10)
# Владелец аккаунта не увидит отправителя

# Пополнение TON видимо
result6 = api.topup_ton('ads_account2', 10, show_sender=True)
# Владелец аккаунта увидит ваш аккаунт

# Прямой перевод (всегда видим - блокчейн публичный)
result7 = api.transfer_ton('recipient.t.me', 0.5, 'платеж')
# Адрес отправителя видим в блокчейне

api.close()
```

## Требования

- Python 3.7+
- `requests >= 2.28.0`
- `aiohttp >= 3.8.0`
- `tonutils >= 0.3.0`
- `pytoniq-core >= 0.1.0`
- `httpx >= 0.23.0`

## Установка с зависимостями

```bash
pip install fragment-api-py
```

Все зависимости установятся автоматически.

## Переменные окружения

```bash
# Обязательные
FRAGMENT_COOKIES="stel_ssid=...; stel_token=..."
FRAGMENT_HASH="abc123def456"
WALLET_MNEMONIC="abandon ability able ... about"
WALLET_API_KEY="AHQSQGXHKZZS..."

# Опциональные
FRAGMENT_TIMEOUT=15  # Timeout запроса в секундах
```

## Логирование

Включите отладочное логирование для просмотра API взаимодействий:

```python
import logging

# Установить логирование
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Включить отладку для Fragment API
logger = logging.getLogger('fragment_api')
logger.setLevel(logging.DEBUG)

# Теперь все вызовы API будут залогированы
api = SyncFragmentAPI(cookies, hash_value, mnemonic, api_key)
result = api.buy_stars('username', 100, show_sender=True)
```

**Пример вывода логов:**
```
2024-01-15 10:30:45,123 - FragmentAPI - DEBUG - Делаю запрос к Fragment API
2024-01-15 10:30:45,456 - FragmentAPI - DEBUG - Пользователь найден: jane_doe
2024-01-15 10:30:45,789 - FragmentAPI - DEBUG - Баланс кошелька: 5.123456 TON
2024-01-15 10:30:46,123 - FragmentAPI - INFO - Транзакция отправлена: EQA...
2024-01-15 10:30:46,456 - FragmentAPI - DEBUG - Транзакция успешна
```

## Ограничение частоты запросов

Библиотека реализует автоматическую логику повтора с экспоненциальной задержкой:

- **Максимум повторов:** 3
- **Timeout:** 15 секунд (настраивается)
- **Автоматический повтор при:**
  - Timeout сетевого запроса
  - Ошибках соединения
  - Временных проблемах сервера

**Пример с пользовательским timeout:**
```python
api = SyncFragmentAPI(
    cookies=cookies,
    hash_value=hash_value,
    wallet_mnemonic=mnemonic,
    wallet_api_key=api_key,
    timeout=30  # 30 секундный timeout
)
```

## Частые проблемы и решения

### "Session expired"
**Проблема:** `AuthenticationError: Session expired: please update cookies`

**Решения:**
- Обновите ваши cookies с fragment.com
- Убедитесь что вы скопировали ВСЕ необходимые cookies (stel_ssid, stel_token, stel_dt, stel_ton_token)
- Cookies истекают со временем, обновляйте их регулярно

```python
# Обновить cookies
api = SyncFragmentAPI(
    cookies="НОВЫЕ_COOKIES_ЗДЕСЬ",  # Обновите свежими cookies
    hash_value=hash_value,
    wallet_mnemonic=mnemonic,
    wallet_api_key=api_key
)
```

### "User not found"
**Проблема:** `UserNotFoundError: User not found`

**Решения:**
- Проверьте что пользователь существует в Telegram
- Имя пользователя должно быть 5-32 символов
- Разрешены только буквы, цифры и подчеркивание
- Удалите @ если включен

```python
from FragmentAPI.utils import validate_username

# Проверить валидность имени
if not validate_username('jane_doe'):
    print("Неверный формат имени пользователя")

# Использование
user = api.get_recipient_stars('jane_doe')  # ✓ Правильно
user = api.get_recipient_stars('john')      # ✗ Слишком короткое
user = api.get_recipient_stars('@jane_doe') # ✓ Работает (@ удаляется)
```

### "Insufficient balance"
**Проблема:** `InsufficientBalanceError: Insufficient balance`

**Решения:**
- Проверьте баланс кошелька перед отправкой
- Убедитесь что кошелек пополнен TON
- Учитывайте комиссию (~0.001 TON)
- Библиотека автоматически проверяет баланс

```python
# Проверить баланс
balance_info = api.get_wallet_balance()
print(f"Доступно: {balance_info['balance_ton']} TON")

# Попытаться отправить (будет ошибка InsufficientBalanceError)
try:
    result = api.buy_stars('username', 100)
except InsufficientBalanceError as e:
    print(f"Ошибка: {e}")
    # Пополните кошелек
```

### "Invalid hash"
**Проблема:** `NetworkError: Request failed`

**Решения:**
- Заново скопируйте hash из DevTools Network tab
- Убедитесь что hash из запроса к fragment.com/api
- Hash может истечь, обновите его

```python
# Шаги для получения hash:
# 1. Откройте fragment.com в браузере
# 2. Нажмите F12 чтобы открыть DevTools
# 3. Перейдите на вкладку Network
# 4. Сделайте любой API запрос
# 5. Скопируйте параметр 'hash' из строки запроса

api = SyncFragmentAPI(
    cookies=cookies,
    hash_value="ПРАВИЛЬНЫЙ_HASH_ЗДЕСЬ",  # Обновите hash
    wallet_mnemonic=mnemonic,
    wallet_api_key=api_key
)
```

### "Invalid quantity/amount"
**Проблема:** `InvalidAmountError: Invalid quantity`

**Решения:**
- Количество должно быть между 1 и 999999
- Месяцы должны быть 3, 6 или 12 для Premium
- Сумма должна быть между 1 и 999999 для TON

```python
from FragmentAPI.utils import validate_amount

# Проверить валидность суммы
validate_amount(100, 1, 999999)  # ✓ True
validate_amount(0, 1, 999999)    # ✗ False (слишком мало)
validate_amount(1000000, 1, 999999)  # ✗ False (слишком много)

# Использование
result = api.buy_stars('username', 100)      # ✓ Валидно
result = api.buy_stars('username', 0)        # ✗ Невалидно
result = api.gift_premium('username', 3)     # ✓ Валидно
result = api.gift_premium('username', 5)     # ✗ Невалидно (должно быть 3, 6 или 12)
```

## Лучшие практики безопасности

### 1. Никогда не hardcode учетные данные

```python
# ❌ НЕПРАВИЛЬНО - Никогда не делайте так!
api = SyncFragmentAPI(
    cookies="stel_ssid=abc123; stel_token=xyz789",
    hash_value="ваш_реальный_хеш_здесь"
)

# ✅ ПРАВИЛЬНО - Используйте переменные окружения
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

### 2. Используйте .env файл (добавьте в .gitignore)

```bash
# .env файл
FRAGMENT_COOKIES="stel_ssid=...; stel_token=..."
FRAGMENT_HASH="ваш_хеш_здесь"
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

### 3. Валидируйте пользовательский ввод

```python
from FragmentAPI.utils import validate_username, validate_amount
from FragmentAPI import UserNotFoundError, InvalidAmountError

def safe_send_stars(api, username, quantity):
    """Безопасно отправить звезды с валидацией"""
    
    # Валидировать имя пользователя
    if not validate_username(username):
        raise UserNotFoundError(f"Неверное имя: {username}")
    
    # Валидировать количество
    if not validate_amount(quantity, 1, 999999):
        raise InvalidAmountError(f"Неверное количество: {quantity}")
    
    # Отправить
    return api.buy_stars(username, quantity)

# Использование
try:
    result = safe_send_stars(api, 'jane_doe', 100)
except UserNotFoundError as e:
    print(f"Неверное имя: {e}")
except InvalidAmountError as e:
    print(f"Неверное количество: {e}")
```

### 4. Правильно обрабатывайте исключения

```python
import logging

logger = logging.getLogger(__name__)

def send_payment_safely(api, username, quantity, show_sender=False):
    """Отправить платеж с полной обработкой ошибок"""
    
    try:
        result = api.buy_stars(username, quantity, show_sender=show_sender)
        
        if result.success:
            logger.info(f"Платеж успешен: {result.transaction_hash}")
            return result
        else:
            logger.error(f"Платеж не прошел: {result.error}")
            return result
            
    except UserNotFoundError as e:
        logger.error(f"Пользователь не найден: {e}")
        return None
        
    except InsufficientBalanceError as e:
        logger.error(f"Недостаточно средств: {e}")
        return None
        
    except AuthenticationError as e:
        logger.error(f"Ошибка аутентификации: {e}")
        logger.info("Пожалуйста обновите ваши cookies с fragment.com")
        return None
        
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}", exc_info=True)
        # Не раскрывайте чувствительные данные пользователям
        return None

# Использование
result = send_payment_safely(api, 'username', 100, show_sender=True)
```

### 5. Используйте timeout для предотвращения зависания

```python
# Установить timeout запроса чтобы предотвратить бесконечное ожидание
api = SyncFragmentAPI(
    cookies=cookies,
    hash_value=hash_value,
    wallet_mnemonic=mnemonic,
    wallet_api_key=api_key,
    timeout=15  # 15 секундный timeout
)
```

### 6. Ограничение частоты и задержки

```python
import time
from FragmentAPI import RateLimitError

def send_with_delays(api, users, delay_seconds=2):
    """Отправить звезды нескольким пользователям с задержками"""
    
    for username, quantity in users:
        try:
            result = api.buy_stars(username, quantity)
            
            if result.success:
                print(f"✓ {username}: {result.transaction_hash}")
            else:
                print(f"✗ {username}: {result.error}")
                
        except RateLimitError as e:
            print(f"Лимит запросов превышен, жду 60 секунд...")
            time.sleep(60)
            # Повторить попытку
            result = api.buy_stars(username, quantity)
            
        except Exception as e:
            print(f"✗ {username}: {type(e).__name__}")
        
        # Ждите перед следующим запросом
        time.sleep(delay_seconds)

# Использование
users = [('user1', 10), ('user2', 20), ('user3', 15)]
send_with_delays(api, users, delay_seconds=2)
```

## Участие в разработке

Вклады приветствуются! Пожалуйста следуйте этим шагам:

1. Сделайте fork репозитория
2. Создайте ветку для функции (`git checkout -b feature/amazing-feature`)
3. Commit ваши изменения (`git commit -m 'Add amazing feature'`)
4. Push на ветку (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## Лицензия

Этот проект лицензирован под MIT License - смотрите [LICENSE](LICENSE) файл для деталей.

## Отказ от ответственности

⚠️ **Важно:**

Эта библиотека **НЕ аффилирована** с Fragment.com или Telegram. Используйте на свой риск. Автор не несет ответственность за какие-либо потери или убытки, связанные с использованием этой библиотеки.

## Поддержка

Для проблем, вопросов или запросов функций:

1. Проверьте существующие [GitHub Issues](https://github.com/S1qwy/fragment-api-py/issues)
2. Создайте новый issue с:
   - Четким описанием
   - Сообщением об ошибке (без учетных данных)
   - Шагами для воспроизведения
   - Информацией о вашем окружении
