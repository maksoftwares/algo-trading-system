# A1 XAU M5 RR2 Profit-Lock Management Probe Preregistration

Generated UTC: `2026-07-05T07:42:20Z`

Purpose: test whether asymmetric trade management can lift the known RR2 long-only A1 momentum baseline toward the owner target without repeating another entry grid. This is diagnostic research only unless an exam row reaches the owner core shape and survives a later full robustness packet.

Runtime boundary:

- Exact MT5 Strategy Tester only in isolated root `C:\MT5A1M5MomentumBacktest`.
- No live/demo runtime terminal, chart, preset, order, position, or broker-action state may be touched.
- Python is orchestration/reporting only; headline metrics come from MT5 trade ledgers parsed manually.

Base entry frozen from the existing RR2 long-only row:

- `InpDirectionMode=1`
- `InpUseH1TrendFilter=true`
- `InpUseH4TrendFilter=true`
- `InpH1TrendMinSlopePoints=0`
- `InpH4TrendMinSlopePoints=0`
- `InpMinAtrAbsoluteForEntry=1.5`
- `InpBlockedEntryHoursCsv=9,10`
- `InpRiskReward=2.00`
- Fixed `0.01` lots, tester deposit/currency `1000 USD`

Design/exam separation:

- Design window: `2016.01.01 -> 2021.12.31`.
- Exam window: `2022.07.01 -> 2026.06.30`.
- Select at most the top three design rows for exam. Selection is mechanical: owner-core hits first, then near-core rows, then highest score from WR/W-L/activity/PF/net.
- Exam metrics cannot influence selection.

Fixed management cells:

| Variant | Trigger | Locked profit | Notes |
| --- | ---: | ---: | --- |
| `rr2_baseline_no_lock` | n/a | n/a | exact baseline behavior |
| `rr2_lock080_010` | `+0.80R` | `+0.10R` | earlier small positive stop |
| `rr2_lock080_020` | `+0.80R` | `+0.20R` | stronger early positive stop |
| `rr2_lock100_010` | `+1.00R` | `+0.10R` | later small positive stop |
| `rr2_lock100_020` | `+1.00R` | `+0.20R` | later stronger positive stop |
| `rr2_lock125_025` | `+1.25R` | `+0.25R` | conservative trigger; protects only clearer moves |

Reviewer spend rule:

- Do not ask reviewer unless an exam row reaches WR `>=50%` and realized average win / average loss `>=2.0`.
- If a row reaches core shape but active days are below `90%`, package it as `CORE_SHAPE_HIT_FREQUENCY_GAP` only after full ledgers, last-12-months metrics, top-winner removal, and daily coverage are present.
- If no row reaches core shape, record frontier and continue without reviewer spend.
