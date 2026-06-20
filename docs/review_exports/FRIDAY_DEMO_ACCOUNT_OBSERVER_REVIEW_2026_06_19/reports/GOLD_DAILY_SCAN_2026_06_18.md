# Gold Daily Scan - 2026-06-18

Status: `READ_ONLY_SCAN_COMPLETE`

No EA, preset, chart, cap, arming, profile, order, or position was changed by this scan.

## Sample Sizes

- Raw closed XAUUSD rows: `35`
- Global unique signal rows: `22`
- Account-scoped unique signal rows: `30`
- Raw PnL AED_001: `-482.92`
- Global deduped representative PnL AED_001: `-173.75`
- Account-scoped deduped representative PnL AED_001: `-466.45`
- Source scan: `C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase1/outputs/reports/EOD_GOLD_SCAN_REPORT_2026_06_18.md`
- Row CSV: `C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase1/outputs/reports/XAUUSD_DAILY_ROWS_2026_06_18.csv`

Global dedup rule: `entry minute Dubai | direction | family`. Account-scoped dedup adds `account` to that key so A1/A2/A3 evidence is not collapsed into one representative.

## Gold Regime

| Open | High | Low | Close | Net move pts | Day type | M5 rows |
| --- | --- | --- | --- | --- | --- | --- |
| 4235.43000 | 4329.84000 | 4201.26000 | 4216.52000 | -1891.00 | down | 277 |

Day-4 regime: `DOWN`. Single-day evidence only; no hypothesis is upgraded from this one scan.

## T1 - Authoritative Trade Set Summary

| account | trades | wins | losses | win rate | pnl aed 001 |
| --- | --- | --- | --- | --- | --- |
| 1025742 | 22 | 6 | 16 | 27.27% | -138.83 |
| 1033030 | 1 | 0 | 1 | 0.00% | -44.12 |
| 1033669 | 12 | 2 | 10 | 16.67% | -299.97 |

### Account-scoped unique representative rows by account

| account | trades | wins | losses | win rate | pnl aed 001 |
| --- | --- | --- | --- | --- | --- |
| 1025742 | 21 | 5 | 16 | 23.81% | -197.39 |
| 1033030 | 1 | 0 | 1 | 0.00% | -44.12 |
| 1033669 | 8 | 2 | 6 | 25.00% | -224.94 |

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
- Full-day exact target result for `2026-06-18`: `CLEAN`; exact chart09/chart11-family broker rows: `0`.

## T3 - A1 Protected Breakout-Core

| magic | candidate | session | trades | wins | losses | win rate | pnl aed 001 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 920101 | breakout_retest | Evening 16:00-19:59 | 1 | 1 | 0 | 100.00% | 48.57 |
| 920101 | breakout_retest | Morning 06:00-11:59 | 1 | 1 | 0 | 100.00% | 20.27 |
| 920101 | breakout_retest | Night 20:00-05:59 | 2 | 0 | 2 | 0.00% | -177.38 |
| 920201 | swing_breakout_retest_v0 | Evening 16:00-19:59 | 1 | 0 | 1 | 0.00% | -45.78 |
| 920201 | swing_breakout_retest_v0 | Morning 06:00-11:59 | 5 | 0 | 5 | 0.00% | -89.28 |

Protected core produced broker rows today. A1 later shows `kill_switch_active` guard blocks in the source EOD report; that is the owner-authorized A1 daily profit-floor lock, not round-quarantine damage.

## T4 - A3 Pause Verification

- A3 pause status: `PAUSE_FAIL`.
- A3 closed XAUUSD rows today: `12`.
- A3 closed PnL AED_001: `-299.97`.
- Open/pending exposure: see the source EOD scan report; it reported zero open XAUUSD positions at scan time.

| magic | candidate | session | trades | wins | losses | win rate | pnl aed 001 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 933200 | a3_breakout_plain | Morning 06:00-11:59 | 4 | 0 | 4 | 0.00% | -74.25 |
| 933200 | a3_breakout_plain | Night 20:00-05:59 | 1 | 0 | 1 | 0.00% | -129.07 |
| 933300 | a3_breakout_improved | Morning 06:00-11:59 | 5 | 1 | 4 | 20.00% | -74.77 |
| 933300 | a3_breakout_improved | Night 20:00-05:59 | 1 | 0 | 1 | 0.00% | -45.52 |
| 933500 | A3_SOFT_RETEST_V2 | Night 20:00-05:59 | 1 | 1 | 0 | 100.00% | 23.64 |

## T4 Detail - A3 Tier-1 Compat 933400

| Entry Dubai | Exit Dubai | Direction | PnL_001 | Cost R | MFE | MAE | Inside server 12-15 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| none | none | none | 0.00 |  | n/a | n/a | n/a |

- `933400` trades in server-hour 12-15 gate: `0` of `0` order-log rows.
- Any outside gate: `false`.
- Trend shadow pass counts: `{'false': 270, 'true': 11}`
- Trend shadow reasons: `{'NO_SIGNAL': 269, 'TREND_PASS': 11, 'TREND_AGAINST_SIGNAL': 1}`
- Trend shadow reasons on would-signals: `{'TREND_PASS': 11, 'TREND_AGAINST_SIGNAL': 1}`
- A3 plain 933200 rows: `5`; PnL AED_001 `-203.32`.
- A3 improved 933300 rows: `6`; PnL AED_001 `-120.29`.

