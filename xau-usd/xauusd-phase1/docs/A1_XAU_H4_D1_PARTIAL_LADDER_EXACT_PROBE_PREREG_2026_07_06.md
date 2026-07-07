# A1 XAU H4/D1 Partial-Ladder Exact Probe Preregistration

Generated UTC: `2026-07-06T10:49:47Z`

## Purpose

Test the reviewer's remaining H4/D1 shape idea with exact MT5 evidence: convert rare H4/D1 tail wins into medium banked wins, then recombine with the current best hybrid and measure closed-P&L week shape.

This is a narrow mechanism probe, not a new optimization pass. No live/demo runtime, chart, preset, order, position, or broker-action state may be touched. Runs must use isolated MT5 Strategy Tester root `C:\MT5A1M5MomentumBacktest`.

## Baseline Recomposition

Use the current best exact-ledger hybrid as the baseline:

- `A1_XAU_HYBRID_F67_H16_NO_F33_COMPOSITION_202207_202606`
- baseline best source replaced: `h4_d1_long_best_box2_atr80`
- already removed source: `step1_f33_r30_be_never`

The new H4/D1 replacement rows must be exact MT5 Strategy Tester rows from `2022.07.01 -> 2026.06.30`.

## Fixed H4/D1 Signal Inputs

All cells use the previously selected H4/D1 source shape:

- `InpSignalMode=7`
- `InpDirectionMode=1`
- `InpUseH1TrendFilter=false`
- `InpUseH4TrendFilter=false`
- `InpRiskReward=2.00`
- `InpMaxEstimatedCostR=0.15`
- `InpStopCeilingPoints=0`
- `InpStopCapPoints=0`
- `InpMaxTradesPerDay=6`
- `InpCooldownMinutes=0`
- `InpOnePositionPerMagic=false`
- `InpMaxOpenPositionsPerMagic=32`
- `InpD1CompressionAtrPercentileMax=80.00`
- `InpD1CompressionBoxDays=2`
- `InpD1CompressionRangeMedianMax=1.50`
- `InpD1CompressionH4MinBodyFraction=0.35`

## Preregistered Cells

| Cell | MT5 lot | Normalizer | Partial | Runner | BE after partial |
| --- | ---: | ---: | --- | --- | --- |
| `p33_t2_run4_be` | `0.03` | `/3` | bank `1/3` at `+2.0R` | close rest at `+4.0R` | yes |
| `p33_t2_run4_nobe` | `0.03` | `/3` | bank `1/3` at `+2.0R` | close rest at `+4.0R` | no |
| `p50_t3_run6_be` | `0.02` | `/2` | bank `1/2` at `+3.0R` | close rest at `+6.0R` | yes |
| `p50_t3_run6_nobe` | `0.02` | `/2` | bank `1/2` at `+3.0R` | close rest at `+6.0R` | no |

Rationale: the first pair tests the reviewer's `1/3 at +2R` ladder using one banked partial and a finite runner; the second pair tests the reviewer's `1/2 at +3R` ladder. Lot multipliers are only used because MT5 cannot partially close below `0.01`; all signal P&L must be normalized back to baseline `0.01` exposure before evaluation. The MT5 input for the one-third partial may use `InpPartialFraction=0.34` solely to force broker-lot rounding to close `0.01` from a `0.03` position; the effective evaluated fraction remains `1/3`.

## Required Parsing Rule

The headline ledger must be reconstructed from the EA deal log keyed by `DEAL_POSITION_ID`, not from the old FIFO HTML trade parser. Each original MT5 position is one signal:

- sum all `DEAL_ENTRY_OUT` profit, commission, and swap for the position;
- normalize total P&L by the cell normalizer;
- entry time is the `DEAL_ENTRY_IN` time;
- exit time is the final `DEAL_ENTRY_OUT` time;
- direction comes from the entry deal;
- positions still open at the tester end are excluded from the closed-P&L ledger and reported separately; positions with partial exits but no final exit are also excluded from signal metrics.

## Gates

For the recomposed book, report:

- WR;
- realized average win / average loss;
- active weekday percentage;
- PF, net, max closed drawdown;
- `+$0.30` per normalized signal stress W/L;
- closed-P&L positive week percentage by final exit date;
- worst week, rolling 4-week positive percentage, positive month percentage, worst month, June 2026;
- ex-top-1% and ex-top-2% winner removal.

Decision:

- `OWNER_WEEKLY90_HIT_REVIEW_REQUIRED` only if WR `>=50%`, W/L `>=2.0`, stress W/L `>=2.0`, active days `>=90%`, and positive weeks `>=90%`.
- `WEEKLY_SHAPE_CLUE_NOT_DEMO_READY` only if WR/W-L/stress hold and weekly shape materially improves over baseline.
- Otherwise reject. No demo spec from this probe unless reviewer and owner explicitly approve.

## Budget

Exactly four cells. No additions after seeing results.
