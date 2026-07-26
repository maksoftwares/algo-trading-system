# FX Multi-Pair Portfolio V1 — Preregistration

Status: `SEARCH_RUN_HYPOTHESIS_REJECTED`
Written: 2026-07-26, before any design-window result was inspected.
Outcome appended 2026-07-26 after the run — see `REJECTIONS.md` R1 and
`FINDINGS.md`. The §3 hypothesis was **rejected**: no grid point in any family
was profitable on all three pairs, and the families remain unprofitable at zero
cost. The text below is preserved unedited as the record of what was committed
to in advance; nothing in it was revised after seeing results.

This document fixes the hypothesis, the families, the grid, the cost model, the
data partitions and the selection rule **before** results exist. Anything not
written here is not permitted to influence selection later.

## 1. Why this lane exists (and why it is not more EURUSD tuning)

The existing Forex lane ended without a clean pass:

- `eur-usd/eurusd-fast-research/regime-specialists-v2/outputs/VERDICT.json` →
  `NO_V2_SPECIALIST_PORTFOLIO_STOP`;
- `.../capital_final_exam/VERDICT.json` → `CAPITAL_EXAM_FAIL_STOP`;
- the surviving fallback reached PF 1.3075 only against a floor that was
  lowered to 1.30 after results were seen, on a window its own contract calls
  "adaptive research, not an untouched holdout", and its PF falls to **1.019**
  once the best 5% of trades are removed.

Two structural weaknesses follow: the result is concentration-dependent, and it
is single-symbol. Both are attacked by a different substrate, not by more
parameter search on EURUSD.

## 2. The measured constraint this design answers

`outputs/REFERENCE_SPREAD_STRESS.json` replays the inherited EURUSD M30
RSI/Bollinger fade on Dukascopy and sweeps broker spread:

| Effective spread (points) | Profit factor |
|---|---|
| 3 (Dukascopy raw) | 1.083 |
| 6 | 1.034 |
| 10 (typical retail EURUSD) | 0.990 |
| 13 | 0.953 |
| 23 | 0.850 |

The inherited rule is **cost-dominated**, which explains the recorded finding
that Dukascopy-first candidates "did not transfer to Capital.com", and warns
that its reported PF 1.20 was measured at an optimistically tight tester spread.

The mechanism is its 0.8R target. Round-trip cost `c`, stop `s`, reward `R·s`
puts breakeven win rate at `(s + c) / (R·s + s)`. At `R = 0.8`, `s = 157`,
`c = 15` that is 60.8% against an actual 57.5% — fatal. At `R = 1.5` the same
cost moves breakeven from 40.0% to only 44.0%.

**Therefore:** every family here uses `RR >= 1.2` and a stop floor of at least
10x modelled round-trip cost, and frequency is bought with more pairs and more
sessions rather than tighter stops.

## 3. Hypothesis under test

> A single, low-parameter mechanism applied **identically** to several FX pairs
> produces a portfolio whose consistency comes from cross-sectional
> diversification rather than per-pair fitting, and which survives realistic
> retail spread.

Falsifiable: if the uniform parameter set is not simultaneously profitable
across pairs in validation, the hypothesis is rejected and recorded as such.

Note on prior art: the earlier lane's portability failure replayed **one
already-tuned EURUSD rule** on GBPUSD/USDJPY. That tests transfer of a fitted
artefact, not whether a uniformly-specified mechanism works cross-sectionally.
This lane tests the second claim, which is untried here.

## 4. Instruments and data

- Pairs: `EURUSD`, `GBPUSD`, `USDJPY`.
- Source: Dukascopy tick archive at
  `D:\AlgoTradingData\C_DRIVE\DukascopyTickDataFoundationV1\raw`.
- Bars: M5 bid/ask OHLC, decoded per the `dukascopy-ticks-v1` source contract;
  higher timeframes derived from M5 because the archive's native higher
  timeframes are known to be holey.
- Integrity: `outputs/BAR_INTEGRITY.json` must report zero duplicate,
  non-monotonic, negative-spread, inverted or containment-violating bars.

## 5. Cost model (fixed now, not tuned later)

Applied as a symmetric spread markup on top of raw Dukascopy quotes, plus entry
and stop slippage. Stop exits fill *worse* than the level; targets do not get a
mirror-image improvement.

