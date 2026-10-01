"""Regression tests for full-page and partial Fragment HTML parsing."""

from FragmentAPI.utils.html import (
    parse_auction_info,
    parse_auction_rows,
    parse_gift_attributes,
    parse_gift_filters,
    parse_gift_items,
    parse_listing_offset,
    parse_login_code,
    parse_my_assets,
    parse_my_bids,
    parse_owner_history,
    parse_profile,
    parse_sessions,
    parse_stars_price_from_html,
    parse_topup_history,
)


def test_wide_status_preferred() -> None:
    """Use the desktop status and retain native currency precision."""
    html = """
    <a class="tm-grid-item" href="/gift/test-1">
      <span class="item-name">Test</span>
      <span class="item-num">1</span>
      <div class="tm-grid-item-status">
        <span class="narrow-only">Auction</span>
        <span class="wide-only">On auction</span>
      </div>
      <div class="tm-grid-item-value icon-ton">1.123456789</div>
    </a>
    <div data-next-offset="25"></div>
    """
    items, cursor = parse_gift_items(html)
    assert items[0]["status"] == "On auction"
    assert items[0]["price"] == "1.123456789"
    assert items[0]["name"] == "Test #1"
    assert cursor == 25


def test_listing_cursor() -> None:
    """Read cursors from pagination-only responses."""
    assert parse_listing_offset(
        '<a data-next-offset="123456">More</a>'
    ) == "123456"


def test_bare_auction_row() -> None:
    """Preserve table rows without their original table wrapper."""
    html = """
    <tr class="tm-row-selectable">
      <td><a href="/username/example?ref=test">
        <div class="tm-value">example</div>
      </a></td>
      <td><div class="tm-value">On auction</div></td>
      <td><div class="icon-ton">1,234.123456789</div></td>
    </tr>
    """
    items = parse_auction_rows(html)
    assert len(items) == 1
    assert items[0]["slug"] == "username/example"
    assert items[0]["status"] == "On auction"
    assert items[0]["price"] == "1234.123456789"


def test_nested_decimal_spans() -> None:
    """Do not add whitespace between integral and fractional price fragments."""
    html = """
    <span class="icon-ton">1,234<span>.000000001</span></span>
    <span>&#036;5.25</span>
    """
    assert parse_stars_price_from_html(html) == ("1234.000000001", "5.25")


def test_horizontal_auction_headers() -> None:
    """Associate horizontal summary headings with their corresponding columns."""
    html = """
    <table>
      <thead><tr>
        <th>Highest Bid</th><th>Bid Step</th><th>Minimum Bid</th>
      </tr></thead>
      <tbody><tr>
        <td><div class="icon-ton">100</div></td>
        <td><div class="icon-ton">5</div></td>
        <td><div class="icon-ton">105</div></td>
      </tr></tbody>
    </table>
    <button data-bid-amount="999">Bid</button>
    <button class="js-buy-now-btn" data-bid-amount="200">Buy</button>
    """
    result = parse_auction_info(html)
    assert result.highest_bid == "100"
    assert result.bid_step == "5"
    assert result.minimum_bid == "105"
    assert result.buy_now_price == "200"


def test_history_does_not_supply_summary_prices() -> None:
    """Do not promote a historical price to the current highest bid."""
    result = parse_auction_info("""
    <section><h3>Bid History</h3><table><tr>
      <td><div class="table-cell-value tm-value icon-before icon-ton">999</div></td>
    </tr></table></section>
    """)
    assert result.highest_bid is None


def test_transferred_owner_history() -> None:
    """Keep transfer labels and the ownership cursor."""
    rows, cursor = parse_owner_history("""
    <section>
      <h3>Ownership History</h3>
      <table><tbody><tr>
        <td><div class="table-cell-value tm-value">Transferred</div></td>
        <td><a href="https://tonviewer.com/UQOWNER?tab=transactions">Wallet</a></td>
      </tr></tbody></table>
      <a class="js-load-more-owners" data-next-offset="42">More</a>
    </section>
    """)
    assert rows[0].price == "Transferred"
    assert rows[0].wallet == "UQOWNER"
    assert cursor == "42"


def test_rarity_not_part_of_attribute_value() -> None:
    """Separate a text-only property value from its rarity badge."""
    result = parse_gift_attributes("""
    <tr>
      <td><div class="table-cell">Model</div></td>
      <td><div class="table-cell-value tm-value">
        Emerald<span class="tm-rarity">2.5%</span>
      </div></td>
    </tr>
    """)
    assert result[0].value == "Emerald"
    assert result[0].rarity == "2.5%"


