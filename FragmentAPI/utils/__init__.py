"""Utility exports without eager client imports."""

from FragmentAPI.utils.decoder import decode_boc, decode_boc_comment
from FragmentAPI.utils.http import (
    FragmentTransport,
    build_headers,
    fetch_fragment_hash,
    fetch_page_ajax,
    post_fragment_api,
)
from FragmentAPI.utils.proxy import build_curl_proxy_args, parse_proxy
from FragmentAPI.utils.retry import with_retry

__all__ = [
    "decode_boc",
    "decode_boc_comment",
    "FragmentTransport",
    "build_headers",
    "fetch_fragment_hash",
    "fetch_page_ajax",
    "post_fragment_api",
    "build_curl_proxy_args",
    "parse_proxy",
    "with_retry",
]