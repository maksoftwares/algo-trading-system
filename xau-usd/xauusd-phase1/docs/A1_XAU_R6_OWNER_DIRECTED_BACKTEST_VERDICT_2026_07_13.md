# A1 XAU R6 Owner-Directed Backtest Verdict

Date: `2026-07-13`

Status: `R6_LOCKED_DEFINITION_REJECTED_INSUFFICIENT_INCIDENCE`

Scope: development-data screening and isolated MT5 Strategy Tester execution only.
No demo/live terminal, broker position, or real capital was touched.

## Locked decade screen

The frozen `R6_H4_DISTRIBUTION_BREAK_FAILED_RECLAIM_SHORT_V1` detector was run once
over the preserved Capital.com native H1/H4/D1 bar exports and native Router V1 rows
for the locked interval `2016-07-01` through `2026-06-30`.

The detector found exactly one structural opportunity:

```text
router state:       CHOP
breakdown H4:       2024-08-30 12:00 broker time
failed reclaim H1: 2024-08-30 16:00 broker time
entry time:         2024-08-30 17:00 broker time
entry bid/ask:      2497.63 / 2497.68
structural stop:    2507.65
minimum-lot risk:   $10.02
reference feasible: yes at the $25 research risk cap
deployment feasible:no at the $2.50 / $1,000 risk cap
```

The locked census required at least `120` raw opportunities, at least `40` in each
five-year half, and broad July-June coverage. The actual result was `1`, split
`0` early and `1` late, in one July-June bucket. Full native tick acquisition can
refine the entry price of this event but cannot create the missing 119 structural
setups because the impulse, box, router, breakdown, and reclaim gates are bar-based.

## Ten-year MT5 execution result

The sole locked event was then executed at `0.01` lot in the isolated MT5 Strategy
Tester over the complete `2016-07-01` to `2026-07-01` tester interval.

| Metric | Result |
| --- | ---: |
| History quality | `98%` |
| Bars | `703,491` |
| Ticks | `358,249,613` |
| Trades | `1` |
| Wins / losses | `1 / 0` |
| Net profit | `+$20.07` |
| Entry | `2497.63` |
| Exit | `2477.56` |
| Exit reason | `2R target` |
| Maximum equity drawdown | `$17.35 / 1.71%` |

MT5 displays profit factor `0.00` because there is no gross loss. With one trade,
profit factor, win rate, expectancy, robustness, concentration, and drawdown
distribution are not statistically estimable.

## Verdict

The one historical trade won, but R6 is not a usable specialist. It fails its
incidence gate by `119` opportunities and is also incompatible with the locked
`$2.50` deployment-risk ceiling at Capital.com's `0.01` minimum lot.

Per the preregistered no-neighbor rule, the current R6 definition should close. Its
thresholds must not be loosened after observing this result. A replacement
independent specialist requires a new economic hypothesis and a new outcome-blind
lock before any P/L is inspected.

## Evidence

- Bar screen: `outputs/reports/A1_XAU_R6_OWNER_DIRECTED_BAR_SCREEN_20260713/`
- Ten-year MT5 report: `outputs/reports/A1_XAU_R6_OWNER_DIRECTED_10Y_MT5_20260713/`
- Tester EA: `mt5/Experts/A1XauR6OwnerDirectedSingleEventBacktest.mq5`
- Runners:
  - `scripts/run_a1_xau_r6_owner_directed_bar_screen.py`
  - `scripts/run_a1_xau_r6_owner_directed_single_event_mt5.py`
