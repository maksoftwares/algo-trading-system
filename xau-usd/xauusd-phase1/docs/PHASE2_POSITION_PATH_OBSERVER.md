# Phase 2 Position Path Observer

Status: `READY_FOR_OWNER_ATTACHMENT_DECISION`
Created: 2026-06-12

## Purpose

This observer records the path of every open demo position every 10 seconds. It is designed to answer questions that closed-trade tables cannot answer:

```text
Did the trade reach profit before reversing?
How far did it get before SL?
Could break-even, partial profit, time stop, or ATR trail have helped?
Did spread spikes or slippage contribute to the exit?
How much same-symbol same-direction stacking existed while the trade was open?
```

## Boundary

This is a camera, not a hand.

```text
No order placement
No position modification
No position exit action
No live capital authorization
No canonical Phase 2 approval
```

The EA is dry-run locked:

```text
InpDryRunOnly=true
broker_action_allowed=false
demo server required
live/real server names refused
```

## Source

```text
xau-usd/xauusd-phase1/mt5/Experts/Phase2PositionPathObserver.mq5
```

Safe preset:

```text
xau-usd/xauusd-phase1/mt5/Presets/Phase2PositionPathObserver.demo_account_readonly.set
```

## Collection Design

One EA instance is enough. `PositionsTotal()` is account-wide, so one observer on one chart snapshots all open positions visible to that MT5 account.

Collection is 24 hours, not evening-only. Session filters are applied later in Python so we do not create blind spots.

Evening analysis target:

```text
Primary review window: Evening 16:00-19:59 Dubai time
Required view: all EAs and all open positions that operate inside that window
Collection rule: do not filter at source; filter reports by time_bucket later
```

This matters because a position can open before evening and still be alive during evening, or open during evening and close later at night. The observer keeps the full path so the evening report can show the real before/during/after behavior instead of a cropped fragment.

Snapshot cadence:

```text
Every 10 seconds
Immediately at startup for already-open positions
Close-detected summary when a tracked ticket disappears
Daily-rotated snapshot CSV
One cumulative close summary CSV
```

## Review #10 Fixes

The reviewer-approved changes have been applied before attachment:

```text
Exit slippage attribution now uses the actual exit reason.
SL exits compare exit price to the latest observed SL.
TP exits compare exit price to the latest observed TP.
Manual, break-even, guardian, unknown, or missing close reasons write NA.
Magic mapping covers current demo, repaired, WR50, WST, W1D1, and historical P2WEAKNESS lanes.
Path logging is protected from slow MT5 history synchronization; ATR/EMA/D1 fields are marked unavailable instead of delaying the account-wide position snapshot.
```

## Restart Semantics

The observer is an enrichment layer, not the legal source of closed trades.

```text
Broker history CSV = closure ground truth
position_path_log_YYYYMMDD.csv = intra-trade path evidence
position_path_summary.csv = close enrichment when the observer was running
```

If the terminal is offline or restarted while a position is open, the broker CSV still owns the final trade result. The observer resumes from the next visible open-position snapshot, and any missing path interval must be treated as unavailable evidence rather than guessed data.

## Files Written In MT5 Files Folder

```text
position_path_log_YYYYMMDD.csv
position_path_summary.csv
position_path_observer_startup.csv
```

## Snapshot Fields

The snapshot log includes:

```text
ts_utc, ts_broker, ts_local, ts_dubai, time_bucket, observed_in_evening
ticket, magic, candidate, comment, symbol, direction, volume
entry time, entry price, current SL/TP, initial SL/TP
bid, ask, spread, current price, floating PnL
unrealized_R using the first-seen SL distance
distance to SL/TP
ATR14 M5
M15/H1 EMA20 slope and status
D1 bias and status
open position count
same-symbol same-direction count
account equity and floating total
row_type: FIRST_SEEN, SNAPSHOT, CLOSE_DETECTED via summary
```

## Evening Review Columns

For the owner's evening-performance review, use:

```text
time_bucket = Evening 16:00-19:59
observed_in_evening = true
candidate
symbol
direction
unrealized_pnl_aed
unrealized_R
distance_to_sl_points
distance_to_tp_points
same_symbol_same_dir_count
row_type
```

`observed_in_evening=true` is the safest filter for "all EAs that operated in evening time" because it keeps a trade in the evening review even if it opened before 16:00 or closed after 19:59.

## What Comes Next

After data accumulates, `analyze_position_paths.py` should answer:

```text
Loser anatomy: what losers reached +0.3R, +0.5R, +1R first?
Winner giveback: how much profit was given back before close?
Spread-spike stop hits
Slippage distribution
Time-stop curve
Exposure concentration replay
ATR-trail replay
```

No exit rule should be deployed directly from this data. Any promising rule must go through shadow rule, fresh forward week, and explicit owner/reviewer approval.
