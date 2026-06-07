# P2WEAKNESS_BR_V1 Runtime Notes

`P2WEAKNESS_BR_V1` is a separate owner-requested experimental demo EA created from the 2026-06-06 demo trade weakness review.

## Boundary

- Non-canonical experimental demo only.
- Does not authorize canonical Phase 2.
- Does not authorize live trading.
- Does not modify or replace the existing running EAs.
- Deployed/compiled into the Capital.com demo terminal data folder only.

## Identity

| Field | Value |
|---|---|
| EA file | `Phase2WeaknessBreakoutRetestExecutor.mq5` |
| Run ID | `P2WEAKNESS_BR_V1` |
| Order comment | `P2WEAKNESS_BR_V1` |
| Magic number | `930101` |
| Candidate | `breakout_retest` |
| Symbol | `XAUUSD` |
| Default lot | `0.01` |
| Signal log | `p2weakness_br_v1_signal_log_xauusd.csv` |
| Startup log | `p2weakness_br_v1_startup_xauusd.csv` |
| Order log | `p2weakness_br_v1_order_log_xauusd.csv` |

## Reviewer-Driven Restrictions

- Only the core `breakout_retest` candidate is executable.
- Weak reviewed variants are not included.
- USDJPY is not included.
- Same-family duplicate exposure is suppressed against known demo-family magic ranges `920000-920999` and `930000-930999`.
- The EA refuses non-demo server markers and account logins outside `InpAllowedAccountLoginsCsv`.

## Deployment Evidence

The compile/deployment report is generated at:

`xau-usd/xauusd-phase1/outputs/reports/PHASE2_WEAKNESS_BR_V1_DEPLOYMENT.md`

The deployment script copies and compiles the EA without closing MT5, restarting MT5, replacing profiles, or attaching charts.
