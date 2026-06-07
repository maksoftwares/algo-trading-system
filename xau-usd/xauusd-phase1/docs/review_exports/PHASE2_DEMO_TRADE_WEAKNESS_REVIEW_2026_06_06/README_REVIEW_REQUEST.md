# Phase 2 Demo Actual Trades - Weakness Review Request

This ZIP contains actual demo broker trade evidence exported from the MT5 account for the week-to-date window starting `2026-06-01 00:00:00`.

The purpose of this packet is to help an independent reviewer diagnose:

- why winning trades are working;
- why losing trades are failing;
- whether duplicate/same-family exposure is distorting the results;
- which EA, symbol, and time bucket combinations look viable;
- whether any trade families should be suspended, narrowed, or researched further;
- what changes could improve win rate without curve-fitting.

## Files

| File | Purpose |
|---|---|
| `PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv` | Direct refreshed actual broker trade table from the dashboard generator. |
| `PHASE2_DEMO_OBSERVER_DASHBOARD_SUMMARY.csv` | Current dashboard summary table. |
| `PHASE2_DEMO_OBSERVER_DASHBOARD_LEDGER.csv` | Current dashboard ledger used by the HTML dashboard. |
| `PHASE2_DEMO_OBSERVER_DASHBOARD.json` | Machine-readable dashboard data. |
| `PHASE2_DEMO_WEEKLY_ALL_TRADES_2026_06_06.csv` | Week-to-date raw broker rows, including duplicates. |
| `PHASE2_DEMO_WEEKLY_UNIQUE_TRADES_2026_06_06.csv` | Week-to-date duplicate-hidden view for cleaner win-rate/PnL analysis. |
| `PHASE2_DEMO_WEEKLY_TRADES_SUMMARY_2026_06_06.md` | Week-to-date summary by symbol, EA, time bucket, and EA-symbol pair. |
| `README_REVIEW_EXPORT.md` | Technical note from the weekly export packet. |

## Reviewer Questions

Please review the trades and answer:

1. Which losses are normal strategy losses versus avoidable logic/execution/session losses?
2. Which EA and symbol combinations should remain active, reduced, suspended, or observer-only?
3. Are duplicate trades or same-family signals inflating exposure?
4. Does the evening performance advantage look real enough to test as a future routing rule?
5. Are the losers caused more by poor entry timing, stop distance, symbol selection, session timing, or duplicate exposure?
6. Is win rate the real problem, or are average loss / risk-reward / duplicate exposure bigger issues?
7. What exact next research hypothesis should be tested to improve the system without tuning after the fact?

## Boundary

This is experimental demo evidence only. It is not live-trading authorization and should not override the official Phase 2 readiness gates.
