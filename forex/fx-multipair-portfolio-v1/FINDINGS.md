# FX Multi-Pair Portfolio V1 — Findings

Date: 2026-07-26
Status: **`NO_DEPLOYABLE_FX_EDGE_FOUND_STOP`**

## Bottom line

I could not find a profitable Forex system on this evidence, and I am not going
to ship one that only looks profitable. **Seven** independent hypothesis classes
were tested and all seven were rejected, the last two against *measured* broker
costs rather than assumed ones. The rejections are in `REJECTIONS.md` with the
evidence that closed each.

This is a negative result, but a *load-bearing* one: it quantifies why the
existing Forex lane never passed, closes the search space with numbers rather
than opinion, and reduces to a single measured inequality.

## The one-line answer

**The bid-ask spread is wider than the entire predictable component of FX
returns.**

Measured on the actual Capital.com MENA demo account: EURUSD trades at a fixed
**0.70 pips (7 points)**. Using tick order-book depth — real quoted sizes, not
bars — the most significant predictor found anywhere in this lane is short-term
mean reversion in signed tick flow, with t-statistics of **−9.3 / −7.8 / −6.3**
across the three pairs. Its magnitude is **1.6 points**.

The signal is real, highly significant, and cross-pair consistent. It is also
four to six times smaller than the cost of trading it. Statistical significance
and tradeability are different things, and in liquid FX the gap between them is
the spread.

And the only income that needs no signal — carry, paid for merely holding — nets
about **+0.5%/yr** on measured swap after historical spot drift, against a
**68.6%** historical drawdown.

## The single most important methodological number

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
| R6 | FX carry with real OECD interbank rates | Real premium (SR 0.40, t 2.11) but 100% of it is interest accrual |
| R6a | Carry re-tested on **measured broker swap** | Favourable-side pass-through is real (91–96% on JPY pairs) but nets only ≈+0.5%/yr vs 68.6% drawdown |
| R7 | **Tick microstructure / order flow** — depth imbalance, microprice, quote asymmetry | Rejected. Best decile spread ~6 pts vs 22–34 pts required. Highly significant (t −9.3) but 1.6 pts wide |

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

## Cost model: now measured, no longer assumed

R1–R6 used an assumed cost model. It has since been **measured** on the live
demo account by read-only tick copy (`measure_broker_spread_ticks.py`, two full
trading weeks, liquid hours 07:00–20:00 UTC):

| Symbol | Measured spread | R1–R6 assumed |
|---|---|---|
| AUDUSD | **0.60 pips** | not tested |
| EURUSD | **0.70 pips** | 1.20 |
| USDJPY | **1.20 pips** | 1.40 |
| GBPUSD | **1.30 pips** | 1.80 |
| USDCHF | 1.40 | — |
| USDCAD | 2.00 | — |
| USDMXN | 21.2 | — |
| USDZAR | 50.0 | — |

Real cost is ~30% *below* what R1–R6 assumed for EURUSD, so those rejections were
run against a pessimistic model. They still stand, because R1's families and R4's
drift both fail at **zero** cost, which bounds anything a cheaper spread could
rescue. R7 was scored against the measured figures from the start.

Two structural details worth keeping:

- The spread is **fixed**, not floating: p25 = median = p95 at every hour except
  the 21:00 UTC rollover (EURUSD 0.7 → 5.0). A fixed-spread broker therefore
  *underprices* liquidity in thin conditions — Dukascopy's raw EURUSD spread hits
  3.0 pips at the 99th percentile while this account still quotes 0.7. That is a
  genuine execution advantage in stressed moments; it is just not worth 22 points.
- Swap is skimmed **asymmetrically**, near-fair on one side and punitive on the
  other (GBPJPY long ~96% pass-through, EURUSD long ~0%). This is what makes the
  favourable-side carry sleeve positive-expectancy at all.

Caveats on the measurement: the account read was `1025742` on
`Capital.ComMena-Demo` (same server as the gold system's 1033030); the window was
two weeks in July 2026, so it reflects current conditions rather than a decade;
and cross symbols (EURGBP, EURJPY, GBPJPY, AUDJPY) returned no tick history in
this terminal, so their spreads remain unmeasured. The terminal also refuses
`copy_rates_*` entirely, so broker-native *bar* history is unavailable here.

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

The cheap decisive experiments have now been run. What remains needs either a
different market or a different cost structure.

1. **Scale the gold system instead.** It is a measured edge on a genuinely less
   efficient instrument. Diversifying into the most efficient market in the world
   to escape single-instrument risk trades a real edge for an unmeasured one, and
   seven hypothesis classes say the second edge is not there.
2. **If Forex exposure is genuinely required, change the cost structure.** Every
   rejection is a cost inequality. A raw-spread/commission ECN account (~0.1–0.3
   pips + commission) instead of a fixed 0.7-pip account would roughly halve
   EURUSD cost, which is the only thing that moves R7's inequality. That is a
   broker decision, not a research one, and it should be tested on the measured
   1.6-point mean-reversion effect before any capital is committed.
3. **Or widen the universe properly.** 20–30 currencies including EM, where carry
   and value premia are larger. Note this account's EM spreads (USDZAR 50 pips,
   USDMXN 21 pips) largely eat that premium, so it needs a venue with tighter EM
   pricing, and `copy_rates_*` being unavailable here means bar history would have
   to come from elsewhere.
4. **Do not** run another parameter search on majors, and do not deploy the carry
   sleeve at +0.5%/yr against a 68.6% drawdown. R1–R7 close that space with
   numbers.

Cross symbols (EURGBP, EURJPY, GBPJPY, AUDJPY) are the one small untested gap —
they are tradeable on the account but have no tick history in this terminal, and
crosses are less efficient than majors. That is a narrow lead, not a likely
system, and it would need broker data to evaluate honestly.

## Requirement status, stated honestly

| Requirement | Status |
|---|---|
| Forex system like the gold one | Infrastructure built and tested; no profitable strategy found |
| Consistent profit | **Not achieved.** Nothing survived out-of-sample at measured cost |
| Good trade frequency | Achievable (R1 families gave 150–1,700 trades/pair/yr) but only unprofitably |
| Demo ready | **Deliberately not shipped.** Nothing here earns demo authority |

Shipping a demo package would mean deploying a strategy measured to be
unprofitable. This repository has already paid three times for results that
looked good until the hindsight was removed — PF 1.99 → 0.82, a claimed PF 2.03
that was really 1.20, and an EURUSD portfolio at PF 1.3075 whose PF fell to 1.019
once the best 5% of trades were dropped. R4 is the fourth instance and the
cleanest: six consecutive positive in-sample years, then sign reversal in both
holdouts.

Adding a fifth by shipping something now would be the one genuinely costly
outcome available here. The honest deliverable is the measurement plus the
infrastructure to act on it.
