'''
HTML parsing utilities for Fragment marketplace pages and item details.
'''

from __future__ import annotations

import re
from typing import Any

from FragmentAPI.types.results import (
    AuctionInfo,
    BidHistoryEntry,
    GiftAttribute,
    OwnerHistoryEntry,
    PremiumPriceOption,
    PremiumTransaction,
    ProfileInfo,
    SessionInfo,
    StarsPrice,
    StarsTransaction,
)

ROW_BLOCK_RE = re.compile(
    r'<tr[^>]*class="[^"]*tm-row-selectable[^"]*"[^>]*>(.*?)</tr>',
    re.DOTALL,
)
HREF_RE = re.compile(r'href="(/(?:username|number|nft)/([^"]+))"')
VALUE_RE = re.compile(r'class="[^"]*tm-value[^"]*"[^>]*>\s*([^<]+?)\s*<')
PRICE_RE = re.compile(r"icon-before\s+icon-ton[^>]*>\s*([0-9][^<]*?)\s*<")
DATETIME_RE = re.compile(
    r'<time[^>]+datetime="([^"]+)"[^>]*data-relative="text"[^>]*>',
)
DATETIME_SHORT_RE = re.compile(
    r'<time[^>]+datetime="([^"]+)"[^>]*data-relative="short-text"[^>]*>',
)
NUMERIC_RE = re.compile(r"^\+?[\d,. ]+$")

GRID_ITEM_RE = re.compile(
    r'<a[^>]*class="[^"]*tm-grid-item[^"]*"[^>]*>(.*?)</a>',
    re.DOTALL,
)
GRID_HREF_RE = re.compile(r'href="(/gift/([^?"]+))')
GRID_NAME_RE = re.compile(r'class="item-name">([^<]+)<')
GRID_NUM_RE = re.compile(r'class="item-num">[^#]*#(\w+)<')
GRID_PRICE_RE = re.compile(
    r'class="[^"]*tm-grid-item-value[^"]*icon-ton[^"]*"'
    r'[^>]*>\s*([0-9][^<]*?)\s*<',
)
GRID_STATUS_RE = re.compile(
    r'class="[^"]*tm-grid-item-status[^"]*"[^>]*>\s*([^<]+?)\s*<',
)
GRID_DATETIME_RE = re.compile(r'<time[^>]+datetime="([^"]+)"')

STATUS_RE = re.compile(
    r'tm-section-header-status[^"]*"[^>]*>\s*([^<]+?)\s*<',
)
TIMER_RE = re.compile(
    r'class="tm-countdown-timer"[^>]*datetime="([^"]+)"',
)
PURCHASED_DATE_RE = re.compile(
    r'Purchased on\s*<time[^>]+datetime="([^"]+)"',
)
BUY_NOW_RE = re.compile(
    r'js-buy-now-btn["\s][^>]*data-bid-amount="([^"]+)"',
)
PLACE_BID_RE = re.compile(
    r'js-place-bid-btn["\s][^>]*data-bid-amount="([^"]+)"',
)
RESTRICTED_RE = re.compile(r"tm-status-restricted")

HISTORY_ROW_RE = re.compile(r"<tr>\s*(.*?)\s*</tr>", re.DOTALL)
HISTORY_PRICE_TON_RE = re.compile(
    r"icon-before\s+icon-ton[^>]*>\s*([^<]+?)\s*<",
)
HISTORY_VALUE_RE = re.compile(
    r'table-cell-value\s+tm-value[^"]*"[^>]*>\s*([^<]+?)\s*<',
)
HISTORY_DATETIME_RE = re.compile(r'<time[^>]+datetime="([^"]+)"')
HISTORY_WALLET_HREF_RE = re.compile(
    r'href="(https://tonviewer\.com/[^"]+)"',
)

NEXT_OFFSET_OWNERS_RE = re.compile(
    r'js-load-more-owners["\s][^>]*data-next-offset="([^"]+)"',
)
NEXT_OFFSET_ORDERS_RE = re.compile(
    r'js-load-more-orders["\s][^>]*data-next-offset="([^"]+)"',
)

