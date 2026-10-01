"""TON BOC decoding helpers."""

from __future__ import annotations

import base64

from ton_core import Cell

from FragmentAPI.exceptions import ParseError


def decode_boc(payload: str) -> Cell:
    """Decode a BOC without modifying its binary contents."""
    try:
        encoded = payload.strip()
        encoded += "=" * (-len(encoded) % 4)
        return Cell.one_from_boc(
            base64.b64decode(encoded, altchars=b"-_", validate=True)
        )
    except Exception as exc:
        raise ParseError(
            ParseError.UNPARSEABLE.format(context="BOC", exc=exc)
        ) from exc


def decode_boc_comment(payload: str) -> str | Cell:
    """Decode a text comment for display, retaining structured cells otherwise."""
    if not payload.strip():
        return ""
    cell = decode_boc(payload)
    try:
        parser = cell.begin_parse()
        if parser.load_uint(32) == 0:
            return parser.load_snake_string()
    except (ValueError, UnicodeDecodeError, IndexError):
        return cell
    return cell