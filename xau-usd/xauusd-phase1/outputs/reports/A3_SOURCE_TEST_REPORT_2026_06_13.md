# A3 Source Test Report

Overall status: PASS

## Global Boundaries

- A3 demo account login: `1033669`.
- Demo only. No live trading. Canonical Phase 2 status unchanged.
- A2 (`1033030`) was not touched.
- A1 (`1025742`) was not touched by T4.
- Committed defaults remain non-executing.
- Locked hypotheses were not edited.

## Test Command

`..\xauusd-phase0\.venv\Scripts\python.exe -m pytest tests\test_a3_executors_source.py tests\test_a3_executor_presets.py`

Result: `14 passed`.

## Gate Coverage

- Non-executing committed defaults.
- Magic bands `933000-933099` and `933100-933199`; reserved `933200-933299`.
- No committed A3 preset with `InpBrokerActionAllowed=true`.
- A3 login allowlist `1033669`.
- Demo marker plus live/real refusal.
- Shared `A3_KILL.txt` kill switch.
- EA-T1 impulse formula and raw-value logging.
- EA-T2 `STRUCT_FILTER_BLOCK` and no impulse-veto residue.
- Required reason codes.
- GV mutex claim before `OrderSend`.
- No `PositionClose`, `PositionModify`, or `OrderDelete`.
- XAUUSD-only scope.
- Locked G3/G4/G5 constants.
- Hypothesis manifest hashes match files.
