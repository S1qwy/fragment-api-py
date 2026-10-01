"""Hash recovery transport tests."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

from FragmentAPI.utils.http import FragmentTransport


def response(data: dict) -> SimpleNamespace:
    """Create a minimal curl-compatible JSON response."""
    return SimpleNamespace(
        status_code=200,
        url="https://fragment.com/api",
        json=lambda: data,
    )


async def test_bad_hash_refreshes_once() -> None:
    """Refresh and retry only after an explicit rejected request."""
    session = SimpleNamespace(
        post=AsyncMock(side_effect=[
            response({"error": "Bad request"}),
            response({"ok": True}),
        ])
    )
    transport = FragmentTransport(session)
    transport.hash = AsyncMock(side_effect=["old", "new"])
    result = await transport.call("searchAuctions", {"type": "gifts"})
    assert result == {"ok": True}
    assert session.post.await_count == 2
    assert transport.hash.await_args_list[1].kwargs["force"] is True


async def test_payload_method_cannot_replace_selected_method() -> None:
    """Use the explicit method argument rather than an injected data field."""
    session = SimpleNamespace(post=AsyncMock(return_value=response({"ok": True})))
    transport = FragmentTransport(session)
    transport.hash = AsyncMock(return_value="hash")
    await transport.call("searchAuctions", {"method": "tonTerminateSession"})
    assert session.post.await_args.kwargs["data"]["method"] == "searchAuctions"