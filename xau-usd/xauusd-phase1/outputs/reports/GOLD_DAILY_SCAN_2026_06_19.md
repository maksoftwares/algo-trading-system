# Gold Daily Scan - 2026-06-19

Status: `READ_ONLY_SCAN_COMPLETE`

No EA, preset, chart, cap, arming, profile, order, or position was changed by this scan.

## Sample Sizes

- Raw closed XAUUSD rows: `5`
- Global unique signal rows: `5`
- Account-scoped unique signal rows: `5`
- Raw PnL AED_001: `66.83`
- Global deduped representative PnL AED_001: `66.83`
- Account-scoped deduped representative PnL AED_001: `66.83`
- Source scan: `C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase1/outputs/reports/EOD_GOLD_SCAN_REPORT_2026_06_19.md`
- Row CSV: `C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase1/outputs/reports/XAUUSD_DAILY_ROWS_2026_06_19.csv`

Global dedup rule: `entry minute Dubai | direction | family`. Account-scoped dedup adds `account` to that key so A1/A2/A3 evidence is not collapsed into one representative.

## Gold Regime

| Open | High | Low | Close | Net move pts | Day type | M5 rows |
| --- | --- | --- | --- | --- | --- | --- |
| 4216.81000 | 4219.41000 | 4121.71000 | 4155.26000 | -6155.00 | down | 240 |

Day-5 regime: `DOWN`. Single-day evidence only; no hypothesis is upgraded from this one scan.

## T1 - Authoritative Trade Set Summary

| account | trades | wins | losses | win rate | pnl aed 001 |
| --- | --- | --- | --- | --- | --- |
| 1025742 | 3 | 2 | 1 | 66.67% | 90.30 |
| 1033030 | 2 | 0 | 2 | 0.00% | -23.47 |

### Account-scoped unique representative rows by account

| account | trades | wins | losses | win rate | pnl aed 001 |
| --- | --- | --- | --- | --- | --- |
| 1025742 | 3 | 2 | 1 | 66.67% | 90.30 |
| 1033030 | 2 | 0 | 2 | 0.00% | -23.47 |

## T2 - A1 Round Quarantine Forward-Week Check

- Work-order threshold: `2026-06-17 11:22 Dubai`.
- Applied-report threshold: `2026-06-17 15:22:35 Dubai` from `created_at_utc=2026-06-17T11:22:35.078853Z`.
- Result using work-order threshold: `CLEAN`; post-threshold rows: `0`.
- Result using applied-report timestamp: `CLEAN`; post-applied rows: `0`.

| Threshold | Pre count | Post count | Post PnL AED_001 |
| --- | --- | --- | --- |
| Work-order 11:22 Dubai | 0 | 0 | 0.00 |
| Applied-report timestamp | 0 | 0 | 0.00 |

Report-based chart state: chart09/chart11 are recorded as `dry_run=true`, `broker_action_allowed=false`; runtime verification remains forward-week evidence.
- Full-day exact target result for `2026-06-19`: `CLEAN`; exact chart09/chart11-family broker rows: `0`.

## T3 - A1 Protected Breakout-Core

| magic | candidate | session | trades | wins | losses | win rate | pnl aed 001 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| n/a | n/a | n/a | 0 | 0 | 0 | n/a | 0.00 |

Protected core produced broker rows today. A1 later shows `kill_switch_active` guard blocks in the source EOD report; that is the owner-authorized A1 daily profit-floor lock, not round-quarantine damage.

## T4 - A3 Pause Verification

- A3 pause status: `PAUSE_HELD`.
- A3 closed XAUUSD rows today: `0`.
- A3 closed PnL AED_001: `0.00`.
- Open/pending exposure: see the source EOD scan report; it reported zero open XAUUSD positions at scan time.

| magic | candidate | session | trades | wins | losses | win rate | pnl aed 001 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| n/a | n/a | n/a | 0 | 0 | 0 | n/a | 0.00 |

## T4 Detail - A3 Tier-1 Compat 933400

| Entry Dubai | Exit Dubai | Direction | PnL_001 | Cost R | MFE | MAE | Inside server 12-15 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| none | none | none | 0.00 |  | n/a | n/a | n/a |

- `933400` trades in server-hour 12-15 gate: `0` of `0` order-log rows.
- Any outside gate: `false`.
- Trend shadow pass counts: `{'false': 236, 'true': 5}`
- Trend shadow reasons: `{'NO_SIGNAL': 232, 'TREND_PASS': 5, 'TREND_AGAINST_SIGNAL': 4}`
- Trend shadow reasons on would-signals: `{'TREND_PASS': 5, 'TREND_AGAINST_SIGNAL': 4}`
- A3 plain 933200 rows: `0`; PnL AED_001 `0.00`.
- A3 improved 933300 rows: `0`; PnL AED_001 `0.00`.

MFE/MAE: not available in this report because the direct trade export does not include intratrade path; use the position-path observer or M5 path replay for exact MFE/MAE.

## T5 - A3 A/B And Per-Magic/Session Deduped Totals

| magic | candidate | session | trades | wins | losses | win rate | pnl aed 001 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| n/a | n/a | n/a | 0 | 0 | 0 | n/a | 0.00 |

A3 plain/improved co-fired same unique signal count: `0`.

## T5 - A2 Breakout

| magic | candidate | session | trades | wins | losses | win rate | pnl aed 001 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 920101 | breakout_retest | Evening 16:00-19:59 | 2 | 0 | 2 | 0.00% | -23.47 |

## T6 - Direction Split

| direction | trades | wins | losses | win rate | pnl aed 001 |
| --- | --- | --- | --- | --- | --- |
| BUY | 2 | 0 | 2 | 0.00% | -23.47 |
| SELL | 3 | 2 | 1 | 66.67% | 90.30 |

## Per Account / Magic / Session

| account | magic | candidate | session | trades | wins | losses | win rate | pnl aed 001 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1025742 | 921101 | symbol_normalized_round_retest_v0_repair_v1 | Evening 16:00-19:59 | 3 | 2 | 1 | 66.67% | 90.30 |
| 1033030 | 920101 | breakout_retest | Evening 16:00-19:59 | 2 | 0 | 2 | 0.00% | -23.47 |

## Hypothesis Tags - Day 5 Only

| Hypothesis | Tag | Reason |
| --- | --- | --- |
| H1 round-no-edge | n/a | Exact chart09/chart11 target rows today: 0. Zero rows proves quarantine compliance, not edge behavior. |
| H2 afternoon-weak | n/a | Afternoon account-scoped unique rows: 0, PnL 0.00 AED_001. |
| H3 counter-trend-loses | support | Gold day type was down; compare BUY vs SELL in T6. |
| H4 cost-predicts-losers | n/a | Needs multi-day cost aggregation; single-day cells are too small. |
| H5 structure-beats-veto | n/a | A3 improved 933300 outperformed plain 933200 today, but sample is small. |

## Honesty Notes

- Single near-EOD day only; no edge claim upgraded.
- A1 quarantine, A3 compat, and A3 A/B are measured separately.
- The quarantine time-basis discrepancy must be resolved with the reviewer/owner: work order says 11:22 Dubai; applied report says 11:22 UTC / 15:22 Dubai.
