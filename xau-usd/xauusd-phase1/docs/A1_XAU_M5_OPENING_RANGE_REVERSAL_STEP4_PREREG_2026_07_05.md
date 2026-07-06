# A1 XAU M5 Opening-Range Reversal Step 4 Preregistration

Generated UTC: `2026-07-05T06:58:15Z`

Purpose: continue the owner GOLD/XAUUSD goal after Step 1 split-shape, Step 2 internal gating, A3 RR2, RR2 causal-filter diagnostic, and V9/V10 RR2 stretch all failed to reach the core shape. This is a new high-hit-rate entry-family probe, not another RR2 retune of the old momentum families.

Owner target:

- Signal-level win rate `>=50%`.
- Realized average winning signal / average losing signal `>=2.0`.
- Daily activity target `100%`; `90%+` is worth showing only if the first two conditions hold.

Runtime boundary:

- Exact MT5 Strategy Tester only in isolated root `C:\MT5A1M5MomentumBacktest`.
- No live/demo runtime terminal, chart, preset, order, position, or broker-action state may be touched.
- Python is orchestration/reporting only; headline metrics come from MT5 trade ledgers parsed manually.

Code change:

- Add `SIGNAL_OPENING_RANGE_REVERSAL = 6` to `A1XauM5MomentumContinuationExecutor.mq5`.
- Defaults remain unchanged; the new mode is inactive unless the tester input explicitly sets `InpSignalMode=6`.
- Signal: after a fixed opening range completes, fade a sweep beyond the range only if the completed M5 bar closes back inside the range with rejection body/close-location confirmation. Entries remain next-tick Strategy Tester market orders through the existing EA execution path.

Design/exam separation:

- Design window: `2016.01.01 -> 2021.12.31`.
- Exam window: `2022.07.01 -> 2026.06.30`.
- Select at most the top three design rows for exam. Selection is mechanical: owner-core hits first, then near-core rows, then highest score from WR/W-L/activity/PF. No exam-window metric may influence selection.
- If MT5 lacks usable 2016-2021 XAUUSD history, record `DESIGN_HISTORY_UNAVAILABLE` and stop the branch rather than redesigning on the exam window.

Fixed 12-cell design grid:

| Session | Range | Trade window | Strictness | Stop | Shared settings |
| --- | ---: | ---: | --- | --- | --- |
| Asia, server hour `2` | `120m` | `6h` | loose | `1.0 ATR` | RR `2.0`, fixed `0.01`, max cost R `0.08`, no HTF filter |
| Asia, server hour `2` | `120m` | `6h` | loose | `1.5 ATR` | same |
| Asia, server hour `2` | `120m` | `6h` | firm | `1.0 ATR` | same |
| Asia, server hour `2` | `120m` | `6h` | firm | `1.5 ATR` | same |
| London, server hour `7` | `60m` | `5h` | loose | `1.0 ATR` | same |
| London, server hour `7` | `60m` | `5h` | loose | `1.5 ATR` | same |
| London, server hour `7` | `60m` | `5h` | firm | `1.0 ATR` | same |
| London, server hour `7` | `60m` | `5h` | firm | `1.5 ATR` | same |
| NY, server hour `13` | `60m` | `5h` | loose | `1.0 ATR` | same |
| NY, server hour `13` | `60m` | `5h` | loose | `1.5 ATR` | same |
| NY, server hour `13` | `60m` | `5h` | firm | `1.0 ATR` | same |
| NY, server hour `13` | `60m` | `5h` | firm | `1.5 ATR` | same |

Strictness definitions:

- Loose: `InpOpeningBreakAtrMultiple=0.05`, `InpReclaimAtrMultiple=0.00`, `InpMinRangeAtr=0.30`, `InpMinBodyFraction=0.25`, `InpLongCloseLocation=0.55`, `InpShortCloseLocation=0.45`.
- Firm: `InpOpeningBreakAtrMultiple=0.10`, `InpReclaimAtrMultiple=0.05`, `InpMinRangeAtr=0.40`, `InpMinBodyFraction=0.35`, `InpLongCloseLocation=0.60`, `InpShortCloseLocation=0.40`.

Shared execution settings:

- `InpSignalMode=6`.
- `InpDirectionMode=0`.
- `InpRiskReward=2.00`.
- `InpMaxEstimatedCostR=0.08`.
- `InpMaxSpreadPoints=75`.
- `InpStopFloorPoints=250`.
- `InpStopCeilingPoints=1400`.
- `InpMaxTradesPerDay=24`.
- `InpCooldownMinutes=0`.
- `InpOnePositionPerMagic=true`.
- `InpAllowDemoTrading=true` only inside Strategy Tester.
- Tester deposit/currency: `1000 USD`.

Reviewer spend rule:

- Do not ask the reviewer unless an exam row reaches at least the owner core shape: WR `>=50%` and realized W/L `>=2.0`.
- If an exam row reaches core shape but daily activity is below `90%`, package it as `CORE_SHAPE_HIT_FREQUENCY_GAP` and ask reviewer only after the full ledger, last-12-months metrics, top-winner removal, and active-day analysis are present.
- If no exam row reaches core shape, record the frontier and continue without reviewer spend.
