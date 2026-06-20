# Gold Daily Scan - 2026-06-15

Status: `READ_ONLY_SCAN_COMPLETE`

No EA, preset, chart, cap, arming, profile, order, or position was changed by this scan.

## Sample Sizes

- Raw closed XAUUSD rows: `103`
- Global unique signal rows: `63`
- Account-scoped unique signal rows: `86`
- Raw PnL AED_001: `538.21`
- Global deduped representative PnL AED_001: `415.54`
- Account-scoped deduped representative PnL AED_001: `387.16`
- Source scan: `C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase1/outputs/reports/EOD_GOLD_SCAN_REPORT_2026_06_15.md`
- Row CSV: `C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase1/outputs/reports/XAUUSD_DAILY_ROWS_2026_06_15.csv`

Global dedup rule: `entry minute Dubai | direction | family`. Account-scoped dedup adds `account` to that key so A1/A2/A3 evidence is not collapsed into one representative.

## Gold Regime

| Open | High | Low | Close | Net move pts | Day type | M5 rows |
| --- | --- | --- | --- | --- | --- | --- |
| 4236.31000 | 4369.18000 | 4236.31000 | 4320.03000 | 8372.00 | up | 265 |

Day-1 regime: `UP`. Single-day evidence only; no hypothesis is upgraded from this one scan.

## T1 - Authoritative Trade Set Summary

| account | trades | wins | losses | win rate | pnl aed 001 |
| --- | --- | --- | --- | --- | --- |
| 1025742 | 66 | 30 | 36 | 45.45% | 426.30 |
| 1033030 | 1 | 1 | 0 | 100.00% | 49.71 |
| 1033669 | 36 | 14 | 22 | 38.89% | 62.20 |

### Account-scoped unique representative rows by account

| account | trades | wins | losses | win rate | pnl aed 001 |
| --- | --- | --- | --- | --- | --- |
| 1025742 | 62 | 27 | 35 | 43.55% | 365.68 |
| 1033030 | 1 | 1 | 0 | 100.00% | 49.71 |
| 1033669 | 23 | 8 | 15 | 34.78% | -28.23 |

## T2 - A1 Round Quarantine Forward-Week Check

- Work-order threshold: `2026-06-17 11:22 Dubai`.
- Applied-report threshold: `2026-06-17 15:22:35 Dubai` from `created_at_utc=2026-06-17T11:22:35.078853Z`.
- Result using work-order threshold: `CLEAN`; post-threshold rows: `0`.
- Result using applied-report timestamp: `CLEAN`; post-applied rows: `0`.

| Threshold | Pre count | Post count | Post PnL AED_001 |
| --- | --- | --- | --- |
| Work-order 11:22 Dubai | 47 | 0 | 0.00 |
| Applied-report timestamp | 47 | 0 | 0.00 |

Report-based chart state: chart09/chart11 are recorded as `dry_run=true`, `broker_action_allowed=false`; runtime verification remains forward-week evidence.
- Full-day exact target result for `2026-06-15`: `FAIL`; exact chart09/chart11-family broker rows: `47`.

## T3 - A1 Protected Breakout-Core

| magic | candidate | session | trades | wins | losses | win rate | pnl aed 001 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 920101 | breakout_retest | Morning 06:00-11:59 | 3 | 2 | 1 | 66.67% | 47.46 |
| 920101 | breakout_retest | Night 20:00-05:59 | 1 | 1 | 0 | 100.00% | 49.34 |
| 920201 | swing_breakout_retest_v0 | Evening 16:00-19:59 | 4 | 3 | 1 | 75.00% | 109.88 |
| 920201 | swing_breakout_retest_v0 | Night 20:00-05:59 | 2 | 2 | 0 | 100.00% | 59.59 |

Protected core produced broker rows today. A1 later shows `kill_switch_active` guard blocks in the source EOD report; that is the owner-authorized A1 daily profit-floor lock, not round-quarantine damage.

## T4 - A3 Pause Verification

- A3 pause status: `PAUSE_FAIL`.
- A3 closed XAUUSD rows today: `36`.
- A3 closed PnL AED_001: `62.20`.
- Open/pending exposure: see the source EOD scan report; it reported zero open XAUUSD positions at scan time.

