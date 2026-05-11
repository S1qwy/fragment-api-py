<p align="center">
  <img src="https://fragment.com/img/fragment_icon.svg" width="200" alt="Fragment API Python">
</p>

<h1 align="center">Fragment API Python v5.0</h1>

<p align="center">
  <strong>Professional Python library for Fragment.com automation</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/fragment-api-py/"><img src="https://img.shields.io/pypi/v/fragment-api-py.svg?style=flat-square" alt="PyPI"></a>
  <a href="https://pypi.org/project/fragment-api-py/"><img src="https://img.shields.io/pypi/pyversions/fragment-api-py.svg?style=flat-square" alt="Python Versions"></a>
  <a href="https://t.me/fragment_api_py"><img src="https://img.shields.io/badge/Telegram-Channel-2CA5E0?style=flat-square&logo=telegram" alt="Telegram"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg?style=flat-square" alt="License"></a>
</p>

---

**Fragment API Python** — полная автоматизация Fragment.com: покупка Stars/Premium, розыгрыши, маркетплейс, ставки (bid), управление номерами. Sync + Async.

📚 [Документация](https://fragment.s1qwy.ru) | 💬 [Telegram чат](https://t.me/fragment_api_py)

---

## Возможности

- **Sync / Async** — `FragmentClient` и `AsyncFragmentClient`
- **Покупки** — Stars (50–10M), Premium (3/6/12 мес), TON Ads, `payment_method="ton"|"usdt_ton"`
- **Розыгрыши** — Stars и Premium для каналов
- **Ставки (Bid)** — `place_bid(item_type=1|3|5, slug, bid)` — если ставка = цене выкупа, покупка моментальна
- **Маркетплейс** — поиск username, numbers, gifts с фильтрами и пагинацией
- **Wallet** — V4R2 и V5R1 (W5)
- **Авто-аутентификация** — получение кук через TON кошелек и Telegram
- **Anonymous numbers** — управление кодами входа и завершение сессий
- **Ошибки** — полная иерархия exceptions, неизвестные ошибки просьба [сообщать](https://github.com/S1qwy/fragment-api-py/issues)

---

## Установка

```bash
pip install fragment-api-py[async]  # sync + async
```

---

## Быстрый старт

```python
from FragmentAPI import FragmentClient

client = FragmentClient(
    seed="24 слова...",
    cookies={"stel_ssid": "...", "stel_token": "...", ...}
)

# Инфо кошелька
w = client.get_wallet()
print(f"{w.balance_ton} TON, {w.balance_usdt} USDT")

# Покупка Stars (USDT)
client.purchase_stars("@durov", 100, payment_method="usdt_ton")

# Покупка Premium (TON, показать отправителя)
client.purchase_premium("@durov", 6, show_sender=True)

# Ставка на username (тип 1)
client.place_bid(1, "username", bid=150)  # 150 TON

# Розыгрыш Stars в канале
client.giveaway_stars("@channel", winners=5, amount=1000)

# Поиск в маркетплейсе
items = client.search_usernames("gold", filter="sale")
```

## Авто-получение кук (функция authenticate)

```python
from FragmentAPI import FragmentClient

# Автоматическая аутентификация через TON кошелек и Telegram
cookies = FragmentClient.authenticate(
    seed="24 слова...",
    wallet_version="V5R1",
    telegram_phone="+71234567890"  # или telegram_auth_data
)

client = FragmentClient(seed="...", cookies=cookies)
```

## Async пример

```python
from FragmentAPI import AsyncFragmentClient

async with AsyncFragmentClient(seed="...", cookies=...) as client:
    wallet = await client.get_wallet()
    result = await client.place_bid(3, "123456789", bid=50)  # номер
```

## Требования

- Python 3.10+
- Куки Fragment: `stel_ssid`, `stel_dt`, `stel_token`, `stel_ton_token`
- Сид-фраза TON кошелька

## Сообщение об ошибках

При неизвестной ошибке — создавайте [Issue](https://github.com/S1qwy/fragment-api-py/issues) или пишите в [Telegram чат](https://t.me/fragment_api_py). Это поможет пополнить базу исключений.

---

**Лицензия MIT** | Разработчик [S1qwy](https://github.com/S1qwy) — `S1qwy@internet.ru`
