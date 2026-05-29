# H1 CYB/UUP Yuan-Dollar FX Rotation Follow-Through v0 Data Blocker

Status: BLOCKED_DATA_COVERAGE
Hypothesis: `docs/hypothesis_h1_cyb_uup_yuan_dollar_fx_rotation_followthrough_v0.md`
Research hash: `bd890fec915d7a13546c333698c1c96267fb3c092ca57055608aa3e72279474a`
Data proxy: `data/reference/etf/cyb_uup_daily_yahoo_2015_2025.csv`
Rows acquired: 2,222

## Decision

Do not run a partial matrix and do not infer edge from incomplete data.

The public Yahoo CYB/UUP proxy only covers through `2023-10-30T13:30:00+00:00`, while the Phase 0 matrix requires coverage through `2024-12-31T23:59:59+00:00`.

## Command Result

```text
Configuration error:
h1_cyb_uup_yuan_dollar_fx_rotation_followthrough_v0 CYB/UUP data
end 2023-10-30T13:30:00+00:00, but required 2024-12-31T23:59:59+00:00.
```

## Interpretation

The idea remains untested rather than rejected. It needs a better yuan-dollar data source before any result-producing run. Because the current candidate hunt is looking for immediately testable EAs, the correct action is to mark this lane blocked and move on.
