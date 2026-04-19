<p align="center">
  <img src="https://fragment.com/img/fragment_icon.svg" width="200" alt="Fragment API Python">
</p>

<h1 align="center">Fragment API Python</h1>

<p align="center">
  <strong>Профессиональная библиотека для полной автоматизации Fragment.com на Python.</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/fragment-api-py/"><img src="https://img.shields.io/pypi/v/fragment-api-py.svg?style=flat-square" alt="PyPI version"></a>
  <a href="https://pypi.org/project/fragment-api-py/"><img src="https://img.shields.io/pypi/pyversions/fragment-api-py.svg?style=flat-square" alt="Python versions"></a>
  <a href="https://fragment.s1qwy.ru"><img src="https://img.shields.io/badge/docs-fragment.s1qwy.ru-blue?style=flat-square" alt="Documentation"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg?style=flat-square" alt="License"></a>
</p>

---

**Fragment API Python** — это мощное решение для взаимодействия с платформой Fragment. Библиотека позволяет автоматизировать покупку Telegram Stars, Premium, номеров и имен, проводить официальные розыгрыши и искать активы в маркетплейсе в режиме реального времени.

## 📚 Полная документация
Подробное описание методов, типов данных и примеры использования доступны на:  
👉 **[https://fragment.s1qwy.ru](https://fragment.s1qwy.ru)**

---

## ✨ Основные возможности

- 🚀 **Sync & Async**: Выбирайте между простым синхронным клиентом и высокопроизводительным асинхронным (asyncio).
- 💎 **Платежи**: Покупка Stars (50 - 1M), Premium (3, 6, 12 мес) и пополнение TON Ads.
- 🎁 **Розыгрыши (Giveaways)**: Полная автоматизация запуска розыгрышей Stars и Premium для каналов.
- 🔍 **Маркетплейс**: Глубокий поиск имен пользователей, анонимных номеров и NFT-подарков с парсингом цен и дат.
- 🛡️ **Безопасность**: Встроенная валидация баланса кошелька и автоматическое вычисление комиссии (газа).
- ⛓️ **Multi-Wallet**: Поддержка самых популярных версий кошельков: **V4R2** и **V5R1 (W5)**.
- ⚙️ **Zero-Config Hash**: Библиотека автоматически извлекает актуальный API-хеш — вам больше не нужно указывать его вручную.

---

## 📦 Установка

```bash
# Базовая версия (только синхронный клиент)
pip install fragment-api-py

# С поддержкой асинхронности
pip install fragment-api-py[async]
```

---

## 🚀 Быстрый старт

### Синхронный клиент (Default)
```python
from FragmentAPI import FragmentClient

client = FragmentClient(
    seed="24 words mnemonic...",
    cookies="stel_ssid=...; stel_token=..."
)

# Проверка кошелька
wallet = client.get_wallet()
print(f"Баланс: {wallet.balance} TON")

# Покупка Stars
result = client.purchase_stars("@durov", amount=50)
print(f"Транзакция отправлена: {result.transaction_id}")
```

### Поиск в маркетплейсе
```python
# Поиск красивых имен
usernames = client.search_usernames(query="gold", filter="sale")
for item in usernames.items:
    print(f"Имя: {item['name']} | Цена: {item['price']} TON")
```

---

## 🛠️ Архитектура проекта

| Компонент | Описание |
|-----------|----------|
| **FragmentClient** | Синхронный интерфейс (на базе `httpx`). |
| **AsyncFragmentClient** | Асинхронный интерфейс для масштабируемых ботов. |
| **Giveaways** | Методы `giveaway_stars` и `giveaway_premium`. |
| **Marketplace** | Поиск по трем категориям: `usernames`, `numbers`, `gifts`. |
| **Exceptions** | Иерархия ошибок для точной обработки (UserNotFound, WalletError и др). |

---

## 🔐 Требования

1. **Python 3.10+**
2. **Сессионные куки Fragment**: `stel_ssid`, `stel_dt`, `stel_token`, `stel_ton_token`.
3. **TON Wallet**: Сид-фраза от вашего кошелька с балансом для оплаты.

---

## 🤝 Поддержка и разработка

- **Документация**: [fragment.s1qwy.ru](https://fragment.s1qwy.ru)
- **GitHub**: [S1qwy/fragment-api-py](https://github.com/S1qwy/fragment-api-py)
- **Разработчик**: [S1qwy](https://github.com/S1qwy)
- **Email**: `S1qwy@internet.ru`

Лицензия **MIT**. Используйте в своих проектах свободно!
