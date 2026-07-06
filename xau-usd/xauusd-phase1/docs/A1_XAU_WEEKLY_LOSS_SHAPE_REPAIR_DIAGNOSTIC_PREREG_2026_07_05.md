# A1 XAU Weekly Loss-Shape Repair Diagnostic Prereg - 2026-07-05

Status: `PREREG_DIAGNOSTIC_ONLY`

## Purpose

The current best exact-ledger frontier clears signal-level WR and realized W/L by a razor-thin
margin, but misses activity and has unacceptable loss clustering. June 2026 shows the problem:
the month reached WR above 50%, yet a single H4/D1 cluster week drove the month negative.

This diagnostic tests whether simple, causal portfolio-level loss-shape controls can reduce weekly
damage without destroying the owner core metrics.

## Boundary

- Exact-ledger diagnostic only using the already published kept-signal CSV:
  `A1_XAU_HYBRID_F67_H16_NO_F33_COMPOSITION_202207_202606_KEPT.csv`.
- No MT5 launch, no chart/profile/preset edit, no order, no position, and no broker/runtime touch.
- No demo claim, no forward spec, no reviewer spend from this diagnostic unless a row preserves
  WR `>=50%`, W/L `>=2.0`, active weekdays `>=86%`, and materially improves positive-week rate
  plus worst-week loss.

## Fixed Tests

### Causal Entry-Count Controls

These are implementable without knowing future trade outcomes:

- H4/D1 source max entries per day: `{1, 2}`
- H4/D1 source max entries per week: `{1, 2, 3}`
- H4/D1 source max entries per day and per week combined:
  - day `1`, week `{1, 2, 3}`
  - day `2`, week `{2, 3}`

The H4/D1 source set is:

- `h4_d1_long_best_box2_atr80`
- `h4_d1_long_broad_box3_atr60`

### Non-Promotional Loss-Cap Sensitivity

These rows are not executable claims. They answer only: "How small would H4/D1 losses need to be
to fix the weekly/monthly shape?"

- Cap H4/D1 individual losses at `{50, 75, 100}` USD.
- Cap all individual signal losses at `{50, 75, 100}` USD.

## Metrics

Every row must report:

- Signals, WR, avg win/loss, active weekdays, PF, net, max drawdown.
- Positive week count and percentage.
- Worst week P&L.
- June 2026 signals, WR, W/L, active weekdays, net, and week table.
- Decision string.

## Decision Rules

- `REPAIR_CANDIDATE_REQUIRES_EXACT_MT5`: WR `>=50%`, W/L `>=2.0`, active weekdays `>=86%`,
  positive-week rate improves by at least 5 percentage points, and worst week improves by at least
  25% versus baseline.
- `LOSS_SHAPE_IMPROVES_CORE_BREAKS`: weekly loss shape improves, but WR/W-L/activity core breaks.
- `SENSITIVITY_ONLY_NOT_EXECUTABLE`: loss-cap sensitivity row, never a promotion candidate.
- `REJECT_NO_WEEKLY_REPAIR`: no useful weekly repair.

## Reporting

Publish a report, JSON, result CSV, and best kept-signal CSV. The report must explicitly state
whether any result is causal/implementable or sensitivity-only.
