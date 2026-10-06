# OracleGuard

OracleGuard is a standalone GenLayer app for bounded oracle incident control. Its Intelligent Contract commits a market pair, a protected feed URL, two reference URLs on distinct hosts, evidence thresholds, and a maximum hold duration at deployment. No method can edit the policy or manually close the gate.

Anyone can open an assessment, which records the exact request and policy URLs on-chain. After that transaction finalizes, anyone can ask validators to fetch the sources and evaluate them. A `TRIGGER_CONFIRMED` result temporarily blocks `request_borrow`. Stale or conflicting references, unavailable sources, malformed data, and non-triggering prices cannot close the gate. The hold expires by timestamp without an administrator transaction.

**Scope:** `request_borrow` is a demonstration admission counter. It transfers no asset and holds no user funds. OracleGuard is not wired to an external lending market. Its effect is limited to this contract's own borrowing demo. See [architecture](docs/ARCHITECTURE.md) and [source requirements](docs/SOURCE_SPEC.md).

## Repository

- `contracts/OracleGuard.py` — immutable policy, independent source inspection, validator comparison, incident ledger, demo borrow gate.
- `tests/direct/` — state, decision, validator, boundary, and fail-safe tests.
- `web/` — React/Vite StudioNet console. Reads use `LATEST_FINAL` state.
- `scripts/deploy_studionet.py` — deploys a configured policy and records the finalized receipt.
- `deployments/` — deployment records, when a source configuration is available.
- `docs/` — design notes and preview images.

## Run locally

```powershell
genvm-lint check contracts/OracleGuard.py
pytest tests/direct -q
cd web
pnpm install
pnpm build
pnpm dev
```

The web app opens in **preview mode** when no contract address is configured. All preview policy values are illustrative and transaction controls are disabled.

## Source format

Each of the three HTTPS endpoints must serve a JSON object such as:

```json
{"pair":"ETH-USD","price_e8":300000000000,"observed_at":1791288000}
```

`price_e8` is the USD price multiplied by 100,000,000. `observed_at` is a Unix timestamp in seconds. The three URLs must have distinct public hostnames. See [source requirements](docs/SOURCE_SPEC.md) for limits and trust assumptions.

## Deploy to StudioNet

Install `genlayer-py` and `eth-account`, then provide three live, independent endpoints:

```powershell
python scripts/deploy_studionet.py --pair ETH-USD `
  --feed-url https://feed.example.org/eth-usd.json `
  --reference-a-url https://reference-a.example.net/eth-usd.json `
  --reference-b-url https://reference-b.example.com/eth-usd.json
```

The example domains above are placeholders; using them produces no meaningful assessment. The script waits for `FINALIZED`, checks execution success, reads back the policy, and writes `deployments/studionet.json`. Copy its contract address into `web/.env.local` as `VITE_ORACLEGUARD_ADDRESS=0x...`, then restart Vite.

## Current verification

`genvm-lint check` passes, all direct tests pass, and the frontend production build passes. Direct tests exercise the leader path and explicitly rerun the captured validator on selected cases. Full network consensus and a live source integration remain to be verified with real independently operated endpoints.
