# Gold Daily Tracking — Week of 2026-06-15

**Purpose:** record the same facts about gold (XAUUSD) trading every day this week, across all
three accounts, so that at week's end we can find what is **common across all days**. The
discipline: one day is noise (e.g., today shorts lost only because gold rose); a pattern that
repeats across up-days, down-days, and chop-days is a **real root cause** worth fixing.

**Rule for the week:** observe and document only. **No live changes to any EA or setting.**

**Daily loop:** each evening Codex exports the day's gold trades (per account) into the repo;
this file gets one new dated entry from that data.

---

## What we record every day (kept identical so days are comparable)
- Gold's behavior: up / down / range, and rough move.
- Per account: trades, net PnL, win rate (A1, A2, A3).
- Best & worst **session** (PnL, win rate).
- Best & worst **direction**, and whether the losing side was **with or against** the day's trend.
- **EA-T1 (veto) vs EA-T2 (structure)** on A3 — which did better.
- **Breakout vs round** performance.
- **Cost** signal (cheap vs expensive setups) — if spread data is exported.
- Anomalies / notable events.

## Common-thread hypotheses (what we're trying to confirm or kill by Friday)
These came out of Day 1. If a hypothesis holds **every day regardless of gold's direction**, it
is a root cause. If it flips with the day, it was coincidence.

- **H1 — Round entry has no edge:** round-retest loses while breakout/structure does better, *every* day.
- **H2 — Afternoon is weak:** the afternoon session is among the worst *regardless* of up/down day.
- **H3 — Counter-trend loses:** the *losing* side flips with gold's direction (down-day → longs lose, shorts win). If the loser is always "shorts," it was just coincidence (every day happened to be up).
- **H4 — Cost predicts losers:** the cheapest-cost setups stay positive; expensive ones lose, every day.
- **H5 — Structure beats veto:** EA-T2 (structure) keeps out-performing EA-T1 (veto).

---

## Regime watch — guard against over-claiming direction-dependent hypotheses

**Regime coverage:** Day 1 (06-15) UP · Day 2 (06-16) UP · Day 3 (06-17) **DOWN** · Day 4 (06-18) **DOWN/WHIPSAW** · Day 5 —
→ so far **2 up-days, 2 down-days, 0 range-days.**

**Day 4 (06-18) — whipsaw, does NOT cleanly test H3.** Net close only −19 (open 4235 → close 4216) but a
huge intraday range (high 4329 / low 4201): gold rallied ~+94 to 4329 first, then crashed. Mechanical
retest **shorts got chopped in the up-leg** — SELL 34 / 5.9% win / −515 vs the lone BUY +49. Superficially
this "contradicts" H3, but it's a whipsaw confound (shorts lost to the intraday rally, not to a clean
down-trend), so treat H3 as **untested today**, not contradicted. Everything lost (−483 raw / −174 deduped),
incl. the protected breakout core (−288) and A2 (−44).
**Governance flag:** A3 (1033669) was supposed to be PAUSED but the scan shows **12 A3 trades today**
(933200/933300 + a new **933500 "A3_SOFT_RETEST_V2"** lane), −300. Pause appears to have failed / been
overridden and an unreviewed candidate is live — see Day-4 writeup; needs urgent resolution.

**Day 3 (DOWN) — the flip occurred as H3 predicts.** Gold fell hard (≈ −106 pts open→close) and the
losing side flipped to **longs**: BUY 60 / 21.7% win / −728 vs SELL 22 / 40.9% / −114 (breakout lanes:
counter-trend longs won just 8.7%). Shorts lost on the two up-days; longs lost on the down-day — the
signature of **counter-trend-loses**, and it rules out the "shorts always lose" alternative. This is
H3's first non-up evidence and it flipped correctly → upgrade H3 from "up-regime only — UNPROVEN" to
**"supported across regimes, 1 down-day observed."** Not yet *confirmed* (one down day, small; with-trend
shorts only lost-less rather than profited) — needs ≥1 more down/range day. H4 (cost) still pending.

**Hard rule for Friday:** do **not** mark H3 confirmed unless a **non-up day** shows the losing side
flip (down-day → longs lose / shorts win). If all five days come in up-trending, H3 stays
**"consistent in up-regime only — UNPROVEN"** and tracking continues into a down week rather than
declaring a root cause. (H1 / round-family is exempt — it already loses across both this week's
up-days and the prior fortnight's down-days, so it is the one direction-independent bleeder we can
already trust.)

