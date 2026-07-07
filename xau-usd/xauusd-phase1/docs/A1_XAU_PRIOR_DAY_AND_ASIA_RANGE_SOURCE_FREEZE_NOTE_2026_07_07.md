# A1 XAU Prior-Day / Asia-Range Source Freeze Note

Date: 2026-07-07

## Decision

Freeze the exact-MT5 prior-day level M5 source (`V15/V15B`) and Asian-range M5 source (`V16`) as practical paths to the relaxed `70-80%` positive-week target.

## Evidence

| Source | Best read | Standalone | Baseline hybrid | Weekly-state combo check | Decision |
|---|---|---|---|---|---|
| V15 prior-day level M5 | `v15_prior_day_level_reversal_rr15_reclaim05` | `1105` trades, WR `38.01%`, W/L `1.5338`, PF `0.9405`, net `-314.64` | positive weeks `54.81%`, active `91.56%`, red weeks flipped/worsened `11/47` | not better than prior ceiling | freeze |
| V15B direction split | `v15b_prior_day_level_reversal_rr15_short_only` | `611` trades, WR `36.82%`, W/L `1.5600`, PF `0.9093`, net `-269.09` | positive weeks `57.69%`, active `89.26%`, red weeks flipped/worsened `12/36` | best weekly-state combo `59.05%` positive weeks / `90.41%` active | freeze |
| V16 Asian range | `v16_asia_range_cont_rr2` | `2658` trades, WR `33.97%`, W/L `2.0593`, PF `1.0596`, net `+904.53` | positive weeks `56.73%`, active `96.84%`, red weeks flipped/worsened `15/52` | weekly-state combo worsens to `57.14%` positive weeks / `96.84%` active | freeze |

## Read

Both source classes are useful diagnostics because they are naturally active. That is also why they are decisive failures: they buy coverage but do not repair weekly distribution. They add too many losing trades into already-red weeks and turn too many green weeks red.

Do not continue with hour masks, direction masks, or threshold micro-tuning inside these exact source classes unless an independent reviewer proposes a materially different causal premise.