def test_requested_account_tab_count() -> None:
    """Read the selected category count even without an active CSS class."""
    html = """
    <a href="/my/bids"><span>12</span></a>
    <a href="/my/bids?type=gifts"><span>1,234</span></a>
    <table><tr class="tm-row-selectable">
      <td><a href="/gift/test-1"><div class="tm-value">Test</div></a></td>
      <td><div class="icon-ton">5</div></td>
      <td><div class="tm-status-avail">Winning</div></td>
    </tr></table>
    """
    rows, total = parse_my_bids(html, "gifts")
    assert total == 1234
    assert rows[0].slug == "gift/test-1"
    assert rows[0].status == "Winning"


def test_row_level_assignment_and_zero_count() -> None:
    """Preserve explicit zero counts and row-level assignment attributes."""
    rows, total = parse_my_assets("""
    <a href="/my/usernames"><span>0</span></a>
    <table><tr class="tm-row-selectable" data-assigned-to="123">
      <td><a href="/username/test"><div class="tm-value">test</div></a></td>
    </tr></table>
    """, "usernames")
    assert total == 0
    assert rows[0].name == "@test"
    assert rows[0].assigned_to == "123"


def test_profile_wallet_is_scoped() -> None:
    """Ignore unrelated JSON addresses and preserve the linked wallet label."""
    result = parse_profile("""
    <div class="tm-settings-account">
      <div class="tm-settings-item-head">Alice</div>
      <div class="tm-settings-item-desc">@alice</div>
    </div>
    <div class="tm-settings-item">
      <div class="tm-settings-item-head">Linked Wallet</div>
      <div class="tm-settings-item-desc"><span class="short">UQ...abc</span></div>
      <span class="tm-badge-verified">Verified</span>
    </div>
    <script>
      other({"address":"WRONG"});
      Wallet.init({"address":"0:123","nested":{"a":1}});
    </script>
    """)
    assert result.username == "alice"
    assert result.wallet_address == "0:123"
    assert result.wallet_label == "UQ...abc"
    assert result.wallet_verified is True


def test_session_location_and_current_date() -> None:
    """Skip activity labels when choosing the session location."""
    rows = parse_sessions("""
    <tr data-session-id="s1">
      <td>
        <div class="table-cell-value tm-value">Browser</div>
        <span class="table-cell-desc-col">now</span>
        <span class="table-cell-desc-col">Berlin, Germany</span>
        <span class="tm-status-avail">Current session</span>
      </td>
    </tr>
    """)
    assert rows[0].session_id == "s1"
    assert rows[0].location == "Berlin, Germany"
    assert rows[0].date == "now"


def test_login_code_fragment() -> None:
    """Count data rows in a bare fragment and ignore a non-code label."""
    code, count = parse_login_code("""
    <tr><td><div class="table-cell-value">No code</div></td></tr>
    <tr><td><div class="table-cell-value">12 345</div></td></tr>
    """)
    assert code == "12345"
    assert count == 2


def test_integral_topup_decimal() -> None:
    """An integral displayed decimal remains an integer, not concatenated digits."""
    rows = parse_topup_history("""
    <tr>
      <td><a href="https://t.me/example">@example</a></td>
      <td><span class="icon-ton">10.00</span></td>
    </tr>
    """)
    assert rows[0].amount == 10


def test_duplicate_filters_merge_metadata() -> None:
    """Merge duplicate categories and retain collection previews."""
    collections, categories = parse_gift_filters("""
    <a class="js-choose-collection-item" data-value="test" data-keywords="Test">
      <span class="tm-main-filters-count">10</span>
      <img src="https://example.com/test.png">
    </a>
    <a class="js-choose-collection-item" data-value="test">
      <span class="tm-popup-filters-desc">20 items</span>
    </a>
    <div class="js-attribute" data-field="attr[Model]">
      <span class="tm-main-filters-name">Model</span>
      <span class="tm-main-filters-count js-filter-cnt">2</span>
      <a class="js-attribute-item" data-value="a" data-keywords="Alpha">
        <span class="tm-main-filters-count">10</span>
        <img src="https://example.com/a.png">
      </a>
    </div>
    <div class="js-attribute" data-field="attr[Model]">
      <a class="js-attribute-item" data-value="a">
        <span class="tm-main-filters-count">12</span>
      </a>
      <a class="js-attribute-item" data-value="b" data-keywords="Beta">
        <span class="tm-main-filters-count">3</span>
      </a>
    </div>
    """)
    assert collections[0].count == 20
    assert collections[0].image_url == "https://example.com/test.png"
    assert len(categories) == 1
    assert categories[0].total_count == 2
    assert len(categories[0].items) == 2
    assert categories[0].items[0].name == "Alpha"
    assert categories[0].items[0].count == 12
    assert categories[0].items[0].image_url == "https://example.com/a.png"