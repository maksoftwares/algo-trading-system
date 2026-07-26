# FX Multi-Pair Portfolio V1 — Findings

Date: 2026-07-26
Status: **`NO_DEPLOYABLE_FX_EDGE_FOUND_STOP`**

## Bottom line

I could not find a profitable Forex system on this evidence, and I am not going
to ship one that only looks profitable. Six independent hypothesis classes were
tested and all six were rejected. The rejections are recorded in
`REJECTIONS.md` with the evidence that closed each one.

This is a negative result, but it is a *load-bearing* negative result: it
quantifies why the existing Forex lane never passed, closes off most of the
search space with numbers rather than opinion, and identifies the one place a
real FX edge does live and exactly why a retail account cannot bank it.

## The single most important number

The one hypothesis with a strong in-sample signature — USD weakening in
01:00-03:00 UTC, **positive in 6 of 6 design years**, t = +2.77 — reversed sign
in both out-of-sample windows:

| Window | Basket edge | t |
|---|---|---|
| Design 2016-07 .. 2022-01 | **+23.39 pts** | +2.77 |
| Validation 2022-01 .. 2024-07 | **−21.25 pts** | −1.38 |
| Final exam 2024-07 .. 2026-07 | **−30.82 pts** | −1.77 |

It loses even at *zero* retail markup. Six consecutive positive years carried no
predictive content. Any FX result in this repo that rests on in-sample year
counts should be re-read in light of this.

## What was tested and what happened

| # | Hypothesis | Result |
|---|---|---|
| R1 | Uniform bar-geometry families (Asia-range London breakout, H4 Donchian, Asia fade) across 3 majors, 48-point grid each | Rejected. 0 of 48 points had PF > 1 on all three pairs. **Zero-cost** PF still 0.87–1.07 |
| R2 | Inherited EURUSD M30 RSI/Bollinger fade at retail cost | Rejected. PF 1.083 at 0.3-pip spread → 0.990 at 1.0 pip → 0.850 at 2.3 pips |
| R3 | 49-bucket intraday conditioning census × 3 horizons × 3 pairs | Rejected. Momentum/reversion are noise; only hour-of-day had magnitude |
| R4 | Tokyo-hour short-USD drift (the R3 survivor) | Rejected. Sign reversed out-of-sample, twice |
| R5 | Cross-sectional price-only premia, 7 majors, 331 months, 1999–2026 | Rejected. TSMOM SR ≤ 0.12, XSMOM negative, value SR 0.22 (t 1.13) |
| R6 | FX carry with real OECD interbank rates | Real premium (SR 0.40, t 2.11) but not retail-capturable — see below |

## Why the existing Forex lane never passed

The inherited "best Forex candidate" is **cost-dominated**, and the arithmetic is
exact. For round-trip cost `c`, stop `s` and reward `R·s`, breakeven win rate is
`(s + c) / (R·s + s)`. The inherited rule used `R = 0.8` and `s ≈ 157` points:

- before cost, it needs a **55.5%** win rate;
- at `c = 15` points it needs **60.8%**;
- it actually won **57.5%**.

That is the whole story. An 0.8R target demands a high win rate, and a high
win-rate strategy has small wins, so a fixed per-trade cost eats it alive. It
also means the inherited MT5 figure of **PF 1.20 was measured at an
optimistically tight tester spread** and is not retail-achievable. This
quantifies the previously vague finding that "Dukascopy-first candidates did not
transfer to Capital.com."

## The one real edge, and why you cannot bank it

Carry is the only genuine premium found: +3.56%/yr, Sharpe 0.40, t = 2.11 over
331 months. Its decomposition is decisive:

| Component | Annual | Sharpe | Max drawdown |
|---|---|---|---|
| Interest accrual only | **+3.48%** | 7.78 | **0.0%** |
| Spot only | **+0.08%** | 0.01 | **55.6%** |

All of the return is interest accrual; none is spot. Spot carries all the risk.
On a retail MT5 account the accrual arrives as broker **swap**, which is marked
up against the client on both sides — so the component that *is* the edge is
precisely the component the broker keeps, and what is left is a 55%-drawdown
spot coin flip.

