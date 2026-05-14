'''
BOC payload decoder for Fragment transaction comments.
'''

from __future__ import annotations

import base64

from ton_core import Cell

from FragmentAPI.exceptions import ParseError


def decode_boc_comment(payload: str) -> str:
    '''
    Decode a base64-encoded BOC payload to a plain-text comment string.

    Fragment returns transaction comments as TON Cells in base64.
    This decodes them to readable text containing the Ref# identifier.

    Args:
        payload: Base64-encoded BOC string.

    Returns:
        Decoded comment string.
    '''
    s = payload.strip().replace("-", "+").replace("_", "/")
    if not s:
        return ""
    s += "=" * (-len(s) % 4)
    try:
        boc = base64.b64decode(s)
        cell = Cell.one_from_boc(boc)
        sl = cell.begin_parse()
        sl.load_uint(32)
        return sl.load_snake_string().strip()
    except Exception as exc:
        raise ParseError(
            ParseError.UNPARSEABLE.format(
                context="payload decode",
                exc=exc,
            )
        ) from exc