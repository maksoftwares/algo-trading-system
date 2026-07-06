# A1 XAU M5 External Macro Traffic-Light Gate Preregistration

Date: 2026-07-05

Purpose: test whether a small causal external macro gate can lift existing exact-MT5 XAU trade streams toward the owner core shape: realized average win / average loss >= 2.0 and win rate >= 50%. Daily frequency remains reported, not hidden.

Boundary:
- Diagnostic only. It uses exact MT5 Strategy Tester trade CSV outcomes already produced in the isolated tester lane.
- No live/demo chart, order, position, preset, profile, or broker runtime is touched.
- No reviewer token is spent unless an exam-window row reaches the owner core shape.

Data policy:
- External files are local Yahoo/FRED-style daily proxies already present in the repo.
- Daily observations are usable only from the next calendar date. For an entry on date D, the gate can see only observations with `date_utc <= D - 1`.
- This deliberately avoids relying on MT5 server timezone precision.

External feature families:
- Gold trend: GLD 5-day and 20-day percentage change.
- Miner confirmation: GDX/GLD 20-day percentage change.
- Rates/dollar pressure: TLT/UUP and TLT/SHY 20-day percentage change.
- Real asset rotation: USO/UUP, HG/GC, and SLV/GLD 20-day score.
- Haven/liquidity: GLD, GDX/GLD, and SPY/TLT 20-day score.

Frozen gate set:
- `all_trades`
- `gold20_directional`
- `gold5_directional`
- `miners20_directional`
- `rates20_directional`
- `real_asset20_directional`
- `haven20_directional`
- `traffic_green_3of4`
- `traffic_green_or_amber_2of4`
- `gold_and_rates`
- `gold_and_miners`
- `gold_rates_miners`

Family set:
- RR2 long-only baseline, no profit lock.
- RR2 profit-lock `rr2_lock100_010`.
- RR2 profit-lock `rr2_lock080_010`.
- Opening-range reversal `orrev_london_firm_stop15`.
- Opening-range reversal `orrev_london_firm_stop10`.
- Opening-range reversal `orrev_london_loose_stop15`.

Selection rule:
- Design window: 2016-01-01 through 2021-12-31.
- Exam window: 2022-07-01 through 2026-06-30.
- Rank design rows by core-shape pass, then near-shape status, then win rate, W/L, active-day percentage, profit factor, and manual P&L.
- Freeze the best two non-`all_trades` gates per family for the exam report. `all_trades` is retained as baseline context.

Reviewer spend rule:
- Do not spend the daily reviewer token unless an exam row reaches WR >= 50% and realized W/L >= 2.0.
- If a row reaches core shape but fails daily frequency, package it as a frequency-gap clue, not demo-ready.
