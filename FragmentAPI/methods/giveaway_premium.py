'''
Premium giveaway method — async only.
'''

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import httpx

from FragmentAPI.exceptions import (
    ConfigError,
    FragmentAPIError,
    FragmentBaseError,
    UnexpectedError,
    UserNotFoundError,
    VerificationError,
)
from FragmentAPI.types.constants import (
    DEVICE_FINGERPRINT,
    PREMIUM_GIVEAWAY_PAGE,
    VALID_PAYMENT_METHODS,
)
from FragmentAPI.types.results import GiveawayPremiumResult
from FragmentAPI.utils.http import (
    build_headers,
    fetch_fragment_hash,
    post_FragmentAPI,
)
from FragmentAPI.utils.wallet import (
    build_account_info,
    execute_transaction,
)

if TYPE_CHECKING:
    from FragmentAPI.client import FragmentClient


async def giveaway_premium(
    client: "FragmentClient",
    channel: str,
    winners: int,
    months: int = 3,
    payment_method: str = "ton",
) -> GiveawayPremiumResult:
    '''
    Run a Telegram Premium giveaway for a channel.

    Args:
        client: Authenticated FragmentClient instance.
        channel: Channel username.
        winners: Number of winners (1-24000).
        months: Duration — 3, 6, or 12.
        payment_method: "ton" or "usdt_ton".

    Returns:
        GiveawayPremiumResult with transaction details.
    '''
    if not isinstance(winners, int) or not (1 <= winners <= 24_000):
        raise ConfigError(ConfigError.INVALID_WINNERS_PREMIUM)
    if months not in (3, 6, 12):
        raise ConfigError(ConfigError.INVALID_MONTHS)
    if payment_method not in VALID_PAYMENT_METHODS:
        raise ConfigError(ConfigError.INVALID_PAYMENT_METHOD)

    try:
        headers = build_headers(PREMIUM_GIVEAWAY_PAGE)

        async with httpx.AsyncClient(
            cookies=client.cookies,
            timeout=client.timeout,
        ) as session:
            fragment_hash = await fetch_fragment_hash(
                client.cookies,
                headers,
                PREMIUM_GIVEAWAY_PAGE,
                client.timeout,
            )

            result = await post_FragmentAPI(
                session,
                fragment_hash,
                headers,
                {
                    "method": "searchPremiumGiveawayRecipient",
                    "query": channel,
                    "quantity": winners,
                    "months": months,
                },
            )
            recipient = result.get("found", {}).get("recipient")
            if not recipient:
                raise UserNotFoundError(
                    UserNotFoundError.NOT_FOUND.format(username=channel),
                )

            result = await post_FragmentAPI(
                session,
                fragment_hash,
                headers,
                {
                    "method": "initGiveawayPremiumRequest",
                    "recipient": recipient,
                    "quantity": str(winners),
                    "months": str(months),
                    "payment_method": payment_method,
                },
            )
            if result.get("error"):
                raise FragmentAPIError(result["error"])

            req_id = result.get("req_id")
            if not req_id:
                raise FragmentAPIError(
                    FragmentAPIError.NO_REQUEST_ID.format(
                        context="Premium giveaway",
                    )
                )

            account = await build_account_info(client)
            transaction = await post_FragmentAPI(
                session,
                fragment_hash,
                headers,
                {
                    "method": "getGiveawayPremiumLink",
                    "account": json.dumps(account),
                    "device": DEVICE_FINGERPRINT,
                    "transaction": 1,
                    "id": req_id,
                },
            )
            if transaction.get("need_verify"):
                raise VerificationError(VerificationError.KYC_REQUIRED)

        tx_result = await execute_transaction(client, transaction)

        if tx_result.boc and req_id:
            try:
                await client.confirm_request(
                    req_id,
                    tx_result.boc,
                    referer="premium/giveaway",
                )
            except Exception:
                pass

        return GiveawayPremiumResult(
            transaction_id=tx_result.tx_hash,
            channel=channel,
            winners=winners,
            amount=months,
            payment_method=payment_method,
        )

    except FragmentBaseError:
        raise
    except Exception as exc:
        raise UnexpectedError(
            UnexpectedError.UNEXPECTED.format(exc=exc),
        ) from exc