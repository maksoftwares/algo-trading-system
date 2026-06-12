# Repo Review 11 — Three-Observer Evidence Analysis (2026-06-12)

Reviewer role: senior quant + trading-systems reviewer.
Inputs: ShadowFixObserver figures (06-08 → 06-12, 15,446 rows, 1,241 would-signals),
TrendGuardedFixObserver first hour (70 rows, 8 would-signals), PositionPathObserver first
session (828+ rows, 4 close summaries), cross-referenced against the actual broker-trade
evidence and code findings from Reviews 7–10. Boundary respected: demo/observer research
evidence only; nothing here is live-capital proof or canonical Phase 2 evidence.

---

## Executive Summary

The observer network is working, and its first window already does three useful things:
it **confirms the clone problem at the signal layer** (the two round-retest EAs emitted
*exactly* 331 XAUUSD would-signals each — byte-level signal parity, not coincidence), it
**quantifies how lopsided the portfolio's signal flow is** (the weak round/session lanes
generate ~70% of all would-signals; the profitable breakout family only ~29%, and most of
*that* is on the two symbols where it doesn't make money), and it **exposes a hole in the
legacy shadow policy itself**: 226 of the 561 "KEEP" signals — 40% of the supposedly clean
stream — are `round_number_retest_v0` signals, the identical twin of an EA the same policy
blocks 100%. The legacy KEEP view is therefore still clone-contaminated, and any PnL
attributed to it overstates the cleaned portfolio.

The trend veto has produced zero evidence either way (one morning hour, 8 signals, 0
fires — the test it was built for is the evening). The path observer's first 4 close
summaries are statistically nothing but forensically perfect: two trade events, each
recorded twice by the clone pair, both counter-trend BUYs, both dead at SL within 8 and 2
minutes — duplication and fast adverse entries, on camera, in one screenshotable table.

Verdict in one line: **proceed — keep collecting through the evening window, fix the one
policy hole and the round_number gap in the shadow rules, quarantine nothing new today,
and resolve outcomes before believing any block-rate.**

---

## Evidence Table

| # | Observation | Source | Strength |
|---|---|---|---|
| 1 | `round_number` and `symbol_normalized` emitted identical XAUUSD signal counts (331 = 331) | ShadowFix | **Proven** (5 days, n=662) — clones at signal layer |
| 2 | Weak lanes (round×2 + session_extreme) = ~876 of 1,241 would-signals (70.5%) | ShadowFix | **Proven** for flow share (says nothing about PnL by itself) |
| 3 | Legacy KEEP stream is 40% round_number clone signals (226/561) | ShadowFix (arithmetic: 1,241−680; 345−119) | **Proven** — policy hole |
| 4 | Breakout-family signals concentrate on USDJPY (163) and EURUSD (120) vs XAUUSD (82) — signal-rich symbols are the low-edge ones (USDJPY actual PF 0.45) | ShadowFix + broker CSV | Strongly suggested |
| 5 | XAUUSD session blocks fire at a uniform ~36–37% across EAs (16/43, 14/39, 119/331) — consistent with morning+afternoon share of signal flow | ShadowFix | Consistent / sanity check passes |
| 6 | Trend veto: 0 fires in 8 signals | TrendGuarded | **No evidence** (1 morning hour; veto needs both M15+H1 slopes ≥50 pts against direction) |
| 7 | First 4 path summaries: 2 trade events × 2 clones, all counter-trend BUY, all SL, holds ≈ 8 min and ≈ 2 min | PositionPath | Illustrative only (n=2 events) — but exactly matches Reviews 7–8 loss anatomy |
| 8 | Path observer mechanics: snapshots flowing, exit reason + slippage captured, twin PnL deltas tiny (−16.20 vs −16.39) | PositionPath | Working as designed; execution/slippage NOT a visible problem so far |
| 9 | Night dominates observer rows (6,479/15,446 = 42%) | ShadowFix | Confirms night churn pressure persists |

---

## Per-Observer Interpretation

