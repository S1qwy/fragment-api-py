# CHANGELOG

<!-- version list -->

## v12.0.0 (2026-08-25)

### Bug Fixes

- **ci**: Fix branches config for semantic-release
  ([`8598988`](https://github.com/S1qwy/fragment-api-py/commit/8598988a0a5590804e5251b89e24f82bfa4d1a0d))

- **ci**: Remove branches config, use default
  ([`6221b34`](https://github.com/S1qwy/fragment-api-py/commit/6221b34e3b7617431d3fc0660b2071af6db1ae56))

- **marketplace**: Fix missing comma in imports causing syntax error, remove usdt_gram references
  ([`8493775`](https://github.com/S1qwy/fragment-api-py/commit/8493775f34432aaec9fd139f1b6a2d88b2c8017f))

- **results**: Fix missing comma in imports, add NoKycBatchResult export
  ([`69599c2`](https://github.com/S1qwy/fragment-api-py/commit/69599c2899629fa14b994cbac5145c456f961a77))

### Chores

- **pyproject**: Drop Python 3.9 support, require Python 3.10+
  ([`b167598`](https://github.com/S1qwy/fragment-api-py/commit/b167598ad0168fef1f2f311df37d1110dc571953))

### Continuous Integration

- **release**: Add semantic-release workflow with PyPI token publishing
  ([`c0637ec`](https://github.com/S1qwy/fragment-api-py/commit/c0637ec95e309ebcd1c7ed70726a747a0d924d49))

### Documentation

- **doc**: Update documentation to v12.0.0 with No-KYC mode
  ([`240eda9`](https://github.com/S1qwy/fragment-api-py/commit/240eda93a77fa26c40ceb9406bf435624d6e1a98))

- **readme**: Update to v12.0.0 with No-KYC mode and unified usdt_ton payment method
  ([`432b109`](https://github.com/S1qwy/fragment-api-py/commit/432b109afaf1d6842adf4e991672f4c96b9106ae))

### Features

- **api**: Major version 12.0.0 with No-KYC mode
  ([`1c4112c`](https://github.com/S1qwy/fragment-api-py/commit/1c4112c2b14071f9ffe43ed910ea90cd23f79cec))

- **client**: Make cookies optional, add No-KYC mode via MarketApp API, add marketapp_token param,
  remove usdt_gram support, update operating modes
  ([`619281b`](https://github.com/S1qwy/fragment-api-py/commit/619281b3ada0731b74dc924f9f18a2573c0f1767))

- **constants**: Add No-KYC mode constants, remove usdt_gram, rename USDT master address, add
  MarketApp defaults
  ([`1ff672a`](https://github.com/S1qwy/fragment-api-py/commit/1ff672ac65179c1a912ddee250a7cb13cac4e9c6))

- **deps**: Add marketapp-api dependency and bump version to 12.0.0
  ([`2c3cf7c`](https://github.com/S1qwy/fragment-api-py/commit/2c3cf7ccc104ec5f5911ef8c348a3bc88dbea477))

- **init**: Export NoKycBatchResult and MarketAppAPIError, update version to 12.0.0
  ([`4b8035c`](https://github.com/S1qwy/fragment-api-py/commit/4b8035cf7bf6f0e22cff10214ecd8db44d191c5a))

- **models**: Add NoKycBatchResult for No-KYC batch operations, remove usdt_gram references
  ([`ab395e9`](https://github.com/S1qwy/fragment-api-py/commit/ab395e9aca348752cf5d5b7d594729b36d3626ff))

- **nokyc**: Add MarketApp API integration for No-KYC mode purchases, giveaways, price lookups and
  recipient search
  ([`ee224c3`](https://github.com/S1qwy/fragment-api-py/commit/ee224c3c0b1a2fb3335c94d3632c0ad3ded62004))

- **types**: Export NoKycBatchResult and MarketAppAPIError
  ([`4fec4a3`](https://github.com/S1qwy/fragment-api-py/commit/4fec4a3f23b9df063f2938a0a9e489471f80e5c8))

- **utils**: Export nokyc module utilities
  ([`e4d8b6b`](https://github.com/S1qwy/fragment-api-py/commit/e4d8b6bf7ca1b002b25cea19720c341c46608d4a))

### Refactoring

- **exceptions**: Remove usdt_gram references, add No-KYC mode error messages and MarketAppAPIError
  ([`5cf34fe`](https://github.com/S1qwy/fragment-api-py/commit/5cf34feec677ee8f445cc3d5fcc3f4acbfb20a6a))

- **purchase**: Remove usdt_gram payment method from normalize function
  ([`427c541`](https://github.com/S1qwy/fragment-api-py/commit/427c541cbce5192182fa46e869d3eaacf37e4acd))

- **wallet**: Renamed the variable USDT_GRAM_MASTER_ADDRESS to USDT_TON_MASTER_ADDRESS
  ([`301ac54`](https://github.com/S1qwy/fragment-api-py/commit/301ac547657a4910aa06398d628942a5b7d5c8d4))

### Breaking Changes

- **api**: Usdt_gram payment method removed, use usdt_ton BREAKING CHANGE: Python 3.9 no longer
  supported, requires 3.10+ BREAKING CHANGE: FragmentClient cookies parameter is now optional


## v11.1.0 (2026-08-25)

### Bug Fixes

- **ci**: Fix branches config for semantic-release
  ([`8598988`](https://github.com/S1qwy/fragment-api-py/commit/8598988a0a5590804e5251b89e24f82bfa4d1a0d))

- **ci**: Remove branches config, use default
  ([`6221b34`](https://github.com/S1qwy/fragment-api-py/commit/6221b34e3b7617431d3fc0660b2071af6db1ae56))

- **marketplace**: Fix missing comma in imports causing syntax error, remove usdt_gram references
  ([`8493775`](https://github.com/S1qwy/fragment-api-py/commit/8493775f34432aaec9fd139f1b6a2d88b2c8017f))

- **results**: Fix missing comma in imports, add NoKycBatchResult export
  ([`69599c2`](https://github.com/S1qwy/fragment-api-py/commit/69599c2899629fa14b994cbac5145c456f961a77))

### Chores

- **pyproject**: Drop Python 3.9 support, require Python 3.10+
  ([`b167598`](https://github.com/S1qwy/fragment-api-py/commit/b167598ad0168fef1f2f311df37d1110dc571953))

### Continuous Integration

- **release**: Add semantic-release workflow with PyPI token publishing
  ([`c0637ec`](https://github.com/S1qwy/fragment-api-py/commit/c0637ec95e309ebcd1c7ed70726a747a0d924d49))

### Documentation

- **doc**: Update documentation to v12.0.0 with No-KYC mode
  ([`240eda9`](https://github.com/S1qwy/fragment-api-py/commit/240eda93a77fa26c40ceb9406bf435624d6e1a98))

- **readme**: Update to v12.0.0 with No-KYC mode and unified usdt_ton payment method
  ([`432b109`](https://github.com/S1qwy/fragment-api-py/commit/432b109afaf1d6842adf4e991672f4c96b9106ae))

### Features

- **client**: Make cookies optional, add No-KYC mode via MarketApp API, add marketapp_token param,
  remove usdt_gram support, update operating modes
  ([`619281b`](https://github.com/S1qwy/fragment-api-py/commit/619281b3ada0731b74dc924f9f18a2573c0f1767))

- **constants**: Add No-KYC mode constants, remove usdt_gram, rename USDT master address, add
  MarketApp defaults
  ([`1ff672a`](https://github.com/S1qwy/fragment-api-py/commit/1ff672ac65179c1a912ddee250a7cb13cac4e9c6))

- **deps**: Add marketapp-api dependency and bump version to 12.0.0
  ([`2c3cf7c`](https://github.com/S1qwy/fragment-api-py/commit/2c3cf7ccc104ec5f5911ef8c348a3bc88dbea477))

- **init**: Export NoKycBatchResult and MarketAppAPIError, update version to 12.0.0
  ([`4b8035c`](https://github.com/S1qwy/fragment-api-py/commit/4b8035cf7bf6f0e22cff10214ecd8db44d191c5a))

- **models**: Add NoKycBatchResult for No-KYC batch operations, remove usdt_gram references
  ([`ab395e9`](https://github.com/S1qwy/fragment-api-py/commit/ab395e9aca348752cf5d5b7d594729b36d3626ff))

- **nokyc**: Add MarketApp API integration for No-KYC mode purchases, giveaways, price lookups and
  recipient search
  ([`ee224c3`](https://github.com/S1qwy/fragment-api-py/commit/ee224c3c0b1a2fb3335c94d3632c0ad3ded62004))

- **types**: Export NoKycBatchResult and MarketAppAPIError
  ([`4fec4a3`](https://github.com/S1qwy/fragment-api-py/commit/4fec4a3f23b9df063f2938a0a9e489471f80e5c8))

- **utils**: Export nokyc module utilities
  ([`e4d8b6b`](https://github.com/S1qwy/fragment-api-py/commit/e4d8b6bf7ca1b002b25cea19720c341c46608d4a))

### Refactoring

- **exceptions**: Remove usdt_gram references, add No-KYC mode error messages and MarketAppAPIError
  ([`5cf34fe`](https://github.com/S1qwy/fragment-api-py/commit/5cf34feec677ee8f445cc3d5fcc3f4acbfb20a6a))

- **purchase**: Remove usdt_gram payment method from normalize function
  ([`427c541`](https://github.com/S1qwy/fragment-api-py/commit/427c541cbce5192182fa46e869d3eaacf37e4acd))

- **wallet**: Renamed the variable USDT_GRAM_MASTER_ADDRESS to USDT_TON_MASTER_ADDRESS
  ([`301ac54`](https://github.com/S1qwy/fragment-api-py/commit/301ac547657a4910aa06398d628942a5b7d5c8d4))


## v11.0.0 (2026-08-20)

### Bug Fixes

- Improve marketplace history parsing and add offer history support
  ([`1526eed`](https://github.com/S1qwy/fragment-api-py/commit/1526eed8c37eff5ea98a46107040df087f2e8ab1))

### Features

- Add exponential backoff retry decorator for HTTP requests
  ([`6b8bdf4`](https://github.com/S1qwy/fragment-api-py/commit/6b8bdf4a9081f9852422e821c37825543bb31cc0))

- Add proxy, retry, session storage and new method constants
  ([`2411e05`](https://github.com/S1qwy/fragment-api-py/commit/2411e058b2f3b249cbe5d9b69d848ad68a0f4541))

- Add session storage interface with file and redis implementations
  ([`80bb67b`](https://github.com/S1qwy/fragment-api-py/commit/80bb67ba2cf6abac749d5829d85863f52f646dfd))

- Add session storage interface with file and redis implementations
  ([`cc662e5`](https://github.com/S1qwy/fragment-api-py/commit/cc662e56ef2c013d6476bf07437cb0619517a540))

### Refactoring

- Add retry decorator, proxy support and improved hash caching to HTTP utilities
  ([`628aa6c`](https://github.com/S1qwy/fragment-api-py/commit/628aa6c21586d32266b7f96c458becb06f1e4b2d))

- Bridge results.py to pydantic models for backward compatibility
  ([`7407c2d`](https://github.com/S1qwy/fragment-api-py/commit/7407c2dc9564b269100ab1dc0c6d4b554e30c900))

- Migrate HTML parsing from regex to selectolax for robustness
  ([`e55b542`](https://github.com/S1qwy/fragment-api-py/commit/e55b542721a09097b18de5bda0e505f7063cfa8a))

- Update type exports for new models and exceptions
  ([`b9ebc9f`](https://github.com/S1qwy/fragment-api-py/commit/b9ebc9f880e20e0aa55879dc3df196a0cfab9b8f))

- Use constants for item type validation in place_bid
  ([`0e4d0db`](https://github.com/S1qwy/fragment-api-py/commit/0e4d0db7f32cd926f62a25dc3c001864e788baa1))

- Use constants for item type validation in place_bid
  ([`bf1ef60`](https://github.com/S1qwy/fragment-api-py/commit/bf1ef60b6a3166a7574a50501c08518653fc2dea))


## v10.0.0 (2026-08-17)

### Bug Fixes

- Name 'item_type' is not defined
  ([`1935e70`](https://github.com/S1qwy/fragment-api-py/commit/1935e70e6e95cec84bf15ee866373885b6eb5946))

### Features

- Add unified purchase() method with GRAM naming and EVM support
  ([`5a39e2b`](https://github.com/S1qwy/fragment-api-py/commit/5a39e2b0f3c92122d82f224cbad81ac1434daadc))

- Add UNSUPPORTED_METHOD error for EVM payment methods
  ([`a91360a`](https://github.com/S1qwy/fragment-api-py/commit/a91360a2c683c66fd182ed3de7c978f2970dc1a5))

- Combine batch and single purchase into unified purchase() method
  ([`09f12db`](https://github.com/S1qwy/fragment-api-py/commit/09f12dba1ad2f96225df881cfd97d72e8a0d8d00))

### Refactoring

- Add structured logging to anonymous number methods
  ([`bb9ccc7`](https://github.com/S1qwy/fragment-api-py/commit/bb9ccc755a528d62016b05ebb7f6347f4d6ba903))

- Add structured logging to authentication flow
  ([`31038f3`](https://github.com/S1qwy/fragment-api-py/commit/31038f3c93f8f1df60a243229c3d544689627fd9))

- Add structured logging to EVM invoice parser
  ([`9aca1df`](https://github.com/S1qwy/fragment-api-py/commit/9aca1dfc9fccc6e763ce5ccdaf7bedc3a0351317))

- Add structured logging to HTTP utilities
  ([`07ec61c`](https://github.com/S1qwy/fragment-api-py/commit/07ec61c7834e311ab39874f714aac5f2ef1d279f))

- Clean up utils package exports
  ([`5b8d453`](https://github.com/S1qwy/fragment-api-py/commit/5b8d4536a40f3f78294e9d29d8c802f53b33454a))

- Improve BOC decoder with structured message support
  ([`9af9773`](https://github.com/S1qwy/fragment-api-py/commit/9af977341374f273c65ecc65e60545e7012ede8e))

- Major client overhaul with optional seed/api_key and GRAM naming
  ([`7bbf335`](https://github.com/S1qwy/fragment-api-py/commit/7bbf335e1a50c7e1c5faeebee6f76c0863458203))

- Major client overhaul with optional seed/api_key and GRAM naming
  ([`c3bbc7f`](https://github.com/S1qwy/fragment-api-py/commit/c3bbc7f478d2ec53967491521e62de0e273fc40b))

- Major wallet utilities overhaul with Toncenter and HighloadV3 support
  ([`735d6c6`](https://github.com/S1qwy/fragment-api-py/commit/735d6c6a2051d515118c70f75c7a617fc86e5d3d))

- Merge giveaway methods into single module
  ([`0511696`](https://github.com/S1qwy/fragment-api-py/commit/0511696dca1bcb46cca18f9f0cda599d39ee9446))

- Rename TON fields to GRAM with backward-compatible aliases
  ([`b7744a0`](https://github.com/S1qwy/fragment-api-py/commit/b7744a05f9a4d321e68f593da3206b6f141169d2))

- Rename TON references to GRAM in HTML parser outputs
  ([`11288db`](https://github.com/S1qwy/fragment-api-py/commit/11288db9fb74f00853bd4ae5a8b0ae2be9f83653))

- Reorganize method exports with unified purchase API
  ([`92835bf`](https://github.com/S1qwy/fragment-api-py/commit/92835bfbf060b69a34e7739120800c8243d2db14))

- Reorganize package exports and bump version to 10.0.0
  ([`0f57098`](https://github.com/S1qwy/fragment-api-py/commit/0f570987bf697711a1518cc56faad1d5ed7a4988))

- Update constants for GRAM naming and add Toncenter support
  ([`7bbf316`](https://github.com/S1qwy/fragment-api-py/commit/7bbf31624361372fe5691c37cbce4e80c72b4a81))

- Update methods __init__.py to import all purchase utilities from purchase module
  ([`a312760`](https://github.com/S1qwy/fragment-api-py/commit/a3127601f2043287c28d387c71f08332cc5f6fe1))

- Update place_bid to use GRAM naming and require wallet
  ([`228b6df`](https://github.com/S1qwy/fragment-api-py/commit/228b6df7e3f396d49998a9824a92af48df901f0a))

- Update search methods to use post_fragment_api
  ([`0ae4931`](https://github.com/S1qwy/fragment-api-py/commit/0ae49311818147311b8f23b61b93611f0fac36f1))

- Update types package exports
  ([`c0180a4`](https://github.com/S1qwy/fragment-api-py/commit/c0180a4de9289b188b9d5e9be34348d288dd3712))


## v9.0.0 (2026-08-10)


## v8.1.0 (2026-06-06)


## v8.0.0 (2026-06-04)


## v7.0.0 (2026-05-29)

### Features

- Add EVM payment methods usdt_eth usdt_pol usdc_eth usdc_base usdc_pol with EvmInvoice and
  EvmPaymentResult types; feat: add anonymous telemetry system with StatsCollector and live
  dashboard at fragment.s1qwy.ru/statistic; feat: add stats_enabled parameter to FragmentClient and
  FRAGMENT_DISABLE_STATS env var; fix: remove EVM support from topup_ton not supported by Fragment
  API; fix: clean up payment_method parameter from methods without EVM support; docs: update
  openapi.json with authentication client setup and EVM flow documentation; chore: bump version to
  v7.0.0
  ([`677e2ab`](https://github.com/S1qwy/fragment-api-py/commit/677e2ab8d34370fec7ea76b3b2ba649d4459aeb7))


## v6.1.0 (2026-05-15)


## v6.0.0 (2026-05-14)

### Bug Fixes

- Files have been fixed due to version differences
  ([`1e5323a`](https://github.com/S1qwy/fragment-api-py/commit/1e5323a8e0074964c6312739bda3421ff6382a15))

### Features

- Add comprehensive account asset management. Implemented get_my_assets, get_my_bids,
  get_assign_accounts, and assign_to_telegram.
  ([`7aeb487`](https://github.com/S1qwy/fragment-api-py/commit/7aeb4875c7d7ed5dc0b7b5acbe1646f6dc45a418))

- Add marketplace selling capabilities. Introduced start_auction and sell_asset methods for
  usernames and gifts.
  ([`7aeb487`](https://github.com/S1qwy/fragment-api-py/commit/7aeb4875c7d7ed5dc0b7b5acbe1646f6dc45a418))

- Add NFT and Stars withdrawal workflows. Included state fetching, initialization, and confirmation
  endpoints (init_nft_withdrawal, confirm_stars_withdrawal, etc.).
  ([`7aeb487`](https://github.com/S1qwy/fragment-api-py/commit/7aeb4875c7d7ed5dc0b7b5acbe1646f6dc45a418))

- Add NFT transfer functionality. Implemented search_nft_transfer_recipient, init_nft_transfer, and
  transfer_nft.
  ([`7aeb487`](https://github.com/S1qwy/fragment-api-py/commit/7aeb4875c7d7ed5dc0b7b5acbe1646f6dc45a418))

- Add Telegram Ads top-up history fetching (get_topup_history).
  ([`7aeb487`](https://github.com/S1qwy/fragment-api-py/commit/7aeb4875c7d7ed5dc0b7b5acbe1646f6dc45a418))

- Implement robust transaction confirmation logic. Added seqno and balance polling to ensure
  transactions are successfully confirmed on the TON blockchain.
  ([`7aeb487`](https://github.com/S1qwy/fragment-api-py/commit/7aeb4875c7d7ed5dc0b7b5acbe1646f6dc45a418))

- Introduce confirmReq method. Automatically sends the signed transaction BOC to Fragment,
  accelerating Premium/Stars delivery time from ~30s down to ~5s.
  ([`7aeb487`](https://github.com/S1qwy/fragment-api-py/commit/7aeb4875c7d7ed5dc0b7b5acbe1646f6dc45a418))

- Release v6.0.0 - transition to async-only, advanced tx confirmation, and extended marketplace API
  ([`7aeb487`](https://github.com/S1qwy/fragment-api-py/commit/7aeb4875c7d7ed5dc0b7b5acbe1646f6dc45a418))

### Refactoring

- Completely migrate to an async-only architecture. Removed all synchronous code (FragmentClient
  sync methods, httpx.Client usage, etc.). The old AsyncFragmentClient is now the default and only
  FragmentClient.
  ([`7aeb487`](https://github.com/S1qwy/fragment-api-py/commit/7aeb4875c7d7ed5dc0b7b5acbe1646f6dc45a418))

- Expand HTML parsers in utils/html.py to scrape data from new pages (My Assets, My Bids, Assign
  popups, Ads History).
  ([`7aeb487`](https://github.com/S1qwy/fragment-api-py/commit/7aeb4875c7d7ed5dc0b7b5acbe1646f6dc45a418))


## v5.0.0 (2026-05-11)

- Initial Release
