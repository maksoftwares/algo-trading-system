# CODEX WORK ORDER — EOD XAUUSD scan, 2026-06-18 (Day 4 of tracking week)

Owner: Ali. **Demo only. READ-ONLY: change no EA, preset, cap, arming, profile, order, or position.**
Gather data; write report/CSV/tracker only. End with `git status` proving only analysis outputs changed.

Context — two things to confirm today:
- **Round quarantine first FULL day.** It was applied ~15:22 Dubai on 2026-06-17, so **2026-06-18 is the
  first complete day** under it. `chart09` `symbol_normalized_round_retest_v0` and `chart11`
  `round_number_retest_v0` (A1) should place **zero** broker-action orders.
- **A3 is PAUSED.** `1033669` lanes 933200/933300/933400 paused, profit-lock DRY_RUN_DISARMED, 0 exposure.
  Confirm the pause held (zero new A3 orders/positions all day).

## Window & scope
- Date: **2026-06-18, 00:00–23:59 Dubai (UTC+4).** All **closed** XAUUSD trades today.
- Accounts: A1 `1025742`, A2 `1033030`, A3 `1033669`. Server `Capital.ComMena-Demo`.
- Snapshot open XAUUSD positions per account at scan time.
- Sessions (Dubai): Morning 06:00–11:59, Afternoon 12:00–15:59, Evening 16:00–19:59, Night 20:00–05:59.

## T1 — Authoritative trade set (real broker fills, not replay)
Per closed trade: account, magic, candidate, direction, entry_time_dubai, exit_time_dubai, session, lots,
entry, exit, sl, tp, `stop_distance_points`, `spread_points`, `cost_r`, profit_aed, **profit_aed_001**,
exit_reason, `unique_signal` dedup key, cofire flag. Report raw rows vs unique signals. **Deduped PnL = one
representative row per unique signal (NOT the sum of co-fires)** — do not relabel the raw co-fire total as "deduped."

## T2 — Round quarantine forward-week check (A1) — headline
- `symbol_normalized_round_retest_v0` and `round_number_retest_v0`: list **any** broker-action order/fill
  today. Expected = **0** (full day). State **CLEAN** or **FAIL** with tickets.
- Confirm chart09/chart11 inputs still `dry_run=true, broker_action=false` (report-based; note runtime-pending).

## T3 — A1 protected breakout-core health
- `breakout_retest` (920101) and `swing_breakout_retest_v0` (920201): trades, win rate, net profit_aed_001,
  by session. Confirm they **kept trading normally** (no halt, no input drift) — proves the quarantine didn't harm them.

## T4 — A3 pause verification
- Confirm A3 `1033669`: **zero** new orders/closed trades today, **0 open positions, 0 pending orders**, all
  lanes paused, profit-lock disarmed. State **PAUSE_HELD** or flag any exposure.

## T5 — A2 + per-account/session/magic deduped totals
- A2 `1033030` breakout: trades, win rate, net profit_aed_001, by session.
- Per account, per magic, per session: trades, win rate, net profit_aed_001 (deduped where co-fire).
- Whole-book deduped total (true one-per-signal), raw vs unique stated separately.

## T6 — Regime (Day 4 of the watch)
- Gold behavior today: **UP / DOWN / RANGE**, open→close move, high/low. Fills the Day-4 regime cell.
- Direction split (BUY vs SELL win rate + PnL) so the H3 (counter-trend) read continues across regimes.

## Outputs
1. `xau-usd/xauusd-phase1/outputs/reports/GOLD_DAILY_SCAN_2026_06_18.md` — tables above, sample sizes up
   front, short factual "what happened today" (no edge claims).
2. `xau-usd/xauusd-phase1/outputs/reports/XAUUSD_DAILY_ROWS_2026_06_18.csv` — one row per closed trade, all T1 fields.
3. Append **Day 4** to `GOLD_DAILY_TRACKING_WEEK_2026_06_15.md`: per-account, sessions, **quarantine
   forward-week result (chart09/11 = 0?)**, **A3 pause held**, regime cell (UP/DOWN/RANGE), direction split,
   H1–H5 tags (support/contradict/n/a — no upgrade on one day).
4. End with `git status` showing only these analysis/report files changed.

## Honesty guards
Single day — report counts prominently, draw no edge conclusions, don't over-read tiny cells. Keep A1
quarantine, A2, and the A3 pause measured separately.
