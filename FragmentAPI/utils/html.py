"""
HTML parsing utilities for Fragment marketplace pages and item details.

Uses selectolax (lexbor backend) for robust CSS-selector based parsing,
with regex fallback for edge cases. Much more resilient to Fragment
HTML changes than pure-regex approach.
"""

from __future__ import annotations

import re
from typing import Any

from selectolax.lexbor import LexborHTMLParser

from FragmentAPI.types.models import (
    AuctionInfo,
    BidHistoryEntry,
    GiftAttribute,
    MyAsset,
    MyBid,
    OwnerHistoryEntry,
    PremiumPriceOption,
    PremiumTransaction,
    ProfileInfo,
    SessionInfo,
    StarsPrice,
    StarsTransaction,
    TelegramAccount,
    TopupTransaction,
)


def _text(node: Any) -> str:
    """Safely extract text from a selectolax node."""
    if node is None:
        return ""
    return (node.text(strip=True) or "").strip()


def _attr(node: Any, name: str) -> str:
    """Safely extract an attribute from a selectolax node."""
    if node is None:
        return ""
    return (node.attributes.get(name) or "").strip()


def _clean_price(raw: str) -> str:
    """Clean price string: remove commas and whitespace."""
    return raw.replace(",", "").replace("\xa0", "").strip()


def parse_auction_rows(html: str) -> list[dict[str, Any]]:
    """Parse Fragment marketplace HTML into structured item dicts."""
    tree = LexborHTMLParser(html)
    items: list[dict[str, Any]] = []

    for row in tree.css("tr.tm-row-selectable"):
        link = row.css_first("a[href]")
        if link is None:
            continue
        href = _attr(link, "href").lstrip("/")
        if not href:
            continue

        values = [_text(v) for v in row.css(".tm-value")]
        name = values[0] if values else href

        status: str | None = None
        for v in values[1:]:
            if v and not v.startswith("@") and not re.match(r"^\+?[\d,. ]+$", v):
                status = v
                break

        price_node = row.css_first(".icon-before.icon-ton")
        price: str | None = None
        if price_node:
            raw = _text(price_node)
            cleaned = _clean_price(raw)
            try:
                price = f"{float(cleaned):.2f}"
            except ValueError:
                price = cleaned

        time_node = row.css_first("time[datetime]")
        date = _attr(time_node, "datetime") if time_node else None

        items.append({"slug": href, "name": name, "status": status, "price": price, "date": date})

    return items


def parse_gift_items(html: str) -> tuple[list[dict[str, Any]], int | None]:
    """Parse Fragment gifts grid HTML into structured item dicts."""
    tree = LexborHTMLParser(html)
    items: list[dict[str, Any]] = []

    for card in tree.css("a.tm-grid-item"):
        href_match = re.search(r'/gift/([^?"]+)', _attr(card, "href"))
        if not href_match:
            continue
        slug = f"gift/{href_match.group(1)}"

        name_node = card.css_first(".item-name")
        num_node = card.css_first(".item-num")
        item_name = _text(name_node) or slug
        item_num = f" #{_text(num_node).lstrip('#')}" if num_node and _text(num_node) else ""
        name = f"{item_name}{item_num}"

        status_node = card.css_first(".tm-grid-item-status")
        status = _text(status_node) or None

        price_node = card.css_first(".tm-grid-item-value.icon-ton, .tm-grid-item-value.icon-before.icon-ton")
        price: str | None = None
        if price_node:
            cleaned = _clean_price(_text(price_node))
            try:
                price = f"{float(cleaned):.2f}"
            except ValueError:
                price = cleaned

        time_node = card.css_first("time[datetime]")
        date = _attr(time_node, "datetime") if time_node else None

        items.append({"slug": slug, "name": name, "status": status, "price": price, "date": date})

    next_offset_node = tree.css_first("[data-next-offset]")
    next_offset = int(_attr(next_offset_node, "data-next-offset")) if next_offset_node and _attr(next_offset_node, "data-next-offset") else None

    return items, next_offset


