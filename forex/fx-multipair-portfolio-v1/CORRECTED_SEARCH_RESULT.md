# Corrected Search Result

Date: 2026-08-01
Status: **`ALL_REVIEW_FIXES_APPLIED_NO_EDGE_REMAINS`**

## What was fixed

The code review found four defects; all four were corrected and the search re-run.

| Defect | Fix |
|---|---|
| `max_hold_bars = 288*(240/tf)` — inverse scaling, M15 held 10 days vs H4 1 day | `hold = 24 * tf/5`, equal decision-bar horizon for every timeframe |
| Both qualification windows were bull markets → 828/830 survivors long-only | Qualify on 2016, 2017, 2018 **and 2022**; hold out 2019, 2020, 2021, 2023 |
| Short side effectively unrepresented | Longs and shorts qualified in separate pools, portfolio drawn from both |
| Equal-lot weighting with 3.8x stop dispersion | Risk-normalised to a 200-point reference stop |
| `range_break` duplicated `breakout` | Family removed (12,600 configs, no duplicates) |

## The fixes worked — as diagnostics

Adding a bear year to qualification raised short representation from **2 of 830
(0.2%)** to **17 of 150 (11.3%)**. The mechanism the review identified was real.

Risk-normalised long/short netting cut qualification drawdown from **8.85% to
1.83%**. Balanced construction genuinely controls risk.

## But the edge does not survive

| Portfolio | Qualify PF | **Holdout PF** | Holdout net |
|---|---:|---:|---:|
| Long-only | 1.163 | **1.009** | +0.80% |
| Balanced (10L/10S) | 1.170 | **0.925** | −6.20% |
| All 150 qualified | 1.206 | **0.960** | −2.11% |

Every portfolio drops from PF 1.16–1.21 in qualification to 0.93–1.01 out of
sample. That gap *is* the overfitting, now measured on a clean split with a bear
market in both arms.

Adding the short side made the holdout **worse** (0.925 vs 1.009), so the
long-only bias was not the cause of failure — it was a symptom of the same thing:
there is no repeatable signal for either side to exploit.

## Conclusion

Fixing the bugs did not reveal an edge; it removed the illusion of one. The
earlier design PF of 1.126 was partly an artefact of holding M15 signals for ten
days in a rising market. With that corrected and a bear market inside
qualification, the best out-of-sample profit factor available from 12,600
configurations is **1.009** — breakeven, before any real-world slippage beyond
the modelled two points.

This is the fifth independent line of evidence on this instrument:
bar-geometry families, the 14,400-attempt search with a null benchmark, the
frequency portfolio, the high-win-rate portfolio, and now the corrected
long/short search. All agree.

**A profitable US500 system cannot be produced from this search space, and no
amount of further parameter work will change that.** The one durable output is
the risk result: balanced long/short construction cuts drawdown roughly fivefold,
which is worth keeping for any future system that does have an edge to protect.
