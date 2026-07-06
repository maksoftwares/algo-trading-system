# A1 XAU M5 Momentum Step 1 Split-Shape Grid Pre-Registration

Date: 2026-07-05

Scope: owner goal Step 1 for GOLD/XAUUSD. This document is written before running the new grid. It freezes the only allowed split-entry family refinement pass for the current 50%+ WR / 2:1 realized W/L / daily-activity goal.

## Goal Metrics

All headline metrics must be reported at signal level, where one split-entry decision is one signal even when it creates multiple tickets.

- Signal win rate: winning signals / closed signals.
- Realized money W/L: average winning signal P&L / absolute average losing signal P&L, in tester account currency after exits.
- Daily activity: market days with at least one kept signal / total market days in the exam window.
- Supporting metrics: PF, net, max closed drawdown, active days, last-12-month standalone metrics, top-winner-removal stress, and +$0.10 / +$0.30 per-ticket slippage stress.

## Fixed Exam Window

- Exact MT5 Strategy Tester only, isolated root: `C:\MT5A1M5MomentumBacktest`.
- Symbol/timeframe: `XAUUSD`, `M5`.
- Exam period: `2022.07.01 -> 2026.06.30`.
- Model: MT5 every tick / tester history quality from each MT5 report.
- Runtime boundary: no live/demo runtime terminal, profile, chart, preset, order, or position may be changed by this grid.

## Frozen Entry Substrate

The grid uses the three existing split-entry components and only changes the declared split-shape inputs below.

Priority stack for composed signal book:

1. `risk_norm_split20_v6_max2_all8`
2. `risk_norm_split20_freq_weak_hours_all8`
3. `risk_norm_split20_v13_rr0p7_all8_22`

Composition rule: if multiple components signal the same direction within the same M5 decision window, keep the highest-priority component and publish the kept/dropped lists. No outcome information may enter dedupe.

Fixed shared inputs:

- `InpSplitEntryEnabled=true`
- `InpSplitEntryShadowOnly=false`
- `InpSplitEntryFirstTargetR=0.70`
- `InpSplitEntryUseMinLotPair=true`
- `InpRiskAmountUsd=10.00`
- `InpMaxRiskLots=0.05`
- `InpManagementLogMode=0` for tester speed only; this does not change entries, exits, stops, or targets.

## Declared Grid

Axes:

- TP1 lot fraction: `1/3`, `1/2`, `2/3`.
- Runner target: `2.0R`, `2.5R`, `3.0R`.
- Runner breakeven timing:
  - `be_tp1`: move runner SL to breakeven only when TP1 closes at TP.
  - `be_1r`: move runner SL to breakeven at +1.0R.
  - `be_never`: never move runner SL to breakeven.

Cell IDs:

| Cell | TP1 lot fraction | Runner target | BE timing |
| --- | ---: | ---: | --- |
| `f33_r20_be_tp1` | 1/3 | 2.0R | on TP1 fill |
| `f33_r20_be_1r` | 1/3 | 2.0R | at +1.0R |
| `f33_r20_be_never` | 1/3 | 2.0R | never |
| `f33_r25_be_tp1` | 1/3 | 2.5R | on TP1 fill |
| `f33_r25_be_1r` | 1/3 | 2.5R | at +1.0R |
| `f33_r25_be_never` | 1/3 | 2.5R | never |
| `f33_r30_be_tp1` | 1/3 | 3.0R | on TP1 fill |
| `f33_r30_be_1r` | 1/3 | 3.0R | at +1.0R |
| `f33_r30_be_never` | 1/3 | 3.0R | never |
| `f50_r20_be_tp1` | 1/2 | 2.0R | on TP1 fill |
| `f50_r20_be_1r` | 1/2 | 2.0R | at +1.0R |
| `f50_r20_be_never` | 1/2 | 2.0R | never |
| `f50_r25_be_tp1` | 1/2 | 2.5R | on TP1 fill |
| `f50_r25_be_1r` | 1/2 | 2.5R | at +1.0R |
| `f50_r25_be_never` | 1/2 | 2.5R | never |
| `f50_r30_be_tp1` | 1/2 | 3.0R | on TP1 fill |
| `f50_r30_be_1r` | 1/2 | 3.0R | at +1.0R |
| `f50_r30_be_never` | 1/2 | 3.0R | never |
| `f67_r20_be_tp1` | 2/3 | 2.0R | on TP1 fill |
| `f67_r20_be_1r` | 2/3 | 2.0R | at +1.0R |
| `f67_r20_be_never` | 2/3 | 2.0R | never |
| `f67_r25_be_tp1` | 2/3 | 2.5R | on TP1 fill |
| `f67_r25_be_1r` | 2/3 | 2.5R | at +1.0R |
| `f67_r25_be_never` | 2/3 | 2.5R | never |
| `f67_r30_be_tp1` | 2/3 | 3.0R | on TP1 fill |
| `f67_r30_be_1r` | 2/3 | 3.0R | at +1.0R |
| `f67_r30_be_never` | 2/3 | 3.0R | never |

Each cell has three MT5 component variants named:

`goal_split_{cell_id}_{component}`, where component is `v6`, `weak`, or `v13`.

Total declared exact MT5 component runs: `27 cells * 3 components = 81`.

## Broker-Minimum-Lot Interpretation

XAUUSD broker minimum lot can make exact fractional sizing impossible at tiny risk sizes. The EA must use broker-valid lots:

- `1/3` TP1 fraction maps to a minimum-lot fallback of `0.01 TP1 / 0.02 runner`.
- `1/2` TP1 fraction maps to `0.01 TP1 / 0.01 runner`.
- `2/3` TP1 fraction maps to `0.02 TP1 / 0.01 runner`.

This changes practical exposure by cell and must be reported honestly in the exposure section. It is not a reason to normalize the metrics away from realized account-currency P&L.

## Required Outputs

- MT5 component report and trade/order/signal CSVs for every attempted component.
- Full component-run ledger: attempted, completed, failed, timed out, elapsed seconds, trade count, history quality, and file paths.
- Composed-cell frontier report with the top 3-5 cells and all 27 cell rows.
- Kept-signal CSV and dropped-signal CSV for every composed cell.
- Last-12-month standalone section for every near-miss and every top cell.
- Slippage stress section at +$0.10 and +$0.30 per ticket.
- Hash manifest for this spec, EA source, runner, and analyzer.

## Kill Rules

- No new parameter, threshold, hour, session, direction, or component changes inside this Step 1 grid.
- If a component times out, improve tester tooling/logging only; do not change strategy logic to make the result look better.
- After this grid is published, the split-entry family is frozen for this goal unless an independent reviewer explicitly rejects a mechanical implementation error.
