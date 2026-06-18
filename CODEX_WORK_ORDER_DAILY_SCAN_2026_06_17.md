# CODEX WORK ORDER — EOD XAUUSD scan, 2026-06-17 (Day 3 of tracking week)

Owner: Ali. **Demo only. READ-ONLY: change no EA, preset, cap, arming, profile, order, or position.**
Gather data; write report/CSV/tracker only. End with `git status` proving only analysis outputs changed.

Context — two runtime changes went live today; today is their **first forward-week evidence day**:
- **A1 round quarantine** (~11:22 Dubai): `chart09` `symbol_normalized_round_retest_v0` and `chart11`
  `round_number_retest_v0` set dry-run / broker-action OFF.
- **A3 Tier-1 compat (`933400`)** attached live broker-action (~09:54 Dubai), gate server-hours 12–15,
  stop floor on, trend guard shadow-only.

## Window & scope
- Date: **2026-06-17, 00:00–23:59 Dubai (UTC+4).** All **closed** XAUUSD trades today.
- Accounts: A1 `1025742`, A2 `1033030`, A3 `1033669`. Server `Capital.ComMena-Demo`.
- Snapshot open XAUUSD positions per account at scan time.
- Sessions (Dubai): Morning 06:00–11:59, Afternoon 12:00–15:59, Evening 16:00–19:59, Night 20:00–05:59.

## T1 — Authoritative trade set (real broker fills, not replay)
Per closed trade: account, magic, candidate, direction, entry_time_dubai, exit_time_dubai, session, lots,
entry, exit, sl, tp, `stop_distance_points`, `spread_points`, `cost_r`, profit_aed, **profit_aed_001**
(0.01-normalized), exit_reason, `unique_signal` dedup key, cofire flag. Report raw rows vs unique signals.
**Deduped PnL = one representative row per unique signal (NOT the sum of co-fires)** — do not relabel the
raw co-fire total as "deduped."

## T2 — Round quarantine forward-week check (A1) — the headline today
- For `symbol_normalized_round_retest_v0` and `round_number_retest_v0` on A1: list **any** broker-action
  order/fill with entry_time **after ~11:22 Dubai**. Expected = **0**. State **CLEAN** or **FAIL**.
- Pre vs post-quarantine count for these two candidates today (before 11:22 vs after).
- Confirm chart09/chart11 inputs still `dry_run=true, broker_action=false` (from the applied report; note
  this is report-based, runtime-pending).

## T3 — Protected breakout-core check (A1)
- `breakout_retest` (920101) and `swing_breakout_retest_v0` (920201): trades, win rate, net profit_aed_001,
  by session. Confirm they **kept trading normally** (no halt, no input drift). This proves the quarantine
  didn't harm the protected lane.

## T4 — A3 Tier-1 compat (`933400`) — the deferred validation
- Did it **trade in the 12–15 server window** today? List its trades (entry/exit, direction, PnL_001,
  cost_r, MFE/MAE). If **zero**, say so explicitly — we still need to confirm it fires in-window.
- Confirm every `933400` trade fell inside the gate window (flag any outside = gate bug).
- Shadow trend-guard: count `trend_shadow_pass` true/false and the `trend_shadow_reason` values from its
  signal log (what the guard **would** have blocked, without blocking).
- Confirm A3 plain `933200` and improved `933300` still present and trading as before.

## T5 — A3 A/B + per-account/session/magic deduped totals
- Plain `933200` vs improved `933300` head-to-head on co-fired signals (as prior scans).
- Per account, per magic, per session: trades, win rate, net profit_aed_001 (deduped where co-fire).
- Whole-book deduped total (true one-per-signal), raw vs unique stated separately.

## T6 — Regime (Day 3 of the watch)
- Gold behavior today: **UP / DOWN / RANGE**, open→close move, high/low. This fills the Day-3 regime cell.
- If still an up-day, state it: H3 (counter-trend) stays **UNPROVEN** until a non-up day.

## Outputs
1. `xau-usd/xauusd-phase1/outputs/reports/GOLD_DAILY_SCAN_2026_06_17.md` — tables above, sample sizes up
   front, a short factual "what happened today" (no edge claims).
2. `xau-usd/xauusd-phase1/outputs/reports/XAUUSD_DAILY_ROWS_2026_06_17.csv` — one row per closed trade, all
   T1 fields.
3. Append **Day 3** to `GOLD_DAILY_TRACKING_WEEK_2026_06_15.md`: per-account, sessions, A/B, **quarantine
   forward-week result (chart09/11 new orders = 0?)**, **compat in-window trades**, regime cell (UP/DOWN/
   RANGE), and H1–H5 tags (support/contradict/n/a — no upgrade on one day).
4. End with `git status` showing only these analysis/report files changed.

## Honesty guards
Single day — report counts prominently, draw no edge conclusions, don't over-read tiny per-lane/session
cells. Keep all three runtime states (A1 quarantine, A3 compat, A3 A/B) measured **separately**.