def _parse_history_rows(html: str, section_title: str) -> tuple[list[dict[str, Any]], str | None]:
    """Parse table rows from a named section."""
    tree = LexborHTMLParser(html)
    entries: list[dict[str, Any]] = []
    offset: str | None = None

    section_html = ""
    m = re.search(rf"{re.escape(section_title)}</h3>.*?</section>", html, re.DOTALL)
    if m:
        section_html = m.group(0)
        section_tree = LexborHTMLParser(section_html)
    else:
        section_tree = tree

    for row in section_tree.css("tr"):
        cells = row.css("td")
        if not cells:
            continue

        row_html = row.html or ""
        price: str | None = None
        price_label: str | None = None

        price_node = row.css_first(".icon-before.icon-ton")
        if price_node:
            price = _clean_price(_text(price_node))
        else:
            val_node = row.css_first(".table-cell-value.tm-value")
            if val_node:
                val = _text(val_node)
                if val == "Transferred":
                    price_label = "Transferred"
                else:
                    price = _clean_price(val)

        time_node = row.css_first("time[datetime]")
        date = _attr(time_node, "datetime") if time_node else None

        wallet: str | None = None
        wallet_link = row.css_first('a[href*="tonviewer.com"]')
        if wallet_link:
            wallet = _attr(wallet_link, "href").replace("https://tonviewer.com/", "")

        entries.append({"price": price, "price_label": price_label, "date": date, "wallet": wallet})

    if section_html:
        offset_match = re.search(r'js-load-more-o(?:wners|rders)["\s][^>]*data-next-offset="([^"]+)"', section_html)
        if offset_match:
            offset = offset_match.group(1)

    return entries, offset


def parse_bid_history(html: str) -> tuple[list[BidHistoryEntry], str | None]:
    """Parse bid history from page HTML."""
    entries, offset = _parse_history_rows(html, "Bid History")
    bids = [BidHistoryEntry(price=e["price"], date=e["date"], wallet=e["wallet"]) for e in entries]
    return bids, offset


def parse_owner_history(html: str) -> tuple[list[OwnerHistoryEntry], str | None]:
    """Parse ownership history from page HTML."""
    entries, offset = _parse_history_rows(html, "Ownership History")
    owners = [
        OwnerHistoryEntry(price=e.get("price_label") or e["price"], date=e["date"], wallet=e["wallet"])
        for e in entries
    ]
    return owners, offset


def parse_item_status(html: str) -> str:
    """Extract item status from page HTML."""
    tree = LexborHTMLParser(html)
    node = tree.css_first("[class*='tm-section-header-status']")
    return _text(node) if node else "Unknown"


def parse_auction_info(html: str) -> AuctionInfo:
    """Parse auction pricing info from HTML."""
    tree = LexborHTMLParser(html)
    info = AuctionInfo()

    bid_values = []
    for cell in tree.css(".table-cell-value.tm-value.icon-before.icon-ton"):
        bid_values.append(_clean_price(_text(cell)))

    if len(bid_values) >= 1:
        info.highest_bid = bid_values[0]
    if len(bid_values) >= 2:
        info.bid_step = bid_values[1]
    if len(bid_values) >= 3:
        info.minimum_bid = bid_values[2]

    sell_m = re.search(
        r"Sell Price[^<]*</th>.*?icon-before\s+icon-ton[^>]*>\s*([^<]+)",
        html, re.DOTALL,
    )
    if sell_m:
        info.sell_price = _clean_price(sell_m.group(1))

    buy_node = tree.css_first("[class*='js-buy-now-btn'][data-bid-amount]")
    if buy_node:
        info.buy_now_price = _attr(buy_node, "data-bid-amount")

    return info


def parse_sold_owner(html: str) -> str | None:
    """Parse owner wallet from sold item page."""
    m = re.search(
        r'(?:Sale Price|Owner).*?class="tm-wallet"[^>]*>.*?'
        r'<span class="(?:head|short)">([^<]+)</span>',
        html, re.DOTALL,
    )
    return m.group(1).strip() if m else None


def parse_gift_attributes(html: str) -> list[GiftAttribute]:
    """Parse gift attributes from detail page HTML."""
    tree = LexborHTMLParser(html)
    attrs: list[GiftAttribute] = []

    for row in tree.css("tr"):
        cells = row.css("td")
        if len(cells) < 2:
            continue

        name_div = cells[0].css_first(".table-cell")
        name = _text(name_div) if name_div else ""
        if not name or name in ("Owner", "Issued"):
            continue

        value_div = cells[1].css_first(".table-cell-value.tm-value")
        if not value_div:
            continue

        link = value_div.css_first("a")
        value = _text(link) if link else _text(value_div)

        rarity_node = value_div.css_first(".tm-rarity")
        rarity = _text(rarity_node) if rarity_node else None

        if name and value:
            attrs.append(GiftAttribute(name=name, value=value, rarity=rarity))

    return attrs


