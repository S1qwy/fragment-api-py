'''
REST API client for fragment-api.tech — used in no-cookie (no-KYC) mode.

Provides access to a hosted Fragment API that allows executing
Stars / Premium / Ads top-up / Giveaway operations and confirming
transactions without requiring the caller to manage cookies or KYC.
'''

from __future__ import annotations

from typing import Any

import httpx

from FragmentAPI.exceptions import (
    FragmentAPIError,
    UnexpectedError,
)
from FragmentAPI.types.constants import DEFAULT_TIMEOUT

REST_API_BASE_URL: str = "https://fragment-api.tech"


async def rest_api_post(
    endpoint: str,
    payload: dict[str, Any],
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    '''Send a POST request to the fragment-api.tech REST API.'''
    url = f"{REST_API_BASE_URL}{endpoint}"
    try:
        async with httpx.AsyncClient(timeout=timeout) as session:
            response = await session.post(
                url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
    except Exception as exc:
        raise UnexpectedError(
            UnexpectedError.UNEXPECTED.format(exc=exc),
        ) from exc

    try:
        data = response.json()
    except Exception as exc:
        raise FragmentAPIError(
            f"fragment-api.tech returned non-JSON response "
            f"(status={response.status_code}): {exc}"
        ) from exc

    if response.status_code >= 400:
        error_msg = data.get("error") if isinstance(data, dict) else None
        raise FragmentAPIError(
            f"fragment-api.tech error (status={response.status_code}): "
            f"{error_msg or data}"
        )

    if not isinstance(data, dict):
        raise FragmentAPIError(
            f"fragment-api.tech returned unexpected payload: {data}"
        )

    return data


def extract_prepared_data(response: dict[str, Any]) -> dict[str, Any]:
    '''
    Extract the prepared-transaction payload from a REST API response.

    The REST API returns {"mode": "prepared", "data": {...}} when no
    seed was passed. This helper validates the mode and returns the
    inner data dict ready for conversion to PreparedTransaction.
    '''
    mode = response.get("mode")
    data = response.get("data")

    if mode != "prepared":
        raise FragmentAPIError(
            f"Expected 'prepared' mode from fragment-api.tech, got: {mode}"
        )
    if not isinstance(data, dict):
        raise FragmentAPIError(
            "fragment-api.tech returned prepared response without data."
        )
    return data