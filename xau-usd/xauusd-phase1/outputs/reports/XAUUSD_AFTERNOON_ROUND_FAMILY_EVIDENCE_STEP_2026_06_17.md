# XAUUSD Afternoon Round-Family Evidence Step - 2026-06-17

Status: `EVIDENCE_STEP_COMPLETE`

Boundary: analysis-only. This file reads the existing duplicate-hidden XAUUSD evidence reports and does not touch MT5 runtime, charts, presets, orders, positions, profiles, or running EAs.

## Source Trail

| Source | Path |
| --- | --- |
| Canonical report | `xau-usd/xauusd-phase1/outputs/reports/XAUUSD_CANONICAL_LOSS_AVOIDANCE_2026_06_17.md` |
| Canonical JSON | `xau-usd/xauusd-phase1/outputs/reports/XAUUSD_CANONICAL_LOSS_AVOIDANCE_2026_06_17.json` |
| Canonical rows | `xau-usd/xauusd-phase1/outputs/reports/XAUUSD_CANONICAL_LOSS_AVOIDANCE_2026_06_17_ROWS.csv` |
| Deduped source rows | `xau-usd/xauusd-phase1/outputs/reports/XAUUSD_DEDUPED_REAL_FILL_EVIDENCE_2026_06_16_ROWS.csv` |

## Evidence Question

Are XAUUSD afternoon losses caused by the afternoon window generally, or mostly by a specific EA family?

## Answer

The evidence currently points to a specific EA-family problem first: `round_family`.

## Duplicate-Hidden Baseline

| View | Rows | Win Rate | PnL AED | Profit Factor |
| --- | ---: | ---: | ---: | ---: |
| All deduped XAUUSD selected signals | 586 | 37.80% | -554.52 | 0.95 |
| Round-family selected signals | 432 | 36.60% | -1359.41 | 0.84 |
| Breakout-core selected signals | 112 | 47.75% | 1059.34 | 1.82 |

## Afternoon Diagnosis

| Segment | Rows | Win Rate | PnL AED | Profit Factor | Share Of Afternoon Loss |
| --- | ---: | ---: | ---: | ---: | ---: |
| All afternoon XAUUSD | 82 | 28.05% | -523.03 | 0.62 | 100.00% |
| Round-family afternoon | 55 | 27.27% | -452.13 | 0.58 | 86.44% |
| Non-round residual after round quarantine | 27 | 29.63% | -70.90 | 0.77 | 13.56% |
| Breakout-core afternoon | 11 | 27.27% | -53.09 | 0.63 | 10.15% |
| Session-extreme afternoon | 16 | 31.25% | -17.81 | 0.89 | 3.41% |

## Rule Check

| Retrospective Rule | Kept Rows | Kept Win Rate | Kept PnL AED | Delta Vs Baseline | Protected Evening/Night Breakout Removed |
| --- | ---: | ---: | ---: | ---: | ---: |
| Round-family quarantine | 154 | 41.18% | 804.89 | +1359.41 | 0 rows / 0.00 AED |
| No afternoon | 504 | 39.40% | -31.49 | +523.03 | 0 rows / 0.00 AED |
| Breakout core only | 112 | 47.75% | 1059.34 | +1613.86 | 0 rows / 0.00 AED |
| Protected breakout evening/night only | 79 | 52.56% | 1027.32 | +1581.84 | n/a |

## Evidence Decision

The first evidence-backed fix candidate is:

```text
Round-family quarantine/restriction
```

This targets:

```text
symbol_normalized_round_retest_v0
round_number_retest_v0
```

The evidence does not yet justify a broad afternoon ban. After removing round-family rows, the remaining afternoon loss is much smaller (`-70.90 AED`) and should keep collecting evidence before a harsher time-window rule is promoted.

## Reviewer Question

Please review whether the current duplicate-hidden evidence supports the following decision:

```text
Approve round-family quarantine/restriction as the first controlled runtime-change candidate.
Do not approve a broad XAUUSD afternoon ban yet.
Do not change breakout-core evening/night behavior.
```

## Runtime Status

No runtime action is authorized by this evidence step.

Before any runtime change:

1. Owner approves the exact item.
2. Profile backup is captured.
3. Before/after chart report is generated.
4. Startup/order logs are verified after restart.
5. One fresh week is scored against protected breakout-core impact.
