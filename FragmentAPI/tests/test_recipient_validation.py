"""Recipient helpers retain validation after the purchase implementation moves."""

from unittest.mock import AsyncMock

import pytest

from FragmentAPI import FragmentClient
from FragmentAPI.exceptions import ConfigurationError
from FragmentAPI.types.constants import STARS_GIVEAWAY_PAGE


async def test_premium_and_giveaway_recipient_validation_before_network():
    client = FragmentClient()
    client._recipient = AsyncMock(return_value=None)
    await client.get_premium_recipient("target", 3)
    await client.get_giveaway_premium_recipient("target", 3)
    with pytest.raises(ConfigurationError):
        await client.get_premium_recipient("target", True)
    with pytest.raises(ConfigurationError):
        await client.get_giveaway_stars_recipient("target", True)
    assert client._recipient.await_count == 2


async def test_stars_giveaway_search_uses_current_query_only_payload():
    """Keep local package validation without sending unrelated search fields."""
    async with FragmentClient() as client:
        client._recipient = AsyncMock(return_value=None)
        await client.get_giveaway_stars_recipient("channel", winners=1, amount=500)
        client._recipient.assert_awaited_once_with(
            "searchStarsGiveawayRecipient", "channel", STARS_GIVEAWAY_PAGE,
        )


@pytest.mark.parametrize("value", [True, "30", float("nan"), float("inf"), -1, 0])
def test_nonfinite_or_invalid_timeouts_rejected(value):
    with pytest.raises(ConfigurationError):
        FragmentClient(timeout=value)
    with pytest.raises(ConfigurationError):
        FragmentClient(confirmation_timeout=value)
