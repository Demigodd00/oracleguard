# Evidence source requirements

The charter commits three public HTTPS URLs on distinct hosts. Each response must be status 200, UTF-8 JSON, and at most 4,096 bytes. Validators independently fetch these exact URLs during an assessment. The contract stores each returned body, HTTP status, SHA-256 digest, parsed price, and observation time in the finalized assessment record.

## Supported source formats

For `ETH-USD`, the contract recognizes these exact public API URLs:

| Role | URL | Parsed fields |
| --- | --- | --- |
| Feed | `https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd&include_last_updated_at=true` | `ethereum.usd`, `ethereum.last_updated_at` |
| Reference A | `https://api.exchange.coinbase.com/products/ETH-USD/trades?limit=1` | First trade's `price`, `time` |
| Reference B | `https://api.kraken.com/0/public/PostTrade?symbol=ETH/USD&count=1` | First trade's `price`, `trade_ts`, `symbol` |

Other URLs must return the canonical format:

```json
{"pair":"ETH-USD","price_e8":300000000000,"observed_at":1791288000}
```

`price_e8` is the quote price multiplied by 100,000,000. `observed_at` is a Unix timestamp in seconds. Unknown fields are ignored. The three operators must be genuinely independent; separate hostnames alone do not prove this.

## Decision rule

The transaction submission timestamp anchors reference freshness. Both reference observations must be no more than the charter's maximum age behind it and no more than 120 seconds apart. Source timestamps may be up to one hour after submission because finalization and validator fetches are asynchronous. The references must agree within the committed spread limit.

After those checks, a feed observation more than the maximum age behind the older reference triggers `FEED_STALE`. A feed price at or beyond the committed deviation from the reference midpoint triggers `PRICE_DEVIATION`. Missing, malformed, unavailable, stale, or conflicting **reference** data creates `INSUFFICIENT_EVIDENCE` and no hold. If the protected feed cannot be parsed, it also creates no authority. A feed timestamp more than 120 seconds newer than the older reference is insufficient evidence.

The public stale-feed fixture at [`evidence/stale-feed.json`](../evidence/stale-feed.json) is synthetic and commit-pinned in the StudioNet trigger charter. It demonstrates the stale-feed rule; it does not claim a real market oracle failure. The live healthy charter uses CoinGecko, Coinbase, and Kraken endpoints. HTTP availability, rate limits, geo variation, and source updates can affect consensus. The recorded bodies let reviewers inspect what validators accepted for each decision.
