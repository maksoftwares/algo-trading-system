# INDEPENDENT REVIEW — 3,900-TRADE MARKET-DAY-COVERAGE PORTFOLIO (target75_cooldown10)
Date: 2026-07-02 | Reviewer: Independent (Claude) | Offline only. Reconstructed from the three named
component tester CSVs + the described dedupe and guard rules.

## VERDICT: REJECT_HEADLINE_AS_STATED — guard layer shows outcome leakage; underlying deduped
portfolio is real but materially weaker. NOT approvable for demo in its claimed form.

## 1. What reproduces and what does not
Component identification is CONFIRMED: my dedupe (same-direction within 5 min, keep first) drops
exactly **1,153 duplicates** — matching their report to the trade. So I am holding the identical
input set (5,389 raw → 4,236 deduped). From there:
| | Claimed | My reconstruction |
|---|--:|--:|
| Trades after guard | 3,900 | 4,214 (faithful guard) / 4,222 (entry-lookahead variant) |
| Win rate | 66.13% | 62.22% |
| Net USD | +3,620.27 | +2,351 |
| PF | 1.44 | 1.245 |
The "+75 target / 10-min loss cooldown" guard as described removes ~22 trades in a faithful
implementation — not 336 — and cannot add net (a stopping rule only removes trades).

## 2. The decisive arithmetic (why the headline cannot be causal)
Their guard removed 336 trades relative to the deduped set, and those removals IMPROVED net by
+$1,279 and WR by +3.9pp. Implied composition of the removed set: 55 winners / 281 losers = **16.4%
win rate**. This book's own loss-anatomy evidence (my deep-dive review, confirmed by Codex's failed
entry-quality run) established that winners and losers are statistically inseparable using
entry-time information. No day-target/cooldown rule operating on information available at entry can
select a 16%-WR subset out of a 62%-WR book. The only way to do it is with knowledge of trade
outcomes — i.e., the guard simulation in the coverage-search pipeline is leaking the future
(plausibly a bug such as dropping the loss that triggers the cooldown, or filtering on
day-final PnL). The 16/16 positive quarters, 0 negative rolling windows, and $111.70 max DD are
artifacts of the same layer. **Codex must publish the guard code and the per-trade kept/dropped list;
until reproduced, the headline is invalid evidence.**

## 3. What is actually there (my numbers, no guard, honest layer)
- **Deduped 3-component portfolio**: 4,236 trades, WR 62.18%, net +2,341, PF 1.24. Cadence is real:
  4.07 trades/market day, active on 70.1% of weekdays, 3+ trades on 49.1% of weekdays, 13/16 quarters
  and 7/8 half-years positive. Breakeven WR at the realized 0.75 payoff is 57.1% → +5.1pp margin,
  raw z≈6.8. This is a genuine, frequency-rich, positive-expectancy book — at PF 1.24, not 1.44.
- **The short leg is the weak component**: portfolio shorts 2022–24 = PF 0.875 (−174 USD on 792
  trades); all short profit lives in 2024–26 (PF 1.44). Same OOS-short-failure pattern as RR2.0.
- **Long-only version**: 3,020 trades, WR 63.5%, PF 1.27, +1,909, 8/8 half-years positive,
  2.98 trades/market day, 3+ trades on 33% of weekdays. More robust, less cadence.

## 4. Demo-trading weak points (the question asked) — in order of expected damage
1. **Guard-layer leakage (§2)** — the candidate as specified would be attached expecting 66% WR/PF
   1.44 and would deliver ~62%/1.24 minus costs; every gate calibrated to the claimed stats would
   misfire. Blocker.
2. **Cost fragility**: net is $0.55/trade on the honest layer. Slippage of $0.10/trade costs 18% of
   net; $0.30 costs 54%. At RR0.7 the average win is ~$4.50 and spread is already ~$0.28 of it. Demo
   fills will compress this book far more than they would the RR2 lane. The forward gates must be set
   against cost-adjusted expectations, not tester numbers.
3. **Currency parity bug risk**: the package target is specified as +75 USD; the A1 demo account is
   AED-denominated (guardian floors are +50/+100 AED). If the EA compares 75 against AED day-PnL, the
   package stops at ≈$20 equivalent — massively under-trading the backtest. Must be verified in code
   before attach.
4. **Concurrency**: the deduped book holds up to 3 simultaneous positions (multi-magic). Runtime needs
   3 lanes/magics with a cross-magic package guard; correlated same-direction stop-outs of 3×0.01
   positions cluster losses ~$18 in one bar at typical stops. Also interacts with the A1 guardian and
   the shared kill-switch file (STILL unresolved from the RR2 review — now three momentum lanes deep).
5. **Selection debt at maximum**: this is rank-1 of (pockets × guard grid) on top of 216 variants, all
   on the same fully-burned four years, with the guard grid optimized on daily equity shape — the most
   overfit-prone layer possible. In-sample "16/16 quarters positive" from a shape-optimized stopping
   rule carries near-zero evidential weight for the forward window.
6. **Short leg regime risk (§3)** — half the short sample's history says PF 0.88.

## 5. Constructive path (what I would accept)
1. Codex publishes guard code + kept/dropped lists; we reconcile. If a leak is confirmed, fix the
   pipeline and rerun the coverage search HONESTLY — the no-guard portfolio is still a viable base.
2. Consider promoting the **long-only no-guard portfolio** (PF 1.27, 8/8 half-years, ~3 trades/market
   day) as the forward candidate — it needs no daily-shape layer, no outcome-dependent stopping, and
   its components are individually tester-exact. A REAL +75 daily target can be added at runtime as an
   owner risk preference — but then forward gates must be derived from a leak-free simulation of it.
3. Gates for whatever attaches: derive from §3 numbers minus a $0.10/trade cost haircut (e.g. expect
   WR ~61–63%, PF ~1.15–1.25); WR floor ≥ 59% (breakeven 57.1% + margin); kill at PF<0.95@100 trades.
4. Non-negotiables carried forward: kill-switch separation, distinct magics (932300/932301/932302),
   +75-vs-AED currency check, pinned start timestamp, no tuning, search freeze (this REALLY must be
   the last combinatorial pass on 2022–2026 data).

## 6. Bottom line for the owner
The cadence goal is closer than ever: a real ~4-trades/market-day, 62%-WR, PF-1.24 book exists in the
components. But the advertised version (66%/1.44/16-of-16-quarters) is an artifact of a guard
simulation that knows the future. Attach the honest version with honest gates, or attach nothing.