**This is falsifiable and cheap to check:** read the actual swap rates for the
demo account's FX symbols. If pass-through is favourable, carry becomes worth a
real design pass. That is the highest-value next experiment in this lane.

## The structural problem

Three factors compound:

1. **Cost vs edge.** Real intraday regularities in majors are ~5–12 points.
   Retail round-trip cost is ~16–22 points. Short-horizon systematic FX on
   majors is arithmetically closed at retail spread.
2. **Horizon.** Cost stops mattering only at multi-week horizons (~1.4bp), but
   at that horizon the price-only premia are dead (R5) and only carry survives,
   which the broker taxes (R6).
3. **Universe.** Three USD majors is far too thin for cross-sectional work, and
   even seven majors over 27 years is thin. Published FX premia use 10–30
   currencies, and the G10 momentum premium largely disappeared after 2008 —
   which R5 independently reproduces.

Gold is a genuinely easier instrument than EURUSD: less efficient, wider
relative ranges, and — per this repo's own record — an edge that leans heavily
on tick microstructure. Majors are the most efficient market in the world. The
gold result should not have been expected to have a Forex analogue, and the
evidence says it does not have one here.

## Cost-model caveat, stated plainly

The retail cost model (12/18/14 points effective spread for
EURUSD/GBPUSD/USDJPY) is an **assumption**. No FX broker spread was ever
measured in this repository — the only artefact is a `maximum_spread_points:
100` guard, and the on-disk `capital_multisymbol` tick files are synthetic
fixtures (every symbol shows bid 4000 / ask 4000.3). Measuring true demo spread
is cheap and would sharpen R1–R4, though it cannot rescue R4, which fails at
zero markup.

## What is genuinely delivered

Reusable infrastructure, all tested and reproducible:

- **Data foundation.** 747k M5 bid/ask bars per pair for EURUSD/GBPUSD/USDJPY,
  2016-07 → 2026-06, decoded from 264k hourly tick files in 97s. Integrity
  report is clean: zero duplicate, non-monotonic, negative-spread, inverted or
  containment-violating bars (`outputs/BAR_INTEGRITY.json`).
- **Execution engine.** Bid/ask engine where longs pay the ask and are stopped
  on the bid path, stop exits slip adversely, ambiguous bars resolve to the stop
  and are counted, and quote-currency conversion is handled for JPY pairs. 17
  contract tests, including one that proves a pre-entry price spike cannot move
  a fill (`tests/test_engine.py`).
- **Long-history panel.** 27.5 years of daily FX for 7 majors plus OECD
  interbank rates.
- **Six recorded rejections** with reproducible scripts.

Anyone continuing this work can test a new FX hypothesis in minutes instead of
rebuilding the substrate.

## Recommended next steps, in value order

1. **Measure the demo account's real FX spread and swap rates.** Cheap,
   read-only, and decides whether R6 (carry) is alive. This is the only
   experiment that could turn a rejection into a candidate.
2. **If swap pass-through is favourable:** design a carry sleeve properly —
   vol-scaled, drawdown-capped, 6–10 pairs, weekly rebalance — and accept that
   it is a low-frequency, high-drawdown premium, not a high-frequency system.
3. **If not:** do not spend more effort on majors. Either widen the universe to
   20+ currencies including EM (where carry and value are still alive and
   spreads are proportionally less punishing relative to the premium), or accept
   that the gold system is the edge and scale *it* rather than diversifying into
   a market where no edge was found.
4. **Do not** run another parameter search on EURUSD. R1–R4 close that space
   with numbers.

## Requirement status, stated honestly

| Requirement | Status |
|---|---|
| Forex system like the gold one | Infrastructure built; no profitable strategy found |
| Consistent profit | **Not achieved.** No hypothesis survived out-of-sample |
| Good trade frequency | Achievable (R1 families gave 150–1,700 trades/pair/yr) but only unprofitably |
| Demo ready | **Deliberately not shipped.** Nothing here earns demo authority |

Shipping a demo package now would mean deploying a strategy I know to be
unprofitable. The honest deliverable is this evidence plus the infrastructure to
act on it once step 1 answers the swap question.
