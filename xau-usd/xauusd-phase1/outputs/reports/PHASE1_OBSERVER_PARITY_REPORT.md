# Phase 1 Observer Parity Report

Overall status: PASS

## Scope

This report proves source-level parity between the Phase 1 MQL `breakout_retest` observer and the Phase 0 Python `breakout_retest` strategy. A PASS report is required before Phase 2 paper-mode implementation can begin.

## Inputs

- Phase 1 root: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1`
- Phase 0 root: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase0`

## Checks

| Check | Status | Evidence |
| --- | --- | --- |
| Phase 1 MQL observer | PASS | Found `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\mt5\Include\Phase1\Phase1BreakoutRetest.mqh`. |
| Phase 0 Python strategy | PASS | Found `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase0\src\phase0\strategies\breakout_retest.py`. |
| Break window | PASS | Both implementations use a 20-bar breakout lookback before the retest bar. |
| Break ATR threshold | PASS | Both require the break close to clear the level by 0.30 ATR. |
| Retest tolerance | PASS | Both use a 5-point retest tolerance around the broken level. |
| Stop ATR buffer | PASS | Both place the stop with a 0.10 ATR retest-bar buffer. |
| Reward multiple | PASS | Both use a 1.5R target from entry-to-stop risk. |
| Level universe | PASS | MQL observer evaluates daily, weekly, and latest-swing levels for both directions. |
| Python level universe | PASS | Python strategy evaluates the same daily, weekly, and latest-swing levels. |
| Duplicate-level tolerance | PASS | Both collapse duplicate candidate levels within 10 points. |
| Candidate selection | PASS | Both select the lowest stop-distance candidate when multiple levels qualify. |
| Dry-run reason-code mapping | PASS | Phase 1 preserves the Phase 0 reason-code stem and adds an explicit dry-run suffix. |

## Boundary

- This is parity evidence only; it does not authorize paper mode or live trading.
- Runtime would-signal review still remains a separate Phase 1 evidence gate.
