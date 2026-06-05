# WR50 Implementation Summary

Document date: 2026-06-04

## Files Added

Added new quarantined lane:

```text
xau-usd/xauusd-wr50-experimental/
```

Key additions:

- `README.md`
- `CODEX_IMPLEMENTATION_SUMMARY.md`
- `docs/WR50_EXPERIMENTAL_LANE_RULES.md`
- `docs/WR50_EA_REGISTRY.md`
- `docs/WR50_MAGIC_NUMBERS.md`
- `docs/WR50_KILL_RULES.md`
- `docs/WR50_REPORTING_POLICY.md`
- `docs/WR50_HYPOTHESIS_TEMPLATE.md`
- `docs/WR50_OWNER_AUTHORIZATION_TEMPLATE.md`
- `docs/WR50_DEPLOYMENT_CHECKLIST.md`
- `docs/WR50_PHASE_BOUNDARY.md`
- `config/wr50_experimental.yaml`
- `config/wr50_blackout_windows.csv`
- `config/wr50_account_allowlist.example.csv`
- `config/wr50_runtime_registry.csv`
- `mt5/Experts/WR50_BreakoutEvening_v0.mq5`
- `mt5/Experts/WR50_BreakoutQuality_v0.mq5`
- `mt5/Experts/WR50_BreakoutExit1R_v0.mq5`
- `mt5/Include/WR50_Common.mqh`
- `mt5/Include/WR50_Types.mqh`
- `mt5/Include/WR50_MagicNumbers.mqh`
- `mt5/Include/WR50_AccountGuard.mqh`
- `mt5/Include/WR50_RiskGuard.mqh`
- `mt5/Include/WR50_SpreadGuard.mqh`
- `mt5/Include/WR50_SessionFilter.mqh`
- `mt5/Include/WR50_BreakoutRetestSignal.mqh`
- `mt5/Include/WR50_OrderExecutor.mqh`
- `mt5/Include/WR50_TradeLogger.mqh`
- `mt5/Include/WR50_FileUtil.mqh`
- `scripts/audit_wr50_boundaries.py`
- `scripts/build_wr50_daily_report.py`
- `scripts/build_wr50_trade_summary.py`
- `scripts/validate_wr50_registry.py`
- `scripts/validate_wr50_logs.py`
- `tests/test_wr50_magic_registry.py`
- `tests/test_wr50_comment_format.py`
- `tests/test_wr50_boundary_audit.py`
- `tests/test_wr50_report_builder.py`
- `outputs/logs/.gitkeep`
- `outputs/ledgers/.gitkeep`
- `outputs/reports/.gitkeep`

Generated reports/logs:

- `outputs/reports/WR50_REGISTRY_VALIDATION.md`
- `outputs/reports/WR50_BOUNDARY_AUDIT.md`
- `outputs/reports/WR50_LOG_VALIDATION.md`
- `outputs/reports/WR50_EXPERIMENTAL_DAILY_REPORT.md`
- `outputs/reports/WR50_EXPERIMENTAL_SUMMARY.csv`
- `outputs/reports/WR50_EA_BREAKDOWN.md`
- `outputs/reports/WR50_MAGIC_ATTRIBUTION_AUDIT.md`
- `outputs/reports/WR50_TRADE_SUMMARY_DETAIL.csv`
- `outputs/reports/compile_BEV0.log`
- `outputs/reports/compile_BQV0.log`
- `outputs/reports/compile_E1R0.log`

## Files Modified

No existing canonical, observed, Phase 0, Phase 1, or Phase 2B source files were modified by this WR50 implementation.

Existing observed EA files touched: no.

Observed-source git status checked clean for:

```text
xau-usd/xauusd-phase1/mt5/Experts/Phase1DryRunShell.mq5
xau-usd/xauusd-phase1/mt5/Experts/Phase2ExperimentalDemoExecutor.mq5
xau-usd/xauusd-phase1/mt5/Include/
xau-usd/xauusd-phase2b-passive-observers/
xau-usd/xauusd-phase0/
```

