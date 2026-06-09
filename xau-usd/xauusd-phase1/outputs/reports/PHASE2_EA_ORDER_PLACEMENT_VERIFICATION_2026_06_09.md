# Phase 2 EA Order-Placement Verification

Generated: 2026-06-09 12:41 UTC / 16:41 Asia-Dubai

Status: RUNNING_BUT_NOT_ALL_PLACING

## Verdict

Not all attached EAs are placing orders.

The standard Capital.com demo terminal is connected, demo-marked, trade-enabled, and expert trading is enabled. The active chart profile has 20 EA charts attached:

- 14 standard experimental demo executors.
- 3 repaired experimental demo executors.
- 3 WR50 experimental charts.

The EAs are not globally stopped. Signal/startup/block logs are still updating after the 16:32 Dubai restart. However, no new broker entry deals were opened after that restart at the time of this verification.

## Entry-Deal Counts

MT5 history was queried directly from `C:\Program Files\MetaTrader 5\terminal64.exe`.

| Window | New broker entry deals | Interpretation |
|---|---:|---|
| Since standard terminal restart at 16:32 Dubai | 0 | Real immediate drop after restart. |
| Last 2 hours | 5 | All entries occurred before the restart. |
| Last 6 hours | 12 | Standard demo, repaired demo, and P2WEAKNESS all had entries. |
| Last 24 hours | 59 | Demo execution is working overall. |

## Standard 14-EA Lane

| Magic | EA | Symbol | Entries last 24h | Latest entry UTC | Latest state |
|---:|---|---:|---:|---|---|
| 920101 | `breakout_retest` | XAUUSD | 4 | 2026-06-09 11:15 | Running; latest signal no setup |
| 920102 | `breakout_retest` | EURUSD | 2 | 2026-06-09 09:35 | Running; latest signal no setup |
| 920104 | `breakout_retest` | GBPUSD | 3 | 2026-06-08 22:05 | Running; latest attempts cost-guarded/no setup |
| 920201 | `swing_breakout_retest_v0` | XAUUSD | 4 | 2026-06-09 11:15 | Running; latest signal no setup |
| 920202 | `swing_breakout_retest_v0` | EURUSD | 1 | 2026-06-08 18:50 | Running; latest signal no setup |
| 920204 | `swing_breakout_retest_v0` | GBPUSD | 1 | 2026-06-08 13:52 | Running; latest attempts cost-guarded/no setup |
| 920301 | `symbol_normalized_round_retest_v0` | XAUUSD | 16 | 2026-06-09 11:00 | Running; currently constrained by per-instance exposure/no setup |
| 920302 | `symbol_normalized_round_retest_v0` | EURUSD | 0 | n/a | Running; no accepted entry in 24h |
| 920304 | `symbol_normalized_round_retest_v0` | GBPUSD | 1 | 2026-06-08 14:20 | Running; latest attempts cost-guarded/no setup |
| 920401 | `round_number_retest_v0` | XAUUSD | 16 | 2026-06-09 11:00 | Running; currently constrained by per-instance exposure/no setup |
| 920404 | `round_number_retest_v0` | GBPUSD | 0 | n/a | Running; no accepted entry in 24h |
| 920501 | `session_extreme_retest_v0` | XAUUSD | 5 | 2026-06-09 00:00 | Running; latest signal no setup |
| 920502 | `session_extreme_retest_v0` | EURUSD | 2 | 2026-06-09 09:05 | Running; latest signal no setup |
| 920504 | `session_extreme_retest_v0` | GBPUSD | 0 | n/a | Running; no accepted entry in 24h |

Standard lane summary: 11 of 14 attached standard EAs opened at least one entry in the last 24 hours. None opened a new entry after the 16:32 Dubai restart.

## Repaired Lane

| Magic | EA | Symbol | Entries last 24h | Latest entry UTC | Latest state |
|---:|---|---:|---:|---|---|
| 921101 | `symbol_normalized_round_retest_v0_repair_v1` | XAUUSD | 1 | 2026-06-09 12:30 | Running; entry existed before restart and later closed by SL |
| 921201 | `session_extreme_retest_v0_repair_v1` | XAUUSD | 0 | n/a | Running; no accepted entry in 24h |
| 921202 | `session_extreme_retest_v0_repair_v1` | EURUSD | 0 | n/a | Running; direction filter blocked latest eligible rows |

## WR50 Lane

| Magic | EA | Symbol | Entries last 24h | Latest log state |
|---:|---|---:|---:|---|
| 930100 | `WR50_BreakoutExit1R_v0` | XAUUSD | 0 | Startup/block logs updated after restart; latest blocks are mostly `no_breakout_retest_signal`. |
| 930300 | `WR50_BreakoutWideStop_v0` WST12 | XAUUSD | 0 | Startup/block logs updated after restart; latest blocks are mostly `no_breakout_retest_signal` or same-symbol exposure. |
| 930400 | `WR50_BreakoutWideStop_v0` WST15 | XAUUSD | 0 | Startup/block logs updated after restart; latest blocks are mostly `no_breakout_retest_signal` or same-symbol exposure. |

## Separate P2WEAKNESS Lane

The separate P2WEAKNESS demo lane also has actual broker evidence:

| Magic | EA | Symbol | Entries last 24h | Latest entry UTC |
|---:|---|---:|---:|---|
| 930101 | `P2WEAKNESS_BR_V1` | XAUUSD | 3 | 2026-06-09 07:35 |

## Main Reasons For The Drop

1. The standard terminal was restarted at 16:32 Dubai; the post-restart sample was only a few M5 bars.
2. Latest standard executor signal rows are updating but mostly show `would_signal=false`.
3. GBPUSD candidates are now set to 0.05 lots, but their latest eligible rows were mostly blocked by `estimated_cost_r_exceeds_threshold` or had no valid setup.
4. XAUUSD `symbol_normalized_round_retest_v0` and `round_number_retest_v0` still have per-instance one-open-position protection, so fresh same-instance entries can be blocked while exposure exists.
5. WR50 is alive but currently block-logging rather than order-logging, mostly because there is no qualifying breakout-retest signal.

## Operator Conclusion

This is not an MT5 permission failure and not a global EA shutdown. It is a real short-term drop in accepted entries after the restart, caused by no fresh setup/guard conditions rather than missing attachments.

No runtime changes were made by this verification task.
