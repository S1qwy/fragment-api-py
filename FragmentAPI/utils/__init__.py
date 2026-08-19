"""
Utility exports for Fragment API library.
"""

from FragmentAPI.utils.decoder import decode_boc_comment
from FragmentAPI.utils.evm import fetch_evm_invoice
from FragmentAPI.utils.html import (
    parse_auction_rows,
    parse_gift_items,
)
from FragmentAPI.utils.http import (
    build_headers,
    fetch_fragment_hash,
    post_fragment_api,
)
from FragmentAPI.utils.proxy import build_curl_proxy_args, parse_proxy
from FragmentAPI.utils.retry import with_retry
from FragmentAPI.utils.wallet import (
    build_account_info,
    execute_transaction,
    execute_batch_transaction,
    fetch_wallet_info,
)

__all__ = [
    "build_account_info",
    "build_curl_proxy_args",
    "build_headers",
    "decode_boc_comment",
    "execute_batch_transaction",
    "execute_transaction",
    "fetch_evm_invoice",
    "fetch_fragment_hash",
    "fetch_wallet_info",
    "parse_auction_rows",
    "parse_gift_items",
    "parse_proxy",
    "post_fragment_api",
    "with_retry",
]