def parse_gift_issued(html: str) -> str | None:
    """Parse gift issued info."""
    m = re.search(
        r'Issued</div>\s*</td>\s*<td>\s*<div class="table-cell">\s*'
        r'<div[^>]*>\s*([^<]+?)\s*</div>',
        html, re.DOTALL,
    )
    return m.group(1).strip() if m else None


def parse_stars_packages(html: str) -> list[StarsPrice]:
    """Parse stars package prices from stars page HTML."""
    tree = LexborHTMLParser(html)
    packages: list[StarsPrice] = []

    for label in tree.css("label"):
        input_node = label.css_first('input[name="stars"]')
        if not input_node:
            continue
        stars = int(_attr(input_node, "value") or "0")
        if stars == 0:
            continue

        label_html = label.html or ""

        ton_m = re.search(r'icon-ton[^>]*>([^<]*(?:<span[^>]*>[^<]*</span>)?)', label_html)
        ton_raw = re.sub(r'<[^>]+>', '', ton_m.group(1)).replace(',', '').strip() if ton_m else "0"

        usd_m = re.search(r'icon-usd[^>]*>([^<]+)', label_html)
        if not usd_m:
            usd_m = re.search(r'(?:&#036;|\$)\s*([\d.,]+)', label_html)
        usd_raw = usd_m.group(1).replace(',', '').strip() if usd_m else "0"

        packages.append(StarsPrice(stars=stars, gram_price=ton_raw, usd_price=usd_raw))

    return packages


def parse_stars_price_from_html(html: str) -> tuple[str | None, str | None]:
    """Parse GRAM and USD price from inline HTML fragment."""
    ton_m = re.search(r'icon-ton[^>]*>([^<]*(?:<span[^>]*>[^<]*</span>)?)', html)
    gram_price = re.sub(r'<[^>]+>', '', ton_m.group(1)).replace(',', '').strip() if ton_m else None

    usd_m = re.search(r'icon-usd[^>]*>([^<]+)', html)
    if not usd_m:
        usd_m = re.search(r'(?:&#036;|\$)\s*([\d.,]+)', html)
    usd_price = usd_m.group(1).replace(',', '').strip() if usd_m else None

    return gram_price, usd_price


def parse_premium_options(html: str) -> list[PremiumPriceOption]:
    """Parse premium price options from premium page HTML."""
    tree = LexborHTMLParser(html)
    options: list[PremiumPriceOption] = []

    for label in tree.css("label"):
        input_node = label.css_first('input[name="months"]')
        if not input_node:
            continue
        months = int(_attr(input_node, "value") or "0")
        if months == 0:
            continue

        label_html = label.html or ""

        label_node = label.css_first(".tm-radio-label")
        label_text = _text(label_node) if label_node else f"{months} months"

        badge_node = label.css_first(".tm-radio-label-badge")
        discount = _text(badge_node) if badge_node else None

        ton_m = re.search(r'icon-ton[^>]*>([^<]*(?:<span[^>]*>[^<]*</span>)?)', label_html)
        ton_raw = re.sub(r'<[^>]+>', '', ton_m.group(1)).replace(',', '').strip() if ton_m else "0"

        usd_m = re.search(r'(?:&#036;|\$)\s*([\d.,]+)', label_html)
        if not usd_m:
            usd_m = re.search(r'icon-usd[^>]*>([^<]+)', label_html)
        usd_raw = usd_m.group(1).replace(',', '').strip() if usd_m else "0"

        options.append(PremiumPriceOption(
            months=months, label=label_text, gram_price=ton_raw,
            usd_price=usd_raw, discount=discount,
        ))

    return options