GIFT_IMAGE_RE = re.compile(
    r'<img\s+src="(https://nft\.fragment\.com/gift/[^"]+)"',
)
GIFT_STICKER_RE = re.compile(
    r'srcset="(https://nft\.fragment\.com/gift/[^"]+\.tgs)"',
)
GIFT_ATTR_ROW_RE = re.compile(
    r'<tr>\s*<td>\s*<div class="table-cell">([^<]+)</div>\s*</td>'
    r'\s*<td>\s*<div class="table-cell">\s*'
    r'<div class="table-cell-value tm-value">\s*'
    r'(?:<a[^>]*>([^<]+)</a>|([^<]+?))\s*'
    r'(?:<span class="tm-rarity">\s*([^<]+?)\s*</span>)?',
    re.DOTALL,
)
GIFT_ISSUED_RE = re.compile(
    r'Issued</div>\s*</td>\s*<td>\s*<div class="table-cell">\s*'
    r'<div[^>]*>\s*([^<]+?)\s*</div>',
    re.DOTALL,
)

SOLD_OWNER_RE = re.compile(
    r'(?:Sale Price|Owner).*?class="tm-wallet"[^>]*>.*?'
    r'<span class="(?:head|short)">([^<]+)</span>',
    re.DOTALL,
)

STARS_RADIO_RE = re.compile(
    r'<input[^>]*name="stars"[^>]*value="(\d+)"[^>]*>.*?'
    r'icon-before\s+icon-ton[^>]*>\s*([^<]+?)\s*<.*?'
    r'(?:&#036;|\$)\s*([^<]+?)\s*<',
    re.DOTALL,
)

PREMIUM_RADIO_RE = re.compile(
    r'<input[^>]*name="months"[^>]*value="(\d+)"[^>]*>.*?'
    r'<div class="tm-radio-label">([^<]*?)'
    r'(?:<span[^>]*>([^<]*)</span>)?</div>\s*'
    r'<div class="tm-value icon-before icon-ton">([^<]+)</div>\s*'
    r'<div class="tm-radio-desc">&#036;([^<]+)</div>',
    re.DOTALL,
)

STARS_PRICE_INLINE_RE = re.compile(
    r"icon-before\s+icon-ton[^>]*>\s*([0-9][^<]*?)\s*<",
)
STARS_USD_INLINE_RE = re.compile(
    r"(?:&#036;|\$)\s*([0-9][^<]*?)\s*<",
)

PROFILE_NAME_RE = re.compile(r'tm-settings-item-head">([^<]+)<')
PROFILE_USERNAME_RE = re.compile(r'tm-settings-item-desc">@([^<]+)<')
PROFILE_PHOTO_RE = re.compile(
    r'tm-settings-account-photo[^>]*>\s*<img\s+src="([^"]+)"',
)
PROFILE_VERIFIED_RE = re.compile(r'tm-badge-verified[^>]*>([^<]+)<')
PROFILE_WALLET_LABEL_RE = re.compile(
    r'Linked Wallet.*?tm-settings-item-desc[^>]*>.*?'
    r'<span class="short">([^<]+)</span>',
    re.DOTALL,
)
PROFILE_WALLET_VERIFIED_RE = re.compile(
    r"Linked Wallet.*?tm-badge-verified",
    re.DOTALL,
)

SESSION_ROW_RE = re.compile(r"<tr>\s*(.*?)\s*</tr>", re.DOTALL)
SESSION_DEVICE_RE = re.compile(
    r'table-cell-value\s+tm-value[^"]*"[^>]*>\s*([^<]+?)\s*<',
)
SESSION_LOCATION_RE = re.compile(
    r'table-cell-desc-col\s+tm-nowrap[^"]*"[^>]*>\s*([^<]+?)\s*<',
)
SESSION_ID_RE = re.compile(r'data-session-id="([^"]+)"')
SESSION_CURRENT_RE = re.compile(r"tm-status-avail[^>]*>Current<")

TRANSACTION_ROW_RE = re.compile(r"<tr>\s*(.*?)\s*</tr>", re.DOTALL)
TX_RECIPIENT_RE = re.compile(r'class="tm-inline-nowrap">@([^<]+)<')
TX_STARS_RE = re.compile(
    r'tm-value\s+tm-nowrap[^"]*"[^>]*>\s*([^<]+?)\s*<',
)
TX_PRICE_RE = re.compile(
    r"icon-before\s+icon-ton[^>]*>\s*([^<]+?)\s*<",
)
TX_DURATION_RE = re.compile(
    r'tm-nowrap[^"]*"[^>]*>\s*([^<]+?)\s*<',
)
TX_DATE_RE = re.compile(r'<time[^>]+datetime="([^"]+)"')

