# OracleGuard — GenLayer Portal submission packet

Prepared for the **Projects** contribution and subsequent **Project Explorer** listing. OracleGuard is a complete frontend plus Intelligent Contract, so select **Projects**, rather than the standalone **Intelligent Contract** contribution type. The Portal requires a connected Builder account for the actual form; its labels or limits may change.

## Submission order

1. Open [GenLayer Portal Builders](https://portal.genlayer.foundation/builders), connect your wallet, and complete the Builder Welcome journey. Link your GitHub account and complete the Portal's repo-star task if it is still required to unlock the Builder role.
2. Open [Builder contributions](https://portal.genlayer.foundation/builders/contributions), choose **Projects**, and start a project submission. Use the public, dedicated [OracleGuard repository](https://github.com/Demigodd00/oracleguard). The project name creates the Explorer URL slug and should be entered as **OracleGuard** before review.
3. Complete the Project Explorer application with the copy below. Upload the [PNG logo](../web/public/oracleguard-logo.png). The Portal currently accepts PNG, JPEG, or WebP logos up to 2 MB; this PNG is 1024 × 1024 and about 62 KB. Add the website and at least one evidence URL. Contract explorer links and a demo video are optional fields; the contract links below are available, while no video is published.
4. Submit the Projects contribution for steward review. An accepted contribution earns points but does **not** automatically publish an Explorer page. After acceptance, open **My Projects**, start a project from that accepted Projects contribution, and submit its Explorer page for the separate listing review. If the steward requests changes, revise and resubmit the same application.

## Paste-ready application

**Project name:** OracleGuard

**One-liner:** Validator-confirmed oracle incidents can temporarily block a no-funds borrowing demo.

**Primary tag:** DeFi. Choose secondary tags about oracles and risk controls if offered; do not add unrelated tags.

**Project description:**

> OracleGuard is a GenLayer Intelligent Contract and live console for bounded oracle incident control. Its immutable charter fixes a protected ETH-USD feed, two independent reference URLs, thresholds, and a maximum hold. Anyone can commit an assessment; GenLayer validators independently fetch the approved sources and verify the decision. A finalized `TRIGGER_CONFIRMED` can temporarily close the contract's no-funds borrow-admission demo. Missing, stale, invalid, or conflicting reference evidence grants no pause authority. The demo holds no user funds and is not connected to an external lending market.

**Website (required):** https://demigodd00.github.io/oracleguard/

**GitHub repository / Project Repository:** https://github.com/Demigodd00/oracleguard

**Documentation / review evidence:** https://github.com/Demigodd00/oracleguard/blob/main/docs/REVIEW.md

**Demo video:** Leave blank unless you publish a direct YouTube video or X post link. The Portal labels this field optional.

**How-to steps:**

1. **Healthy source:** Open the [live market console](https://demigodd00.github.io/oracleguard/). The finalized record is `NO_TRIGGER / WITHIN_POLICY`; the borrow gate remains operational.
2. **Confirmed trigger:** Select **STALE** or open the [synthetic stale-feed console](https://demigodd00.github.io/oracleguard/?scenario=stale). Inspect assessment #1 and its recorded source responses. It finalized as `TRIGGER_CONFIRMED / FEED_STALE`. The fixture is disclosed and synthetic. The pause is time bounded and may have expired by the time you review it; the historical record remains.
3. **Fail-safe:** Select **MISSING** or open the [missing-reference console](https://demigodd00.github.io/oracleguard/?scenario=invalid). Assessment #1 finalized as `INSUFFICIENT_EVIDENCE / SOURCE_INVALID`; the missing reference returned HTTP 404 and the gate remains open.
4. **Verify consensus:** Open the [review guide](https://github.com/Demigodd00/oracleguard/blob/main/docs/REVIEW.md) and its three linked evaluation transactions. Each receipt is `FINALIZED` with `MAJORITY_AGREE` and successful execution. The committed deployment and acceptance JSON files provide the exact URLs, raw responses, hashes, and `LATEST_FINAL` readbacks.

**Expected verification outcome:**

> The healthy case leaves the gate open. The disclosed synthetic stale-feed case records a finalized trigger and a bounded hold; its first finalized read showed 858 seconds remaining from a 900-second request. The missing-reference case records insufficient evidence and no hold. All three assessments preserve inspectable source data and finalized consensus receipts. The gate opens automatically when the deadline passes.

**Contribution notes / description (under 1,000 characters):**

> OracleGuard solves a specific trust problem: one caller cannot declare an oracle incident and pause a protected action. The charter fixes three public HTTPS sources and decision thresholds at deployment. GenLayer validators independently fetch and compare those sources before a `TRIGGER_CONFIRMED` result can close the no-funds borrowing demo. The frontend calls the deployed StudioNet contracts and reads finalized state. Review the live console, source code, tests, deployment records, and three finalized healthy, trigger, and missing-evidence scenarios at the review-guide URL. This is a demo admission gate, not an external lending integration; it holds no user funds. The 900–1,800 second hold deadline starts at evaluation submission, so finalization reduces the remaining window.

**Evidence URL:** https://github.com/Demigodd00/oracleguard/blob/main/docs/REVIEW.md

## Logo and public project links

| Purpose | URL |
| --- | --- |
| Square PNG logo for Portal upload | https://demigodd00.github.io/oracleguard/oracleguard-logo.png |
| SVG logo / favicon | https://demigodd00.github.io/oracleguard/oracleguard-logo.svg |
| Main website | https://demigodd00.github.io/oracleguard/ |
| Synthetic stale-feed scenario | https://demigodd00.github.io/oracleguard/?scenario=stale |
| Missing-reference scenario | https://demigodd00.github.io/oracleguard/?scenario=invalid |
| Dedicated source repository | https://github.com/Demigodd00/oracleguard |
| Review guide | https://github.com/Demigodd00/oracleguard/blob/main/docs/REVIEW.md |
| Intelligent Contract source | https://github.com/Demigodd00/oracleguard/blob/main/contracts/OracleGuard.py |
| Architecture and scope | https://github.com/Demigodd00/oracleguard/blob/main/docs/ARCHITECTURE.md |
| Evidence source specification | https://github.com/Demigodd00/oracleguard/blob/main/docs/SOURCE_SPEC.md |
| Direct tests | https://github.com/Demigodd00/oracleguard/blob/main/tests/direct/test_oracle_guard.py |
| v1.2 contract and evidence commit | https://github.com/Demigodd00/oracleguard/commit/317a083a1429c7bfded9df90e7dee454b91e472d |

## Contract deployments and finalized evaluations

Network: **Studio / Studionet, chain ID 61999**. If a single contract is requested, use the healthy charter as the primary contract and put the other two in supporting evidence.

| Scenario | Contract explorer URL | Finalized evaluation URL | Deployment record | Acceptance record |
| --- | --- | --- | --- | --- |
| Healthy | https://explorer-studio.genlayer.com/address/0x2AACfD82195A342e47a4C4589802f897F3BEC559 | https://explorer-studio.genlayer.com/tx/0x61dc32986056d4c41751e88cd16d7c5c34d7c51c1b63e3a3215418fb734e2c03 | https://github.com/Demigodd00/oracleguard/blob/main/deployments/studionet.json | https://github.com/Demigodd00/oracleguard/blob/main/deployments/acceptance_healthy.json |
| Synthetic stale | https://explorer-studio.genlayer.com/address/0x663De815860ca7719268c4D1381A7D080e8522B1 | https://explorer-studio.genlayer.com/tx/0x0020b6add67044c8ffdfe1557d0917c16bcc85a21c99c2cc6c41ecc23e78d9fd | https://github.com/Demigodd00/oracleguard/blob/main/deployments/studionet_synthetic_stale.json | https://github.com/Demigodd00/oracleguard/blob/main/deployments/acceptance_synthetic_stale.json |
| Missing reference | https://explorer-studio.genlayer.com/address/0x736F6dC07F882B37ACB860D86735A8d8fd544937 | https://explorer-studio.genlayer.com/tx/0x6fb7aaa7391fe877bc152f72ee3fb15d97e2d502e45bb642be220d382f7edd27 | https://github.com/Demigodd00/oracleguard/blob/main/deployments/studionet_invalid_reference.json | https://github.com/Demigodd00/oracleguard/blob/main/deployments/acceptance_invalid_reference.json |

## Accurate scope statement

The protected target is OracleGuard's own `request_borrow` admission counter. It issues no loans, transfers no assets, and holds no user funds. There is no administrator pause bypass or policy update method. The synthetic trigger is a test fixture, not a real market incident. StudioNet pins transaction time before consensus; therefore the effective hold after finality can be shorter than the requested 900–1,800 seconds. The demo does not guarantee a full duration after finality or claim to pause an external lending market.
