# Phase 1 Would-Signal Manual Review

Overall status: TELEMETRY_REVIEW_COMPLETE_CHART_REVIEW_PENDING

Generated at UTC: 2026-05-27

## Scope

Source CSV:

```text
outputs/reports/PHASE1_WOULD_SIGNAL_REVIEW.csv
```

Current evidence:

| Field | Value |
| --- | ---: |
| Would-signal rows | 83 |
| Setup clusters | 83 |
| BR-only conflicts | 3 |
| SBR-only conflicts | 0 |
| Both same direction | 40 |
| Both opposite direction | 0 |

This review checks telemetry consistency from the existing CSV. It does not replace a visual chart review in MT5.

## Classification Values

- `MECHANICALLY_VALID`
- `OBSERVER_MISMATCH`
- `COST_BLOCKED_VALIDLY`
- `SESSION_OR_ROUTER_CONCERN`
- `DATA_OR_TIMESTAMP_ISSUE`

## Sample Review

| Item | Cluster / Bar | Scope | Direction | Level Kind | Classification | Note |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | WS001 / 2026.05.22 11:25 | breakout_retest sample | SHORT | latest_swing_low | MECHANICALLY_VALID | Dry-run true, permission false, execution OK, target/stop present. |
| 2 | WS003 / 2026.05.22 11:50 | breakout_retest sample | LONG | latest_swing_high | MECHANICALLY_VALID | Dry-run true, permission false, execution OK, target/stop present. |
| 3 | WS005 / 2026.05.22 12:45 | breakout_retest sample | LONG | latest_swing_high | MECHANICALLY_VALID | Dry-run true, permission false, execution OK, target/stop present. |
| 4 | WS007 / 2026.05.22 12:50 | breakout_retest sample | LONG | latest_swing_high | MECHANICALLY_VALID | Dry-run true, permission false, execution OK, target/stop present. |
| 5 | WS009 / 2026.05.22 14:05 | breakout_retest sample | SHORT | latest_swing_low | MECHANICALLY_VALID | Dry-run true, permission false, execution OK, target/stop present. |
| 6 | WS011 / 2026.05.25 05:50 | breakout_retest sample | SHORT | latest_swing_low | MECHANICALLY_VALID | Dry-run true, permission false, execution OK, target/stop present. |
| 7 | WS013 / 2026.05.25 07:40 | breakout_retest sample | SHORT | latest_swing_low | MECHANICALLY_VALID | Dry-run true, permission false, execution OK, target/stop present. |
| 8 | WS015 / 2026.05.25 12:50 | breakout_retest sample | SHORT | latest_swing_low | MECHANICALLY_VALID | Dry-run true, permission false, execution OK, target/stop present. |
| 9 | WS017 / 2026.05.25 13:20 | breakout_retest sample | SHORT | latest_swing_low | MECHANICALLY_VALID | Dry-run true, permission false, execution OK, target/stop present. |
| 10 | WS019 / 2026.05.25 15:05 | breakout_retest sample | LONG | latest_swing_high | MECHANICALLY_VALID | Dry-run true, permission false, execution OK, target/stop present. |
| 11 | 2026.05.22 11:25 | both same direction | SHORT | latest_swing_low | MECHANICALLY_VALID | BR and SBR agreed on direction and levels. |
| 12 | 2026.05.22 11:50 | both same direction | LONG | latest_swing_high | MECHANICALLY_VALID | BR and SBR agreed on direction and levels. |
| 13 | 2026.05.22 12:45 | both same direction | LONG | latest_swing_high | MECHANICALLY_VALID | BR and SBR agreed on direction and levels. |
| 14 | 2026.05.22 12:50 | both same direction | LONG | latest_swing_high | MECHANICALLY_VALID | BR and SBR agreed on direction and levels. |
| 15 | 2026.05.22 14:05 | both same direction | SHORT | latest_swing_low | MECHANICALLY_VALID | BR and SBR agreed on direction and levels. |
| 16 | 2026.05.25 05:50 | both same direction | SHORT | latest_swing_low | MECHANICALLY_VALID | BR and SBR agreed on direction and levels. |
| 17 | 2026.05.25 07:40 | both same direction | SHORT | latest_swing_low | MECHANICALLY_VALID | BR and SBR agreed on direction and levels. |
| 18 | 2026.05.25 12:50 | both same direction | SHORT | latest_swing_low | MECHANICALLY_VALID | BR and SBR agreed on direction and levels. |
| 19 | 2026.05.25 13:20 | both same direction | SHORT | latest_swing_low | MECHANICALLY_VALID | BR and SBR agreed on direction and levels. |
| 20 | 2026.05.25 15:05 | both same direction | LONG | latest_swing_high | MECHANICALLY_VALID | BR and SBR agreed on direction and levels. |
| 21 | 2026.05.26 00:55 | BR-only | SHORT | previous_daily_low | MECHANICALLY_VALID | BR-only is expected for prior-day level families; no SBR mismatch implied. |
| 22 | 2026.05.27 07:55 | BR-only | SHORT | previous_daily_low | MECHANICALLY_VALID | BR-only is expected for prior-day level families; no SBR mismatch implied. |
| 23 | 2026.05.27 12:45 | BR-only | SHORT | previous_weekly_low | MECHANICALLY_VALID | BR-only is expected for prior-week level families; no SBR mismatch implied. |

## Open Chart Review

Before Phase 2 authorization, the owner or reviewer should still inspect the underlying chart context for the sampled rows. This file confirms telemetry consistency only:

- all reviewed rows are dry-run
- all reviewed rows keep `trade_permission=false`
- no both-opposite-direction conflicts exist
- BR-only rows are explainable by BR using previous daily/weekly levels that the swing observer is not expected to mirror

## Boundary

This review does not authorize paper-mode execution. It does not add an expert, change observer logic, or alter runtime code.