LOGIN_CODE_RE = re.compile(
    r'class="[^"]*table-cell-value[^"]*"[^>]*>([^<]+)<',
)
LOGIN_ROW_RE = re.compile(r"<tr[\s>]")


def parse_auction_rows(html: str) -> list[dict[str, Any]]:
    '''Parse Fragment marketplace HTML into structured item dicts.'''
    items: list[dict[str, Any]] = []
    for row_match in ROW_BLOCK_RE.finditer(html):
        row = row_match.group(1)

        href_m = HREF_RE.search(row)
        if not href_m:
            continue
        slug = href_m.group(1).lstrip("/")

        values = [m.group(1).strip() for m in VALUE_RE.finditer(row)]
        name = values[0] if values else slug

        status: str | None = None
        for v in values[1:]:
            if (
                v
                and v not in ("Unknown",)
                and not v.startswith("@")
                and not NUMERIC_RE.match(v)
            ):
                status = v
                break

        price_m = PRICE_RE.search(row)
        price: str | None = None
        if price_m:
            raw_price = price_m.group(1).strip().replace(",", "")
            try:
                price = f"{float(raw_price):.2f}"
            except ValueError:
                price = raw_price

        time_m = DATETIME_RE.search(row) or DATETIME_SHORT_RE.search(row)
        date: str | None = time_m.group(1) if time_m else None

        items.append({
            "slug": slug,
            "name": name,
            "status": status,
            "price": price,
            "date": date,
        })
    return items


def parse_gift_items(
    html: str,
) -> tuple[list[dict[str, Any]], int | None]:
    '''Parse Fragment gifts grid HTML into structured item dicts.'''
    items: list[dict[str, Any]] = []
    for item_match in GRID_ITEM_RE.finditer(html):
        block = item_match.group(0)

        href_m = GRID_HREF_RE.search(block)
        if not href_m:
            continue
        slug = href_m.group(1).lstrip("/")

        name_m = GRID_NAME_RE.search(block)
        num_m = GRID_NUM_RE.search(block)
        item_name = name_m.group(1).strip() if name_m else slug
        item_num = f" #{num_m.group(1)}" if num_m else ""
        name = f"{item_name}{item_num}"

        status_m = GRID_STATUS_RE.search(block)
        status: str | None = (
            status_m.group(1).strip() if status_m else None
        )

        price_m = GRID_PRICE_RE.search(block)
        price: str | None = None
        if price_m:
            raw_price = price_m.group(1).strip().replace(",", "")
            try:
                price = f"{float(raw_price):.2f}"
            except ValueError:
                price = raw_price

        time_m = GRID_DATETIME_RE.search(block)
        date: str | None = time_m.group(1) if time_m else None

        items.append({
            "slug": slug,
            "name": name,
            "status": status,
            "price": price,
            "date": date,
        })

    next_offset_m = re.search(r'data-next-offset="(\d+)"', html)
    next_offset = (
        int(next_offset_m.group(1)) if next_offset_m else None
    )

    return items, next_offset


def _parse_table_rows(html: str) -> list[dict[str, Any]]:
    '''Parse table rows from HTML body content.'''
    entries: list[dict[str, Any]] = []
    for row_m in HISTORY_ROW_RE.finditer(html):
        row = row_m.group(1)
        if "table-cell-more" in row or "<th" in row:
            continue
        if "table-cell" not in row:
            continue

        price_m = HISTORY_PRICE_TON_RE.search(row)
        value_m = HISTORY_VALUE_RE.search(row)
        price = None
        price_label = None
        if price_m:
            price = price_m.group(1).strip().replace(",", "")
        elif value_m:
            val = value_m.group(1).strip()
            if val == "Transferred":
                price_label = "Transferred"
            else:
                price = val.replace(",", "")

        date_m = HISTORY_DATETIME_RE.search(row)
        date = date_m.group(1) if date_m else None

        wallet_href_m = HISTORY_WALLET_HREF_RE.search(row)
        wallet = None
        if wallet_href_m:
            full_url = wallet_href_m.group(1)
            wallet = full_url.replace(
                "https://tonviewer.com/", "",
            )

        entries.append({
            "price": price,
            "price_label": price_label,
            "date": date,
            "wallet": wallet,
        })
    return entries


