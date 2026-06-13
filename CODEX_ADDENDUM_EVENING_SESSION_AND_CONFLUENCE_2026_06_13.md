# Codex Addendum — Evening Session Ledger, Stand-Down Shadow, Confluence Logging, Bar Refresh (2026-06-13)

Authorization: owner-approved, additive to `CODEX_WORK_ORDER_A3_REPAIR_LANE_2026_06_13.md`
(T0-T8). Does not change, delay, or reorder T0-T8. All items here are observability/shadow
-logging only — **no new entry-blocking, no new order-sending logic, nothing armed.**
Source basis: `DEEP_DIVE_PROFIT_DUPLICATION_AND_CONSENSUS_2026_06_13.md` and
`EVENING_SESSION_POSITIVE_GOAL_PLAN_2026_06_13.md`.

---

## T9 — Live evening-session PnL ledger (observability only)

- Extend `Phase2PositionPathObserver` (or the weekly-packet generator, whichever already
  has the broker-history read) to compute a running **"Evening session PnL"** figure:
  realized + floating PnL across all accounts/magics, for trades opened in the
  16:00:00-19:59:59 Dubai window, resetting daily.
- Write it to the existing heartbeat/telemetry output (whatever the dashboard already
  reads) and include it as a new line in `A3_WEEKLY_REVIEW_PACKET.md` and the daily
  guard-attribution report: `Evening session PnL (16:00-19:59 Dubai): <value>, status:
  <open/closed for the day>`.
- No new files needed if an existing report already has a natural home for this line.

## T10 — Portfolio-wide evening stand-down: SHADOW LOG ONLY

- Add a computed signal (logged, not enforced): once cumulative Evening-session PnL
  (T9's figure) reaches **<= -200 AED** on a given day, log a row
  `EVENING_STANDDOWN_WOULD_FIRE` with timestamp and the running PnL value, for every
  subsequent entry attempt that evening (whether or not it would have been taken).
- This produces, for each evening, a clear "would the stand-down have fired, and what was
  the realized PnL of trades after that point" comparison — exactly the backtest done in
  `EVENING_SESSION_POSITIVE_GOAL_PLAN_2026_06_13.md` §Finding 3, but live-validated.
- **Do not block any entries.** This is pure logging for 3-5 evenings before any
  arming decision. Add a `T10_evening_standdown_shadow` section to the daily
  guard-attribution report summarizing: did it fire, at what time, what was the
  post-trigger realized PnL.

## T11 — Cross-family confluence shadow logging

- On every signal row already being logged (vetoed or not, per T1's would-signal logging),
  add two fields: `confluence_families` (list of distinct families — ROUND/SESSION/
  BREAKOUT/WR50 — that produced a same-direction signal on the same symbol within the same
  M5 bar) and `confluence_count` (count of distinct families, 1 if none agree).
- This is a read-only cross-reference against the other accounts' signal logs for the same
  bar — no behavioral change to any EA. Reference computation:
  `DEEP_DIVE_PROFIT_DUPLICATION_AND_CONSENSUS_2026_06_13.md` §4 (62 confluent trades,
  41.9% WR vs 34.5% single-family in the existing 11-day sample — this field lets that
  sample grow).
- Include a `confluence_count` breakdown table in `A3_WEEKLY_REVIEW_PACKET.md`.

## T12 — Refresh M5 bar export (prerequisite for two open items)

- Regenerate `xau-usd/xauusd-phase1/outputs/reports/m5_replay_bars/XAUUSD_M5_*.csv` (and
  the equivalent for EURUSD/GBPUSD/USDJPY if not already produced) through **current time**,
  not just through 2026-06-12 09:20. Currently the most recent export stops mid-June-12,
  which blocks:
  1. Backtesting G1 (impulse veto) for the June 9-10 and June-12-evening trades (flagged in
     `DEEP_DIVE_PROFIT_DUPLICATION_AND_CONSENSUS_2026_06_13.md` as a data gap).
  2. Computing the "16:00 Dubai session momentum bias" signal from
     `EVENING_SESSION_POSITIVE_GOAL_PLAN_2026_06_13.md` Step 3.
- Also refresh `PHASE2_IMPULSE_VETO_SHADOW_ROWS.csv` to the same current-time coverage
  (currently stops 2026-06-12 12:29:47, 134/274 of June 12's trades).
- **Ideally this becomes a scheduled/repeatable export** (daily or on-demand) so future
  reviews don't hit the same staleness gap. If a simple cron/scheduled-task pattern already
  exists for other reports, reuse it.

---

## Reports affected

- `A3_WEEKLY_REVIEW_PACKET.md`: add T9 evening-PnL line, T10 stand-down-shadow section,
  T11 confluence breakdown table.
- Daily guard-attribution report (`A3_GUARD_ATTRIBUTION_DAILY_YYYY_MM_DD.md`): add T10
  shadow section.
- New/refreshed data files per T12 (no new report doc required — refresh existing CSVs).

## What NOT to do (carries over from the main work order)

No entry-blocking changes from T9-T11 (shadow/logging only). No threshold tuning beyond
what's specified (-200 AED is the backtested value from the deep-dive; do not adjust without
new evidence). T12 is a data-pipeline task only — it does not itself trigger any new
hypothesis or guard.
