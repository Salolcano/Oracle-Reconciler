# Threat model

| Threat | Mitigation | Residual risk |
|---|---|---|
| One source returns a wrong value | Median + outlier rule; source counted as outlier and tracked in `src_stats` | If a majority of sources are wrong together, the result is wrong |
| Prompt injection on an LLM-extracted page | Page is wrapped as data; output must be a plain number; median isolates a single poisoned source (tested) | If most sources use LLM extraction, injection becomes more dangerous. Prefer `path` sources |
| Malicious leader fabricates data | Validator checks 1, 2, 5 in docs/CONSENSUS.md | Needs enough honest validators |
| Source outage | `min_sources` below total sources tolerates failures; round returns INSUFFICIENT_SOURCES without writing | Prolonged outage means stale feed. Consumers use `min_round` |
| Stale data used by consumers | `get_value_checked(feed_id, min_round)` | Consumers must choose a sensible `min_round` |
| Spam of `reconcile` | Each call costs fees; a failed quorum writes nothing except `attempts` | `attempts` can be overwritten by anyone |
| Correlated sources (all mirror one upstream) | Not detectable on-chain | Feed creators should choose independent upstreams |
| Feed squatting | Feed IDs are first-come; creator is recorded in config | Namespacing is the creator's job |
| Rounding differences between nodes | Integer fixed-point, deterministic half-up rounding, no floats in aggregation | None known |