def parse_bid_history(
    html: str,
) -> tuple[list[BidHistoryEntry], str | None]:
    '''Parse bid history from page HTML.'''
    bid_section = ""
    m = re.search(
        r"Bid History</h3>.*?</section>",
        html,
        re.DOTALL,
    )
    if m:
        bid_section = m.group(0)

    entries = _parse_table_rows(bid_section)
    bids = [
        BidHistoryEntry(
            price=e["price"],
            date=e["date"],
            wallet=e["wallet"],
        )
        for e in entries
    ]
    offset_m = NEXT_OFFSET_ORDERS_RE.search(bid_section)
    return bids, offset_m.group(1) if offset_m else None


def parse_owner_history(
    html: str,
) -> tuple[list[OwnerHistoryEntry], str | None]:
    '''Parse ownership history from page HTML.'''
    owner_section = ""
    m = re.search(
        r"Ownership History</h3>.*?</section>",
        html,
        re.DOTALL,
    )
    if m:
        owner_section = m.group(0)

    entries = _parse_table_rows(owner_section)
    owners = [
        OwnerHistoryEntry(
            price=e.get("price_label") or e["price"],
            date=e["date"],
            wallet=e["wallet"],
        )
        for e in entries
    ]
    offset_m = NEXT_OFFSET_OWNERS_RE.search(owner_section)
    return owners, offset_m.group(1) if offset_m else None


def parse_item_status(html: str) -> str:
    '''Extract item status from page HTML.'''
    m = STATUS_RE.search(html)
    return m.group(1).strip() if m else "Unknown"


def parse_auction_info(html: str) -> AuctionInfo:
    '''Parse auction pricing info from HTML.'''
    info = AuctionInfo()

    bid_table_match = re.search(
        r'<table[^>]*class="[^"]*tm-table[^"]*"[^>]*>.*?'
        r"Highest Bid.*?Bid Step.*?Minimum Bid.*?</tbody>",
        html,
        re.DOTALL,
    )

    if bid_table_match:
        table_html = bid_table_match.group(0)

        cell_values = re.findall(
            r'<div class="table-cell-value tm-value '
            r'icon-before icon-ton">([^<]+)</div>',
            table_html,
        )

        if len(cell_values) >= 1:
            info.highest_bid = (
                cell_values[0].strip().replace(",", "")
            )
        if len(cell_values) >= 2:
            info.bid_step = (
                cell_values[1].strip().replace(",", "")
            )
        if len(cell_values) >= 3:
            info.minimum_bid = (
                cell_values[2].strip().replace(",", "")
            )

    sell_m = re.search(
        r"Sell Price[^<]*</th>.*?"
        r"icon-before\s+icon-ton[^>]*>\s*([^<]+)",
        html,
        re.DOTALL,
    )
    if sell_m:
        info.sell_price = sell_m.group(1).strip().replace(",", "")

    buy_m = BUY_NOW_RE.search(html)
    if buy_m:
        info.buy_now_price = buy_m.group(1).strip()

    return info


def parse_sold_owner(html: str) -> str | None:
    '''Parse owner wallet from sold item page.'''
    m = SOLD_OWNER_RE.search(html)
    return m.group(1).strip() if m else None


def parse_gift_attributes(html: str) -> list[GiftAttribute]:
    '''Parse gift attributes from detail page HTML.'''
    attrs: list[GiftAttribute] = []
    for m in GIFT_ATTR_ROW_RE.finditer(html):
        name = m.group(1).strip()
        value = (m.group(2) or m.group(3) or "").strip()
        rarity = m.group(4).strip() if m.group(4) else None
        if name and value and name not in ("Owner", "Issued"):
            attrs.append(
                GiftAttribute(
                    name=name,
                    value=value,
                    rarity=rarity,
                )
            )
    return attrs


def parse_gift_issued(html: str) -> str | None:
    '''Parse gift issued info.'''
    m = GIFT_ISSUED_RE.search(html)
    return m.group(1).strip() if m else None


