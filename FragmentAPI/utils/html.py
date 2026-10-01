"""Fragment HTML parsers for full pages and partial AJAX responses."""

from __future__ import annotations

import json
import re
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import parse_qs, urlsplit

from selectolax.lexbor import LexborHTMLParser

from FragmentAPI.types.models import (
    AuctionInfo,
    BidHistoryEntry,
    GiftAttribute,
    GiftAttributeCategory,
    GiftAttributeValue,
    GiftCollection,
    MyAsset,
    MyBid,
    OfferHistoryEntry,
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


_ASSET_PREFIXES = {
    "usernames": "username",
    "numbers": "number",
    "gifts": "gift",
}

_NUMBER_RE = re.compile(r"\d[\d,\s\u00a0\u202f]*")
_SPACE_RE = re.compile(r"[\s\u00a0\u202f]+")
_PRICE_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$")


def _tree(html: str) -> LexborHTMLParser:
    """Preserve table fragments that an HTML document parser would otherwise drop."""
    text = html or ""
    if not re.search(r"<table\b", text, re.IGNORECASE):
        if re.search(r"<(?:thead|tbody|tfoot|tr)\b", text, re.IGNORECASE):
            text = f"<table>{text}</table>"
        elif re.search(r"<(?:td|th)\b", text, re.IGNORECASE):
            text = f"<table><tbody><tr>{text}</tr></tbody></table>"
    return LexborHTMLParser(text)


def _text(node: Any) -> str:
    """Extract text without inserting separators into nested decimal prices."""
    if node is None:
        return ""
    return (node.text(strip=True) or "").strip()


def _words(node: Any) -> str:
    """Extract human-readable text with normalized word separators."""
    if node is None:
        return ""
    return _SPACE_RE.sub(" ", node.text(separator=" ", strip=True) or "").strip()


def _attr(node: Any, name: str) -> str:
    """Read an optional HTML attribute."""
    if node is None:
        return ""
    return str(node.attributes.get(name) or "").strip()


def _first(root: Any, *selectors: str) -> Any:
    """Select the first match by selector priority rather than document order."""
    if root is None:
        return None
    for selector in selectors:
        node = root.css_first(selector)
        if node is not None:
            return node
    return None


def _without(node: Any, selectors: str, *, words: bool = False) -> str:
    """Extract text from an isolated copy with decorative descendants removed."""
    if node is None:
        return ""
    tree = _tree(node.html or "")
    for child in tree.css(selectors):
        child.decompose()
    root = tree.body
    if root is None:
        root = tree.root
    return _words(root) if words else _text(root)


def _status(node: Any) -> str:
    """Prefer desktop status text without affecting ordinary names or prices."""
    if node is None:
        return ""
    wide = node.css_first(".wide-only")
    if wide is not None:
        value = _words(wide)
        if value:
            return value
    return _words(node)


def _clean_price(value: str) -> str:
    """Remove visual digit grouping without rounding the decimal amount."""
    return _SPACE_RE.sub("", value.replace(",", "")).strip()


def _numeric(value: str) -> str | None:
    """Normalize plain nonnegative currency text and reject nonnumeric labels."""
    cleaned = _clean_price(value)
    cleaned = cleaned.removeprefix("$")
    cleaned = re.sub(r"(?:TON|GRAM|USD)$", "", cleaned, flags=re.IGNORECASE)
    if not _PRICE_RE.fullmatch(cleaned):
        return None
    try:
        number = Decimal(cleaned)
    except InvalidOperation:
        return None
    if not number.is_finite() or number < 0:
        return None
    return cleaned


def _price(node: Any) -> str | None:
    """Keep full price precision while retaining two-decimal listing formatting."""
    value = _numeric(_text(node))
    if value is None:
        return _clean_price(_text(node)) or None
    number = Decimal(value)
    if number.as_tuple().exponent >= -2:
        return format(number, ".2f")
    return format(number, "f")


def _count(value: str) -> int:
    """Read a displayed integer, including comma and nonbreaking-space grouping."""
    match = _NUMBER_RE.search(value or "")
    if match is None:
        return 0
    digits = re.sub(r"\D", "", match.group())
    return int(digits) if digits else 0


def _integer_amount(value: str) -> int:
    """Read an integral amount without turning a decimal point into extra digits."""
    normalized = _numeric(value)
    if normalized is None:
        return 0
    number = Decimal(normalized)
    if number != number.to_integral_value():
        return 0
    return int(number)


def _offset(root: Any, selector: str = "[data-next-offset]") -> str | None:
    """Read the first nonempty pagination cursor."""
    for node in root.css(selector):
        value = _attr(node, "data-next-offset")
        if value:
            return value
    return None


def _date(root: Any) -> str | None:
    """Read a machine-readable timestamp."""
    return _attr(root.css_first("time[datetime]"), "datetime") or None


def _image(root: Any) -> str | None:
    """Read an image URL with lazy-image and source-set fallbacks."""
    image = _first(root, "img[src]", "img[data-src]")
    value = _attr(image, "src") or _attr(image, "data-src")
    if not value:
        source = _first(root, "source[srcset]", "img[srcset]")
        srcset = _attr(source, "srcset")
        if srcset:
            value = srcset.split(",", 1)[0].strip().split()[0]
    return value.replace("\\/", "/") or None


def _asset_slug(href: str, prefixes: tuple[str, ...]) -> str | None:
    """Extract a Fragment asset path without query strings or fragments."""
    try:
        parsed = urlsplit(href.replace("\\/", "/"))
    except ValueError:
        return None
    if parsed.netloc and parsed.hostname != "fragment.com":
        return None
    path = parsed.path.strip("/")
    for prefix in prefixes:
        if path.startswith(f"{prefix}/") and len(path) > len(prefix) + 1:
            return path
    return None


def _asset_link(root: Any, prefixes: tuple[str, ...]) -> tuple[Any, str | None]:
    """Find an asset link without mistaking wallet or Telegram links for assets."""
    for link in root.css("a[href]"):
        slug = _asset_slug(_attr(link, "href"), prefixes)
        if slug is not None:
            return link, slug
    return None, None


def _wallet_address(root: Any) -> str | None:
    """Extract a wallet identifier from a Tonviewer link."""
    if root is None:
        return None
    for link in root.css("a[href]"):
        try:
            parsed = urlsplit(_attr(link, "href").replace("\\/", "/"))
        except ValueError:
            continue
        if parsed.hostname in {"tonviewer.com", "www.tonviewer.com"}:
            return parsed.path.strip("/") or None
    return None


def _row_status(row: Any) -> str | None:
    """Support explicit status classes and older secondary tm-value labels."""
    node = _first(
        row,
        '[class*="tm-status-"]',
        ".tm-grid-item-status",
        ".table-cell-status",
    )
    if node is not None:
        return _status(node) or None
    values = row.css(".tm-value")
    for node in values[1:]:
        value = _status(node)
        if not value or value.startswith(("@", "+")):
            continue
        if node.css_first("time") is not None:
            continue
        if "icon-ton" in _attr(node, "class").split():
            continue
        if _numeric(value) is not None:
            continue
        return value
    return None


def parse_auction_rows(html: str) -> list[dict[str, Any]]:
    """Parse username and number rows from full tables or bare row fragments."""
    items: list[dict[str, Any]] = []
    for row in _tree(html).css("tr.tm-row-selectable"):
        _, slug = _asset_link(row, ("username", "number"))
        if slug is None:
            continue
        name = _first(row, ".table-cell-value.tm-value", ".tm-value")
        items.append({
            "slug": slug,
            "name": _text(name) or slug,
            "status": _row_status(row),
            "price": _price(row.css_first(".icon-ton")),
            "date": _date(row),
        })
    return items


def parse_listing_offset(html: str) -> str | None:
    """Read a listing cursor from a page or pagination-only fragment."""
    return _offset(_tree(html))


def parse_gift_items(html: str) -> tuple[list[dict[str, Any]], int | None]:
    """Parse gift cards without merging mobile and desktop status labels."""
    tree = _tree(html)
    items: list[dict[str, Any]] = []
    for card in tree.css("a.tm-grid-item"):
        slug = _asset_slug(_attr(card, "href"), ("gift",))
        if slug is None:
            continue
        name = _text(card.css_first(".item-name")) or slug
        number = _text(card.css_first(".item-num")).lstrip("#").strip()
        if number and not re.search(rf"#\s*{re.escape(number)}$", name):
            name = f"{name} #{number}"
        items.append({
            "slug": slug,
            "name": name,
            "status": _status(card.css_first(".tm-grid-item-status")) or None,
            "price": _price(_first(
                card,
                ".tm-grid-item-value.icon-ton",
                ".icon-ton",
            )),
            "date": _date(card),
        })
    cursor = _offset(tree)
    numeric_cursor = int(cursor) if cursor and cursor.isdigit() else None
    return items, numeric_cursor


def _heading_matches(node: Any, title: str) -> bool:
    """Match a section title even when a count badge follows it."""
    text = _words(node).casefold()
    expected = title.casefold()
    return text == expected or bool(
        re.fullmatch(rf"{re.escape(expected)}\s*[\[(]?\s*[\d,\s]+\s*[\])]?", text)
    )


def _history_scope(tree: Any, title: str, marker: str) -> Any:
    """Find the relevant history section without borrowing unrelated rows."""
    for section in tree.css("section"):
        heading = _first(section, "h3", "h2", ".tm-section-header-text")
        if _heading_matches(heading, title):
            return section
    for heading in tree.css("h3, h2"):
        if not _heading_matches(heading, title):
            continue
        parent = heading.parent
        while parent is not None and parent.tag not in {"body", "html"}:
            if parent.css_first("tr") is not None:
                return parent
            parent = parent.parent
    marker_node = tree.css_first(marker)
    if marker_node is not None and not tree.css("h2, h3"):
        return tree
    return None


def _parse_history_rows(
    html: str,
    section_title: str,
) -> tuple[list[dict[str, Any]], str | None]:
    """Parse a named history section while preserving transfer labels."""
    markers = {
        "Bid History": ".js-load-more-orders",
        "Ownership History": ".js-load-more-owners",
        "Latest Offers": ".js-load-more-offers",
    }
    tree = _tree(html)
    marker = markers[section_title]
    scope = _history_scope(tree, section_title, marker)
    if scope is None:
        return [], None

    entries: list[dict[str, Any]] = []
    for row in scope.css("tr"):
        if not row.css("td"):
            continue
        price_node = row.css_first(".icon-ton")
        price = _clean_price(_text(price_node)) or None
        price_label = None
        if price is None:
            value = _text(_first(
                row,
                ".table-cell-value.tm-value",
                ".table-cell-value",
            ))
            if value.casefold() == "transferred":
                price_label = "Transferred"
            elif _numeric(value) is not None:
                price = _numeric(value)
        date = _date(row)
        wallet = _wallet_address(row)
        if price is None and price_label is None and date is None and wallet is None:
            continue
        entries.append({
            "price": price,
            "price_label": price_label,
            "date": date,
            "wallet": wallet,
        })
    cursor = _offset(scope, f"{marker}[data-next-offset]") or _offset(scope)
    return entries, cursor


def parse_bid_history(html: str) -> tuple[list[BidHistoryEntry], str | None]:
    """Read item bid history."""
    rows, cursor = _parse_history_rows(html, "Bid History")
    return [
        BidHistoryEntry(price=row["price"], date=row["date"], wallet=row["wallet"])
        for row in rows
    ], cursor


def parse_owner_history(html: str) -> tuple[list[OwnerHistoryEntry], str | None]:
    """Read ownership history, retaining the Transferred label."""
    rows, cursor = _parse_history_rows(html, "Ownership History")
    return [
        OwnerHistoryEntry(
            price=row["price_label"] or row["price"],
            date=row["date"],
            wallet=row["wallet"],
        )
        for row in rows
    ], cursor


def parse_offer_history(html: str) -> tuple[list[OfferHistoryEntry], str | None]:
    """Read item offer history."""
    rows, cursor = _parse_history_rows(html, "Latest Offers")
    return [
        OfferHistoryEntry(price=row["price"], date=row["date"], wallet=row["wallet"])
        for row in rows
    ], cursor


def parse_item_status(html: str) -> str:
    """Read the item-level status."""
    return _status(_tree(html).css_first(
        '[class*="tm-section-header-status"]'
    )) or "Unknown"


def parse_sold_owner(html: str) -> str | None:
    """Read the owner wallet from the item summary."""
    tree = _tree(html)
    return _wallet_address(tree.css_first(".tm-section-bid-info"))


def _auction_label(value: str) -> str | None:
    """Map recognized pricing headings to public AuctionInfo fields."""
    text = _SPACE_RE.sub(" ", value).strip().rstrip(":").casefold()
    return {
        "highest bid": "highest_bid",
        "current bid": "highest_bid",
        "bid step": "bid_step",
        "minimum bid": "minimum_bid",
        "min bid": "minimum_bid",
        "sell price": "sell_price",
        "sale price": "sell_price",
        "buy now": "buy_now_price",
        "buy now price": "buy_now_price",
    }.get(text)


def parse_auction_info(html: str) -> AuctionInfo:
    """Associate prices with headings in vertical and horizontal pricing tables."""
    tree = _tree(html)
    values: dict[str, str | None] = {}

    for table in tree.css("table"):
        rows = table.css("tr")
        for index, row in enumerate(rows):
            headers = row.css("th")
            cells = row.css("td")

            if len(headers) == 1 and cells:
                key = _auction_label(_words(headers[0]))
                price = _numeric(_text(row.css_first(".icon-ton")))
                if key and price is not None:
                    values.setdefault(key, price)

            if len(headers) > 1:
                for later in rows[index + 1:]:
                    later_cells = later.css("td")
                    if len(later_cells) != len(headers):
                        continue
                    for header, cell in zip(headers, later_cells):
                        key = _auction_label(_words(header))
                        price = _numeric(_text(cell.css_first(".icon-ton")))
                        if key and price is not None:
                            values.setdefault(key, price)
                    break

            if len(cells) >= 2:
                key = _auction_label(_words(cells[0]))
                price = _numeric(_text(cells[1].css_first(".icon-ton")))
                if key and price is not None:
                    values.setdefault(key, price)

    summary = tree.css_first(".tm-section-bid-info")
    if summary is not None:
        for node in summary.css(".table-cell"):
            label = _first(node, ".table-cell-desc", ".table-cell-label")
            key = _auction_label(_words(label))
            price = _numeric(_text(node.css_first(".icon-ton")))
            if key and price is not None:
                values.setdefault(key, price)

    buy = _first(
        tree,
        ".js-buy-now-btn[data-bid-amount]",
        '[class*="js-buy-now-btn"][data-bid-amount]',
    )
    if buy is not None:
        values["buy_now_price"] = _attr(buy, "data-bid-amount") or None

    return AuctionInfo(**values)


def parse_gift_attributes(html: str) -> list[GiftAttribute]:
    """Read property values separately from their rarity badges."""
    result: list[GiftAttribute] = []
    for row in _tree(html).css("tr"):
        cells = row.css("td")
        if len(cells) < 2:
            continue
        label = cells[0].css_first(".table-cell")
        name = _words(label if label is not None else cells[0])
        if not name or name.casefold() in {"owner", "issued"}:
            continue
        value_node = _first(
            cells[1],
            ".table-cell-value.tm-value",
            ".table-cell-value",
        )
        if value_node is None:
            continue
        if value_node.css_first(".icon-ton") is not None:
            continue
        link = value_node.css_first("a")
        value = _words(link) if link is not None else _without(
            value_node, ".tm-rarity", words=True
        )
        if not value:
            continue
        result.append(GiftAttribute(
            name=name,
            value=value,
            rarity=_words(cells[1].css_first(".tm-rarity")) or None,
        ))
    return result


def parse_gift_issued(html: str) -> str | None:
    """Read issuance information from the matching property row."""
    for row in _tree(html).css("tr"):
        cells = row.css("td")
        if len(cells) < 2:
            continue
        if _words(cells[0]).casefold() != "issued":
            continue
        value = _first(cells[1], ".table-cell-value", ".tm-value")
        return _words(value if value is not None else cells[1]) or None
    return None


def parse_stars_price_from_html(html: str) -> tuple[str | None, str | None]:
    """Read native and USD prices without rounding nested fractional spans."""
    tree = _tree(html)
    native = _numeric(_text(tree.css_first(".icon-ton")))
    usd = _numeric(_text(tree.css_first(".icon-usd")))
    if usd is None:
        match = re.search(
            r"\$\s*(\d[\d,\u00a0\u202f]*(?:\.\d+)?)",
            tree.text(),
        )
        if match:
            usd = _numeric(match.group(1))
    return native, usd


def parse_stars_packages(html: str) -> list[StarsPrice]:
    """Read available Stars packages and merge duplicate responsive controls."""
    packages: dict[int, StarsPrice] = {}
    for label in _tree(html).css("label"):
        quantity = _attr(label.css_first('input[name="stars"]'), "value")
        if not quantity.isdigit() or int(quantity) <= 0:
            continue
        native, usd = parse_stars_price_from_html(label.html or "")
        if native is None:
            continue
        count = int(quantity)
        previous = packages.get(count)
        packages[count] = StarsPrice(
            stars=count,
            gram_price=native,
            usd_price=usd or (previous.usd_price if previous else "0"),
        )
    return list(packages.values())


def parse_premium_options(html: str) -> list[PremiumPriceOption]:
    """Read Premium duration options without including badges in their labels."""
    options: dict[int, PremiumPriceOption] = {}
    for label in _tree(html).css("label"):
        duration = _attr(label.css_first('input[name="months"]'), "value")
        if not duration.isdigit() or int(duration) <= 0:
            continue
        native, usd = parse_stars_price_from_html(label.html or "")
        if native is None:
            continue
        months = int(duration)
        previous = options.get(months)
        label_node = label.css_first(".tm-radio-label")
        text = _without(label_node, ".tm-radio-label-badge", words=True)
        options[months] = PremiumPriceOption(
            months=months,
            label=text or f"{months} months",
            gram_price=native,
            usd_price=usd or (previous.usd_price if previous else "0"),
            discount=_words(label.css_first(".tm-radio-label-badge")) or (
                previous.discount if previous else None
            ),
        )
    return list(options.values())


def _data_rows(html: str) -> list[Any]:
    """Read data rows from either a complete table or an AJAX row fragment."""
    return [
        row for row in _tree(html).css("tr")
        if row.css("td") and not row.css("th")
    ]


def parse_stars_history(html: str) -> list[StarsTransaction]:
    """Read account Stars transactions."""
    result: list[StarsTransaction] = []
    for row in _data_rows(html):
        target = _text(row.css_first(".tm-inline-nowrap")).lstrip("@")
        if not target:
            continue
        result.append(StarsTransaction(
            recipient=target,
            stars=_integer_amount(_text(row.css_first(".tm-value.tm-nowrap"))),
            price_gram=_clean_price(_text(row.css_first(".icon-ton"))),
            date=_date(row) or "",
        ))
    return result


def parse_premium_history(html: str) -> list[PremiumTransaction]:
    """Read account Premium history without confusing recipient and duration."""
    result: list[PremiumTransaction] = []
    for row in _data_rows(html):
        target = _text(row.css_first(".tm-inline-nowrap")).lstrip("@")
        if not target:
            continue
        duration = ""
        for node in row.css(".tm-nowrap"):
            value = _words(node)
            if re.search(r"\b(?:months?|years?)\b", value, re.IGNORECASE):
                duration = value
                break
        if not duration:
            for node in row.css(".tm-nowrap"):
                if node.css_first(".tm-inline-nowrap, .icon-ton, time") is not None:
                    continue
                if "tm-inline-nowrap" in _attr(node, "class").split():
                    continue
                duration = _words(node)
                if duration:
                    break
        result.append(PremiumTransaction(
            recipient=target,
            duration=duration,
            price_gram=_clean_price(_text(row.css_first(".icon-ton"))),
            date=_date(row) or "",
        ))
    return result


def parse_topup_history(html: str) -> list[TopupTransaction]:
    """Read Ads top-ups without concatenating fractional digits into integers."""
    result: list[TopupTransaction] = []
    for row in _data_rows(html):
        link = row.css_first('a[href*="t.me/"]')
        target = _text(link).lstrip("@")
        if not target and link is not None:
            try:
                target = urlsplit(_attr(link, "href")).path.strip("/")
            except ValueError:
                target = ""
        if not target:
            continue
        result.append(TopupTransaction(
            recipient=target,
            amount=_integer_amount(_text(row.css_first(".icon-ton"))),
            date=_date(row) or "",
        ))
    return result


def _wallet_init(html: str) -> dict[str, Any]:
    """Decode Wallet.init JSON without matching unrelated address fields."""
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\bWallet\.init\s*\(", html):
        try:
            value, _ = decoder.raw_decode(html[match.end():].lstrip())
        except ValueError:
            continue
        if isinstance(value, dict):
            return value
    return {}


def _settings_scope(tree: Any, title: str) -> Any:
    """Find the settings row containing a named section heading."""
    for heading in tree.css(".tm-settings-item-head, h3, h4"):
        if title.casefold() not in _words(heading).casefold():
            continue
        parent = heading.parent
        while parent is not None and parent.tag not in {"body", "html"}:
            classes = _attr(parent, "class").split()
            if "tm-settings-item" in classes:
                return parent
            if parent.css_first(".tm-settings-item-desc") is not None:
                return parent
            parent = parent.parent
    return None


def parse_profile(html: str) -> ProfileInfo:
    """Read profile information and scope linked-wallet details correctly."""
    tree = _tree(html)
    account = _first(
        tree,
        ".tm-settings-account",
        ".tm-settings-item-account",
    )
    if account is None:
        photo = tree.css_first(".tm-settings-account-photo")
        parent = photo.parent if photo is not None else None
        while parent is not None and parent.tag not in {"body", "html"}:
            if parent.css_first(".tm-settings-item-head") is not None:
                account = parent
                break
            parent = parent.parent
    if account is None:
        account = tree

    linked = _settings_scope(tree, "Linked Wallet")
    identity = _settings_scope(tree, "Identity")
    data = _wallet_init(html)
    address = data.get("address")
    if not isinstance(address, str) or address.casefold() in {"", "false", "null"}:
        address = None

    label = _words(_first(
        linked,
        ".tm-settings-item-desc .short",
        ".short",
        ".tm-wallet",
        ".tm-settings-item-desc",
    )) or None

    identity_verified = any(
        "identity" in _words(node).casefold()
        for node in tree.css(".tm-badge-verified")
    )
    if identity is not None and identity.css_first(".tm-badge-verified") is not None:
        identity_verified = True

    return ProfileInfo(
        name=_words(account.css_first(".tm-settings-item-head")),
        username=_text(account.css_first(".tm-settings-item-desc")).lstrip("@"),
        photo_url=_image(tree.css_first(".tm-settings-account-photo")),
        identity_verified=identity_verified,
        wallet_address=address,
        wallet_label=label,
        wallet_verified=bool(
            linked is not None
            and linked.css_first(".tm-badge-verified") is not None
        ),
    )


def _tab_total(tree: Any, item_type: str, *, bids: bool) -> int | None:
    """Read the requested category count rather than whichever tab is active."""
    for link in tree.css("a[href]"):
        try:
            parsed = urlsplit(_attr(link, "href"))
        except ValueError:
            continue
        if bids:
            if parsed.path.rstrip("/") != "/my/bids":
                continue
            category = parse_qs(parsed.query).get("type", ["usernames"])[0]
            if category != item_type:
                continue
        elif parsed.path.rstrip("/") != f"/my/{item_type}":
            continue
        for node in reversed(link.css("span")):
            value = _words(node)
            if re.fullmatch(r"[\d,\s\u00a0\u202f]+", value):
                return _count(value)

    active = _first(
        tree,
        ".tm-tabs .active .tm-tab-count",
        ".tm-tabs .active .badge",
        ".tm-tabs .active span",
    )
    value = _words(active)
    if re.fullmatch(r"[\d,\s\u00a0\u202f]+", value):
        return _count(value)
    return None


def _account_name(row: Any, slug: str, item_type: str) -> str:
    """Preserve username display prefixes in account result models."""
    value = _text(_first(row, ".table-cell-value.tm-value", ".tm-value")) or slug
    if item_type == "usernames" and value != slug:
        return f"@{value.lstrip('@')}"
    return value


def parse_my_bids(html: str, item_type: str) -> tuple[list[MyBid], int]:
    """Read account bids directly without reparsing isolated table rows."""
    tree = _tree(html)
    prefix = _ASSET_PREFIXES.get(item_type)
    if prefix is None:
        return [], 0
    items: list[MyBid] = []
    for row in tree.css("tr.tm-row-selectable"):
        _, slug = _asset_link(row, (prefix,))
        if slug is None:
            continue
        value = _numeric(_text(row.css_first(".icon-ton")))
        items.append(MyBid(
            item_type=item_type,
            slug=slug,
            name=_account_name(row, slug, item_type),
            bid=float(value) if value is not None else 0.0,
            status=_row_status(row) or "Unknown",
            date=_date(row) or "",
            image_url=_image(row) if item_type == "gifts" else None,
            description=_words(row.css_first(".table-cell-desc")) or None,
        ))
    total = _tab_total(tree, item_type, bids=True)
    return items, total if total is not None else len(items)


def parse_assign_accounts(html: str) -> tuple[list[TelegramAccount], bool]:
    """Read assignment destinations and the optional disable-display action."""
    tree = _tree(html)
    popup = tree.css_first(".js-assign-popup")
    if popup is None:
        return [], False
    accounts: dict[str, TelegramAccount] = {}
    for label in popup.css("label.tm-assign-account-item"):
        input_node = label.css_first("input[value]")
        if input_node is None:
            continue
        identifier = _attr(input_node, "value")
        accounts[identifier] = TelegramAccount(
            id=identifier,
            name=_words(label.css_first(".tm-assign-account-name")) or "Unknown",
            type=_words(label.css_first(".tm-assign-account-desc")) or "Unknown",
            photo_url=_image(label),
        )
    text = _words(popup).replace("’", "'").casefold()
    return list(accounts.values()), "don't display on telegram" in text


def parse_my_assets(html: str, item_type: str) -> tuple[list[MyAsset], int]:
    """Read owned assets, assignment names, and the requested tab's total."""
    tree = _tree(html)
    prefix = _ASSET_PREFIXES.get(item_type)
    if prefix is None:
        return [], 0
    accounts, _ = parse_assign_accounts(html)
    names = {account.id: account.name for account in accounts}
    items: list[MyAsset] = []
    for row in tree.css("tr.tm-row-selectable"):
        _, slug = _asset_link(row, (prefix,))
        if slug is None:
            continue
        assigned = _attr(row, "data-assigned-to") or _attr(
            row.css_first("[data-assigned-to]"), "data-assigned-to"
        )
        assigned_node = row.css_first(".js-assigned-to")
        assigned_name = names.get(assigned) or _words(assigned_node) or None
        if item_type == "gifts" and assigned_node is not None and not assigned_name:
            assigned_name = "Wallet"
        items.append(MyAsset(
            item_type=item_type,
            slug=slug,
            name=_account_name(row, slug, item_type),
            description=_words(row.css_first(".table-cell-desc")) or None,
            image_url=_image(row) if item_type == "gifts" else None,
            assigned_to=assigned or None,
            assigned_name=assigned_name,
        ))
    total = _tab_total(tree, item_type, bids=False)
    return items, total if total is not None else len(items)


def parse_sessions(html: str) -> list[SessionInfo]:
    """Read sessions while separating location labels from activity timestamps."""
    sessions: list[SessionInfo] = []
    for row in _data_rows(html):
        device = _words(_first(
            row,
            ".table-cell-value.tm-value",
            ".table-cell-value",
        ))
        identifier = _attr(row, "data-session-id") or _attr(
            row.css_first("[data-session-id]"), "data-session-id"
        )
        if not device and not identifier:
            continue
        location = ""
        for node in row.css(".table-cell-desc-col"):
            value = _words(node)
            if not value or node.css_first("time") is not None:
                continue
            if re.match(
                r"^(?:now\b|today\b|yesterday\b|last seen\b|\d+\s+\w+\s+ago\b)",
                value,
                re.IGNORECASE,
            ):
                continue
            location = value
            break
        status = _status(row.css_first('[class*="tm-status-"]'))
        current = "current" in status.casefold()
        sessions.append(SessionInfo(
            session_id=identifier,
            device=device,
            location=location,
            date=_date(row) or ("now" if current else None),
            is_current=current,
        ))
    return sessions


def parse_login_code(html: str) -> tuple[str | None, int]:
    """Read a numeric login code and count actual session rows."""
    tree = _tree(html)
    code = None
    for node in tree.css(".table-cell-value"):
        value = _text(node)
        if re.fullmatch(r"\d(?:[\d\s-]*\d)?", value):
            digits = re.sub(r"\D", "", value)
            if 4 <= len(digits) <= 8:
                code = digits
                break
    rows = [
        row for row in tree.css("tr")
        if row.css("td") and not row.css("th")
    ]
    return code, len(rows)


def _parse_count(raw: str) -> int:
    """Compatibility wrapper for count parsing."""
    return _count(raw)


def _merge_collection(previous: GiftCollection, candidate: GiftCollection) -> None:
    """Merge responsive collection duplicates without losing useful metadata."""
    if not previous.name:
        previous.name = candidate.name
    previous.count = max(previous.count, candidate.count)
    if not previous.image_url:
        previous.image_url = candidate.image_url


def _merge_attribute(previous: GiftAttributeValue, candidate: GiftAttributeValue) -> None:
    """Merge duplicate trait values while retaining names and preview images."""
    if not previous.name or previous.name == previous.value:
        previous.name = candidate.name
    previous.count = max(previous.count, candidate.count)
    if not previous.image_url:
        previous.image_url = candidate.image_url


def parse_gift_filters(
    html: str,
) -> tuple[list[GiftCollection], list[GiftAttributeCategory]]:
    """Merge desktop and popup filters instead of overwriting richer entries."""
    tree = _tree(html)
    collections: dict[str, GiftCollection] = {}
    categories: dict[str, GiftAttributeCategory] = {}

    for node in tree.css("a.js-choose-collection-item[data-value]"):
        slug = _attr(node, "data-value")
        if not slug:
            continue
        candidate = GiftCollection(
            slug=slug,
            name=_attr(node, "data-keywords") or _words(_first(
                node,
                ".tm-main-filters-name",
                ".tm-popup-filters-name",
            )),
            count=_count(_words(_first(
                node,
                ".tm-main-filters-count",
                ".tm-popup-filters-desc",
            ))),
            image_url=_image(node),
        )
        if slug in collections:
            _merge_collection(collections[slug], candidate)
        else:
            collections[slug] = candidate

    for box in tree.css(".js-attribute[data-field]"):
        field = _attr(box, "data-field")
        if not field:
            continue
        display_match = re.fullmatch(r"attr\[(.+)]", field)
        fallback = display_match.group(1) if display_match else field

        header_tree = _tree(box.html or "")
        for item in header_tree.css(".js-attribute-item"):
            item.decompose()

        name = _words(_first(
            header_tree,
            ".tm-main-filters-name",
            ".tm-popup-filters-name",
        )) or fallback
        total = _count(_words(_first(
            header_tree,
            ".js-filter-cnt",
            ".tm-main-filters-count",
            ".tm-popup-filters-count",
        )))

        category = categories.get(field)
        if category is None:
            category = GiftAttributeCategory(
                field=field,
                name=name,
                total_count=total,
            )
            categories[field] = category
        else:
            if not category.name or category.name == fallback:
                category.name = name
            category.total_count = max(category.total_count, total)

        values = {item.value: item for item in category.items}
        for node in box.css(".js-attribute-item[data-value]"):
            value = _attr(node, "data-value")
            if not value:
                continue
            candidate = GiftAttributeValue(
                name=_attr(node, "data-keywords") or _words(_first(
                    node,
                    ".tm-main-filters-name",
                    ".tm-popup-filters-name",
                )) or value,
                value=value,
                count=_count(_words(_first(
                    node,
                    ".tm-main-filters-count",
                    ".tm-popup-filters-desc",
                ))),
                image_url=_image(node),
            )
            if value in values:
                _merge_attribute(values[value], candidate)
            else:
                values[value] = candidate
        category.items = list(values.values())

    return list(collections.values()), list(categories.values())