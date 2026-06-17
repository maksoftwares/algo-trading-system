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

**Regime coverage:** Day 1 (06-15) UP · Day 2 (06-16) UP · Day 3 — · Day 4 — · Day 5 —
→ so far **2/2 up-days, 0 down-days, 0 range-days.**

H3 (counter-trend loses) and H4 (cost predicts losers) are **direction-sensitive and cannot be
confirmed inside a single regime.** Both tracked days were up-trends, so "shorts lose" and
"counter-trend loses" are indistinguishable right now — the losing side has had no chance to flip.

**Hard rule for Friday:** do **not** mark H3 confirmed unless a **non-up day** shows the losing side
flip (down-day → longs lose / shorts win). If all five days come in up-trending, H3 stays
**"consistent in up-regime only — UNPROVEN"** and tracking continues into a down week rather than
declaring a root cause. (H1 / round-family is exempt — it already loses across both this week's
up-days and the prior fortnight's down-days, so it is the one direction-independent bleeder we can
already trust.)

---

## Day 1 — Monday 2026-06-15

**Gold:** **UP day** (confirmed from context export): open 4236 → close 4320 (+84), high 4369, low = open — gold never traded below the open. Afternoon stall near the highs, then a late-session fade.

**Per account (gold only, all 0.01 lot) — FINALIZED at midnight from Codex's scan report:**

| Account | Trades | Net PnL | Win rate |
|---|---:|---:|---:|
| A1 (1025742) | 66 | +426.3 | 45% |
| A2 (1033030) | 1 | +49.7 | 100% (1 evening breakout, won at TP) |
| A3 (1033669) | 36 | +62.2 | 39% |
| **All gold** | **103** | **+538.2** | **44%** |

_(The partial 21:48 snapshot read +649; the day faded late — A3 gave back roughly half its gains in the final hours. Final = +538.)_

**Sessions (combined real trades):** Night **best** (A1 +318/77%, A3 +209/86%); Evening good (A1 +306/65%); Morning flat; **Afternoon worst** (A1 −197/8%, A3 −106/22%).

**Direction:** longs (with the up-trend) won; shorts (against) lost. 80% of winners were longs, all exited at take-profit; 67% of losers were shorts, all exited at stop. Realized reward:risk ~1.8:1 — *mechanics were fine; outcome was decided by trend side.*

**A3 lanes:** EA-T2 structure **+101.6** > EA-T1 veto **+24.3**. (supports H5)

**Breakout vs round:** breakout/structure positive; plain round-fade the weak link. (supports H1)

**Cost:** from the observer dataset (not today's live export — no spread column today): cheapest-cost setups +0.16 R / 48% win, most expensive −0.40 R. Robust, direction-independent. (supports H4)

**Anomalies / notes:**
- Same losing night short (sell 4289 → stop 4305) taken on **both A1 and A3** — correlated accounts double the same wrong bet.
- Observer "session" verdict (replay-based) **contradicts** the real trades (replay said Night worst; reality Night best). Observers score by synthetic replay, not real fills — their timing answer is currently untrustworthy.

**Day-1 candidate root cause:** the round entry fades levels and loses fighting a trend, worst in the afternoon stall. The trend-direction part is *day-dependent* (today was up) and must be re-checked on a down day before trusting.

**Counterfactual (illustrative only):** with afternoon + counter-trend filters, A3 today would have been better than actual — but most of that gain was hindsight on an up-day, not a proven edge.

**Cost (first real-trade read of H4):** today's export finally includes spread/cost per trade. On the trades visible, the cost signal showed up strongly and for the first time on *real* fills — cheapest-cost quarter ~86% win, most expensive quarter ~10% win (−226 AED). Preliminary (late trades not yet fully synced) but the direction is unmistakable and matches the observer data. H4 is the standout so far.

**Day-1 hypothesis scorecard:**
- H1 round-no-edge: _tentative_ — A3 (round) only +62 at 39% while breakout/structure did better.
- H2 afternoon-weak: **held** — afternoon worst on both A1 (−197) and A3 (−106).
- H3 counter-trend-loses: _pending_ — longs won / shorts lost, but it was an up-day; need a **down day** to see if it flips.
- H4 cost-predicts-losers: **held strongly (preliminary)** — cheap won, expensive lost.
- H5 structure-beats-veto: **did NOT hold today** — A3 lanes finished roughly tied (~+101 each).

**Data-quality note:** tonight's per-trade CSVs landed incomplete in my view (84 of 103 trades; A2 profit blank/NaN). Day-1 totals above are taken from Codex's scan-report summary (its complete computation). Action for Codex before tomorrow: confirm the export writes every closed row and fix the A2 blank profit, so the week's per-trade data is clean.

---

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

## Day 3 — Wednesday 2026-06-17
_(same template)_

## Day 4 — Thursday 2026-06-18
_(same template)_

## Day 5 — Friday 2026-06-19
_(same template)_

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

