# Friday Demo Account And Observer Review Export - 2026-06-19

Status: `REVIEW_PACKAGE_READY`

Boundary: evidence package only. Creating this folder did not touch MT5 runtime, EAs, presets, charts, orders, positions, profiles, or broker settings.

## What Happened Today

Friday 2026-06-19 was a down day for XAUUSD in the EOD gold context:

| Metric | Value |
| --- | ---: |
| XAUUSD open | 4216.81000 |
| XAUUSD high | 4219.41000 |
| XAUUSD low | 4121.71000 |
| XAUUSD close | 4155.26000 |
| Net move | -6155 points |
| M5 rows | 240 |

## Trading Accounts

### A1 - Standard Experimental Demo, `1025742`

Gold-only EOD export showed 3 closed XAUUSD trades, 2 wins / 1 loss, +90.30 AED at 0.01-lot normalization.

All-symbol dashboard broker table showed 19 Friday rows, 19 closed, 7 wins / 7 losses / 5 flat-zero rows, -7.79 AED. This table has a known discrepancy for two A1 XAUUSD entries: the dashboard CSV shows them as closed 0.00 rows with blank exits, while the gold EOD exporter correctly pairs their exits and profits as +41.74 and +68.95 AED. Treat the EOD gold export as authoritative for XAUUSD and ask Codex to repair the all-symbol dashboard parser before using it for XAUUSD PnL.

### A2 - Tier-1 Clean Breakout Account, `1033030`

Friday XAUUSD EOD export showed 2 closed trades, both losses, -23.47 AED. Direct A2 history since June 1 shows balance 3944.91 AED, 12 closed XAUUSD positions, 4 wins / 8 losses, -55.09 AED.

### A3 - Repair Lane, `1033669`

Friday EOD export showed 0 closed XAUUSD trades and 0 open XAUUSD positions. Runtime authorization reconciliation marks A3 paused. Direct A3 history since June 1 shows 75 closed historical XAUUSD positions, 22 wins / 53 losses, -738.38 AED net, and 0 open positions.

## Observer And Hypothesis Read

| Item | Result |
| --- | --- |
| Runtime authorization | `PASS_CURRENT` |
| A3 pause | `PAUSE_HELD` |
| H1 round-family night/evening shorts | `FAIL` |
| H2 M15/H1 trend veto | `PENDING_INSUFFICIENT_BROKER_JOINED_SAMPLE` |
| H3 family mutex | `FAIL_OVERALL_WITH_DUPLICATE_COMPONENT_PASS` |
| H4 breakout-retest control stability | `FAIL` |
| Repair forward-week report | `FORWARD_CONFIRMATION_FAILED_REVIEW_REQUIRED` |

The family mutex appears to have worked mechanically: post-mutex A1 920xxx rows had 0 duplicate rows, 0.00% duplicate rate, and max same-family stack 1. The profit side did not pass: H3 unique-view PF was only 0.6315 and H4 breakout control had 2 positive days vs 3 negative days.

Observer outcome resolution on 2026-06-19 resolved only 2 broker-joined rows and left 2641 unresolved rows because fresh M5 replay bars were not supplied. H2 is therefore pending, not failed.

## Included Files

Top-level docs:

- `docs/FORWARD_WEEK_HYPOTHESES_2026_06_15.md`
- `GOLD_DAILY_TRACKING_WEEK_2026_06_15.md`
- `status_summary.md`
- `status_summary.json`

Reports:

- `FORWARD_WEEK_FRIDAY_SCORE_2026_06_19.md`
- `GOLD_DAILY_SCAN_2026_06_15.md`
- `GOLD_DAILY_SCAN_2026_06_16.md`
- `GOLD_DAILY_SCAN_2026_06_17.md`
- `GOLD_DAILY_SCAN_2026_06_18.md`
- `GOLD_DAILY_SCAN_2026_06_19.md`
- `EOD_GOLD_SCAN_REPORT_2026_06_15.md`
- `EOD_GOLD_SCAN_REPORT_2026_06_17.md`
- `EOD_GOLD_SCAN_REPORT_2026_06_18.md`
- `EOD_GOLD_SCAN_REPORT_2026_06_19.md`
- `OBSERVER_OUTCOME_RESOLUTION_REPORT_2026_06_19.md/json/csv`
- `OBSERVER_SHADOW_POLICY_SCOREBOARD_2026_06_19.md/json/csv`
- `DIRECTION_STATE_SHADOW_SCOREBOARD_2026_06_19.md/json/csv`
- `RUNTIME_AUTHORIZATION_RECONCILIATION_2026_06_19.md/json`
- `A2_TIER1_ACCOUNT_HISTORY_2026_06_19.md/json/rows.csv`
- `A3_REPAIR_LANE_ACCOUNT_HISTORY_2026_06_19.md/json/closed_rows.csv/open_rows.csv`
- `PHASE2_DEMO_REPAIR_FORWARD_WEEK_REPORT.md/json`
- `PHASE2_EA_WEAKNESS_SHADOW_REPORT.md/json`

CSV/data:

- `XAUUSD_DAILY_ROWS_2026_06_15.csv` through `XAUUSD_DAILY_ROWS_2026_06_19.csv`
- `EOD_GOLD_A1/A2/A3_20260619.csv`
- `EOD_GOLD_OBSERVER_JOIN_INPUT_20260619.csv`
- `EOD_GOLD_CONTEXT_20260619.csv`
- `PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv`
- `PHASE2_DEMO_OBSERVER_DASHBOARD_SUMMARY.csv`
- `PHASE2_DEMO_OBSERVER_DASHBOARD_LEDGER.csv`

Dashboard:

- `demo-observer-dashboard.html`
- `PHASE2_DEMO_OBSERVER_DASHBOARD.json`

## Questions For Reviewer

1. Does the broker-joined evidence justify keeping A1/A2 running unchanged next week?
2. Is the A1 Friday XAU repair-lane win (+90.30 AED) structurally meaningful, or just a small-sample down-day effect?
3. Should H2 trend-veto scoring wait for fresh M5 replay bars, or is broker-joined sample too thin to act on?
4. Does the all-symbol dashboard broker parser need immediate repair because it mis-paired two A1 XAU exits?
5. Given H1/H3/H4 failures, should any runtime rule be promoted, rolled back, or left unchanged?
