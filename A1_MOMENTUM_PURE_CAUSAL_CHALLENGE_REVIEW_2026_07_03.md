# INDEPENDENT CHALLENGE REVIEW — PURE_CAUSAL_REPAIR + NEXT REPAIR DIRECTION
Date: 2026-07-03 | Reviewer: Independent (Claude) | Offline only. All stats recomputed; exit ideas
path-simulated on broker bid/ask M5 bars (coverage 2022-07→2025-06; sim validated 96.7% sign match,
corr 0.93 vs tester on this book — sim is conservative, so read DELTAS, not absolutes).

## VERDICT: ACCEPT AS BEST FREQUENT CANDIDATE (with named caveats) + one repair direction clearly wins: PARTIAL 0.7R + BE RUNNER.

## 1. Verification
Everything reproduces: 3,156 / 66.00% / +2,773.63 / PF 1.417 / 3.03 trades/market day / top-200
+647.77 / top-300 −158.91 / 0 negative quarters / 0 negative rolling-250. Recent window reproduces
too (72 / 63.89% / +75.06 / PF 1.209). Guard causality now PASSES my checks: zero kept-trade
violations of the +75 target and 10-min cooldown — the leak I flagged is fixed, and publishing the
full trades CSV is exactly the right practice.

## 2. Answers to the seven questions
**Q1 — best candidate?** Yes, among frequent candidates — with three honesty notes. (a) The two cell
blocks (v13@3, v13@8) were chosen BY looking at what caused the failing rolling windows, so
"0 negative rolling-250" is constructed, not discovered; the fair base rate is the pure control
(PF 1.30, 64.0%, +2,128). (b) The `v4_combo_rank1` component is dead weight after dedupe (89 trades,
+20 USD) — remove it; simpler book, same result. (c) The sparse RR2 long-only lane remains the
higher-expectancy-per-trade system (+0.23R vs +0.09R/trade); "best" here means best against the
cadence goal, not best edge.
**Q2 — is RR 0.7 acceptable?** Yes. AvgLoss > avgWin is the DESIGN, not a defect: realized W/L 0.729
→ breakeven WR 57.8%, observed 66.0% (+8.2pp, raw z≈9.7). Fragility lives elsewhere: thin per-trade
net ($0.88) → cost sensitivity, and the top-300 caveat (honest disclosure; note top-300 = removing
14% of winners from a book whose edge is breadth — top-200 positive is the meaningful pass).
**Q3 — can avg win ≥ avg loss without killing WR/frequency?** Strictly: NO — W/L ≥ 1 at WR ≥ 60% is
+0.6R/trade expectancy, the mythical-portfolio zone; nothing in four years of this system supports
it. But the spirit of the question has a real answer: see Q4 — you can raise avg win ~25–65% at
IDENTICAL WR and identical frequency.
**Q4 — which repair direction wins?** Path-sim results on the same entries (n=2,398, deltas vs sim
replicate WR 62.34 / net 765 / PF 1.18 / W/L 0.71):
| Variant | WR | net Δ | PF | W/L |
|---|--:|--:|--:|--:|
| RR 1.0 retest | 53.5% | +13% | 1.16 | 1.01 |
| RR 1.2 retest | 48.9% | +29% | 1.17 | 1.22 |
| **PARTIAL 50% @0.7R, runner 1.5R, BE** | **62.3%** | **+47%** | **1.26** | 0.76 |
| PARTIAL 50% @0.7R, runner 2.0R, BE | 62.3% | +66% | 1.30 | 0.78 |
| BE at +0.5R (TP 0.7R) | 51.8% | −17% | 1.18 | 0.71 |
| lock/partial-70% variants | 62.3% | +15–39% | 1.20–1.25 | 0.73–0.75 |
**Winner: partial 50% at 0.7R + break-even runner to 1.5R (or 2.0R).** WR is mechanically UNCHANGED
(any trade reaching 0.7R stays a win; losers unchanged), frequency unchanged, net +47–66%, PF +0.08
to +0.12. Why this succeeds where BE/locks always failed here: it never truncates a winner below the
old target — it adds a BE-protected option on the documented fat tail (our RR-sweep evidence). BE-at-
0.5R fails again (−17%) — do not use. Loss-side entry filters remain a dead end (winners/losers
inseparable at entry — established twice). Dynamic ATR trailing: skip — dominated by the partial
structure and adds parameters. Sizing/risk-normalized lots: changes nothing at 0.01 demo; defer.
**Q5 — night-only?** NO. On the full four years every session is positive (night PF 1.60, morning
1.41, evening 1.37, afternoon 1.25). The weak recent sessions are n=6–7 buckets — pure noise. Keep
all sessions; the cadence collapse (§3) is regime, not session mix.
**Q6 — exact Codex test list:**
1. Implement default-off partial-close inputs in the EA (`InpPartialCloseEnabled`,
   `InpPartialFraction=0.5`, `InpPartialTriggerR=0.7`, `InpRunnerTargetR=1.5`,
   `InpMoveSLToBEOnPartial=true`). Exact MT5 rerun of the 3 live components (drop v4_rank1) over
   2022-07→2026-06 — this also covers the 2025-07→2026-06 year my sim cannot reach.
2. Same with runner 2.0R (the only other pre-registered exit variant; nothing else).
3. RR 1.0 full-book single run — only to give the owner the W/L≥1 option with honest WR ~53%.
4. Recompose the portfolio with the causal dedupe/guard; publish kept/dropped lists (as now); ALSO
   report the no-block version (without v13@3/8) under partial exits — if rolling-250 negatives
   reappear, report, don't re-block.
5. No new hour masks, cells, targets, or components. This is an EXIT test on a frozen entry book.
**Q7 — forward-demo gates** (for the partial-runner config if step 1–2 confirm): n ≥ 150 or 12
weeks (state expected cadence honestly: recent regime gives ~1.1/day, not 3); PF ≥ 1.20; WR ≥ 60%
(breakeven ~55–58% under partial structure — recompute from the exact run and set the floor 3pp
above it); net > 0 after a $0.10/trade cost haircut; positive after top-2% winners removed; no day
> 25% of net; kill at rolling-80 PF < 0.95, WR < 55% after 100 trades, or lane DD > 1.5× backtest.
Plus the standing pre-attach conditions: kill-switch filename separation, +75-USD-vs-AED currency
check, distinct magics, pinned start timestamp, no tuning.

## 3. Two things the headline hides (say them to the owner)
1. **Cadence has already collapsed in-sample**: 2026Q1 = 139 trades, 2026Q2 = 72 (1.07/market day vs
   the 3.03 four-year average; peak quarters were 315–375). The recent quarter is also the weakest
   (PF 1.21, +75) — and it is still IN-sample. The "multiple trades per day" goal is currently not
   being met by the market, and no causal repair can fix that without re-opening filters we know lose
   money. Forward expectations must be set on ~1/day, not 3/day.
2. **Component concentration**: v6_max2 (PF 2.48) and block_weak_hours_v1 carry the book; v13 makes
   only +96 USD in the first two years (its shorts remain the historically weak leg). If shorts sour
   forward, the book leans on two correlated long components.

## 4. Bottom line
The candidate is real, causal, and the best cadence/quality compromise found so far. The highest-
probability path to the owner's goal is NOT more entry surgery — it is the partial-at-0.7R +
BE-runner exit, which in simulation raises net ~50% and PF to ~1.26–1.30 while keeping WR at 62–66%
and frequency untouched. Confirm it with the exact MT5 partial-close implementation, then freeze a
forward spec with the gates above.
