# Architecture and decision boundary

1. **Policy deployment.** The constructor fixes the pair, three source URLs, maximum sample age, reference spread limit, deviation trigger, and maximum hold. The deployer address is informational; it has no mutation or pause method.
2. **Incident opening.** `open_assessment(duration_seconds, note)` records an immutable incident with the exact charter URLs and bounded requested duration. The frontend waits for finality before offering evaluation.
3. **Evidence evaluation.** `evaluate_assessment(id)` fetches all three URLs inside a GenVM nondeterministic block. The leader proposes the source response bodies, hashes, parsed values, and decision. Validators fetch independently, reparse the proposed bodies, verify the hashes and decision, and compare live prices within 2% and timestamps within five minutes. Substantive disagreement prevents consensus on the proposed transition.
4. **Decision.** Fresh reference prices must agree within the policy spread. A stale feed or deviation beyond the trigger yields `TRIGGER_CONFIRMED`. Missing, invalid, stale, or conflicting reference evidence yields `INSUFFICIENT_EVIDENCE`. A healthy feed yields `NO_TRIGGER`.
5. **Effect.** Only `TRIGGER_CONFIRMED` sets `suspended_until`, bounded by the requested duration and immutable maximum. `request_borrow` is an on-chain admission counter with no funds. It checks the hold timestamp on every call. The console reads finalized state.

## Trust and limits

GenLayer validators independently retrieve web data. That makes a single client or proposer insufficient to claim a trigger, but it does **not** establish the authenticity of a source operator. Deployers must choose reputable, independently operated endpoints and validate their economic relevance to the protected pair. Three domains alone do not prove independence.

Sources can change between the leader and validator requests. The validator compares the categorical decision, replays the leader's recorded response bodies, and confirms live price fields within a 2% tolerance. Near a threshold, changing data can produce disagreement and delay finality. An unavailable source creates no pause. A bad protected feed also creates no pause if the two references cannot be trusted at assessment time.

An `Accepted` GenLayer result is still appealable. The UI reads `LATEST_FINAL` and requires `FINALIZED`, an agreeing consensus result, and successful execution before reporting success. This is a bounded response mechanism, not an instantaneous market breaker. A production lending integration would require a lending contract to enforce a finalized OracleGuard signal, plus integration tests for asynchronous cross-contract behavior.
