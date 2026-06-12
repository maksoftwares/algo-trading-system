# Forward Week Impulse Veto Hypothesis - 2026-06-15

Status: PENDING_FORWARD_WEEK

Boundary:

- Shadow-only analysis; no chart, preset, order, position, or running-EA behavior changes.
- Canonical Phase 2 status is unchanged.
- `breakout_retest` entry, stop, and target logic remain frozen.
- This document pre-registers the impulse-veto scoring before the 2026-06-15 forward week.

## Research Question

Do weak level-retest lanes lose because they fade the freshest one-hour impulse?

The measured feature is:

```text
ret12_atr = (last closed M5 close - close 12 completed M5 bars earlier) / ATR14
impulse_alignment = direction_sign * ret12_atr
```

Where:

- `direction_sign = +1` for BUY/LONG.
- `direction_sign = -1` for SELL/SHORT.
- Negative `impulse_alignment` means the trade fights the most recent one-hour move.

## Target Scope

The shadow veto applies only to:

```text
round_retest_family
session_extreme_family
```

Included candidates:

```text
symbol_normalized_round_retest_v0
round_number_retest_v0
symbol_normalized_round_retest_v0_repair_v1
round_number_retest_v0_repair_v1
session_extreme_retest_v0
session_extreme_retest_v0_repair_v1
```

The `breakout_retest` family is a control group only. It must not be blocked by this rule during the locked week because prior evidence says its structure anchor already handles many counter-impulse cases.

## Pre-Registered Thresholds

Score all three thresholds without mid-week tuning:

```text
T1: impulse_alignment < -1.0
T2: impulse_alignment < -1.5
T3: impulse_alignment < -2.0
```

The primary threshold for review is `T2 = -1.5`, matching the forensics document. T1 and T3 are sensitivity checks only.

## Expected Result

For weak families, blocked trades should be materially worse than kept trades.

Expected pattern:

```text
blocked bucket: lower win rate, lower PF, negative net PnL
kept bucket: improved PF and net PnL versus baseline
kept share: >= 60%
```

The dose-response table should remain monotonic or near-monotonic:

```text
hard_against < mild_against < fresh_flat/mild_with/extended_with
```

## Promotion Bar

No runtime change is allowed from this document alone.

A future owner packet may propose a demo guard only if a fresh forward week shows:

- broker-joined evidence only;
- at least 30 closed target-family trades;
- blocked bucket is clearly negative;
- kept bucket improves PF and net PnL versus baseline;
- kept share is at least 60%;
- result is not carried by one isolated day;
- reviewer and owner approve the exact threshold and scope.

## Current Baseline Report

The baseline report generator is:

```text
xau-usd/xauusd-phase1/scripts/generate_phase2_impulse_veto_shadow_report.py
```

Current output paths:

```text
xau-usd/xauusd-phase1/outputs/reports/PHASE2_IMPULSE_VETO_SHADOW_REPORT.md
xau-usd/xauusd-phase1/outputs/reports/PHASE2_IMPULSE_VETO_SHADOW_REPORT.json
xau-usd/xauusd-phase1/outputs/reports/PHASE2_IMPULSE_VETO_SHADOW_ROWS.csv
```

Review interpretation:

- Use the report as a shadow research artifact.
- Do not use it as authorization to change running EAs.
- Do not tune thresholds after seeing the forward-week results.