| magic | candidate | session | trades | wins | losses | win rate | pnl aed 001 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 933000 | a3_round_retest_guarded_v1 | Afternoon 12:00-15:59 | 4 | 1 | 3 | 25.00% | -45.11 |
| 933000 | a3_round_retest_guarded_v1 | Evening 16:00-19:59 | 4 | 1 | 3 | 25.00% | -27.52 |
| 933000 | a3_round_retest_guarded_v1 | Morning 06:00-11:59 | 5 | 2 | 3 | 40.00% | 21.29 |
| 933000 | a3_round_retest_guarded_v1 | Night 20:00-05:59 | 6 | 3 | 3 | 50.00% | 43.79 |
| 933100 | a3_round_retest_structured_v1 | Afternoon 12:00-15:59 | 5 | 1 | 4 | 20.00% | -61.02 |
| 933100 | a3_round_retest_structured_v1 | Evening 16:00-19:59 | 3 | 2 | 1 | 66.67% | 50.68 |
| 933100 | a3_round_retest_structured_v1 | Morning 06:00-11:59 | 4 | 1 | 3 | 25.00% | -21.42 |
| 933100 | a3_round_retest_structured_v1 | Night 20:00-05:59 | 5 | 3 | 2 | 60.00% | 101.51 |

## T4 Detail - A3 Tier-1 Compat 933400

| Entry Dubai | Exit Dubai | Direction | PnL_001 | Cost R | MFE | MAE | Inside server 12-15 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| none | none | none | 0.00 |  | n/a | n/a | n/a |

- `933400` trades in server-hour 12-15 gate: `0` of `0` order-log rows.
- Any outside gate: `false`.
- Trend shadow pass counts: `{}`
- Trend shadow reasons: `{}`
- Trend shadow reasons on would-signals: `{}`
- A3 plain 933200 rows: `0`; PnL AED_001 `0.00`.
- A3 improved 933300 rows: `0`; PnL AED_001 `0.00`.

MFE/MAE: not available in this report because the direct trade export does not include intratrade path; use the position-path observer or M5 path replay for exact MFE/MAE.

## T5 - A3 A/B And Per-Magic/Session Deduped Totals

| magic | candidate | session | trades | wins | losses | win rate | pnl aed 001 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 933000 | a3_round_retest_guarded_v1 | Afternoon 12:00-15:59 | 4 | 1 | 3 | 25.00% | -45.11 |
| 933000 | a3_round_retest_guarded_v1 | Evening 16:00-19:59 | 4 | 1 | 3 | 25.00% | -27.52 |
| 933000 | a3_round_retest_guarded_v1 | Morning 06:00-11:59 | 5 | 2 | 3 | 40.00% | 21.29 |
| 933000 | a3_round_retest_guarded_v1 | Night 20:00-05:59 | 6 | 3 | 3 | 50.00% | 43.79 |
| 933100 | a3_round_retest_structured_v1 | Afternoon 12:00-15:59 | 1 | 0 | 1 | 0.00% | -15.91 |
| 933100 | a3_round_retest_structured_v1 | Evening 16:00-19:59 | 1 | 1 | 0 | 100.00% | 30.07 |
| 933100 | a3_round_retest_structured_v1 | Morning 06:00-11:59 | 2 | 0 | 2 | 0.00% | -34.84 |

A3 plain/improved co-fired same unique signal count: `0`.

## T5 - A2 Breakout

| magic | candidate | session | trades | wins | losses | win rate | pnl aed 001 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 920101 | breakout_retest | Evening 16:00-19:59 | 1 | 1 | 0 | 100.00% | 49.71 |

## T6 - Direction Split

| direction | trades | wins | losses | win rate | pnl aed 001 |
| --- | --- | --- | --- | --- | --- |
| BUY | 45 | 29 | 16 | 64.44% | 877.34 |
| SELL | 41 | 7 | 34 | 17.07% | -490.18 |

## Per Account / Magic / Session