def parse_stars_history(html: str) -> list[StarsTransaction]:
    """Parse stars transaction history from HTML."""
    tree = LexborHTMLParser(html)
    transactions: list[StarsTransaction] = []

    tbody = tree.css_first("tbody")
    if not tbody:
        return transactions

    for row in tbody.css("tr"):
        if row.css_first("th"):
            continue

        recip_node = row.css_first(".tm-inline-nowrap")
        recipient = _text(recip_node).lstrip("@") if recip_node else ""
        if not recipient:
            continue

        stars_node = row.css_first(".tm-value.tm-nowrap")
        stars_str = _clean_price(_text(stars_node)) if stars_node else "0"
        try:
            stars = int(stars_str)
        except ValueError:
            stars = 0

        price_node = row.css_first(".icon-before.icon-ton")
        price_raw = ""
        if price_node:
            raw = _text(price_node)
            price_raw = _clean_price(re.sub(r'<[^>]+>', '.', raw).replace(' ', ''))

        time_node = row.css_first("time[datetime]")
        date = _attr(time_node, "datetime") if time_node else ""

        transactions.append(StarsTransaction(recipient=recipient, stars=stars, price_gram=price_raw, date=date))

    return transactions


def parse_premium_history(html: str) -> list[PremiumTransaction]:
    """Parse premium transaction history from HTML."""
    tree = LexborHTMLParser(html)
    transactions: list[PremiumTransaction] = []

    tbody = tree.css_first("tbody")
    if not tbody:
        return transactions

    for row in tbody.css("tr"):
        if row.css_first("th"):
            continue

        recip_node = row.css_first(".tm-inline-nowrap")
        recipient = _text(recip_node).lstrip("@") if recip_node else ""
        if not recipient:
            continue

        dur_node = row.css_first(".tm-nowrap")
        duration = _text(dur_node) if dur_node else ""

        price_node = row.css_first(".icon-before.icon-ton")
        price_raw = ""
        if price_node:
            raw = _text(price_node)
            price_raw = _clean_price(re.sub(r'<[^>]+>', '.', raw).replace(' ', ''))

        time_node = row.css_first("time[datetime]")
        date = _attr(time_node, "datetime") if time_node else ""

        transactions.append(PremiumTransaction(recipient=recipient, duration=duration, price_gram=price_raw, date=date))

    return transactions


def parse_topup_history(html: str) -> list[TopupTransaction]:
    """Parse topup transaction history from Ads page HTML."""
    tree = LexborHTMLParser(html)
    transactions: list[TopupTransaction] = []

    tbody = tree.css_first("tbody")
    if not tbody:
        return transactions

    for row in tbody.css("tr"):
        if row.css_first("th"):
            continue

        link = row.css_first('a[href*="t.me/"]')
        recipient = ""
        if link:
            text = _text(link).lstrip("@")
            recipient = text

        price_node = row.css_first(".icon-before.icon-ton")
        amount = 0
        if price_node:
            try:
                amount = int(_clean_price(_text(price_node)))
            except ValueError:
                pass

        time_node = row.css_first("time[datetime]")
        date = _attr(time_node, "datetime") if time_node else ""

        transactions.append(TopupTransaction(recipient=recipient, amount=amount, date=date))

    return transactions


def parse_profile(html: str) -> ProfileInfo:
    """Parse profile info from profile page HTML."""
    tree = LexborHTMLParser(html)

    name_node = tree.css_first(".tm-settings-item-head")
    name = _text(name_node)

    user_node = tree.css_first(".tm-settings-item-desc")
    username = _text(user_node).lstrip("@")

    photo_node = tree.css_first(".tm-settings-account-photo img")
    photo_url = _attr(photo_node, "src").replace("\\/", "/") if photo_node else None

    verified_node = tree.css_first(".tm-badge-verified")
    identity_verified = bool(verified_node and "Identity" in _text(verified_node))

    wallet_label: str | None = None
    wallet_section = re.search(r'Linked Wallet.*?tm-settings-item-desc[^>]*>.*?<span class="short">([^<]+)</span>', html, re.DOTALL)
    if wallet_section:
        wallet_label = wallet_section.group(1).strip()

    wallet_verified = bool(re.search(r"Linked Wallet.*?tm-badge-verified", html, re.DOTALL))

    wallet_address: str | None = None
    addr_m = re.search(r'Wallet\.init\(\{[^}]*"address"\s*:\s*"([^"]+)"', html)
    if addr_m:
        addr_val = addr_m.group(1)
        if addr_val and addr_val != "false":
            wallet_address = addr_val

    return ProfileInfo(
        name=name, username=username, photo_url=photo_url,
        identity_verified=identity_verified, wallet_address=wallet_address,
        wallet_label=wallet_label, wallet_verified=wallet_verified,
    )


