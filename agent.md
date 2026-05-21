# Agent Handoff

Last updated: 2026-05-21

## Workspace

- Root: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system`
- Active package: `xau-usd\xauusd-phase0`
- Current branch: `main`
- Remote: `https://github.com/maksoftwares/algo-trading-system.git`

## Standing Rules

- Do not add live EA trade execution until Phase 0 real-data gates approve an expert.
- No `OrderSend`, `OrderSendAsync`, `CTrade`, `trade.Buy`, `trade.Sell`, or position-opening logic in Phase 0.
- Keep all MT5 tools passive: file export, logging, or diagnostics only.
- Prefer generated manifests, snapshots, and hashable artifacts over informal notes.
- Do not push unless explicitly asked.

## Current State

- Latest committed acquisition helper: `generate-mt5-bar-presets`.
- Passive MT5 tools exist for spread logging and historical bar export.
- Synthetic workflow is passing mechanically but all prototype experts still fail the consolidated verdict.
- Real-data readiness is blocked because broker bar CSVs are not present.
- Latest known import status: `0 imported, 25 missing, 0 failed`.

## Key Commands

```powershell
cd xau-usd\xauusd-phase0
.\.venv\Scripts\phase0.exe generate-data-requirements
.\.venv\Scripts\phase0.exe generate-mt5-bar-presets
.\.venv\Scripts\phase0.exe import-required-bars --fail-on-missing
.\.venv\Scripts\phase0.exe check-data-availability
.\.venv\Scripts\phase0.exe run-all
.\.venv\Scripts\phase0.exe run-all --synthetic-sample
.\.venv\Scripts\phase0.exe audit-safety
.\.venv\Scripts\python.exe -m pytest
```

## Remaining Gates Before Live EA Coding

1. Export or acquire required OHLC bar CSVs for all broker/symbol/timeframe sets.
2. Place CSVs under `xau-usd\xauusd-phase0\data\raw\{broker}\`.
3. Run `import-required-bars --fail-on-missing` and fix missing, malformed, overlap, gap, identity, or coverage blockers.
4. Run `check-data-availability` until all 25 required timeframe sets pass.
5. Run the full real-data Phase 0 workflow and generate a fresh verdict/snapshot.
6. Only if at least one expert has a full PASS, freeze the Phase 1 EA implementation spec and begin live EA coding.

## Current Recommendation

Use the generated MT5 presets in `outputs\mt5_bar_export_presets\` to produce the missing broker bar files, then rerun the strict import and availability gates.
