# Oracle Reconciler

A composable GenLayer Intelligent Contract primitive that reconciles a fact or price across several independent sources, rejects outliers, and only publishes a value when enough sources agree. Other contracts read it with one call.

It is **not** "ask an LLM for the price". Extraction is deterministic (JSON path) by default, the aggregation is a median with a quorum rule, and validators run a custom acceptance check instead of comparing strings. An LLM is only an optional fallback for sources that have no JSON API, and the median means a single poisoned page cannot move the result.

## Why this is useful beyond a demo
- Any prediction market, insurance, lending, or escrow contract needs a trustworthy external number. This is a drop-in source.
- Every round records which sources agreed, were outliers, or failed, and per-source reliability counters accumulate on-chain.
- `get_value_checked(feed_id, min_round)` gives consumers stale-data protection without relying on wall-clock time.

## Contract API
| Method | Type | Purpose |
|---|---|---|
| `register_feed(feed_id, sources_json, decimals, tolerance_bps, drift_bps, min_sources, min_agree)` | write | Create a feed (2-8 sources) |
| `reconcile(feed_id)` | write | Permissionless. Run one round. Returns `OK`, `NO_QUORUM`, or `INSUFFICIENT_SOURCES` |
| `get_value(feed_id)` | view | Latest fixed-point value (reverts if none) |
| `get_value_checked(feed_id, min_round)` | view | Same, but reverts if the feed round is older than `min_round` |
| `get_latest(feed_id)` / `get_round_data(feed_id, n)` | view | Full round JSON: value, agreeing, outliers, failed, per-source values |
| `get_last_attempt(feed_id)` | view | Last attempt of any status (shows failed quorums) |
| `get_source_stats(feed_id)` | view | Per-source ok / outlier / fail counters |
| `get_feed`, `list_feeds`, `get_round` | view | Config and listing |

Source object: `{"url": "...", "path": "data.amount"}` for JSON extraction, or `{"url": "...", "hint": "current BTC price in USD"}` for LLM extraction.

## How consensus is used
See [docs/CONSENSUS.md](docs/CONSENSUS.md). Short version: the leader fetches and reconciles; each validator independently re-fetches and accepts only if the leader's result is internally consistent, every per-source value matches the validator's own observation within `drift_bps`, the final value is within `drift_bps`, the status matches, and at least `min_agree` of the leader's quorum was independently verified.

## Project layout
```
contracts/oracle_reconciler.py     the primitive
examples/collateral_gate.py        a consumer contract
test/unit/                         27 offline tests (logic + storage flow + simulated validator disagreement)
test/integration/live.test.mjs     live Studio Next round
deploy/                            genlayer-js deploy + example BTC-USD feed
docs/                              architecture, consensus, threat model
```

## Run the tests
```
npm run test            # offline, no dependencies beyond Python 3
```
The offline tests use a small stub of the `genlayer` module (`test/unit/genlayer_stub.py`). They prove the contract logic, not GenVM behavior.

## Deploy to Studio Next
Network: https://studio-next.genlayer.com/api, chain ID 61997, explorer https://explorer-studio-dev.genlayer.com/
```
npm install
cp .env.example .env     # set PRIVATE_KEY
PRIVATE_KEY=0x... npm run deploy
RUN_LIVE=1 PRIVATE_KEY=0x... npm run test:live
```
Deployed address: _fill in after deploy_

## Known limitations
- Feeds are non-negative scalars (prices, counts, rates). Negative values are rejected.
- Scientific notation (`1e-7`) in source data is rejected rather than guessed.
- `updated_at` is best effort from the message timestamp and may be empty on some runtimes; use `min_round` for freshness guarantees.