## Broker-Action Functions Added

WR50 broker action is isolated to:

```text
xau-usd/xauusd-wr50-experimental/mt5/Include/WR50_OrderExecutor.mqh
```

Terms added there:

```text
TRADE_ACTION_PENDING
OrderSend
```

The boundary audit also reports the pre-existing, unmodified quarantined Phase 1 experimental executor:

```text
xau-usd/xauusd-phase1/mt5/Experts/Phase2ExperimentalDemoExecutor.mq5
```

That file was not changed by this work.

## Magic Numbers Assigned

| EA | Short code | Magic range | Active magic |
| --- | --- | --- | ---: |
| `WR50_BreakoutEvening_v0` | `BEV0` | `930000-930099` | `930000` |
| `WR50_BreakoutQuality_v0` | `BQV0` | `930100-930199` | `930100` |
| `WR50_BreakoutExit1R_v0` | `E1R0` | `930200-930299` | `930200` |

## Compile Status

MetaEditor could not compile directly from the repo path because the Windows path with spaces was truncated by MetaEditor as `C:\Users\ZHAO`. A compile-only scratch copy was used instead:

```text
C:\MT5CompileScratch\WR50_20260604\MQL5\
```

Results copied into `outputs/reports/`:

| EA | Log | Result |
| --- | --- | --- |
| `WR50_BreakoutEvening_v0` | `compile_BEV0.log` | `0 errors, 0 warnings` |
| `WR50_BreakoutQuality_v0` | `compile_BQV0.log` | `0 errors, 0 warnings` |
| `WR50_BreakoutExit1R_v0` | `compile_E1R0.log` | `0 errors, 0 warnings` |

No MT5 terminal deployment, chart attachment, or runtime change was performed.

## Safety And Boundary Audit Status

| Check | Status |
| --- | --- |
| WR50 registry validation | PASS |
| WR50 boundary audit | PASS |
| WR50 log validation | PASS |
| Existing observed EA source modification check | PASS |

The WR50 docs preserve:

```text
breakout_retest_family = COST_SUSPENDED_CANONICAL
canonical_phase2_execution = BLOCKED
live_trading = ABSOLUTE NO
```

## Test Status

Command:

```powershell
cd xau-usd\xauusd-wr50-experimental
..\xauusd-phase0\.venv\Scripts\python.exe -m pytest -p no:cacheprovider tests
```

Result:

```text
11 passed
```

## Known Limitations

- MQL5 reads `config/wr50_runtime_registry.csv` only after a human copies it to `MQL5/Files/WR50/wr50_runtime_registry.csv`; it does not parse the repo Markdown registry at runtime.
- Manual blackout windows require copying a CSV into `MQL5/Files/WR50/`; if absent, the EA logs `blackout_file_not_loaded` and relies on the rollover blackout.
- The MQL5 ledger records startup, signal, block, and order-placement rows. Full exit metrics should be completed from MT5 exported account history or broker history CSVs in the report scripts.
- The first v0 signal module is mechanical and intentionally untuned. Any parameter change after deployment should become a new EA version.

## Next Human Steps

1. Review this lane for source isolation and demo-only guard behavior.
2. Fill a real owner authorization file outside the template.
3. Copy `config/wr50_runtime_registry.csv` to `MQL5/Files/WR50/wr50_runtime_registry.csv`.
4. Optionally copy an account allowlist and blackout CSV to `MQL5/Files/WR50/`.
5. Compile in the target demo-only MT5 environment.
6. Attach only to an approved demo chart after review.
7. Confirm the first attempted order has the expected magic/comment and hard SL/TP.
8. Build daily WR50 reports before interpreting any result.

## Final Boundary Statement

The WR50 lane is demo-only win-rate research. It does not authorize canonical Phase 2, does not authorize live trading, does not touch existing observed EAs, and does not reactivate canonical `breakout_retest` execution.

