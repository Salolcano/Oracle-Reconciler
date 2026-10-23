# Architecture

## State
| Field | Type | Meaning |
|---|---|---|
| `owner` | Address | Deployer (reserved for future admin hooks) |
| `feeds` | TreeMap[str, str] | feed_id -> config JSON (sources, decimals, tolerance, drift, quorum) |
| `latest` | TreeMap[str, str] | feed_id -> last **accepted** round |
| `attempts` | TreeMap[str, str] | feed_id -> last attempt of any status |
| `rounds` | TreeMap[str, u256] | feed_id -> accepted round counter |
| `history` | TreeMap[str, str] | `feed_id:0000000007` -> round JSON (zero padded so keys sort) |
| `src_stats` | TreeMap[str, u256] | `feed_id:idx:ok|out|fail` -> counter |

Values are fixed-point integers (`decimals` per feed), never floats. Round JSON stores numbers as strings so large values survive JSON consumers.

## Flow of `reconcile`
```
caller -> reconcile(feed_id)
  1. read feed config from storage into local variables (no storage access inside nondet)
  2. leader_fn : for each source -> render page -> JSON path (or LLM fallback) -> to_scaled
                 -> median -> agreeing/outliers -> status
  3. validator_fn: re-run collect_observations independently, then is_equivalent(leader, mine, cfg)
  4. on agreement: if status == OK, bump round, write latest + history, update source stats
```

## Pure vs non-deterministic code
Everything that decides the outcome (`to_scaled`, `reconcile_values`, `is_equivalent`) is pure and unit tested. Only `collect_observations` touches the network or an LLM.

## Composability
A consumer calls `gl.get_contract_at(oracle).view().get_value_checked(feed_id, min_round)`. See `examples/collateral_gate.py`.
