# OracleGuard review guide

## Open the app

- [Live market console](https://demigodd00.github.io/oracleguard/) — CoinGecko protected feed, Coinbase Exchange and Kraken references.
- [Synthetic stale-feed console](https://demigodd00.github.io/oracleguard/?scenario=stale) — commit-pinned stale feed and live Coinbase/Kraken references. The fixture is a test case, not a real oracle incident.
- [Missing-reference console](https://demigodd00.github.io/oracleguard/?scenario=invalid) — commit-pinned nonexistent reference URL to demonstrate fail-safe behavior.
- [Standalone source repository](https://github.com/Demigodd00/oracleguard).

The contract controls only its own no-funds borrow admission counter. It does not pause an external lending market. No account has an administrator pause or policy update method.

## Finalized StudioNet evidence

| Case | Contract | Evaluation transaction | Final result |
| --- | --- | --- | --- |
| Live healthy market | [`0xa6CED7...154E6`](https://explorer-studio.genlayer.com/address/0xa6CED7CA87Da7e2195928efeD31DEe9a08d154E6) | [`0x100cb4...aaf2a`](https://explorer-studio.genlayer.com/tx/0x100cb42e6bc4f3a7a04dd1ee4d204ccabb1cc7e7d2de4995dd80e50bf45aaf2a) | `NO_TRIGGER / WITHIN_POLICY` |
| Synthetic stale feed | [`0x81e640...aA228`](https://explorer-studio.genlayer.com/address/0x81e640216983AA95e6B917Dc02CeED802AaaA228) | [`0x42d36b...490b3`](https://explorer-studio.genlayer.com/tx/0x42d36bc0078430e81ffba8e040a1d7b8ee54d815606bb25e14fa1d67d7c490b3) | `TRIGGER_CONFIRMED / FEED_STALE` |
| Missing reference | [`0x9Ac6c8...19d34`](https://explorer-studio.genlayer.com/address/0x9Ac6c8fC37c8637b6F9002b9562f568B46819d34) | [`0xe782bd...4c27`](https://explorer-studio.genlayer.com/tx/0xe782bd5d70b46e6256ae8059d95c73bbc08c71228650f76490e97cdb046d4c27) | `INSUFFICIENT_EVIDENCE / SOURCE_INVALID` |

Each case has a `FINALIZED` receipt, `MAJORITY_AGREE` result, successful leader execution, and `LATEST_FINAL` readback. Assessment records include the exact source URLs, available raw HTTP responses, SHA-256 hashes, timestamps, parsed prices, decision, and bounded pause expiry. The missing reference records HTTP 404 with no body. See [`deployments/acceptance_healthy.json`](../deployments/acceptance_healthy.json), [`deployments/acceptance_synthetic_stale.json`](../deployments/acceptance_synthetic_stale.json), and [`deployments/acceptance_invalid_reference.json`](../deployments/acceptance_invalid_reference.json).

The stale fixture is [`evidence/stale-feed.json`](../evidence/stale-feed.json), pinned at Git commit `886c3f3` in the charter. A `TRIGGER_CONFIRMED` pause lasts only for the requested 900 seconds; the gate then opens automatically. The source code SHA-256 recorded with each deployment is `22b5b93a7b639e13b0e5a74f113d18bf60d0d885168e605e98cd8878828cec72`.

## Reproduce checks

```powershell
genvm-lint check contracts/OracleGuard.py
python -m pytest tests/direct -q
cd web
pnpm install --frozen-lockfile
pnpm build
```

The direct suite covers healthy feed, price deviation, bounded expiry, prolonged stale feed, conflicting and unavailable references, forged leader data, public API parsers, and one-shot assessment rules. Live API output changes, so near-threshold assessments can fail to reach consensus instead of issuing authority. See [source requirements](SOURCE_SPEC.md) for the decision rule and trust limits.
