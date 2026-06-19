# Entry Acceptance Bar V1 - 2026-06-19

Status: `ACTIVE_STANDARD_FOR_FUTURE_CANDIDATE_SCREENS`

Scope: any future XAUUSD entry candidate screened after the A3 breakout-retest falsification.

This document promotes the hardened Round 3 screen to the standard entry-acceptance bar. It is intentionally stricter than the earlier gross/backtest screens because the live-demo evidence showed that cost, duplicate leverage, and post-hoc survivor slices can flatter weak entries.

## Primary Rule

Judge the raw deduped book first.

A candidate cannot advance because a cost filter removed most losing or expensive trades unless that filter was pre-registered as part of the entry rule before the screen.

## Required Methodology

- Use one virtual position at a time per candidate or family, unless the hypothesis explicitly pre-registers a different exposure model.
- Deduplicate same-signal and same-family stack effects before scoring.
- Apply measured cost before scoring.
- Charge the worse of realized spread or measured median spread for the entry hour.
- Stress with the worse of realized spread or measured P95 spread for the entry hour.
- Include slippage in both base and stress models.
- Default XAU slippage floor:
  - Entry slippage: `10` points.
  - Stop-exit slippage: `50` points.
- Reject or separately report any trade with estimated `cost_R > 0.12`.
- Report both raw deduped metrics and any cost-guard survivor diagnostics.

## Discovery Gates

All must pass on the raw deduped book:

| Gate | Required |
| --- | ---: |
| Net expectancy | `>= +0.10R/trade` |
| Net profit factor | `>= 1.25` |
| P95-stress net expectancy | `>= +0.10R/trade` |
| P95-stress net profit factor | `>= 1.25` |
| Closed trades | `>= 100` |
| Long trades | `>= 25`, unless one-sided hypothesis is pre-registered |
| Short trades | `>= 25`, unless one-sided hypothesis is pre-registered |
| Max drawdown | `<= 8R` |
| t-stat | `>= 2.0` |
| Worst day | `> -4R` |
| Best-days removed | positive after best 1 and best 2 days removed |
| Worst-day removed | positive after worst 1 day removed |
| Market regime | positive on both up-day and down-day aggregates, unless one-regime hypothesis is pre-registered |
| P95 cost_R | `<= 0.10` |
| Max accepted trade cost_R | `<= 0.12` |

## Promotion Gates

To move beyond discovery into forward/tick validation, tighten the core edge bar:

| Gate | Required |
| --- | ---: |
| Net expectancy | `>= +0.15R/trade` |
| Net profit factor | `>= 1.30` |
| All discovery gates | PASS |

## Reporting Requirements

Every candidate screen must show:

- Candidate id and hypothesis file path.
- Whether the hypothesis was locked before the run.
- Raw deduped PF, expectancy, total R, drawdown, win rate, t-stat.
- P95-stress PF and expectancy.
- Cost rejection count and percentage.
- Worst day and best-days-removed results.
- Up-day and down-day aggregate results.
- Clear PASS/FAIL and failure reasons.

## Governance Rule

If a candidate fails this bar, do not tune the same entry repeatedly. Either:

1. pre-register one materially different entry hypothesis, or
2. stop researching that instrument/family and reallocate effort.

The A3 breakout-retest falsification report is the precedent:

`xau-usd/xauusd-phase1/outputs/reports/A3_NET_COST_FALSIFICATION_2026_06_19.md`