def parse_stars_packages(html: str) -> list[StarsPrice]:
    '''Parse stars package prices from stars page HTML.'''
    packages: list[StarsPrice] = []
    for m in STARS_RADIO_RE.finditer(html):
        stars = int(m.group(1))
        ton_raw = m.group(2).strip().replace(",", "")
        ton_raw = re.sub(r"<[^>]+>", ".", ton_raw).replace(" ", "")
        usd_raw = m.group(3).strip().replace(",", "")
        packages.append(
            StarsPrice(
                stars=stars,
                ton_price=ton_raw,
                usd_price=usd_raw,
            )
        )
    return packages


def parse_stars_price_from_html(
    html: str,
) -> tuple[str | None, str | None]:
    '''Parse TON and USD price from inline HTML fragment.'''
    ton_m = re.search(
        r"icon-before\s+icon-ton[^>]*>\s*([0-9][^<]*?)"
        r'(?:<span class="mini-frac">([^<]*)</span>)?',
        html,
        re.DOTALL,
    )
    ton_price = None
    if ton_m:
        integer_part = ton_m.group(1).strip().replace(",", "")
        frac_part = ton_m.group(2).strip() if ton_m.group(2) else ""
        ton_price = f"{integer_part}{frac_part}"

    usd_m = re.search(
        r"(?:&#036;|\$)\s*([0-9][^<]*?)\s*<",
        html,
    )
    usd_price = usd_m.group(1).strip() if usd_m else None

    return ton_price, usd_price


def parse_premium_options(html: str) -> list[PremiumPriceOption]:
    '''Parse premium price options from premium page HTML.'''
    options: list[PremiumPriceOption] = []

    pattern = re.compile(
        r'<input[^>]*name="months"[^>]*value="(\d+)"[^>]*>.*?'
        r'<div class="tm-form-radio-label">\s*'
        r'<div class="tm-radio-label">([^<]*?)'
        r"(?:<span[^>]*>([^<]*)</span>)?</div>\s*"
        r'<div class="tm-value icon-before icon-ton">'
        r"([^<]+(?:<span class=\"mini-frac\">[^<]*</span>)?)"
        r"</div>\s*"
        r'<div class="tm-radio-desc">'
        r"(?:&#036;|\$)([^<]+)</div>",
        re.DOTALL,
    )

    for m in pattern.finditer(html):
        months = int(m.group(1))
        label = m.group(2).strip()
        discount = m.group(3).strip() if m.group(3) else None

        ton_raw = m.group(4).strip()
        ton_raw = re.sub(r'<span class="mini-frac">', "", ton_raw)
        ton_raw = re.sub(r"</span>", "", ton_raw)
        ton_raw = ton_raw.replace(",", "").strip()

        usd_raw = m.group(5).strip().replace(",", "")

        options.append(
            PremiumPriceOption(
                months=months,
                label=label,
                ton_price=ton_raw,
                usd_price=usd_raw,
                discount=discount,
            )
        )
    return options


def parse_stars_history(html: str) -> list[StarsTransaction]:
    '''Parse stars transaction history from HTML.'''
    transactions: list[StarsTransaction] = []
    tbody_m = re.search(r"<tbody>(.*?)</tbody>", html, re.DOTALL)
    if not tbody_m:
        return transactions

    for row_m in TRANSACTION_ROW_RE.finditer(tbody_m.group(1)):
        row = row_m.group(1)
        if "<th" in row:
            continue

        recip_m = TX_RECIPIENT_RE.search(row)
        recipient = recip_m.group(1).strip() if recip_m else ""

        stars_m = TX_STARS_RE.search(row)
        stars_str = (
            stars_m.group(1).strip().replace(",", "")
            if stars_m
            else "0"
        )
        try:
            stars = int(stars_str)
        except ValueError:
            stars = 0

        price_m = TX_PRICE_RE.search(row)
        price_raw = ""
        if price_m:
            price_raw = price_m.group(1).strip()
            price_raw = (
                re.sub(r"<[^>]+>", ".", price_raw)
                .replace(" ", "")
                .replace(",", "")
            )

        date_m = TX_DATE_RE.search(row)
        date = date_m.group(1) if date_m else ""

        if recipient:
            transactions.append(
                StarsTransaction(
                    recipient=recipient,
                    stars=stars,
                    price_ton=price_raw,
                    date=date,
                )
            )
    return transactions