---

## Day 1 - Monday 2026-06-15

**Gold:** UP day from scan context: open 4236.31000 -> close 4320.03000 (8372.00 points), high 4369.18000, low 4236.31000.

**Per account (gold only, normalized to 0.01 lot, closed broker fills):** see `xau-usd/xauusd-phase1/outputs/reports/GOLD_DAILY_SCAN_2026_06_15.md` and `XAUUSD_DAILY_ROWS_2026_06_15.csv`.

- 1025742: 66 raw closed rows, 426.30 AED_001, 45.45% win rate.
- 1033030: 1 raw closed rows, 49.71 AED_001, 100.00% win rate.
- 1033669: 36 raw closed rows, 62.20 AED_001, 38.89% win rate.
- Whole-book raw: 103 rows, 538.21 AED_001.

**Round quarantine:** chart09/chart11 target rows `47` = `FAIL`.

**A3 pause:** `PAUSE_FAIL`; A3 closed rows `36`, PnL `62.20` AED_001.

**Direction split (account-scoped unique):** BUY 45 / 64.44% / 877.34; SELL 41 / 17.07% / -490.18.

**Hypothesis scorecard (one-day tags only):** H1 `contradict`; H2 `support`; H3 `contradict`; H4 `n/a`; H5 `n/a`.

**No edge upgrade:** this is one day and is reported as measurement only.

## Day 2 - Tuesday 2026-06-16

**Gold:** **UP day** from scan context: open 4320.55 -> latest/close 4337.54 (+16.99), high 4354.84, low 4305.71.

**Per account (gold only, normalized to 0.01 lot, closed broker fills):**

| group | trades | wins | losses | win_rate | pnl_aed_001 |
| --- | --- | --- | --- | --- | --- |
| A1 | 74 | 28 | 46 | 37.84% | -75.48 |
| A3 | 15 | 4 | 11 | 26.67% | -155.49 |

**Raw vs unique:** raw closed rows `89`, unique-signal groups `76`. Whole-book raw PnL `-230.97` AED_001; unique-signal PnL `-230.97` AED_001.

**Best/worst session:** Evening was best (`+184.99`, 50.00% win rate). Afternoon was worst (`-181.26`, 18.75% win rate).

**A3 A/B:** `933200` plain closed `2` trade(s), PnL `-30.28` AED_001. `933300` improved closed `0` trades; no Lane B management events fired. This is n/a for H5 today, not evidence of failure.

**Round shutdown:** retired round magics `933000/933100` closed `13` trade(s) today. Residual ticket `4100781` closed as SL for -21.02 AED_001. New round entries after ~15:23 Dubai: `0` (CLEAN).

**Hypothesis scorecard (one-day tags only):** H1 `support`; H2 `support`; H3 `n/a`; H4 `n/a - cost needs multi-day aggregation`; H5 `n/a - improved Lane B had no broker fills today`.

**Notes:** See `xau-usd/xauusd-phase1/outputs/reports/GOLD_DAILY_SCAN_2026_06_16.md` and `XAUUSD_DAILY_ROWS_2026_06_16.csv`. Single day only; no edge conclusion upgraded.

## Day 3 - Wednesday 2026-06-17

**Gold:** DOWN day from scan context: open 4333.76 -> latest/close 4227.41 (-10635 points), high 4382.10, low 4226.27.

**Regime update:** this is the first DOWN day in the forward-week tracker. Current coverage is Day 1 UP, Day 2 UP, Day 3 DOWN, Day 4 pending, Day 5 pending. H3 gets directional support today, but one down day is still too small to confirm it.

**Per account (gold only, normalized to 0.01 lot, closed broker fills):** see `xau-usd/xauusd-phase1/outputs/reports/GOLD_DAILY_SCAN_2026_06_17.md` and `XAUUSD_DAILY_ROWS_2026_06_17.csv`.

- A1: 71 raw closed rows, -344.60 AED_001, 30.99% win rate.
- A2: 1 raw closed row, -92.42 AED_001, 0.00% win rate.
- A3: 10 raw closed rows, -404.90 AED_001, 0.00% win rate.
- Whole-book raw: 82 rows, -841.92 AED_001.