| account | magic | candidate | session | trades | wins | losses | win rate | pnl aed 001 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1025742 | 920101 | breakout_retest | Morning 06:00-11:59 | 3 | 2 | 1 | 66.67% | 47.46 |
| 1025742 | 920101 | breakout_retest | Night 20:00-05:59 | 1 | 1 | 0 | 100.00% | 49.34 |
| 1025742 | 920201 | swing_breakout_retest_v0 | Evening 16:00-19:59 | 4 | 3 | 1 | 75.00% | 109.88 |
| 1025742 | 920201 | swing_breakout_retest_v0 | Night 20:00-05:59 | 2 | 2 | 0 | 100.00% | 59.59 |
| 1025742 | 920301 | symbol_normalized_round_retest_v0 | Afternoon 12:00-15:59 | 9 | 1 | 8 | 11.11% | -110.25 |
| 1025742 | 920301 | symbol_normalized_round_retest_v0 | Evening 16:00-19:59 | 7 | 4 | 3 | 57.14% | 98.61 |
| 1025742 | 920301 | symbol_normalized_round_retest_v0 | Morning 06:00-11:59 | 16 | 5 | 11 | 31.25% | -18.47 |
| 1025742 | 920301 | symbol_normalized_round_retest_v0 | Night 20:00-05:59 | 10 | 6 | 4 | 60.00% | 179.64 |
| 1025742 | 920401 | round_number_retest_v0 | Afternoon 12:00-15:59 | 1 | 0 | 1 | 0.00% | -36.45 |
| 1025742 | 920401 | round_number_retest_v0 | Evening 16:00-19:59 | 1 | 1 | 0 | 100.00% | 24.71 |
| 1025742 | 920401 | round_number_retest_v0 | Morning 06:00-11:59 | 1 | 1 | 0 | 100.00% | 17.95 |
| 1025742 | 920401 | round_number_retest_v0 | Night 20:00-05:59 | 1 | 0 | 1 | 0.00% | -25.98 |
| 1025742 | 920501 | session_extreme_retest_v0 | Afternoon 12:00-15:59 | 3 | 0 | 3 | 0.00% | -50.78 |
| 1025742 | 920501 | session_extreme_retest_v0 | Evening 16:00-19:59 | 2 | 1 | 1 | 50.00% | 39.46 |
| 1025742 | 920501 | session_extreme_retest_v0 | Night 20:00-05:59 | 1 | 0 | 1 | 0.00% | -19.03 |
| 1033030 | 920101 | breakout_retest | Evening 16:00-19:59 | 1 | 1 | 0 | 100.00% | 49.71 |
| 1033669 | 933000 | a3_round_retest_guarded_v1 | Afternoon 12:00-15:59 | 4 | 1 | 3 | 25.00% | -45.11 |
| 1033669 | 933000 | a3_round_retest_guarded_v1 | Evening 16:00-19:59 | 4 | 1 | 3 | 25.00% | -27.52 |
| 1033669 | 933000 | a3_round_retest_guarded_v1 | Morning 06:00-11:59 | 5 | 2 | 3 | 40.00% | 21.29 |
| 1033669 | 933000 | a3_round_retest_guarded_v1 | Night 20:00-05:59 | 6 | 3 | 3 | 50.00% | 43.79 |
| 1033669 | 933100 | a3_round_retest_structured_v1 | Afternoon 12:00-15:59 | 1 | 0 | 1 | 0.00% | -15.91 |
| 1033669 | 933100 | a3_round_retest_structured_v1 | Evening 16:00-19:59 | 1 | 1 | 0 | 100.00% | 30.07 |
| 1033669 | 933100 | a3_round_retest_structured_v1 | Morning 06:00-11:59 | 2 | 0 | 2 | 0.00% | -34.84 |

## Hypothesis Tags - Day 1 Only

| Hypothesis | Tag | Reason |
| --- | --- | --- |
| H1 round-no-edge | contradict | Exact chart09/chart11 target rows today: 47. Zero rows proves quarantine compliance, not edge behavior. |
| H2 afternoon-weak | support | Afternoon account-scoped unique rows: 18, PnL -258.50 AED_001. |
| H3 counter-trend-loses | contradict | Gold day type was up; compare BUY vs SELL in T6. |
| H4 cost-predicts-losers | n/a | Needs multi-day cost aggregation; single-day cells are too small. |
| H5 structure-beats-veto | n/a | A3 improved 933300 outperformed plain 933200 today, but sample is small. |

## Honesty Notes

- Single near-EOD day only; no edge claim upgraded.
- A1 quarantine, A3 compat, and A3 A/B are measured separately.
- The quarantine time-basis discrepancy must be resolved with the reviewer/owner: work order says 11:22 Dubai; applied report says 11:22 UTC / 15:22 Dubai.
