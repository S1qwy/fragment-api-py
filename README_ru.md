# Клиент FragmentAPI для Python

[![PyPI version](https://badge.fury.io/py/fragment-api-py.svg)](https://badge.fury.io/py/fragment-api-py)
[![Python versions](https://img.shields.io/pypi/pyversions/fragment-api-py.svg)](https://pypi.org/project/fragment-api-py/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**[Читать на английском (English version)](README.md)**

Библиотека Python для взаимодействия с Fragment API, предназначенная для управления аутентификацией, сессиями и транзакциями в Telegram, такими как покупка Telegram Stars, подарок Telegram Premium и пополнение TON.

## Содержание
- [Обзор](#обзор)
- [Установка](#установка)
- [Использование](#использование)
  - [Инициализация](#инициализация)
  - [Аутентификация](#аутентификация)
  - [Управление сессиями](#управление-сессиями)
  - [Методы API](#методы-api)
  - [Обработка ошибок](#обработка-ошибок)
- [Примеры](#примеры)
- [Как внести вклад](#как-внести-вклад)
- [Лицензия](#лицензия)

## Обзор
Класс `FragmentAPI` предоставляет удобный интерфейс для взаимодействия с Fragment API (`https://fragment.s1qwy.ru`). Поддерживаемые функции:
- Аутентификация с использованием мнемонической фразы кошелька, куки и хэш-значения.
- Управление сессиями (сохранение, загрузка, удаление сессий).
- Получение баланса кошелька.
- Выполнение транзакций в Telegram (покупка Stars, подарок Premium, пополнение TON).
- Запрос информации о пользователях для транзакций Stars и Premium.
- Проверка состояния API.

Клиент использует библиотеку `requests` для HTTP-взаимодействия и включает подробное логирование ответов сервера для отладки, выводя полный ответ сервера (код состояния, заголовки и тело) для каждого запроса API.

## Установка
Установите пакет непосредственно из PyPI с помощью pip:

```bash
pip install fragment-api-py
```

### Требования
- Python 3.6 или выше
- Библиотека `requests` (устанавливается автоматически как зависимость)

Для проверки установки выполните:
```bash
pip show fragment-api-py
```

Для разработки клонируйте репозиторий (если доступен) и установите в режиме редактирования:
```bash
git clone https://github.com/your-username/fragment-api-py.git
cd fragment-api-py
pip install -e .
```

## Использование

### Инициализация
Импортируйте и создайте экземпляр класса `FragmentAPI`, при необходимости указав базовый URL.

```python
from fragment_api import FragmentAPI  # Настройте импорт в зависимости от структуры пакета

# Инициализация с базовым URL по умолчанию
api = FragmentAPI()

# Или укажите пользовательский базовый URL
api = FragmentAPI(base_url="https://custom-fragment-api.com")
```

### Аутентификация
Аутентифицируйтесь в API, используя мнемоническую фразу кошелька, куки и хэш-значение. Полный ответ сервера (код состояния, заголовки, тело) выводится для прозрачности.

```python
result = api.create_auth(
    wallet_mnemonic="ваша мнемоническая фраза",
    cookies="ваши куки сессии",
    hash_value="ваше хэш-значение"
)
print(result)  # Содержит auth_key при успешной аутентификации
```

### Управление сессиями
- **Сохранение сессии**: Сохраняет ключ аутентификации в файл (по умолчанию: `fragment_session.json`).
  ```python
  api.save_session()  # Имя файла по умолчанию
  api.save_session("custom_session.json")  # Пользовательское имя файла
  ```
- **Загрузка сессии**: Загружает ранее сохраненную сессию.
  ```python
  api.load_session()  # Имя файла по умолчанию
  api.load_session("custom_session.json")  # Пользовательское имя файла
  ```
- **Удаление сессии**: Удаляет сохраненный файл сессии и очищает ключ аутентификации.
  ```python
  api.delete_session()
  api.delete_session("custom_session.json")  # Пользовательское имя файла
  ```
- **Проверка действующей сессии**: Проверяет наличие активной сессии.
  ```python
  if api.has_valid_session():
      print("Доступна действующая сессия")
  ```

### Методы API
Все методы, требующие аутентификации (`get_balance`, `buy_stars`, `gift_premium`, `topup_ton`, `get_user_stars`, `get_user_premium`), вызывают исключение `ValueError`, если ключ `auth_key` не установлен. Каждый запрос API выводит полный ответ сервера, включая код состояния, заголовки и тело (JSON, если возможно, иначе необработанный текст).

- **`get_balance()`**: Получает баланс кошелька.
  ```python
  balance = api.get_balance()
  # Пример ответа: {"ok": true, "balance": 100.50}
  ```

- **`buy_stars(username, quantity=50, show_sender=False)`**: Покупает Telegram Stars для пользователя (имя пользователя с префиксом @).
  ```python
  result = api.buy_stars("@username", quantity=100, show_sender=True)
  # Пример ответа: {"ok": true, "transaction_hash": "abc123"}
  ```

- **`gift_premium(username, months=3, show_sender=False)`**: Делает подарок Telegram Premium пользователю.
  ```python
  result = api.gift_premium("@username", months=6, show_sender=True)
  # Пример ответа: {"ok": true, "transaction_hash": "xyz789"}
  ```

- **`topup_ton(username, amount, show_sender=False)`**: Пополняет баланс TON для пользователя.
  ```python
  result = api.topup_ton("@username", amount=10, show_sender=True)
  # Пример ответа: {"ok": true, "transaction_hash": "def456"}
  ```

- **`get_user_stars(username)`**: Запрашивает информацию о пользователе для транзакций Telegram Stars.
  ```python
  result = api.get_user_stars("@username")
  ```

- **`get_user_premium(username)`**: Запрашивает информацию о пользователе для транзакций Telegram Premium.
  ```python
  result = api.get_user_premium("@username")
  ```

- **`health_check()`**: Проверяет состояние API (аутентификация не требуется).
  ```python
  status = api.health_check()
  # Пример ответа: {"ok": true, "timestamp": "2025-09-12T00:00:00Z"}
  ```

- **`close()`**: Закрывает HTTP-сессию и очищает ключ аутентификации.
  ```python
  api.close()
  ```

### Обработка ошибок
- **Ошибки аутентификации**: Методы, требующие аутентификации, вызывают `ValueError`, если `auth_key` не установлен.
- **HTTP-ошибки**: Неудавшиеся запросы (например, 400, 401, 500) вызывают `requests.exceptions.HTTPError`. Перед вызовом исключения клиент выводит:
  - Сообщение об ошибке
  - Полные детали ответа (код состояния, заголовки, тело)
- **Сетевые ошибки**: Проблемы, такие как сбои соединения, вызывают `requests.exceptions.RequestException` с выводом деталей.
- **Ошибки сессий**: Ошибки ввода-вывода файлов при управлении сессиями (например, сохранение/загрузка сессий) выводят сообщения об ошибках и возвращают `False`.
- **Подробный вывод**: Каждый запрос API выводит детали в следующем формате:
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

Пример вывода ошибки:
```
HTTP Error occurred: 401 Client Error: Unauthorized for url: https://fragment.s1qwy.ru/balance/abc123
Response details:
--- API Request: GET https://fragment.s1qwy.ru/balance/abc123 ---
Status Code: 401
Headers: {'Content-Type': 'application/json', ...}
Response Body: {
  "ok": false,
  "error": "Недействительный ключ аутентификации"
}
--- End of Response ---
```

Оберните вызовы API в блоки try-except для надежной обработки ошибок:
```python
try:
    balance = api.get_balance()
except ValueError as e:
    print(f"Ошибка аутентификации: {e}")
except requests.exceptions.HTTPError as e:
    print(f"HTTP ошибка: {e}")
except requests.exceptions.RequestException as e:
    print(f"Ошибка запроса: {e}")
```

## Примеры
### Аутентификация и проверка баланса
```python
from fragment_api import FragmentAPI

api = FragmentAPI()
try:
    api.create_auth("мнемоническая_фраза", "куки", "хэш")  # Выводит ответ
    if api.has_valid_session():
        balance = api.get_balance()  # Выводит ответ
        print(f"Баланс: {balance.get('balance', 0)}")
except Exception as e:
    print(f"Ошибка: {e}")
finally:
    api.close()
```

### Загрузка сессии и покупка Stars
```python
from fragment_api import FragmentAPI

api = FragmentAPI()
try:
    if api.load_session():
        result = api.buy_stars("@example_user", quantity=50, show_sender=True)  # Выводит ответ
        print(f"Результат транзакции: {result}")
    else:
        print("Действующая сессия не найдена")
except Exception as e:
    print(f"Ошибка: {e}")
finally:
    api.close()
```

### Подарок подписки Premium
```python
from fragment_api import FragmentAPI

api = FragmentAPI()
try:
    if api.load_session():
        result = api.gift_premium("@example_user", months=3, show_sender=False)  # Выводит ответ
        print(f"Результат транзакции: {result}")
    else:
        print("Действующая сессия не найдена")
except Exception as e:
    print(f"Ошибка: {e}")
finally:
    api.close()
```

Для дополнительных примеров проверьте папку `examples/` в исходном коде (если предоставлена) или репозиторий проекта на GitHub.

## Как внести вклад
Приветствуются любые вклады! Чтобы внести вклад:
1. Сделайте форк репозитория.
2. Создайте ветку для новой функции (`git checkout -b feature/AmazingFeature`).
3. Зафиксируйте изменения (`git commit -m 'Добавлена новая функция'`).
4. Отправьте ветку в репозиторий (`git push origin feature/AmazingFeature`).
5. Откройте Pull Request.

Сообщайте об ошибках или предлагайте функции через трекер проблем на GitHub.

## Лицензия
Проект распространяется под лицензией MIT. Подробности см. в файле [LICENSE](LICENSE).

Для дополнительной информации посетите проект на [PyPI](https://pypi.org/project/fragment-api-py/).
