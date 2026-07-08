# A1 XAU Realistic Candidate Monthly Health Preregistration

Generated: 2026-07-08

## Purpose

Try to turn the current chart-context long/short review candidate into a stronger realistic candidate. The previous pass reached the core shape (`50.03% WR`, `2.13 W/L`) but still had only `31/48` positive closing months. This pass tests a causal source-health gate to improve monthly consistency without pretending the standalone short is solved.

This is research-only. It does not authorize demo/live trading.

## Baseline

Use the current best chart-context blend:

`A1_XAU_CHART_CONTEXT_LONG_SHORT_BLEND_20260708_replace_v2_with_short_v4_impulse_retest_d1_structural_h1h4_KEPT.csv`

Baseline metrics:

- WR: about `50.03%`
- W/L: about `2.13`
- Net: about `$20,882`
- Max closed DD: about `$958.86`
- Positive closing months: `31/48`

## Fixed Causal Gate

At the start of each calendar month, check each selected source's **previous completed calendar month closed PnL** using only trades kept by the gate. If that source's previous month net is below `0`, block that source's new entries for the current month.

No current-month PnL may affect current-month blocking.

## Variants

Run exactly four variants:

| Variant | Sources gated |
| --- | --- |
| `freq_only_prev_month_health` | `freq_step3_frontier` only |
| `short_only_prev_month_health` | `short_v4_impulse_retest_d1_structural_h1h4` only |
| `freq_and_short_prev_month_health` | frequency plus V4 short |
| `all_sources_prev_month_health` | frequency, V4 short, and `h4_d1_long_best_box2_atr80` |

## Candidate Gate

A row can be a realistic review candidate only if all are true:

- WR `>= 50%`.
- raw W/L `>= 2.00`.
- stress W/L after `-$0.30` per ticket `>= 1.90`.
- net `>= 19000`.
- active weekdays `>= 84%`.
- max closed drawdown `<=` baseline.
- positive closing months `>= 32`.
- negative closing months `<= 16`.
- Q2-2026 net `> 0`.
- recent-three-month net `> 0`.
- positive weeks `>=` baseline.

## Forbidden

- No hour/session/day/month masks.
- No tuning the previous-month threshold.
- No deleting individual bad months after seeing results.
- No changing RR.
- No demo claim from this pass.

## Decision

If a row passes:

- Status: `REALISTIC_CANDIDATE_REVIEW_READY`.
- Keep research-only and request review.

If no row passes:

- Status: `REALISTIC_MONTHLY_HEALTH_NO_SURVIVOR`.
- Keep the chart-context blend as the best current review candidate and stop pushing monthly smoothness without reviewer advice.