def parse_premium_history(html: str) -> list[PremiumTransaction]:
    '''Parse premium transaction history from HTML.'''
    transactions: list[PremiumTransaction] = []
    tbody_m = re.search(r"<tbody>(.*?)</tbody>", html, re.DOTALL)
    if not tbody_m:
        return transactions

    for row_m in TRANSACTION_ROW_RE.finditer(tbody_m.group(1)):
        row = row_m.group(1)
        if "<th" in row:
            continue

        recip_m = TX_RECIPIENT_RE.search(row)
        recipient = recip_m.group(1).strip() if recip_m else ""

        dur_m = TX_DURATION_RE.search(row)
        duration = dur_m.group(1).strip() if dur_m else ""

        price_m = TX_PRICE_RE.search(row)
        price_raw = ""
        if price_m:
            price_raw = price_m.group(1).strip()
            price_raw = (
                re.sub(r"<[^>]+>", ".", price_raw)
                .replace(" ", "")
                .replace(",", "")
            )

        date_m = TX_DATE_RE.search(row)
        date = date_m.group(1) if date_m else ""

        if recipient:
            transactions.append(
                PremiumTransaction(
                    recipient=recipient,
                    duration=duration,
                    price_ton=price_raw,
                    date=date,
                )
            )
    return transactions


def parse_profile(html: str) -> ProfileInfo:
    '''Parse profile info from profile page HTML.'''
    name_m = PROFILE_NAME_RE.search(html)
    name = name_m.group(1).strip() if name_m else ""

    user_m = PROFILE_USERNAME_RE.search(html)
    username = user_m.group(1).strip() if user_m else ""

    photo_m = PROFILE_PHOTO_RE.search(html)
    photo_url = (
        photo_m.group(1).replace("\\/", "/") if photo_m else None
    )

    verified_m = PROFILE_VERIFIED_RE.search(html)
    identity_verified = bool(
        verified_m and "Identity" in verified_m.group(1),
    )

    wallet_label_m = PROFILE_WALLET_LABEL_RE.search(html)
    wallet_label = (
        wallet_label_m.group(1).strip() if wallet_label_m else None
    )

    wallet_verified = bool(
        PROFILE_WALLET_VERIFIED_RE.search(html),
    )

    wallet_address = None
    addr_m = re.search(
        r'Wallet\.init\(\{[^}]*"address"\s*:\s*"([^"]+)"',
        html,
    )
    if addr_m:
        addr_val = addr_m.group(1)
        if addr_val and addr_val != "false":
            wallet_address = addr_val

    return ProfileInfo(
        name=name,
        username=username,
        photo_url=photo_url,
        identity_verified=identity_verified,
        wallet_address=wallet_address,
        wallet_label=wallet_label,
        wallet_verified=wallet_verified,
    )


def parse_sessions(html: str) -> list[SessionInfo]:
    '''Parse active sessions from sessions page HTML.'''
    sessions: list[SessionInfo] = []
    tbody_m = re.search(
        r"<tbody[^>]*>(.*?)</tbody>",
        html,
        re.DOTALL,
    )
    if not tbody_m:
        return sessions

    for row_m in SESSION_ROW_RE.finditer(tbody_m.group(1)):
        row = row_m.group(1)
        if "<th" in row:
            continue

        device_m = SESSION_DEVICE_RE.search(row)
        device = device_m.group(1).strip() if device_m else ""

        locations = []
        for loc_m in SESSION_LOCATION_RE.finditer(row):
            val = loc_m.group(1).strip()
            if val and not val.startswith("now") and "at " not in val:
                locations.append(val)
        location = locations[0] if locations else ""

        sid_m = SESSION_ID_RE.search(row)
        session_id = sid_m.group(1) if sid_m else ""

        is_current = bool(SESSION_CURRENT_RE.search(row))

        date_m = TX_DATE_RE.search(row)
        date = date_m.group(1) if date_m else (
            "now" if is_current else None
        )

        if device or session_id:
            sessions.append(
                SessionInfo(
                    session_id=session_id,
                    device=device,
                    location=location,
                    date=date,
                    is_current=is_current,
                )
            )
    return sessions


def parse_login_code(html: str) -> tuple[str | None, int]:
    '''Extract the pending login code and active session count.'''
    match = LOGIN_CODE_RE.search(html)
    code = match.group(1).strip() if match else None
    active_sessions = len(LOGIN_ROW_RE.findall(html))
    return code, active_sessions