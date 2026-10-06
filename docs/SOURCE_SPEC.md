# Evidence source requirements

Each endpoint must be public HTTPS and respond with status 200, UTF-8 JSON, and at most 4,096 bytes. The contract accepts only these fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `pair` | string | Exact deployed pair, such as `ETH-USD` |
| `price_e8` | integer | Positive quote price × 100,000,000 |
| `observed_at` | integer | Source observation time, Unix seconds |

The three hosts must differ. URLs are committed at deployment and copied into every assessment record. The source operator must not return personalized, geo-dependent, or requester-specific results. Upstream provenance should be documented by each operator; OracleGuard does not validate signatures or fetch a second upstream document.

At assessment time, timestamps more than 30 seconds in the future or more than 24 hours in the past are invalid. Both reference observations must be within the deployed maximum age and must agree within the spread limit. The protected feed can be older than the maximum age; that is a possible trigger only when both references are fresh and consistent.

**Do not deploy with the `example.*` URLs in the README.** They are schema illustrations. Replace them with independently operated sources that serve the exact JSON format, and verify response bodies from each endpoint before deploying the immutable policy.
