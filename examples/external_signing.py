"""Prepare an unsigned invoice and report an externally broadcast transaction."""

import json
import os

from FragmentAPI import PreparedTransaction

from _common import (
    make_client,
    require_execution,
    required,
    run,
    setting,
    show_result,
)


async def prepare() -> None:
    """Export the complete message list without signing or broadcasting it."""
    async with make_client(mode="prepare") as client:
        result = await client.purchase_stars(required("FRAGMENT_TARGET"), 100)
        if not isinstance(result, PreparedTransaction):
            raise RuntimeError("Expected a prepared TON transaction.")
        show_result(result)

        payload = {
            "validUntil": result.valid_until,
            "from": result.sender_address,
            "network": "-239",
            "messages": [
                message.model_dump(by_alias=True, exclude_none=True)
                for message in result.messages
            ],
        }
        document = {
            "req_id": result.req_id,
            "confirm_referer": result.confirm_referer,
            "transaction": payload,
        }
        path = setting("FRAGMENT_PREPARED_FILE", "prepared-transaction.json")
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(document, handle, ensure_ascii=False, indent=2)
        print(f"Unsigned transaction exported to {path}")
        print("Review every message and use the requested sender account.")
        print("Keep this Fragment session available for confirmation.")


async def confirm() -> None:
    """Report an already broadcast signed BOC using its original Fragment session."""
    require_execution()
    async with make_client(account=True) as client:
        result = await client.confirm_request(
            req_id=required("FRAGMENT_REQ_ID"),
            boc=required("TON_SIGNED_BOC"),
            referer=setting("FRAGMENT_CONFIRM_REFERER", "stars/buy"),
        )
        print(f"Response keys: {sorted(result)}")
        print("Reporting a BOC is not proof of invoice fulfillment.")


if __name__ == "__main__":
    run({"prepare": prepare, "confirm": confirm}, "prepare")