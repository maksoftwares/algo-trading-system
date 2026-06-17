# CODEX WORK ORDER — Daily XAUUSD trade scan, 2026-06-16 (Day 2 of tracking week)

Owner: Ali (mohdalikhans97.com@gmail.com). **Demo only. READ-ONLY: change no EA, preset, cap,
arming, profile, or live setting.** Gather data and write report/CSV files only. End with `git status`
proving only analysis/report outputs changed.

Context: today the A3 breakout A/B went live (~15:23 Dubai) — round lanes detached, plain breakout
`933200` and improved breakout `933300` now trading. So today's headline is the A/B, plus confirming
round is winding down. A1 `1025742` and A2 `1033030` ran as usual and must not be touched.

## Window & scope
- Date: **2026-06-16, 00:00–23:59 Dubai (UTC+4).** All **closed** XAUUSD trades today.
- Accounts: A1 `1025742`, A2 `1033030`, A3 `1033669`. Server `Capital.ComMena-Demo`.
- Also snapshot **currently-open** XAUUSD positions per account at scan time.
- Sessions (Dubai): Morning 06:00–11:59, Afternoon 12:00–15:59, Evening 16:00–19:59, Night 20:00–05:59.

## T1 — Authoritative trade set (real broker fills, not replay/observer logs)
Per closed trade: account, magic, lane/candidate, direction, entry_time_dubai, exit_time_dubai,
session, lots, entry, exit, sl, tp, `stop_distance_points`, `spread_points`, `cost_r` (= spread ÷
stop_distance), profit_aed, **profit_aed_001** (normalized to 0.01 lot), exit_reason, and a
`unique_signal` dedup key (same entry_time + symbol + direction + entry price collapses stacked
lanes). Report raw row count vs unique-signal count, and how many were real broker-closed vs only
replay-resolvable. Flag **co-fire** where `933200` and `933300` (or any A1/A2 lane) share a signal.

## T2 — A3 A/B head-to-head (today's headline)
- Per magic **933200 (plain)** and **933300 (improved)**: n trades, wins, win rate, net profit_aed_001,
  MFE/MAE in R, avg & max `cost_r`.
- **Co-fired signals only:** for every signal both lanes saw, line them up — what did plain do
  (won/lost, R) vs improved (took it? blocked it? BE/partial changed the exit?).
- Lane B management events from the management log: counts of `TREND_AGAINST_SIGNAL` (guard blocks),
  `BREAKEVEN_SLTP_SENT`, `PARTIAL_CLOSE_SENT`, `PARTIAL_SKIP_MIN_VOLUME`.
- **For each Lane B trend-block:** what did the matching plain `933200` trade do (win/lose, R)? This
  is the direct read on whether the guard helped or hurt *today*.
- Net-of-improvements line: (losers the guard/exits saved) − (winners they clipped), in R and AED_001.
- Note the partial reality: at fixed 0.01 lot a partial cannot leave a runner — confirm
  `PARTIAL_SKIP_MIN_VOLUME` is what logs, and treat BE as the only live exit modifier.

## T3 — Round shutdown reconciliation
- Magic `933000` and `933100`: any closed trades today, with final closed profit_aed today.
- The residual open position **ticket `4100781`, magic `933100`** (BUY 0.01, open 4341.79, SL 4336.14,
  TP 4350.21): did it close today? If yes, at SL or TP, and PnL. If still open, current floating PnL.
- **Confirm zero NEW round entries after detach** (no `933000`/`933100` order with entry_time after the
  ~15:23 switchover). State explicitly: clean or not.

## T4 — A1/A2 as usual (and untouched)
- Per account & magic: trades, win rate, net profit_aed_001, broken out by session.
- Confirm A1/A2 configs unchanged today (process/account snapshot; no preset/arming edits).

## T5 — Deduped daily totals (with honesty guards)
- Account-level and whole-book deduped profit_aed_001 for today, raw vs unique.
- **Label everything single-day.** This is ONE day — report counts prominently, draw no "edge"
  conclusions, don't over-read tiny per-session/per-lane cells. Just the numbers.

## Outputs
1. `xau-usd/xauusd-phase1/outputs/reports/GOLD_DAILY_SCAN_2026_06_16.md` — the tables above, sample
   sizes stated up front, plus a short factual "what happened today" (no edge claims).
2. `xau-usd/xauusd-phase1/outputs/reports/XAUUSD_DAILY_ROWS_2026_06_16.csv` — one row per closed trade
   with all T1 fields (+ dedup key + cofire flag).
3. Append a **Day 2** row to `GOLD_DAILY_TRACKING_WEEK_2026_06_15.md` and tag any observation against
   the existing H1–H5 hypotheses (support / contradict / n/a) — without upgrading any hypothesis on
   one day.
4. End with `git status` showing only these analysis/report files changed.
