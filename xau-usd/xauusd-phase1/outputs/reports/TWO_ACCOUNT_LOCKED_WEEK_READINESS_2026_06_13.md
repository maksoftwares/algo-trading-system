# Two-Account Locked Week Readiness - 2026-06-13

Overall status: `READY_WITH_EXPLICIT_LIMITATIONS`

This report connects the standard noisy demo account and the Tier-1 clean account before the locked 2026-06-15 forward week. It does not approve canonical Phase 2, live trading, or real capital.

## Lock

- Forward-week hypothesis relock commit: `0e719e9cdd8a2f0f372baa712b918fe41df32291`
- Reason for relock: H3 now explicitly states that A1/A4/A5 were declined, so the PF leg tests the owner-approved noisy configuration rather than a fully tightened floor configuration.

## Account 1 - Standard Noisy Demo

| Item | Status | Evidence |
|---|---|---|
| Terminal | RUNNING | `C:\Program Files\MetaTrader 5\terminal64.exe` |
| Account | ACTIVE | `1025742 / Capital.ComMena-Demo` |
| Floor subset | PASS | `PHASE2_FLOOR_DECISIONS_APPLIED.md` |
| A3 mutex | APPLIED | `WOULD_DUPLICATE_FAMILY_EVENT` in `Phase2ExperimentalDemoExecutor.mq5` |
| A6 USDJPY | PASS | No USDJPY broker-action charts found |
| A7 guardian | PASS | `EQUITY_GUARDIAN_SHADOW_STARTUP.csv` and `EQUITY_GUARDIAN_SHADOW_LOG.csv` |
| Declined items | PRESERVED | A1/A2/A4/A5 not changed |

## Account 2 - Tier-1 Clean Demo

| Item | Status | Evidence |
|---|---|---|
| Terminal | RUNNING | `C:\MT5PortableTier1BestEA` |
| Account | ACTIVE | `1033030 / Capital.ComMena-Demo` |
| EA set | CLEAN | `breakout_retest` only on XAUUSD |
| Magic | PASS | `920101` |
| Lot | PASS | `0.01` |
| Guards | ACTIVE | local owner preset; spread/cost/session/one-instance guard |
| Setup report | PASS | `TIER1_BREAKOUT_RETEST_PORTABLE_TERMINAL.md` |
| Preflight | PENDING_MANUAL_NOTES | kill-switch block test and one-chart owner confirmation remain manual |
| First order verification | PENDING_MANUAL_NOTE | mechanical checks pass; MT5 history comment remains manual |
| Path observer | RUNNING | `C:\MT5PortableTier1PathObserver`, read-only, account `1033030 / Capital.ComMena-Demo` |

## Known Limitations To Score Separately

- Repair lanes use `921xxx` magic numbers and are outside the A3 mutex because A2 was declined. Residual repair-family duplicates are not automatic A3 failure.
- If same-second same-family duplicates appear without `WOULD_DUPLICATE_FAMILY_EVENT` rows, treat that as a fresh race-condition finding for a future GlobalVariable check-and-send lock.
- Replay remains permanently quarantined pending a new design, so Friday scoring should use broker-joined evidence first.

## Friday Scoring Rule

Score the locked week after fresh broker rows exist. Do not edit runtime during the locked week unless the owner opens a new maintenance window.