MFE/MAE: not available in this report because the direct trade export does not include intratrade path; use the position-path observer or M5 path replay for exact MFE/MAE.

## T5 - A3 A/B And Per-Magic/Session Deduped Totals

| magic | candidate | session | trades | wins | losses | win rate | pnl aed 001 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 933200 | a3_breakout_plain | Morning 06:00-11:59 | 4 | 0 | 4 | 0.00% | -74.25 |
| 933200 | a3_breakout_plain | Night 20:00-05:59 | 1 | 0 | 1 | 0.00% | -129.07 |
| 933300 | a3_breakout_improved | Morning 06:00-11:59 | 1 | 1 | 0 | 100.00% | 0.26 |
| 933300 | a3_breakout_improved | Night 20:00-05:59 | 1 | 0 | 1 | 0.00% | -45.52 |
| 933500 | A3_SOFT_RETEST_V2 | Night 20:00-05:59 | 1 | 1 | 0 | 100.00% | 23.64 |

A3 plain/improved co-fired same unique signal count: `4`.

## T5 - A2 Breakout

| magic | candidate | session | trades | wins | losses | win rate | pnl aed 001 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 920101 | breakout_retest | Evening 16:00-19:59 | 1 | 0 | 1 | 0.00% | -44.12 |

## T6 - Direction Split

| direction | trades | wins | losses | win rate | pnl aed 001 |
| --- | --- | --- | --- | --- | --- |
| BUY | 1 | 1 | 0 | 100.00% | 48.57 |
| SELL | 29 | 6 | 23 | 20.69% | -515.02 |

## Per Account / Magic / Session

| account | magic | candidate | session | trades | wins | losses | win rate | pnl aed 001 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1025742 | 920101 | breakout_retest | Evening 16:00-19:59 | 1 | 1 | 0 | 100.00% | 48.57 |
| 1025742 | 920101 | breakout_retest | Morning 06:00-11:59 | 1 | 1 | 0 | 100.00% | 20.27 |
| 1025742 | 920101 | breakout_retest | Night 20:00-05:59 | 2 | 0 | 2 | 0.00% | -177.38 |
| 1025742 | 920201 | swing_breakout_retest_v0 | Evening 16:00-19:59 | 1 | 0 | 1 | 0.00% | -45.78 |
| 1025742 | 920201 | swing_breakout_retest_v0 | Morning 06:00-11:59 | 5 | 0 | 5 | 0.00% | -89.28 |
| 1025742 | 920501 | session_extreme_retest_v0 | Evening 16:00-19:59 | 1 | 1 | 0 | 100.00% | 59.44 |
| 1025742 | 921101 | symbol_normalized_round_retest_v0_repair_v1 | Evening 16:00-19:59 | 8 | 2 | 6 | 25.00% | -11.69 |
| 1025742 | 921201 | session_extreme_retest_v0_repair_v1 | Evening 16:00-19:59 | 2 | 0 | 2 | 0.00% | -1.54 |
| 1033030 | 920101 | breakout_retest | Evening 16:00-19:59 | 1 | 0 | 1 | 0.00% | -44.12 |
| 1033669 | 933200 | a3_breakout_plain | Morning 06:00-11:59 | 4 | 0 | 4 | 0.00% | -74.25 |
| 1033669 | 933200 | a3_breakout_plain | Night 20:00-05:59 | 1 | 0 | 1 | 0.00% | -129.07 |
| 1033669 | 933300 | a3_breakout_improved | Morning 06:00-11:59 | 1 | 1 | 0 | 100.00% | 0.26 |
| 1033669 | 933300 | a3_breakout_improved | Night 20:00-05:59 | 1 | 0 | 1 | 0.00% | -45.52 |
| 1033669 | 933500 | A3_SOFT_RETEST_V2 | Night 20:00-05:59 | 1 | 1 | 0 | 100.00% | 23.64 |

## Hypothesis Tags - Day 4 Only

| Hypothesis | Tag | Reason |
| --- | --- | --- |
| H1 round-no-edge | n/a | Exact chart09/chart11 target rows today: 0. Zero rows proves quarantine compliance, not edge behavior. |
| H2 afternoon-weak | n/a | Afternoon account-scoped unique rows: 0, PnL 0.00 AED_001. |
| H3 counter-trend-loses | contradict | Gold day type was down; compare BUY vs SELL in T6. |
| H4 cost-predicts-losers | n/a | Needs multi-day cost aggregation; single-day cells are too small. |
| H5 structure-beats-veto | support | A3 improved 933300 outperformed plain 933200 today, but sample is small. |

## Honesty Notes

- Single near-EOD day only; no edge claim upgraded.
- A1 quarantine, A3 compat, and A3 A/B are measured separately.
- The quarantine time-basis discrepancy must be resolved with the reviewer/owner: work order says 11:22 Dubai; applied report says 11:22 UTC / 15:22 Dubai.