**Round quarantine:** using the applied report timestamp (`2026-06-17 11:22 UTC` / `15:22 Dubai`), post-quarantine target rows were 0 = CLEAN. Using the work-order's `11:22 Dubai` wording, there are 11 target rows and the time basis needs owner/reviewer clarification.

**A3 Tier-1 compat:** magic `933400` fired 1 closed trade, inside server-hour gate 12-15, PnL -92.31 AED_001. Shadow trend guard remained shadow-only.

**A3 A/B:** plain `933200` lost materially more than improved `933300`; no plain-vs-improved same-signal cofire was observed in the daily rows.

**Hypothesis scorecard (one-day tags only):** H1 `support`; H2 `support but weaker`; H3 `support on first down day`; H4 `n/a`; H5 `support, tiny sample`.

**No edge upgrade:** this is one near-EOD day and is reported as measurement only.

## Day 4 - Thursday 2026-06-18

**Gold:** DOWN day from scan context: open 4235.43000 -> close 4216.52000 (-1891.00 points), high 4329.84000, low 4201.26000.

**Per account (gold only, normalized to 0.01 lot, closed broker fills):** see `xau-usd/xauusd-phase1/outputs/reports/GOLD_DAILY_SCAN_2026_06_18.md` and `XAUUSD_DAILY_ROWS_2026_06_18.csv`.

- 1025742: 22 raw closed rows, -138.83 AED_001, 27.27% win rate.
- 1033030: 1 raw closed rows, -44.12 AED_001, 0.00% win rate.
- 1033669: 12 raw closed rows, -299.97 AED_001, 16.67% win rate.
- Whole-book raw: 35 rows, -482.92 AED_001.

**Round quarantine:** chart09/chart11 target rows `0` = `CLEAN`.

**A3 pause:** `PAUSE_FAIL`; A3 closed rows `12`, PnL `-299.97` AED_001.

**Direction split (account-scoped unique):** BUY 1 / 100.00% / 48.57; SELL 29 / 20.69% / -515.02.

**Hypothesis scorecard (one-day tags only):** H1 `n/a`; H2 `n/a`; H3 `contradict`; H4 `n/a`; H5 `support`.

**No edge upgrade:** this is one day and is reported as measurement only.

## Day 5 - Friday 2026-06-19

**Gold:** DOWN day from scan context: open 4216.81000 -> close 4155.26000 (-6155.00 points), high 4219.41000, low 4121.71000.

**Per account (gold only, normalized to 0.01 lot, closed broker fills):** see `xau-usd/xauusd-phase1/outputs/reports/GOLD_DAILY_SCAN_2026_06_19.md` and `XAUUSD_DAILY_ROWS_2026_06_19.csv`.

- 1025742: 3 raw closed rows, 90.30 AED_001, 66.67% win rate.
- 1033030: 2 raw closed rows, -23.47 AED_001, 0.00% win rate.
- 1033669: 0 raw closed rows, 0.00 AED_001, n/a win rate.
- Whole-book raw: 5 rows, 66.83 AED_001.

**Round quarantine:** chart09/chart11 target rows `0` = `CLEAN`.

**A3 pause:** `PAUSE_HELD`; A3 closed rows `0`, PnL `0.00` AED_001.

**Direction split (account-scoped unique):** BUY 2 / 0.00% / -23.47; SELL 3 / 66.67% / 90.30.

**Hypothesis scorecard (one-day tags only):** H1 `n/a`; H2 `n/a`; H3 `support`; H4 `n/a`; H5 `n/a`.

**No edge upgrade:** this is one day and is reported as measurement only.

---

## End-of-Week Synthesis (fill Friday)
For each hypothesis H1–H5, mark how many of the 5 days it held. Anything that held on
**up-days, down-days, and chop-days alike** is a confirmed root cause to address next week.
Anything that flipped with the day's direction was coincidence. The confirmed common thread
becomes the single problem we fix.

**Regime-coverage gate (required):** if the week contained no down-day or range-day, H3 and H4 are
**not** eligible to be marked "confirmed" no matter how many up-days they held — record them as
"unproven (up-regime only)" and carry them into a down week. Only hypotheses demonstrably held on a
non-up day (plus H1, already proven across both regimes) may be called a root cause. See the
**Regime watch** section near the top.

