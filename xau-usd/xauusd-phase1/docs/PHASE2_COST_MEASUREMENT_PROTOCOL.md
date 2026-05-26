# Phase 2 Cost Measurement Protocol

Last updated: 2026-05-23

Phase 2 is a paper-mode cost-measurement experiment. It is not a profit-confirmation phase and it does not authorize live capital.

## Objective

Measure whether real broker conditions preserve enough of the modeled `breakout_retest` edge to justify later live-pilot review.

Current modeled baseline:

| Metric | Value |
| --- | ---: |
| Net expectancy | 0.1888R |
| Mean all-in cost | 0.3228R |
| Gross expectancy estimate | 0.5115R |
| Cost consumption | 63.09% |

The modeled cost is provisional until the measured cost model and measured-cost revalidation reports both pass.

## Required Inputs

| Input | Required status |
| --- | --- |
| `MEASURED_COST_MODEL.md` | PASS |
| `BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md` | PASS |
| Phase 1 five-trading-day soak | PASS |
| Phase 1 uninterrupted 72-hour active-market streak | PASS |
| Phase 1 observer parity report | PASS |
| Phase 1 review index | PASS |
| Owner approval file | PASS |

## Paper-Mode Measurement Fields

Every paper-mode would-order or paper-order observation must preserve:

| Field | Purpose |
| --- | --- |
| `timestamp_broker` | Broker-time execution review. |
| `timestamp_utc` | Cross-system normalization. |
| `symbol` | Instrument validation. |
| `expert_family` | Single-edge concentration tracking. |
| `expert_name` | Variant-level attribution. |
| `intended_entry` | Strategy-intended price. |
| `paper_fill_price` | Broker paper fill proxy. |
| `spread_points` | Direct cost input. |
| `slippage_points` | Execution-quality input. |
| `commission_points_or_usd` | Broker fee input when available. |
| `modeled_cost_R` | Phase 0 baseline comparison. |
| `measured_cost_R` | Paper-mode realized cost proxy. |
| `net_expectancy_R_after_measured_cost` | Phase 2 viability metric. |

## Kill And Suspension Rule

Pre-committed threshold:

```text
MIN_NET_EXPECTANCY_R_AFTER_MEASURED_COST = +0.15R
```

Decision rule:

```text
IF measured paper/live execution cost pushes breakout_retest family net expectancy below +0.15R
THEN suspend the breakout-retest family and return to research.
```

This rule applies to the family, not only one timeframe flavor. `breakout_retest` and `swing_breakout_retest_v0` are same-family variants.

## Review Cadence

| Review point | Required action |
| --- | --- |
| Daily during Phase 2 | Check cost, spread, slippage proxy, stale ticks, and dry-run/paper permission state. |
| Weekly during Phase 2 | Produce a cost-retention summary against the 0.1888R modeled baseline. |
| Before any live pilot | Recompute net expectancy after measured costs and confirm it remains at or above +0.15R. |

## Interpretation

| Outcome | Decision |
| --- | --- |
| Net expectancy >= +0.15R and drift acceptable | Continue paper-mode evidence collection. |
| Net expectancy between +0.00R and +0.15R | Suspend family; do not live-pilot. |
| Net expectancy <= +0.00R | Retire or redesign as a new locked hypothesis. |
| Cost evidence incomplete | Remain in Phase 1/2 preparation. |

No filter may be added to rescue the result inside the same hypothesis version.
