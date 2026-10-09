# OracleGuard

OracleGuard is a standalone GenLayer app for bounded oracle incident control. Its Intelligent Contract commits a market pair, a protected feed URL, two reference URLs on distinct hosts, evidence thresholds, and a maximum hold duration at deployment. No method can edit the policy or manually close the gate.

**Live console:** [healthy market](https://demigodd00.github.io/oracleguard/) · [synthetic stale feed](https://demigodd00.github.io/oracleguard/?scenario=stale) · [missing reference](https://demigodd00.github.io/oracleguard/?scenario=invalid) · [review guide](docs/REVIEW.md)

**Portal listing packet:** [paste-ready application, logo, review steps, and all public links](docs/PORTAL_SUBMISSION.md).

Anyone can open an assessment, which records the exact request and policy URLs on-chain. After that transaction finalizes, anyone can ask validators to fetch the sources and evaluate them. A `TRIGGER_CONFIRMED` result temporarily blocks `request_borrow`. Stale or conflicting references, unavailable sources, malformed data, and non-triggering prices cannot close the gate. The hold expires by timestamp without an administrator transaction.

The minimum requested hold is 900 seconds. Its deadline is anchored to the evaluation transaction timestamp, so consensus and finalization consume part of that window. The console shows the time actually remaining after a finalized read. If network finality takes longer than the requested window, the result is still recorded but the gate is open; a fresh assessment must evaluate current evidence again. StudioNet cannot start the timer from an EVM finalization callback.

**Scope:** `request_borrow` is a demonstration admission counter. It transfers no asset and holds no user funds. OracleGuard is not wired to an external lending market. Its effect is limited to this contract's own borrowing demo. See [architecture](docs/ARCHITECTURE.md) and [source requirements](docs/SOURCE_SPEC.md).

## Repository

- `contracts/OracleGuard.py` — immutable policy, independent source inspection, validator comparison, incident ledger, demo borrow gate.
- `tests/direct/` — state, decision, validator, boundary, and fail-safe tests.
- `web/` — React/Vite StudioNet console. Reads use `LATEST_FINAL` state.
- `scripts/deploy_studionet.py` — deploys a configured policy and records the finalized receipt.
- `scripts/acceptance_studionet.py` — records resumable, finalized assessment checks.
- `deployments/` — StudioNet deployments and consensus evidence.
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

OracleGuard has exact parsers for CoinGecko, Coinbase Exchange, and Kraken ETH/USD responses. Other HTTPS endpoints must serve a JSON object such as:

```json
{"pair":"ETH-USD","price_e8":300000000000,"observed_at":1791288000}
```

`price_e8` is the USD price multiplied by 100,000,000. `observed_at` is a Unix timestamp in seconds. The three URLs must have distinct public hostnames. The stale demo uses a disclosed, commit-pinned synthetic fixture. See [source requirements](docs/SOURCE_SPEC.md) for supported API URLs, limits, and trust assumptions.

## Deploy to StudioNet

Install `genlayer-py` and `eth-account`, then provide three live, independent endpoints:

```powershell
python scripts/deploy_studionet.py --pair ETH-USD `
  --feed-url 'https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd&include_last_updated_at=true' `
  --reference-a-url 'https://api.exchange.coinbase.com/products/ETH-USD/trades?limit=1' `
  --reference-b-url 'https://api.kraken.com/0/public/PostTrade?symbol=ETH/USD&count=1'
```

The script waits for `FINALIZED`, checks execution success, reads back the policy, and writes `deployments/studionet.json`. The deployed address is committed in `web/.env.production`. Use `web/.env.local` to point a local preview at another charter.

## Current verification

`genvm-lint check` passes, nine direct tests pass, and the frontend production build passes. StudioNet finalized a healthy assessment as `NO_TRIGGER`, a synthetic stale-feed assessment as `TRIGGER_CONFIRMED`, and a missing-reference assessment as `INSUFFICIENT_EVIDENCE`. Each received `MAJORITY_AGREE` consensus. Usable source responses were recorded with hashes. See the [review guide](docs/REVIEW.md) and JSON journals in `deployments/`.
