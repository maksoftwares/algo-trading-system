# Gold Daily Scan - 2026-06-17

Status: `READ_ONLY_SCAN_COMPLETE_NEAR_EOD`

No EA, preset, chart, cap, arming, profile, order, or position was changed by this scan.

## Sample Sizes

- Raw closed XAUUSD rows: `82`
- Global unique signal rows: `71`
- Account-scoped unique signal rows: `81`
- Raw PnL AED_001: `-841.92`
- Global deduped representative PnL AED_001: `-344.60`
- Account-scoped deduped representative PnL AED_001: `-749.61`
- Source scan: `C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase1/outputs/reports/EOD_GOLD_SCAN_REPORT_2026_06_17.md`
- Row CSV: `C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase1/outputs/reports/XAUUSD_DAILY_ROWS_2026_06_17.csv`

Global dedup rule: `entry minute Dubai | direction | family`. Account-scoped dedup adds `account` to that key so A1/A2/A3 evidence is not collapsed into one representative.

## Gold Regime

| Open | High | Low | Close | Net move pts | Day type | M5 rows |
| --- | --- | --- | --- | --- | --- | --- |
| 4333.76000 | 4382.10000 | 4226.27000 | 4227.41000 | -10635.00 | down | 270 |

Day-3 regime: `DOWN`. H3 is no longer only up-regime evidence, but one down day still is not enough for final confirmation.

## T1 - Authoritative Trade Set Summary

| account | trades | wins | losses | win rate | pnl aed 001 |
| --- | --- | --- | --- | --- | --- |
| 1025742 | 71 | 22 | 49 | 30.99% | -344.60 |
| 1033030 | 1 | 0 | 1 | 0.00% | -92.42 |
| 1033669 | 10 | 0 | 10 | 0.00% | -404.90 |

### Account-scoped unique representative rows by account

| account | trades | wins | losses | win rate | pnl aed 001 |
| --- | --- | --- | --- | --- | --- |
| 1025742 | 71 | 22 | 49 | 30.99% | -344.60 |
| 1033030 | 1 | 0 | 1 | 0.00% | -92.42 |
| 1033669 | 9 | 0 | 9 | 0.00% | -312.59 |

## T2 - A1 Round Quarantine Forward-Week Check

- Work-order threshold: `2026-06-17 11:22 Dubai`.
- Applied-report threshold: `2026-06-17 15:22:35 Dubai` from `created_at_utc=2026-06-17T11:22:35.078853Z`.
- Result using work-order threshold: `FAIL_TIME_BASIS_REVIEW_REQUIRED`; post-threshold rows: `11`.
- Result using applied-report timestamp: `CLEAN`; post-applied rows: `0`.

| Threshold | Pre count | Post count | Post PnL AED_001 |
| --- | --- | --- | --- |
| Work-order 11:22 Dubai | 28 | 11 | -5.80 |
| Applied-report timestamp | 39 | 0 | 0.00 |

Report-based chart state: chart09/chart11 are recorded as `dry_run=true`, `broker_action_allowed=false`; runtime verification remains forward-week evidence.

## T3 - A1 Protected Breakout-Core

| magic | candidate | session | trades | wins | losses | win rate | pnl aed 001 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 920101 | breakout_retest | Afternoon 12:00-15:59 | 2 | 1 | 1 | 50.00% | 0.39 |
| 920101 | breakout_retest | Evening 16:00-19:59 | 2 | 2 | 0 | 100.00% | 76.18 |
| 920101 | breakout_retest | Morning 06:00-11:59 | 3 | 0 | 3 | 0.00% | -37.18 |
| 920101 | breakout_retest | Night 20:00-05:59 | 2 | 0 | 2 | 0.00% | -115.15 |
| 920201 | swing_breakout_retest_v0 | Afternoon 12:00-15:59 | 1 | 1 | 0 | 100.00% | 17.29 |
| 920201 | swing_breakout_retest_v0 | Evening 16:00-19:59 | 1 | 0 | 1 | 0.00% | -92.42 |
| 920201 | swing_breakout_retest_v0 | Morning 06:00-11:59 | 2 | 0 | 2 | 0.00% | -23.85 |
| 920201 | swing_breakout_retest_v0 | Night 20:00-05:59 | 4 | 0 | 4 | 0.00% | -92.53 |

Protected core continued producing rows today, so no halt is visible in direct broker history.

## T4 - A3 Tier-1 Compat 933400

| Entry Dubai | Exit Dubai | Direction | PnL_001 | Cost R | MFE | MAE | Inside server 12-15 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-06-17 18:55:01 | 2026-06-17 22:04:28 | BUY | -92.31 | 0.0200 | PENDING_PATH | PENDING_PATH | true |

- `933400` trades in server-hour 12-15 gate: `1` of `1` order-log rows.
- Any outside gate: `false`.
- Trend shadow pass counts: `{'false': 113, 'true': 5}`
- Trend shadow reasons: `{'NO_SIGNAL': 107, 'TREND_AGAINST_SIGNAL': 6, 'TREND_PASS': 5}`
- Trend shadow reasons on would-signals: `{'TREND_AGAINST_SIGNAL': 6, 'TREND_PASS': 5}`
- A3 plain 933200 rows: `7`; PnL AED_001 `-276.84`.
- A3 improved 933300 rows: `2`; PnL AED_001 `-35.75`.

