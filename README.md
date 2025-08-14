# Fragment API Python Client

[![PyPI version](https://badge.fury.io/py/fragment-api-py.svg)](https://badge.fury.io/py/fragment-api-py)
[![Python versions](https://img.shields.io/pypi/pyversions/fragment-api-py.svg)](https://pypi.org/project/fragment-api-py/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Неофициальный Python клиент для работы с [Fragment API](https://fragment-api.net) - сервисом покупки Telegram Stars, Premium и TON.

## Возможности

- Полная поддержка всех методов Fragment API
- Удобное управление сессиями (автосохранение auth_key)
- Подробная обработка ошибок с понятными сообщениями
- Поддержка всех типов операций:
  - Telegram Stars
  - Telegram Premium
  - TON переводы
- Автоматическая загрузка и сохранение сессий

## Установка

```bash
pip install fragment-api-py
```

## Быстрый старт

```python
from FragmentAPI import FragmentAPI, FragmentAuth

# Инициализация API
api = FragmentAPI("https://fragment-api.net")

# Аутентификация
auth = FragmentAuth(api)
session = auth.create_auth_key("your_fragment_cookies", "your_seed_phrase")

# Работа с API
general = api.general()
print(general.get_balance())
```

## Примеры использования

### Покупка Telegram Premium

```python
premium = api.premium()
order = premium.create_premium_order("@username", 12)  # 12 месяцев
payment = premium.pay_premium_order(order["order_id"], order["cost"])
```

### Покупка Telegram Stars

```python
stars = api.stars()
order = stars.create_stars_order("@username", 100)  # 100 Stars
payment = stars.pay_stars_order(order["order_id"], order["cost"])
```

### Перевод TON

```python
ton = api.ton()
order = ton.create_ton_order("@username", 5)  # 5 TON
payment = ton.pay_ton_order(order["order_id"], order["cost"])
```

## Документация

Полная документация доступна на [GitHub Wiki](https://github.com/S1qwy/fragment-api-py/wiki).

## Лицензия

MIT License. Смотрите файл [LICENSE](LICENSE).