def parse_my_bids(html: str, item_type: str) -> tuple[list[MyBid], int]:
    """Parse My Bid History HTML into structured bid objects."""
    tree = LexborHTMLParser(html)
    items: list[MyBid] = []

    total_count = 0
    if item_type == "usernames":
        tab_pattern = r'<a href="/my/bids"[^>]*>.*?Usernames.*?<span[^>]*>(\d+)</span>'
    else:
        tab_pattern = r'<a href="/my/bids\?type={}"[^>]*>.*?<span[^>]*>(\d+)</span>'.format(item_type)
    tab_match = re.search(tab_pattern, html, re.DOTALL)
    if tab_match:
        total_count = int(tab_match.group(1))

    for row in tree.css("tr.tm-row-selectable"):
        row_html = row.html or ""

        if item_type == "usernames":
            href_match = re.search(r'href="/(username/[^"]+)"', row_html)
            slug = href_match.group(1) if href_match else ""
            val_node = row.css_first(".table-cell-value.tm-value")
            name = f"@{_text(val_node).lstrip('@')}" if val_node else slug
            image_url = None
        elif item_type == "gifts":
            href_match = re.search(r'href="(/gift/[^"]+)"', row_html)
            slug = href_match.group(1).lstrip("/") if href_match else ""
            val_node = row.css_first(".table-cell-value.tm-value")
            name = _text(val_node) or slug
            img = row.css_first("img[src]")
            image_url = _attr(img, "src") if img else None
        else:
            href_match = re.search(r'href="/(number/[^"]+)"', row_html)
            slug = href_match.group(1) if href_match else ""
            val_node = row.css_first(".table-cell-value.tm-value")
            name = _text(val_node) or slug
            image_url = None

        desc_node = row.css_first(".table-cell-desc.tm-nowrap")
        description = _text(desc_node) if desc_node else None

        bid_node = row.css_first(".icon-before.icon-ton")
        bid = float(_clean_price(_text(bid_node))) if bid_node else 0.0

        time_node = row.css_first("time[datetime]")
        date = _attr(time_node, "datetime") if time_node else ""

        status_m = re.search(r'tm-status-([a-z]+)[^>]*>([^<]+)</div>', row_html)
        status = status_m.group(2).strip() if status_m else "Unknown"

        if slug:
            items.append(MyBid(
                item_type=item_type, slug=slug, name=name, bid=bid,
                status=status, date=date, image_url=image_url, description=description,
            ))

    return items, total_count