MFE/MAE: not available in this report because the direct trade export does not include intratrade path; use the position-path observer or M5 path replay for exact MFE/MAE.

## T5 - A3 A/B And Per-Magic/Session Deduped Totals

| magic | candidate | session | trades | wins | losses | win rate | pnl aed 001 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 933200 | a3_breakout_plain | Afternoon 12:00-15:59 | 1 | 0 | 1 | 0.00% | -16.46 |
| 933200 | a3_breakout_plain | Evening 16:00-19:59 | 1 | 0 | 1 | 0.00% | -92.64 |
| 933200 | a3_breakout_plain | Morning 06:00-11:59 | 3 | 0 | 3 | 0.00% | -36.93 |
| 933200 | a3_breakout_plain | Night 20:00-05:59 | 2 | 0 | 2 | 0.00% | -130.81 |
| 933300 | a3_breakout_improved | Night 20:00-05:59 | 2 | 0 | 2 | 0.00% | -35.75 |

A3 plain/improved co-fired same unique signal count: `0`.

## Per Account / Magic / Session

| account | magic | candidate | session | trades | wins | losses | win rate | pnl aed 001 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1025742 | 920101 | breakout_retest | Afternoon 12:00-15:59 | 2 | 1 | 1 | 50.00% | 0.39 |
| 1025742 | 920101 | breakout_retest | Evening 16:00-19:59 | 2 | 2 | 0 | 100.00% | 76.18 |
| 1025742 | 920101 | breakout_retest | Morning 06:00-11:59 | 3 | 0 | 3 | 0.00% | -37.18 |
| 1025742 | 920101 | breakout_retest | Night 20:00-05:59 | 2 | 0 | 2 | 0.00% | -115.15 |
| 1025742 | 920201 | swing_breakout_retest_v0 | Afternoon 12:00-15:59 | 1 | 1 | 0 | 100.00% | 17.29 |
| 1025742 | 920201 | swing_breakout_retest_v0 | Evening 16:00-19:59 | 1 | 0 | 1 | 0.00% | -92.42 |
| 1025742 | 920201 | swing_breakout_retest_v0 | Morning 06:00-11:59 | 2 | 0 | 2 | 0.00% | -23.85 |
| 1025742 | 920201 | swing_breakout_retest_v0 | Night 20:00-05:59 | 4 | 0 | 4 | 0.00% | -92.53 |
| 1025742 | 920301 | symbol_normalized_round_retest_v0 | Afternoon 12:00-15:59 | 10 | 3 | 7 | 30.00% | -25.99 |
| 1025742 | 920301 | symbol_normalized_round_retest_v0 | Morning 06:00-11:59 | 18 | 3 | 15 | 16.67% | -142.53 |
| 1025742 | 920301 | symbol_normalized_round_retest_v0 | Night 20:00-05:59 | 9 | 4 | 5 | 44.44% | -11.53 |
| 1025742 | 920401 | round_number_retest_v0 | Morning 06:00-11:59 | 2 | 1 | 1 | 50.00% | 0.39 |
| 1025742 | 920501 | session_extreme_retest_v0 | Evening 16:00-19:59 | 3 | 2 | 1 | 66.67% | -14.80 |
| 1025742 | 920501 | session_extreme_retest_v0 | Night 20:00-05:59 | 9 | 4 | 5 | 44.44% | 112.25 |
| 1025742 | 921101 | symbol_normalized_round_retest_v0_repair_v1 | Evening 16:00-19:59 | 3 | 1 | 2 | 33.33% | 4.88 |
| 1033030 | 920101 | breakout_retest | Evening 16:00-19:59 | 1 | 0 | 1 | 0.00% | -92.42 |
| 1033669 | 933200 | a3_breakout_plain | Afternoon 12:00-15:59 | 1 | 0 | 1 | 0.00% | -16.46 |
| 1033669 | 933200 | a3_breakout_plain | Evening 16:00-19:59 | 1 | 0 | 1 | 0.00% | -92.64 |
| 1033669 | 933200 | a3_breakout_plain | Morning 06:00-11:59 | 3 | 0 | 3 | 0.00% | -36.93 |
| 1033669 | 933200 | a3_breakout_plain | Night 20:00-05:59 | 2 | 0 | 2 | 0.00% | -130.81 |
| 1033669 | 933300 | a3_breakout_improved | Night 20:00-05:59 | 2 | 0 | 2 | 0.00% | -35.75 |

## Hypothesis Tags - Day 3 Only

| Hypothesis | Tag | Reason |
| --- | --- | --- |
| H1 round-no-edge | support | Round-family target rows today: 39, PnL -179.66 AED_001. |
| H2 afternoon-weak | support | Afternoon account-scoped unique PnL remains negative, but not necessarily worst today. |
| H3 counter-trend-loses | support | Gold was down; long side carried most losses. |
| H4 cost-predicts-losers | n/a | Needs multi-day cost aggregation; single-day cells are too small. |
| H5 structure-beats-veto | support | A3 improved 933300 outperformed plain 933200 today, but sample is small. |

## Honesty Notes

- Single near-EOD day only; no edge claim upgraded.
- A1 quarantine, A3 compat, and A3 A/B are measured separately.
- The quarantine time-basis discrepancy must be resolved with the reviewer/owner: work order says 11:22 Dubai; applied report says 11:22 UTC / 15:22 Dubai.