**ShadowFixObserver (the workhorse).** Five days, all 14 instances alive. Its real
contribution is flow accounting and the policy hole (#3). Its limit: it logs decisions,
not outcomes — block rates are meaningless for PnL until each would-signal is resolved
offline (replay logged entry/SL/TP against M5 bars, plus join to actual broker trades
where the live EAs took the same signal). Do not read "680 blocked" as "680 bad trades
avoided."

**TrendGuardedFixObserver.** One morning hour. The only honest statement: the pipeline
runs (v2 schema, 5 instances, rows flowing). The veto exists for evenings like June 11;
judge it after ≥1 full week including evenings. Zero fires in a quiet morning is the
*expected* behavior of a well-calibrated veto, not a failure.

**PositionPathObserver.** The youngest and already the most information-dense per row.
Four summaries can't support statistics, but they validated every pipeline feature in one
session (FIRST_SEEN→SNAPSHOT→CLOSE_DETECTED, R math, exit reason, slippage, stacking
count). The 8-minute and 2-minute SL deaths hint at the question its first real report
must answer: *do these entries ever see green at all?* (MFE before SL.)

---

## Per-EA Interpretation

| EA | Observer read | Combined with broker evidence (Reviews 7–8) | Standing |
|---|---|---|---|
| `breakout_retest` | Moderate, sane signal rate (~41/wk XAUUSD); 0 EA-blocks; session block trims ~37% on XAUUSD | Only profitable lane, 3 windows running | **Cleanest. Control. Don't touch.** |
| `swing_breakout_retest_v0` | Signal counts track breakout closely (39 vs 43 XAUUSD) — clone confirmed again | 1:1 trade duplication | Logger only / mutex with breakout |
| `symbol_normalized_round_retest_v0` | 435 signals, 100% blocked by legacy policy | −630 AED, negative all buckets | **Weakest — quarantine stands** |
| `round_number_retest_v0` | 345 signals, only the session slice blocked (119) — **escapes the EA-quarantine its identical twin gets** | clone of the above, −445 raw | **Same family, same verdict — close the policy hole** |
| `session_extreme_retest_v0` | 96 signals, 100% blocked | PF 0.64, WR 27% | Quarantine stands; repair_v1 evidence still n≈3 |

## Per-Symbol Interpretation

- **XAUUSD:** scarce breakout signals (82/wk family-wide) but all the realized edge; flooded by 662 round-clone signals. The symbol is fine — the flow mix on it is not.
- **USDJPY:** the signal-richest symbol (163 breakout-family would-signals) and the worst realized performer (PF 0.45, avg win 5 AED). High flow + no edge = pure churn surface. The earlier "turn USDJPY off" call survives the observer data unchallenged.
- **EURUSD:** middling flow, thin realized edge concentrated in evening breakouts (+49.6 evening vs −41.6 night). Candidate for evening-only whitelisting, decided at n≥30.
- Note for trade-count planning: signal frequency anti-correlates with edge in this portfolio. Preserving count via raw flow means preserving churn; count must come from validated cells instead.

---

## Q4: Where is the problem, ranked by evidence weight?

1. **Strategy logic (direction selection)** — primary. Proven by code (Review 8) and re-illustrated by both path-observer events (counter-trend BUYs, instant SL).
2. **Duplication/stacking** — primary. Now proven at *three* layers: code (no mutex), trades (247/565 dup rows), signals (331=331).
3. **Timing/session mix** — secondary but real (evening +426 vs night −431 realized; 42% of observer rows at night).
4. **Trend direction** — same root as #1; veto evidence pending.
5. **Cost** — tertiary; only USDJPY (and night spreads) — passive observer puts XAUUSD cost_R ≈ 0.14, not a blocker.
6. **Execution** — no evidence of a problem; twin-trade PnL deltas of ~0.2 AED and clean SL fills so far. Watch the slippage column, expect boredom.

---

## Evening-Session Research Plan (next sessions, esp. Friday evening)

Pre-registered questions — write these down before the data lands:

1. **Trend veto fire-rate and split** (TrendGuarded): of evening XAUUSD would-signals, how many BLOCK vs KEEP; resolve both buckets via SL/TP replay + broker-trade join. Success direction: blocked bucket clearly negative, kept bucket ≥ baseline, controls (breakout/swing) lose <25% of signals to the veto.
2. **Loser anatomy in the evening** (PositionPath): % of SL-deaths that ever reached +0.3R/+0.5R; time-to-SL distribution (are the 2–8-minute deaths the norm or the tail?).
3. **Stacking census at cluster hours** (PositionPath): max `same_symbol_same_dir_count` in 17:00–19:30 Dubai — June 11's wipeout window.
4. **Spread regime** (PositionPath): spread_points distribution evening vs night per symbol; count SL hits where spread > 2× session median (phantom-stop candidates).
5. **Legacy-KEEP honesty check** (ShadowFix): resolve the 561 KEEPs with and without the 226 round_number clones — how much does the policy hole flatter the "clean" stream?

## Concrete Next Actions

1. **Fix the legacy shadow policy hole:** add `round_number_retest_v0` to the EA-block list (or better: convert both EA blocks to one family-level rule). One line in the shadow policy; bump `shadow_policy_version`.
2. **Build the outcome-resolution script** (one script serves all three observers): replay logged entry/SL/TP vs M5 bars + join to broker trades by minute/symbol/direction. Without it, every table above stays a flow report.
3. Generate, daily: `OBSERVER_DAILY_SCOREBOARD.md` — per EA×symbol×bucket: signals, KEEP/BLOCK by each policy (legacy, trend-veto), resolved outcome of each bucket, coverage stats for the path observer (per Review 10 §6).
4. Keep all three observers running through the weekend close; verify heartbeats (a silent observer death currently looks identical to a quiet market — add a per-hour heartbeat row or check file mtimes in the hourly supervisor).
5. Apply Review 10's two path-observer fixes (slippage reference, magic bands) if not yet landed.

## What NOT to Change Yet

- No trend-veto enforcement (zero evidence either way).
- No threshold tuning of the 50-point slope (sweep offline from logged raw slopes after a week).
- No new blocks/filters on `breakout_retest` or EURUSD (evening whitelist waits for n≥30).
- No exit-rule changes (partial/BE already rejected; ATR-trail waits for path data volume).
- No new EA variants, no repair re-arms, and no "fixes" derived from the 4 path summaries — two events is an anecdote with a CSV.

## Rules: shadow-only vs promotable

| Rule | Status |
|---|---|
| M15/H1 trend veto | **Shadow-only** — needs ≥1 full week incl. evenings + outcome resolution |
| XAUUSD morning/afternoon session block for weak lanes | Shadow-validated twice on actual trades; eligible for demo-guard **when the weak lanes themselves return from quarantine** (moot while they're observer-only) |
| Session block applied to breakout_retest | **Do not promote** — its non-evening buckets are ~flat; one week of bucket data is not a filter |
| Family duplicate mutex | **Promotable to demo-guard now** — three independent evidence layers; this is execution hygiene, not strategy, and Reviews 7–8 already recommended it |
| Round-family + session_extreme quarantine | Already justified by three windows of actual broker PnL (Reviews 7–8 position unchanged: demo-act now, validated prospectively by their observer logs) |
| USDJPY off | Same — cheap, justified, reversible |

## Observer-Design Changes I'd Make

1. The legacy-policy round_number hole (above) — the only urgent one.
2. Heartbeat/uptime visibility for all three observers (hourly supervisor should alert if any log's mtime stalls >15 min during market hours).
3. Unify the time-base across observers (TrendGuarded v1 used `TimeLocal`; v2 and PositionPath use `TimeGMT()+240` — confirm ShadowFix matches; mixed bases will corrupt cross-observer joins).
4. Consider folding the three portable terminals into one observer terminal next month — 3 terminals × N instances is operational sprawl; not urgent.
5. Nothing else. Resist adding fields/rules until the first outcome-resolved week is reviewed.

## Q10: Biggest risks of concluding too early

1. **Counts are not money.** Block rates and signal shares say nothing about PnL until outcomes are resolved. The June portfolio looked *raw-positive* while being dedup-negative; flow tables can mislead the same way.
2. **One regime.** Everything observed sits inside one strongly trending-up gold week. Vetoes, session blocks, and quarantines fitted here may misfire in a range; the fresh-forward-week rule exists precisely for this.
3. **Partial in-sample evaluation.** The legacy shadow policy was *derived* from 06-01→06-09 trades; evaluating it on an 06-08→06-12 window overlaps its training data. Only the post-derivation slice counts as forward evidence.
4. **Tiny n everywhere that matters:** 8 trend-veto signals, 4 path summaries, 2 unique trade events. The only big-n facts are flow shares and the clone parity — which is why those are the only things this review calls proven.
5. **Multiplicity.** Three observers × 5 EAs × 4 symbols × 4 buckets × 2 policies is hundreds of cells; something will look significant by luck. Pre-registered questions and family-level (not cell-level) rules are the defense.
6. **Demo execution ≠ live execution** — fills, spread behavior, and slippage on demo are gentler; the path observer's slippage column is the start of quantifying that gap, not the end.

---

## Reviewer Verdict: **PROCEED** (with the two small modifications)

Proceed = keep all three observers running through the evening window and the next full
week; fix the round_number policy hole and add heartbeat visibility; build the
outcome-resolution script before the weekend review. Wait = on trend-veto judgment, on any
breakout_retest filtering, and on exit rules. Modify observers = only items 1–3 above.
Quarantine candidates = no *new* names; the standing Reviews 7–8 recommendation
(round family + session_extreme + repair lanes observer-only, family mutex, USDJPY off)
remains the unexecuted decision this data keeps re-confirming from new angles.
