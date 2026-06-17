# CODEX WORK ORDER — Verify the cost-gate findings on REAL broker fills (2026-06-16)

Owner: Ali (mohdalikhans97.com@gmail.com). Demo only. **READ-ONLY analysis — change no EA, preset,
cap, arming, or live setting.** This independently checks claims made from partial/replay data.

## Why
A cost analysis suggested that on gold, **cheap trades win and expensive trades lose**, with a
cost-R cutoff (~0.05–0.07) below which trades are net positive — and that the live cost caps are
too loose. But that analysis used the observer **replay** outcomes (synthetic) and a partially-
synced single-day file. Re-derive everything on **real broker fills**, de-duplicated and lot-
normalized, and confirm or refute each claim.

Definitions: `cost_r = spread ÷ stop_distance` (both in points). "Unique signal" = collapse rows
with the same entry time + symbol + direction + entry price (the stacked-EA duplicates).

## Tasks

### T1 — Build the authoritative trade set (real fills only)
From actual MT5 broker history (NOT observer/replay logs), all **closed gold (XAUUSD)** trades
since demo start through now, both accounts of interest (A1 `1025742`, A3 `1033669`). Per trade:
account, entry_time_dubai, symbol, candidate, magic, direction, lots, entry, exit, sl, tp,
`stop_distance_points`, `spread_points`, `cost_r`, profit_aed, exit_reason. Add `profit_aed_001`
(profit normalized to 0.01 lot) and a `unique_signal` dedup key. Report total rows, unique
signals, and how many are real broker-closed vs how many could only be replay-resolved.

### T2 — Cost → outcome on real fills (the core claim)
On de-duplicated, real-fill gold trades, bucket by `cost_r` (e.g. ≤0.05, 0.05–0.07, 0.07–0.09,
0.09–0.11, 0.11–0.13, >0.13). For each bucket: n, win rate, avg net result, total `profit_aed_001`.
Then the cumulative view: keeping only `cost_r ≤ cutoff` for cutoffs 0.04…0.15, report kept n / WR
/ avg-R / PnL and the blocked set's PnL. **State the cutoff where expectancy crosses from positive
to negative.** Verdict: is the ~0.05 threshold confirmed on real fills, refuted, or
insufficient-sample?

### T3 — Robustness (don't get fooled)
For the "kept" (cheap) set, break it down **by day** — is the positive expectancy spread across
many days or carried by a few? Show per-day signals / wins / PnL_001. Also show the raw-vs-dedup
and 0.05-vs-0.01-lot effect sizes, so we know how much each confound mattered.

### T4 — Account counterfactual (full history, not one day)
For A3 (`1033669`) and A1 (`1025742`) separately, over the **full** real-fill gold history: what
would total `profit_aed_001` have been keeping only `cost_r ≤ {0.05, 0.06, 0.08, 0.10}`? Show kept
n / PnL / WR and blocked n / PnL per account, **plus the per-day breakdown** so we can see whether
any positive result depends on a couple of days. (This replaces the single-day, partial-data view.)

### T5 — Verify the factual claims
- Current cost-cap inputs in the live EAs: A3 `Account3RoundRetest*Executor` `InpMaxEstimatedCostR`
  value, and the A1/A2 `Phase2ExperimentalDemoExecutor` cost-cap value. Quote them from source.
- Confirm or refute: **breakout trades are low-cost, round trades higher-cost** — report `cost_r`
  by candidate/family on real fills.

## Reporting → `COST_GATE_VERIFICATION_REPORT_2026_06_16.md`
A claim-by-claim table, each marked **CONFIRMED / REFUTED / INSUFFICIENT DATA** with the numbers:
1. Cheap gold trades win, expensive lose (real fills).
2. There is a cost-R cutoff (~0.05–0.07) below which gold trades are net positive.
3. Live cost caps (A3 0.15, A1/A2 ~0.30) are looser than that cutoff.
4. Breakout = low cost / round = high cost.
5. The cost-gate benefit is NOT driven by one or two days (state honestly if it is).
State the real-fill sample size prominently so we know the evidence strength, and **be strict**:
if the sample is too small or the threshold is unstable across days, say so. Append raw query
output. End with `git status` proving only analysis files changed.
