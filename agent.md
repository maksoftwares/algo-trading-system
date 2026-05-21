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
- Phase 1 currently means dry-run shell only: telemetry, lifecycle, risk, router contracts, and blocked reasons.
- Prefer generated manifests, snapshots, and hashable artifacts over informal notes.
- Do not push unless explicitly asked.

## Current State

- Latest committed acquisition helper: `generate-mt5-bar-presets`.
- Passive MT5 tools exist for spread logging and historical bar export.
- MT5 passive exports and public Dukascopy acquisition are complete for the Phase 0 required bar set.
- Latest bar import status: `25 imported, 0 missing, 0 failed`.
- Latest data readiness status: `PASS`, `25/25` required timeframe sets ready.
- Fresh post-review real-data `run-all` completed successfully on 2026-05-21 after hypothesis completion and re-registration:
  - Matrix output sets: 27.
  - Decile files: 3.
  - Multisymbol summaries: 3.
  - Adversarial packets: 3.
  - Aggregation files: 3.
- Latest verdict: no expert has a full final PASS yet.
  - `breakout_retest` passed automated 9-cell, decile, multisymbol, and hash gates, but remains `PENDING` on manual adversarial review.
  - `trend_pullback` and `range_mr` are rejected by the current Phase 0 verdict.
- Audit correction: the previous real-data run is exploratory evidence only because the registered hypothesis files still contained placeholder text when the run was produced.
- Do not treat automated PASS as final PASS until hypothesis completeness, fresh hash registration, rerun evidence, manual adversarial review, and review bundle are complete.
- Reviewer-prompt cleanup now includes reference validation, true-holdout run context manifests, intrabar ambiguity reporting, review-bundle generation, and real-artifact verification.
- Latest snapshot: `xau-usd\xauusd-phase0\outputs\snapshots\phase0_snapshot_20260521_111442.zip`.
- Latest result manifest: `xau-usd\xauusd-phase0\outputs\manifests\PHASE0_RESULT_MANIFEST.csv`.
- Latest review bundle: `xau-usd\xauusd-phase0\outputs\review_bundles\PHASE0_REVIEW_BUNDLE_20260521_111406.zip`.
- Verification after code changes: `128 passed`; safety audit OK.
- `verify-real-artifacts` currently returns FAIL only because `PHASE0_VERDICT.md` still contains pending manual-review states; all structural artifact checks pass or are documented.
- Phase 1 dry-run shell is started under `xau-usd\xauusd-phase1`; it has no approved expert module and keeps `breakout_retest` blocked until Gate 9 is complete.

## Local MT5 Discovery

- Standard install: `C:\Program Files\MetaTrader 5\terminal64.exe`.
- Portable clone: `C:\Users\ZHAO ZHU INFORMATION\Documents\Codex\2026-04-18-open-metatrader\mt5portable_clone\terminal64.exe`.
- Portable Gold Mission install: `C:\MT5PortableGoldMission\terminal64.exe`.
- Terminal data roots:
  - `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075` -> standard install.
  - `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\FB0D851E25D6B0EABBB1517331AB5827` -> portable clone.
  - `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\FDAC074599BBCDE0F5549DAB937D2E01` -> `C:\MT5PortableGoldMission`.
- Capital.com bars were exported through the passive MT5 script from `C:\MT5PortableGoldMission` for XAUUSD, EURUSD, and USDJPY across M5, M15, H1, H4, D1.
- Pepperstone XAUUSD bars were exported through the passive MT5 script from the standard MT5 install across M5, M15, H1, H4, D1.
- Raw MT5 exports are staged under:
  - `xau-usd\xauusd-phase0\data\raw\capital_com\`
  - `xau-usd\xauusd-phase0\data\raw\pepperstone\`
- MT5 binary history caches were not parsed directly; they were only used to identify promising coverage and broker installs.
- No local Dukascopy MT5/cache source was found. Dukascopy XAUUSD was acquired through the public Dukascopy feed via `dukascopy-node`.
- Dukascopy M15 was derived from acquired Dukascopy M5 bars and normalized as `XAUUSD_dukascopy_M15_20220101_20250101.csv`.
- Hugging Face is authenticated as `wierdali`; it can help with remote compute/artifact storage, but dataset search did not find a high-confidence XAUUSD/Dukascopy broker-history replacement.

## Key Commands

```powershell
cd xau-usd\xauusd-phase0
.\.venv\Scripts\phase0.exe generate-data-requirements
.\.venv\Scripts\phase0.exe generate-mt5-bar-presets
.\.venv\Scripts\phase0.exe validate-reference
.\.venv\Scripts\phase0.exe validate-hypotheses-complete
.\.venv\Scripts\phase0.exe hash-hypotheses --register --force
.\.venv\Scripts\phase0.exe import-required-bars --fail-on-missing
.\.venv\Scripts\phase0.exe check-data-availability
.\.venv\Scripts\phase0.exe run-all
.\.venv\Scripts\phase0.exe run-all --synthetic-sample
.\.venv\Scripts\phase0.exe audit-safety
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\phase0.exe generate-snapshot
.\.venv\Scripts\phase0.exe score-adversarial-review --expert breakout_retest
.\.venv\Scripts\phase0.exe generate-intrabar-ambiguity-report --expert breakout_retest
.\.venv\Scripts\phase0.exe generate-review-bundle
.\.venv\Scripts\phase0.exe verify-real-artifacts
cd ..\xauusd-phase1
..\xauusd-phase0\.venv\Scripts\python.exe scripts\audit_phase1_safety.py
..\xauusd-phase0\.venv\Scripts\python.exe -m pytest tests
```

## Remaining Gates Before Live EA Coding

1. Complete the hypothesis files and run `validate-hypotheses-complete`.
2. Re-register hypothesis hashes before any new real-data run.
3. Rerun Phase 0 real-data workflow; old real-data outputs stay exploratory.
4. Complete and score Gate 9 manual adversarial review for `breakout_retest`.
5. Generate intrabar ambiguity reports and the review bundle for third-party inspection.
6. Run `verify-real-artifacts` and resolve any FAIL findings.
7. Only after the final verdict becomes PASS should Phase 1 dry-run EA work begin.

## Current Recommendation

Do not start EA execution code yet. First close the pre-registration audit gap, rerun Phase 0 with completed hypotheses, review `outputs\adversarial_review\breakout_retest_losing_trades_review.csv`, mark logic-gap outcomes, score the review, regenerate the verdict, and proceed only if `breakout_retest` receives a full PASS.
