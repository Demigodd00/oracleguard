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
| Live healthy market | [`0x2AACfD...EC559`](https://explorer-studio.genlayer.com/address/0x2AACfD82195A342e47a4C4589802f897F3BEC559) | [`0x61dc32...e2c03`](https://explorer-studio.genlayer.com/tx/0x61dc32986056d4c41751e88cd16d7c5c34d7c51c1b63e3a3215418fb734e2c03) | `NO_TRIGGER / WITHIN_POLICY` |
| Synthetic stale feed | [`0x663De8...522B1`](https://explorer-studio.genlayer.com/address/0x663De815860ca7719268c4D1381A7D080e8522B1) | [`0x0020b6...8d9fd`](https://explorer-studio.genlayer.com/tx/0x0020b6add67044c8ffdfe1557d0917c16bcc85a21c99c2cc6c41ecc23e78d9fd) | `TRIGGER_CONFIRMED / FEED_STALE` |
| Missing reference | [`0x736F6d...44937`](https://explorer-studio.genlayer.com/address/0x736F6dC07F882B37ACB860D86735A8d8fd544937) | [`0x6fb7aa...2f7e2`](https://explorer-studio.genlayer.com/tx/0x6fb7aaa7391fe877bc152f72ee3fb15d97e2d502e45bb642be220d382f7edd27) | `INSUFFICIENT_EVIDENCE / SOURCE_INVALID` |

Each case has a `FINALIZED` receipt, `MAJORITY_AGREE` result, successful leader execution, and `LATEST_FINAL` readback. Assessment records include the exact source URLs, available raw HTTP responses, SHA-256 hashes, timestamps, parsed prices, decision, and bounded pause expiry. The missing reference records HTTP 404 with no body. See [`deployments/acceptance_healthy.json`](../deployments/acceptance_healthy.json), [`deployments/acceptance_synthetic_stale.json`](../deployments/acceptance_synthetic_stale.json), and [`deployments/acceptance_invalid_reference.json`](../deployments/acceptance_invalid_reference.json).

The stale fixture is [`evidence/stale-feed.json`](../evidence/stale-feed.json), pinned at Git commit `886c3f3` in the charter. The minimum requested hold is 900 seconds. Its deadline starts at the evaluation transaction timestamp, so the effective window after finality is shorter. In this v1.2 stale run, the finalized read showed **858 seconds remaining** after 42 seconds of consensus and finalization. The gate then opens automatically at the recorded deadline. If finality takes 900 seconds or more, the recorded trigger has no active hold; a fresh assessment must use fresh evidence. The source code SHA-256 recorded with each v1.2 deployment is `5b0b902ebabbd30b761ec82c2e104fdca2ee137cb0f138a4cc292acbca82a99a`. Superseded v1.1 records are retained under [`deployments/v1.1/`](../deployments/v1.1/).

## Reproduce checks

```powershell
genvm-lint check contracts/OracleGuard.py
python -m pytest tests/direct -q
cd web
pnpm install --frozen-lockfile
pnpm build
```

The direct suite covers healthy feed, price deviation, bounded expiry, prolonged stale feed, conflicting and unavailable references, forged leader data, public API parsers, and one-shot assessment rules. Live API output changes, so near-threshold assessments can fail to reach consensus instead of issuing authority. See [source requirements](SOURCE_SPEC.md) for the decision rule and trust limits.
