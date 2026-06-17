# CODEX NIGHTLY GOLD SCAN — reusable, run ~00:00 Dubai each night this week

Owner: Ali (mohdalikhans97.com@gmail.com). Demo only. **READ-ONLY — change nothing live this week.**

## Purpose
End-of-day snapshot of GOLD (XAUUSD) trading for the day just finished, across all three demo
accounts, so the day can be documented and compared with the rest of the week. Pure export.

## Each night
Set `DATE` = the Dubai trading day that just ended (e.g. tonight = 2026-06-15).
Window = that Dubai day 00:00 → 24:00 (for the first night, market-open Sunday 22:00 UTC → now).
Symbol = **XAUUSD only.** Write everything to `xau-usd/xauusd-phase1/outputs/reports/`.

## What to export

### 1. Per-account gold trades → `EOD_GOLD_A1_<DATE>.csv`, `EOD_GOLD_A2_<DATE>.csv`, `EOD_GOLD_A3_<DATE>.csv`
A1 = `1025742`, A2 = `1033030`, A3 = `1033669`. One row per closed XAUUSD deal, columns:
`account, entry_time_utc, entry_time_dubai, exit_time_utc, candidate, magic, direction, lots,
entry_price, exit_price, sl, tp, stop_distance_points, spread_points, cost_r, exit_reason(SL/TP/other),
profit_aed, dirstate_regime`
**Important: include `spread_points` and `cost_r` (= spread ÷ stop distance) this time — they were
missing before and the cost signal is the one we most need to track.**

### 2. Open gold positions right now → include per account
ticket, magic, direction, lots, entry, current floating PnL.

### 3. Day's gold context → `EOD_GOLD_CONTEXT_<DATE>.csv` (one row)
`date, gold_open, gold_high, gold_low, gold_close, net_move_pts, day_type(up/down/range)` — from
XAUUSD H1/M5 bars. (This is how we classify the day for the trend test.)

### 4. Refresh the observer evidence (so we can read what they say)
Regenerate/append `OBSERVER_OUTCOME_RESOLUTION_ROWS.csv` and
`DIRECTION_STATE_SHADOW_SCOREBOARD_*` for the day if the pipeline supports it. If observer
outcomes are still replay-only (not broker-fill), note that in the report — do not change it.

## Report → `EOD_GOLD_SCAN_REPORT_<DATE>.md`
Per account: total XAUUSD trades, net PnL, win rate, best/worst session, long vs short PnL.
The day_type from section 3. Row counts and file paths. Raw broker-history query appended.
If an account had zero gold trades, say so explicitly.

## Boundaries
Read-only. Do not modify any EA, preset, arming flag, session gate, magic, or the observers'
logic. Gold only. This is the same prompt every night — only `DATE` changes.
