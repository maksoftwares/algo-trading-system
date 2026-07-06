# A1 XAU M5 Early Adverse Exit Exact Probe Preregistration

Generated: 2026-07-05

## Objective

Test whether MT5-side loss truncation can move the current best exact-MT5 frequency frontier closer to the owner goal without capping winners.

Owner goal:

- Realized average win / average loss >= 2.0
- Win rate >= 50%
- At least one trade every trading day; 90%+ active days is worth showing if the first two hold

## Boundary

This is an exact MT5 Strategy Tester probe in isolated tester root `C:\MT5A1M5MomentumBacktest`.

No live/demo runtime attachment is allowed. Python is used only for orchestration and manual aggregation from exported MT5 trade CSVs.

No reviewer token is spent unless the exact MT5 result reaches at least the core shape: WR >= 50% and realized W/L >= 2.0.

## Frozen Base

Use the current best frequency/payoff compromise from Step 1:

- `goal_split_f33_r30_be_1r_v6`, priority 1
- `goal_split_f33_r30_be_1r_weak`, priority 2
- `goal_split_f33_r30_be_1r_v13`, priority 3

The three component streams are deduped after MT5 using the same 4-minute priority rule as the split frontier work.

## Frozen MT5 Cells

All cells enable:

- `InpEarlyAdverseExitEnabled=true`
- `InpEarlyAdverseExitShadowOnly=false`
- `InpManagementLogMode=1`

Cells:

| Cell | Exit age | Adverse R threshold |
| --- | ---: | ---: |
| `eae30_r035` | 30 minutes | -0.35R |
| `eae60_r035` | 60 minutes | -0.35R |
| `eae30_r050` | 30 minutes | -0.50R |
| `eae60_r050` | 60 minutes | -0.50R |

Rationale: these cells test loss-size truncation while keeping the 3R runner intact. The grid is intentionally small to avoid tuning-by-inspection.

## Acceptance

Primary acceptance:

- Core shape hit if exact deduped signal results have WR >= 50% and realized W/L >= 2.0.
- Owner goal hit only if the core shape also has active trading days >= 90% of weekdays in the test window.

Secondary robustness flags:

- Last-12-month WR/WL
- Top-10 and top-25 removed net
- Max closed drawdown from manually aggregated signal P&L
- Component-level contribution

## Decision Rule

- If no cell reaches WR >= 50% and W/L >= 2.0, reject the branch and do not spend reviewer token.
- If one cell reaches core shape but active days are below 90%, package it as a frequency-gap clue before deciding whether review is worth the daily reviewer budget.
- If a cell reaches the full owner goal, freeze all artifacts and prepare a reviewer prompt with source hashes, exact config, MT5 reports, manual aggregation, and runtime-isolation evidence.
