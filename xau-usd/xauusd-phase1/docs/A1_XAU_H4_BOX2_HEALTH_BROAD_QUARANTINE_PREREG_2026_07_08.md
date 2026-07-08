# A1 XAU H4 Box2 Health Gate / Broad Quarantine Preregistration

Date: 2026-07-08

## Objective

Test whether the exact-MT5 previous-month health gate should be applied only to the profitable H4/D1 box2 engine, while the broad H4/D1 component is either kept in its prior supportive-guard form or quarantined.

The prior exact implementation improved monthly consistency from 29/19 to 31/17, but worsened max closed drawdown and worst month because broad H4 rows survived dedupe after box2 rows were blocked. This pass isolates that composition effect.

## Boundary

- Use existing exact-MT5 component ledgers only.
- Do not launch live/demo runtime.
- Do not change charts, presets, orders, positions, or broker state.
- Do not sweep thresholds.
- Compare only the preregistered compositions below.

## Fixed Inputs

Baseline portfolio:

- `A1_XAU_SHORT_HEDGE_EXACT_202207_202606_short_hedge_v2_breakdown_retest_KEPT.csv`

Raw recomposition base:

- `A1_XAU_HYBRID_F67_H16_EXACT_REPAIR_202207_202606_HYBRID_RAW.csv`
- Remove `step1_f33_r30_be_never`
- Remove existing H4/D1 long rows
- Add reconstructed raw V2 short rows from kept + dropped V2 ledgers
- Add exact-MT5 H4 component rows listed below
- Run the same existing dedupe pipeline

Exact H4 component rows:

- Previous-month health-gated box2 from `h4_prev_month_health_gate_box2`
- Previous-month health-gated broad from `h4_prev_month_health_gate_broad`
- Supportive-guard box2 from `supportive_guard_box2`
- Supportive-guard broad from `supportive_guard_broad`

## Variants

1. `control_supportive_box2_supportive_broad`: supportive box2 + supportive broad + unchanged frequency + V2 short.
2. `prevhealth_box2_supportive_broad`: previous-month health-gated box2 + supportive broad + unchanged frequency + V2 short.
3. `prevhealth_box2_broad_quarantined`: previous-month health-gated box2 + no broad H4 + unchanged frequency + V2 short.
4. `supportive_box2_broad_quarantined`: supportive box2 + no broad H4 + unchanged frequency + V2 short.
5. `prevhealth_box2_prevhealth_broad`: previous-month health-gated box2 + previous-month health-gated broad + unchanged frequency + V2 short. This is the prior exact implementation control.

## Pass / Fail

A variant is a review candidate only if all hold versus baseline:

- Positive months improve by at least 2.
- Net >= 19000 USD.
- Win rate >= 48%.
- W/L >= 2.0.
- W/L after -0.30 USD/ticket stress >= 1.90.
- Active weekdays >= 84%.
- Max closed drawdown is not worse than baseline.
- Worst closing month is not worse than baseline.

If monthly consistency improves but drawdown or worst month worsens, it remains watchlist-only or reject, not demo-ready.

