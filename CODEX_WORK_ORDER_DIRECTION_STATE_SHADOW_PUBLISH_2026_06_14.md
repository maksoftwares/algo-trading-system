# CODEX WORK ORDER — Deploy DirectionState as a shadow signal across all demo EAs (2026-06-14)

Owner: Ali (mohdalikhans97.com@gmail.com), 2026-06-14. Demo only.

## Objective
Add the regime/direction detector on top of every demo EA as a **published signal that each
EA reads and logs** — so we accumulate per-strategy, per-regime forward evidence. **No EA
changes any trade decision in this work order.** It is observe-and-record only.

## Why shadow-first (context — keep in the report)
The detector is validated as a classifier, but used as a hard trade gate it *reduced* profit
in backtest: on 7,041 Phase-0 breakout trades (2016–2018), restricting breakout to trend
regimes cut +1,484 R down to +538 R, and aligning trades to the trend direction showed no
stable edge (with-trend +0.171 R vs against +0.195 R, inconsistent year to year). So the
signal ships as **logged-only** now; promotion to an active filter for any specific EA is a
separate, owner-approved step that must be earned on forward evidence.

## Detector logic (port exactly from `direction-detector/direction_state.py`)
Computed on **XAUUSD H1**: `ema_fast=12`, `ema_slow=34`, EMA-slope over `6` bars, Kaufman
efficiency ratio over `12` bars. Rules: direction = sign of (ema_fast−ema_slow) only when it
agrees with the slope sign; force FLAT when efficiency ratio < `0.30`; escalate to STRONG
when efficiency ratio ≥ `0.50`. Output: `direction` (+1/0/−1), `regime`
(STRONG_UP/UP/FLAT/DOWN/STRONG_DOWN), `strength` (0–1).

## Boundaries
- Demo only. **No change to any entry/exit/stop/TP/session logic** on breakout (A2), the A3
  lanes, or anything on A1. EAs only *read and log* the signal.
- Respect the A2 "one trading EA" boundary: the publisher is **not** a second trading EA on
  A2. Run it on an existing observer terminal (or its own observer chart), trading nothing.
- Cross-terminal mechanism: MT5 GlobalVariables are per-terminal, so use the **shared Common
  folder** (`FILE_COMMON`) — publisher writes the state file there; every consumer reads it
  from there. Do not rely on GlobalVariables across terminals.

## Tasks
### T1 — Build the DirectionState publisher (MQL5, trades nothing)
- New observer-style EA/indicator that, on each XAUUSD H1 close, computes the regime per the
  logic above and writes a state file to `FILE_COMMON`, e.g. `dirstate_xauusd.csv` with:
  `utc_time, dubai_time, direction, regime, strength, ema_fast, ema_slow, er`.
- It places no orders, has its own non-trading identity, and appends a history log so the
  state series is auditable.

### T2 — Consumers read + log it (no decision change)
- In the breakout EA on A2 (magic 920101) and the A3 lanes (`Account3RoundRetestGuardedExecutor`
  933000, `Account3RoundRetestStructuredExecutor` 933100), at each signal/order row read the
  latest `dirstate_xauusd` from `FILE_COMMON` and add columns
  `dirstate_direction, dirstate_regime, dirstate_strength` to the existing signal/order CSV.
- The value MUST NOT enter any guard, veto, or order decision. It is recorded and ignored.

### T3 — Prove zero behavior change
- Show that trade/position behavior is identical to before (same signals fire, same orders),
  i.e. the new columns are populated but no trade was taken or skipped because of them.
  Paste evidence (a before/after of the decision path, or a code diff showing the value is
  only written to the log, never read by a guard).

### T4 — Forward scoreboard
- Generate a per-EA, per-regime scoreboard (trades, win rate, PnL by regime) that accumulates
  over the coming weeks, so a future promotion decision can be made on real forward data.

## Reporting
Write `DIRECTION_STATE_SHADOW_PUBLISH_REPORT_2026_06_14.md` with raw evidence: the publisher
file path + sample rows, the new log columns populated on each EA, the T3 no-behavior-change
proof, and the scoreboard template. List any recommended later promotion as a proposal only.

## Out of scope (explicitly not now)
Any active use of the signal in a trade decision — gate, veto, sizing, or direction filter —
on any EA. That is a separate owner-approved step, earned only if the forward scoreboard shows
the signal helps a specific strategy.