def parse_my_assets(html: str, item_type: str) -> tuple[list[MyAsset], int]:
    """Parse My Assets HTML into structured asset objects."""
    tree = LexborHTMLParser(html)
    items: list[MyAsset] = []

    if item_type == "usernames":
        tab_pattern = r'<a href="/my/usernames"[^>]*>.*?Usernames.*?<span[^>]*>(\d+)</span>'
    elif item_type == "gifts":
        tab_pattern = r'<a href="/my/gifts"[^>]*>.*?Gifts.*?<span[^>]*>(\d+)</span>'
    else:
        tab_pattern = r'<a href="/my/numbers"[^>]*>.*?(?:Collectible )?Numbers.*?<span[^>]*>(\d+)</span>'

    total_match = re.search(tab_pattern, html, re.DOTALL)
    total_count = int(total_match.group(1)) if total_match else 0

    assign_name_map: dict[str, str] = {}
    popup = tree.css_first(".popup-container.js-assign-popup")
    if popup:
        for label in popup.css("label.tm-assign-account-item"):
            input_node = label.css_first("input[value]")
            name_node = label.css_first(".tm-assign-account-name")
            if input_node and name_node:
                assign_name_map[_attr(input_node, "value")] = _text(name_node)

    for row in tree.css("tr.tm-row-selectable"):
        row_html = row.html or ""

        if item_type == "usernames":
            href_match = re.search(r'href="/(username/[^"]+)"', row_html)
            slug = href_match.group(1) if href_match else ""
            val_node = row.css_first(".table-cell-value.tm-value")
            name = f"@{_text(val_node).lstrip('@')}" if val_node else slug
            image_url = None
            description = None
            assigned_to_m = re.search(r'data-assigned-to="([^"]+)"', row_html)
            assigned_to = assigned_to_m.group(1) if assigned_to_m else None
            assigned_name = assign_name_map.get(assigned_to) if assigned_to else None
        elif item_type == "gifts":
            href_match = re.search(r'href="(/gift/[^"?]+)', row_html)
            slug = href_match.group(1).lstrip("/") if href_match else ""
            val_node = row.css_first(".table-cell-value.tm-value")
            name = _text(val_node) or slug
            img = row.css_first("img[src]")
            image_url = _attr(img, "src") if img else None
            desc_node = row.css_first(".table-cell-desc.tm-nowrap")
            description = _text(desc_node) if desc_node else None
            assigned_to_m = re.search(r'data-assigned-to="([^"]+)"', row_html)
            assigned_to = assigned_to_m.group(1) if assigned_to_m else None
            assigned_name_node = row.css_first(".js-assigned-to")
            assigned_name = _text(assigned_name_node) or "Wallet" if assigned_name_node else None
        else:
            href_match = re.search(r'href="/(number/[^"]+)"', row_html)
            slug = href_match.group(1) if href_match else ""
            val_node = row.css_first(".table-cell-value.tm-value")
            name = _text(val_node) or slug
            image_url = None
            description = None
            assigned_to = None
            assigned_name = None

        if slug:
            items.append(MyAsset(
                item_type=item_type, slug=slug, name=name,
                description=description, image_url=image_url,
                assigned_to=assigned_to, assigned_name=assigned_name,
            ))

    return items, total_count


def parse_assign_accounts(html: str) -> tuple[list[TelegramAccount], bool]:
    """Parse available Telegram accounts from assign popup HTML."""
    tree = LexborHTMLParser(html)
    accounts: list[TelegramAccount] = []
    can_disable = False

    popup = tree.css_first(".popup-container.js-assign-popup")
    if not popup:
        return accounts, can_disable

    popup_html = popup.html or ""
    can_disable = "Don't display on Telegram" in popup_html

    for label in popup.css("label.tm-assign-account-item"):
        input_node = label.css_first("input[value]")
        if not input_node:
            continue

        account_id = _attr(input_node, "value")
        name_node = label.css_first(".tm-assign-account-name")
        name = _text(name_node) or "Unknown"
        type_node = label.css_first(".tm-assign-account-desc")
        acc_type = _text(type_node) or "Unknown"
        img = label.css_first("img[src]")
        photo_url = _attr(img, "src") if img else None

        accounts.append(TelegramAccount(id=account_id, name=name, type=acc_type, photo_url=photo_url))

    return accounts, can_disable


def parse_sessions(html: str) -> list[SessionInfo]:
    """Parse active sessions from sessions page HTML."""
    tree = LexborHTMLParser(html)
    sessions: list[SessionInfo] = []

    tbody = tree.css_first("tbody")
    if not tbody:
        return sessions

    for row in tbody.css("tr"):
        if row.css_first("th"):
            continue

        row_html = row.html or ""

        device_node = row.css_first(".table-cell-value.tm-value")
        device = _text(device_node)

        loc_nodes = row.css(".table-cell-desc-col.tm-nowrap")
        location = ""
        for ln in loc_nodes:
            val = _text(ln)
            if val and not val.startswith("now") and "at " not in val:
                location = val
                break

        sid_m = re.search(r'data-session-id="([^"]+)"', row_html)
        session_id = sid_m.group(1) if sid_m else ""

        is_current = "Current" in row_html and "tm-status-avail" in row_html

        time_node = row.css_first("time[datetime]")
        date = _attr(time_node, "datetime") if time_node else ("now" if is_current else None)

        if device or session_id:
            sessions.append(SessionInfo(
                session_id=session_id, device=device, location=location,
                date=date, is_current=is_current,
            ))

    return sessions


def parse_login_code(html: str) -> tuple[str | None, int]:
    """Extract the pending login code and active session count."""
    tree = LexborHTMLParser(html)

    code_node = tree.css_first(".table-cell-value")
    code = _text(code_node) if code_node else None

    active_sessions = len(tree.css("tr"))
    return code, active_sessions