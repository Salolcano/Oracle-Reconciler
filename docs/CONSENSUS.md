# Consensus design

`reconcile` uses `gl.vm.run_nondet_unsafe(leader_fn, validator_fn)` with a custom validator rather than `strict_eq`. Strict equality would fail constantly: two honest validators fetching a live price a second apart will not see identical numbers.

## Parameters
- `tolerance_bps`: how far a source may sit from the median and still count as agreeing. Defines outliers.
- `drift_bps`: how far a validator's observation may differ from the leader's. Defines honest timing noise. Keep it **<= tolerance_bps**.
- `min_sources`: fewest successfully fetched sources before a round is even considered.
- `min_agree`: fewest agreeing sources to publish.

## Validator acceptance rule (`is_equivalent`)
A validator accepts the leader's result only if all of these hold:
1. **Internal consistency.** Recomputing median, agreeing set, and status from the leader's own reported `values` reproduces the leader's `status`, `value`, and `agreeing`.
2. **No fabricated observations.** For every source both sides fetched, the leader's value is within `drift_bps` of the validator's value.
3. **Value agreement.** The final value is within `drift_bps` of the validator's own final value.
4. **Status agreement.** OK / NO_QUORUM / INSUFFICIENT_SOURCES must match.
5. **Independent verification of the quorum.** At least `min_agree` of the leader's agreeing sources were also fetched by this validator.

## Why each check exists
| Attack or failure | Caught by |
|---|---|
| Leader invents a value for a source | 2 |
| Leader reports a median that does not follow from its data | 1 |
| Leader publishes a quorum the validator can't reproduce (e.g. sources it blocked or mocked) | 5 |
| Market moves between leader and validator | tolerated by `drift_bps` |
| Real disagreement about the data | 3 and 4, round fails and leader rotates |

## What is intentionally not compared
The order of failed sources, and per-source values for sources only one side could fetch. Network flakiness is normal and should not stall consensus.

## Offline coverage
`test/unit/test_logic.py` covers each rejection reason. `test/unit/test_contract_flow.py` simulates a validator that sees a different world (rejected) and one that sees small drift (accepted).
