# A1 XAU H4/D1 Geometry V2 Weekly-Shape Preregistration

Date: 2026-07-06

## Purpose

Run one bounded exact-MT5 H4/D1 geometry pass against the current best hybrid blocker: weak weekly shape when P&L is grouped by final signal exit date.

The anatomy report `A1_XAU_HYBRID_WEEKLY_EXIT_ANATOMY_202207_202606.md` found:

- current hybrid closed-P&L positive weeks: `54.81%`
- current hybrid worst closed week: `$-878.18`
- red weeks with no positive H4/D1 contribution: `97.87%`
- H4/D1 source net: `$16,132.83`, but it dominates the worst loss clusters
- frequency/frontier filler is not the primary repair lever

Therefore this pass targets H4/D1 loss distribution and recovery timing, not extra M5 frequency.

## Frozen Measurement

- Symbol: `XAUUSD`
- Tester: exact MT5 Strategy Tester, isolated backtest root
- Period: `2022.07.01` through `2026.06.30`
- Weekly metric: broker-time Monday-Sunday week, grouped by final signal `exit_time`
- Zero-trade weeks: excluded from positive-week ratio
- Recomposition: replace only `h4_d1_long_best_box2_atr80` inside the current best hybrid; all non-H4 sources remain unchanged
- No live/demo runtime, chart, preset, order, position, or broker state is touched

## Frozen Base Component

- `InpSignalMode=7`
- `InpDirectionMode=1`
- `InpRiskReward=2.00`
- `InpMaxEstimatedCostR=0.15`
- `InpStopCeilingPoints=0`
- `InpMaxTradesPerDay=6`
- `InpCooldownMinutes=0`
- `InpOnePositionPerMagic=false`
- `InpMaxOpenPositionsPerMagic=32`
- `InpD1CompressionAtrPercentileMax=80.00`
- `InpD1CompressionBoxDays=2`
- `InpD1CompressionRangeMedianMax=1.50`
- `InpD1CompressionH4MinBodyFraction=0.35`

## Geometry V2 Cells

Maximum cells in this pass: `6`.

| Cell | Stop geometry | Early adverse exit |
| --- | --- | --- |
| `cap6000` | `InpStopCapPoints=6000` | off |
| `cap7500` | `InpStopCapPoints=7500` | off |
| `cap9000` | `InpStopCapPoints=9000` | off |
| `cap6000_eae240_r060` | `InpStopCapPoints=6000` | close at `-0.60R` after `240` minutes |
| `cap7500_eae240_r060` | `InpStopCapPoints=7500` | close at `-0.60R` after `240` minutes |
| `cap9000_eae240_r060` | `InpStopCapPoints=9000` | close at `-0.60R` after `240` minutes |

`InpStopCapPoints` is a default-off EA input added for this pass. It caps the effective SL distance before SL/TP, cost-R, and lot sizing are calculated. It is not the old stop-ceiling filter, which merely rejected wide-stop entries.

## Partial-Ladder Constraint

The reviewer suggested geometry including partial ladders. Current implementation constraints:

- true partial close is not meaningful at fixed `0.01` lot because broker minimum lot prevents closing a fraction;
- the existing split-entry workaround can force multiple `0.01` tickets and change exposure;
- a three-rung ladder would require a separate EA implementation and exposure-normalization review.

Therefore no partial-ladder result is allowed to compete in this pass. If stop-cap or early-adverse cells materially improve weekly shape while preserving core edge, a separate default-off ladder implementation can be preregistered later.

## Promotion Gates

A cell is only a useful clue if the recomposed hybrid satisfies all of:

- WR `>= 50%`
- average win/loss `>= 2.00`
- active weekday percentage not materially worse than current frontier
- +`$0.30` per ticket stress keeps average win/loss `>= 2.00`, or the report explicitly marks the cell as not promotion-ready
- closed-P&L positive weeks improve over `54.81%`
- worst closed week improves materially versus `$-878.18`
- rolling 4-week positive percentage improves over `63.41%`
- ex-top-1% and ex-top-2% winner removal remains reported

Owner aspiration remains `90%` positive weeks, but this pass is not allowed to claim demo readiness unless the stricter owner target and the core gates are both met. A partial improvement is a research clue only.

## Stop Rule

After this pass, the H4/D1 family is frozen unless a cell shows a clear weekly-shape improvement while preserving the core WR/W-L edge. If all six cells fail, do not continue tuning H4/D1 geometry without external review or a materially new idea.
