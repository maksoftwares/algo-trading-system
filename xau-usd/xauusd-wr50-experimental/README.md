# WR50 Experimental Demo EA Lane

Document date: 2026-06-04

This folder is a quarantined WR50 research lane for demo-only win-rate experiments. It is separate from the canonical Phase 1 dry-run shell, the existing experimental demo executor, Phase 2B passive observers, and Phase 0/Phase 0R research artifacts.

## Boundary

- WR50 EAs are demo-experiment only.
- WR50 results do not authorize canonical Phase 2.
- WR50 results do not authorize live trading.
- WR50 results do not reactivate `breakout_retest` canonical execution.
- The canonical `breakout_retest_family` state remains `COST_SUSPENDED_CANONICAL`.
- Canonical Phase 2 broker-side execution remains `BLOCKED`.
- Live trading remains `ABSOLUTE NO`.

## Contents

| Path | Purpose |
| --- | --- |
| `docs/` | Lane rules, registry, magic numbers, kill rules, reporting policy, deployment checklist, and owner templates. |
| `config/` | YAML lane config, blackout windows, account allowlist example, and runtime registry CSV for MT5 file-sandbox use. |
| `mt5/Experts/` | WR50 experimental demo EAs and safe-by-default review presets. |
| `mt5/Include/` | Shared MQL5 guards, signal module, logger, and order executor. |
| `scripts/` | Boundary audit, registry validation, log validation, and reporting scripts. |
| `tests/` | Focused pytest coverage for the WR50 lane. |
| `outputs/` | Generated logs, ledgers, and reports. |

## First EAs

| EA | Short code | Magic | Purpose |
| --- | --- | ---: | --- |
| `WR50_BreakoutEvening_v0` | `BEV0` | `930000` | Evening/night breakout-retest subset, TP 1.5R. |
| `WR50_BreakoutQuality_v0` | `BQV0` | `930100` | Stricter breakout/retest quality filter, TP 1.5R. |
| `WR50_BreakoutExit1R_v0` | `E1R0` | `930200` | Baseline breakout-retest with shorter TP 1.0R. |
| `WR50_BreakoutWideStop_v0` | `WST12` | `930300` | Same breakout-retest entries, minimum 375-point stop, TP 1.2R. |
| `WR50_BreakoutWideStop_v0` | `WST15` | `930400` | Same breakout-retest entries, minimum 375-point stop, TP 1.5R. |
| `WR50_BreakoutPartialBE_v0` | `PBE0` | `930500` | Reserved and disabled pending partial-close safety review. |

## 2026-06-09 Improvement Brief

The active improvement experiment is de-dilution plus wide-stop A/B testing:

- Existing demo EAs remain the control and must not be edited to produce the treatment result.
- `WST12` and `WST15` reuse the shared `WR50_BreakoutRetestSignal.mqh` entry logic, then widen only the stop and recompute the target.
- The promotion KPI is net R after measured cost, not win rate alone.
- No variant can be promoted before at least 150 fresh closed trades.
- `PartialBE` is reserved but not enabled in this slice because 0.01 fixed-lot partial close may be broker-volume-infeasible and introduces `PositionModify` / partial `PositionClose` behavior.

## Safe Defaults

The EAs compile with safe defaults. They do not trade unless the owner explicitly changes runtime inputs:

```text
InpExperimentalDemoOnly = true
InpAllowDemoTrading = false
InpRequireRuntimeRegistryFile = true
InpOwnerAuthorizationToken = ""
```

Startup hard-fails on non-demo accounts, missing runtime registry, invalid magic numbers, wrong symbol, unknown/real/live server text, blocked margin mode, missing authorization, or disabled registry status.

## Runtime Registry

MQL5 cannot reliably read repo Markdown files from the terminal sandbox. Copy the CSV registry into the terminal data folder before enabling demo trading:

```text
<MQL5 data folder>/MQL5/Files/WR50/wr50_runtime_registry.csv
```

Source file in this repo:

```text
config/wr50_runtime_registry.csv
```

## Validation

From the repo root:

```powershell
cd xau-usd\xauusd-wr50-experimental
..\xauusd-phase0\.venv\Scripts\python.exe -m pytest tests
..\xauusd-phase0\.venv\Scripts\python.exe scripts\validate_wr50_registry.py
..\xauusd-phase0\.venv\Scripts\python.exe scripts\audit_wr50_boundaries.py
..\xauusd-phase0\.venv\Scripts\python.exe scripts\validate_wr50_logs.py
..\xauusd-phase0\.venv\Scripts\python.exe scripts\build_wr50_daily_report.py
```

## Human Review Required

Only after human review should any WR50 EA be copied to MT5 and attached to a demo chart. The reviewer must confirm no existing observed EA changed, the account is demo-only, magic/comment attribution is correct, every order has hard SL/TP, and reports can separate each EA.
