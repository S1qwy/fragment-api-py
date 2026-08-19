"""
BOC payload decoder for Fragment transaction comments.

Decodes base64-encoded TON Cell payloads into readable text or raw Cell objects.
"""

from __future__ import annotations

import base64
import logging

from ton_core import Cell

from FragmentAPI.exceptions import ParseError

logger = logging.getLogger("FragmentAPI")


def decode_boc_comment(payload: str) -> str | Cell:
    """Decode a base64-encoded BOC payload to a plain-text comment or raw Cell.

    Fragment returns transaction comments as TON Cells in base64.
    Text comments (op=0) are decoded to readable strings containing the Ref# identifier.
    Structured messages (op!=0) such as jetton transfers are returned as Cell objects.

    Args:
        payload: Base64-encoded BOC string.

    Returns:
        Decoded comment string for text payloads, or Cell for structured messages.

    Raises:
        ParseError: If the payload cannot be decoded at all.
    """
    s = payload.strip().replace("-", "+").replace("_", "/")
    if not s:
        return ""
    s += "=" * (-len(s) % 4)
    try:
        boc = base64.b64decode(s)
        cell = Cell.one_from_boc(boc)
        sl = cell.begin_parse()
        op = sl.load_uint(32)
        if op != 0:
            logger.debug("Non-zero op code %d in BOC payload, returning raw Cell", op)
            return cell
        try:
            return sl.load_snake_string().strip()
        except UnicodeDecodeError:
            logger.debug("Failed to decode BOC payload as UTF-8 text, returning raw Cell")
            return cell
    except Exception as exc:
        logger.error("Failed to decode BOC payload: %s", exc)
        raise ParseError(
            ParseError.UNPARSEABLE.format(context="payload decode", exc=exc)
        ) from exc