| Symbol | Raw median (pts) | Markup (pts) | Effective spread (pts) | Entry slip | Stop slip | Round-trip cost |
|---|---|---|---|---|---|---|
| EURUSD | 3 | 9 | 12 | 2 | 2 | 16 |
| GBPUSD | 9 | 9 | 18 | 2 | 2 | 22 |
| USDJPY | 4 | 10 | 14 | 2 | 2 | 18 |

Commission is 0 (spread-only retail account). `stop_floor_points = 10 x
round-trip cost`, i.e. 160 / 220 / 180.

A **cost-stress** rerun at 2x markup is mandatory before any promotion.

## 6. Families (trigger definitions frozen)

Sessions are UTC and fixed by market structure; they are never swept.

**A. `london_breakout`** — Asia range (00:00–07:00) broken after London opens.
Triggers on a *completed* M5 mid close beyond the Asia extreme within
07:00–12:00; fills next M5 open; at most the first break per side per day.

**B. `donchian_h4`** — completed H4 mid close beyond the prior 30-H4-bar
extreme (channel excludes the signal bar); fills next M5 open.

**C. `asia_fade`** — completed M30 mid close at least 1.5 ATR(14) away from a
24-bar mean during 00:00–07:00, traded *against* the excursion.

All three read completed bars only. `src/indicators.py::decision_to_execution`
maps a completed decision bar to the first M5 bar opening at or after its close;
`tests/test_engine.py` pins that no pre-entry bar can affect a fill.

## 7. Parameter grid (the only knobs)

Swept jointly, **identically for all three pairs**:

- `rr` ∈ {1.2, 1.5, 2.0, 2.5}
- `atr_mult` ∈ {1.0, 1.5, 2.0, 3.0}
- `context_mult` ∈ {0.0, 0.5, 1.0}
- `max_hold_bars`: 288 for A and C (one day), 288x10 for B (ten days)

Fixed: `stop_floor_points` per §5, `stop_cap_points = 1500`, `lot = 0.01`,
one position per sleeve, `max_entries_per_day = 3` per sleeve.

Grid size is 48 per family. This is small deliberately: the measured
selection-leak ladder on this repo is PF 1.99 → 1.45 → 0.82 as hindsight is
removed, so a wide grid would buy nothing but leak.

## 8. Partitions

| Partition | Window | Use |
|---|---|---|
| Design | 2016-07-01 .. 2021-12-31 | choose one parameter set per family |
| Validation | 2022-01-01 .. 2024-06-30 | accept or reject the choice |
| Final exam | 2024-07-01 .. 2026-06-30 | run **once**, reported as-is |

The final exam is **not** described as untouched: earlier EURUSD lanes have
already inspected 2024-07..2026-06. It is a final adaptive check. The only
genuinely untouched evidence is prospective demo collection after deployment.

## 9. Selection rule (leak-resistant, fixed now)

From the design window only, per family, choose the parameter set maximising the
**median PF across the three pairs**, subject to all of:

1. PF > 1.0 on **every** pair (no averaging away a failing pair);
2. at least 60 trades per pair in the design window;
3. the chosen point is a **plateau**: at least two of its immediate grid
   neighbours in `rr` / `atr_mult` also satisfy (1).

Ties break toward the wider stop, then the lower `rr`. The maximum is taken over
a median, never over a single pair's best — a fixed dev-era threshold is not a
fixed selectivity, and picking a per-pair maximum is the leak this repo has
already paid for twice.

## 10. Acceptance gates

A family is carried to the portfolio only if, in **validation**:

- PF >= 1.10 on the pooled three-pair ledger;
- PF > 1.0 on at least 2 of 3 pairs individually;
- >= 150 pooled trades;
- pooled PF after removing the best 5% of trades >= 1.00 (the concentration
  test the inherited candidate failed at 1.019).

The **portfolio** is demo-eligible only if, in validation and again in the final
exam:

- pooled PF >= 1.20;
- >= 1.0 trade per active trading day;
- >= 55% of active months positive;
- max closed-trade drawdown <= 15% of the modelled account;
- PF >= 1.10 under the 2x cost stress;
- at least 2 families and 2 pairs contribute trades.

Passing these produces `DEMO_FORWARD_CANDIDATE`, never live authority.

## 11. Declared discount

Any figure produced here is a development figure. This repo's measured cost of
hindsight is PF 1.99 → 1.45 → 0.82 across the leak ladder. Expect realized
prospective PF materially below backtest PF, and size demo risk accordingly.
