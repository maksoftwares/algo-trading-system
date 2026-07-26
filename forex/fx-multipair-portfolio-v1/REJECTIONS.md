# Recorded rejections

Append-only. Every hypothesis this lane closes is written here with the evidence
that closed it, so it is not silently retried later.

## R1 — Uniform bar-geometry families across majors (2026-07-26)

**Hypothesis (PREREGISTRATION.md §3):** one low-parameter mechanism applied
identically to EURUSD/GBPUSD/USDJPY yields a cross-sectionally diversified
portfolio that survives retail spread.

**Families tested:** `london_breakout` (Asia range broken after London opens),
`donchian_h4` (30-H4-bar channel break), `asia_fade` (1.5-ATR M30 excursion
faded inside Asia hours).

**Grid:** 48 points each (`rr` × `atr_mult` × `context_mult`), design window
2016-07-01 .. 2021-12-31, all three pairs, identical parameters per pair.

**Result: REJECTED.** Not one of 48 grid points, in any family, had PF > 1.0 on
all three pairs. Best median PF across pairs was 0.998 (`london_breakout`,
rr 1.5, atr_mult 3.0).

**Why it is a real rejection and not a cost artefact.** Rerunning at *zero*
cost leaves PF at 0.87–1.07, mean ≈ 0.97:

| Family | Zero-cost PF range | Cost as % of stop |
|---|---|---|
| `london_breakout` | 0.931 – 1.038 | 6.3 – 6.7% |
| `donchian_h4` | 0.868 – 0.955 | 2.7 – 3.2% |
| `asia_fade` | 0.934 – 1.070 | 8.0 – 8.6% |

`donchian_h4` is the decisive case: cost is only ~3% of its stop, so it is
essentially cost-free, and it is still PF 0.87–0.96. These geometries carry no
exploitable edge on majors — cost merely converts a coin flip into a loser.

Evidence: `outputs/DESIGN_GRID.csv`, `outputs/DESIGN_SELECTION.json`.

**Conclusion carried forward.** Raw OHLC geometry on liquid majors is
efficient at these horizons. Do not retry breakout/channel/fade variants on bar
geometry alone; any further hypothesis must add an information source that bar
geometry does not contain.

## R3 — Intraday conditioning census: no cross-pair predictability (2026-07-26)

**Tested:** 49 conditioner buckets × 3 horizons (1h, 4h, 1d) × 3 pairs on the
design window — hour-of-day, weekday, month-end, momentum at 1h/4h/1d/3d
lookbacks × 3 magnitude bands, reversion from a 1-day mean, and volatility-
regime interactions. t-statistics on non-overlapping samples.

**Result: REJECTED.** Momentum and mean-reversion conditioners are noise
(|t| ≤ 2.6, no sign agreement, means ≈ 0). Not one bucket had |t| > 2 on all
three pairs at the 4h or 1d horizon. The only structure with real magnitude was
hour-of-day, which R4 then tested and killed.

Evidence: `outputs/EDGE_CENSUS.json`.

## R4 — Tokyo-hour short-USD drift (2026-07-26)

**The strongest in-sample effect found anywhere in this lane, and it failed.**

Hour 01:00–02:00 UTC showed all three pairs significant with a single coherent
economic reading — EURUSD and GBPUSD up, USDJPY down, i.e. USD systematically
weakening in early Tokyo. Design window: +8.5 points/hour for the basket,
**positive in 6 of 6 years**, hour 02:00 adding +4.0 more, also 6/6.

Traded literally (enter 01:00 UTC, exit 03:00 UTC, long EURUSD + long GBPUSD +
short USDJPY), measured gross of any retail markup:

| Window | Basket | t |
|---|---|---|
| Design 2016-07 .. 2022-01 | **+23.39 pts** | +2.77 |
| Validation 2022-01 .. 2024-07 | **−21.25 pts** | −1.38 |
| Final exam 2024-07 .. 2026-07 | **−30.82 pts** | −1.77 |

**Result: REJECTED.** The sign reversed in *both* out-of-sample windows, and it
loses even at zero added spread. Six consecutive positive in-sample years
carried no predictive content whatsoever.

The holdout was consumed here deliberately: one pre-specified hypothesis, tested
once, reported as-is. That is what it was reserved for.

## R5 — Cross-sectional price-only FX premia, 7 majors, 1999–2026 (2026-07-26)

**Tested:** 331 months of currency excess returns for EUR/GBP/AUD/NZD/JPY/CAD/
CHF vs USD. Time-series momentum (1/3/6/12m), cross-sectional momentum
(1/3/6/12m, top2−bottom2), long-run value reversal (36m, 60m), and the dollar
factor.

**Result: REJECTED.** Everything is indistinguishable from zero: TSMOM Sharpe
+0.06 to +0.12 (t ≤ 0.62), XSMOM *negative* at every lookback, value reversal
the best at Sharpe +0.22 (t = 1.13) and negative 2021–2026, dollar factor
Sharpe +0.01. Consistent with the published finding that G10 FX momentum
largely disappeared after 2008.

## R6 — FX carry: real but not retail-capturable (2026-07-26)

**Tested:** carry on the same 7-major panel using OECD 3-month interbank rates
from FRED, signal lagged one month, total return = spot + interest differential.

**Result: real premium, rejected as a retail deliverable.** Top2−bottom2 carry
returns +3.56%/yr, Sharpe 0.40, t = 2.11 — the only genuine edge this lane
found. But the decomposition is decisive:

| Component | Annual | Sharpe | Max drawdown |
|---|---|---|---|
| Interest differential only | **+3.48%** | 7.78 | **0.0%** |
| Spot only | **+0.08%** | 0.01 | **55.6%** |

100% of the return is interest accrual and 0% is spot, while spot carries all
the risk. On a retail MT5 account that accrual arrives as broker **swap**, which
is marked up against the client on both sides, so the component that *is* the
edge is precisely the component the broker keeps. Combined with a 45% strategy
drawdown, this is not a demo-ready proposition without verified swap rates
showing favourable pass-through.

## R7 — Tick microstructure / order-flow (2026-07-26)

**The last untried information source, and the most decisive rejection.**

Every earlier test read OHLC bars. The Dukascopy archive turns out to carry real
top-of-book depth (`bidVolumes`/`askVolumes` are populated quoted sizes, median
~4.6M on EURUSD), so this tested order-flow information that bars do not contain:
depth imbalance, microprice deviation from mid, quote-update asymmetry, signed
tick flow, realised activity and mean spread — plus a z-scored composite. 747k
M5 rows per pair.

Scored against **measured** broker cost, not an assumption. A long-top-decile /
short-bottom-decile strategy earns about half the decile spread per trade, so the
bar is a decile spread above 2x round-trip cost: 22 points on EURUSD, 34 on
GBPUSD, 32 on USDJPY.

**Result: REJECTED.** No feature, on any pair, at any horizon (5/15/30/60 min),
cleared the bar. The largest decile spread found anywhere was ~6 points against
22+ required — short by a factor of 4 to 6.

**The instructive part.** `signed_flow` is overwhelmingly significant and
consistent across all three pairs at the 5-minute horizon: t = −9.3 (EURUSD),
−7.8 (GBPUSD), −6.3 (USDJPY), a genuine short-term mean-reversion effect. Its
magnitude is **1.6 points**, against a measured 7-point EURUSD spread.

This is the central result of the whole lane: **the bid-ask spread is wider than
the entire predictable component of FX returns.** The information is real and
highly significant; it is simply smaller than the cost of acting on it.
Statistical significance and tradeability are not the same thing.

Evidence: `outputs/MICRO_CENSUS.json`, `outputs/BROKER_SPREAD_TICKS.json`.

## R11 — Microstructure ML with interactions (2026-07-26)

**The most persuasive rejection in this lane, because it is the experiment a
skeptic would demand.**

R7, R8 and R10 all measured features *univariately* — single-feature deciles or a
plain z-score average. None allowed a model to find interactions, and this repo's
own record for gold is that tick-microstructure features carried most of that
edge as an **ML** result rather than a decile table. That was the last
methodological gap.

Gradient boosting (13 microstructure features, 60-minute forward return), one
frozen configuration with no hyperparameter search, trained on design and
evaluated on validation. Scored as a strategy would trade it: take the model's
most confident decile and require the realised mean move to exceed full
round-trip cost.

| Pair | Cost | **Design edge** | t | **Validation edge** | t | Clears? |
|---|---:|---:|---:|---:|---:|---|
| EURUSD | 11 | **19.09** | **9.67** | 3.69 | 1.04 | no |
| GBPUSD | 17 | **32.10** | **8.48** | 4.84 | 0.97 | no |
| USDJPY | 16 | **20.79** | **8.20** | 7.04 | −0.61 | no |

**Result: REJECTED.** In-sample the model clears cost by 1.7–1.9x at t = 8.2–9.7
on all three pairs simultaneously — an unambiguous "working system" by any
in-sample standard. Out-of-sample the edge decays roughly **80%**, falls below
cost on every pair, and reaches significance on none.

Two things make this decisive:

1. The validation edges (3.69 / 4.84 / 7.04 points) land almost exactly on the
   univariate results from R7 and R10. **The interactions the model found were
   noise.** There is no hidden multivariate structure that decile analysis missed.
2. It closes the "you just didn't use ML" objection with the strongest possible
   in-sample number. Nothing about the method was underpowered; t = 9.67 on
   ~34,000 training rows is not a lack of statistical power. The signal genuinely
   is not there out-of-sample.

Evidence: `outputs/MICRO_ML_TEST.json`.

## R10 — The fixed-spread structural advantage (2026-07-26)

**The last stone, and the one that makes the conclusion airtight.**

This lane measured a genuine asymmetry and had not exploited it: the broker quotes
a **fixed** spread (EURUSD 0.70 pips at every hour) while the true interbank
spread in the Dukascopy quotes reaches 3.0 pips at its 99th percentile. Inside
those bars the account is offered materially better-than-market execution — and
liquidity withdrawal is exactly when transient dislocations are largest, which is
where R7's real mean-reversion effect should pay.

Critically this is *not* R8 repeated: R8 conditioned on realised volatility (how
big moves are), R10 conditions on quoted spread (market-maker inventory stress).
Different variable, different hypothesis.

Method: measure the R7 effects inside the top-decile-quoted-spread bars, and
charge the broker's **fixed** cost rather than the true spread. Grid deliberately
pre-specified and small after R8's lesson — 2 signals × 4 horizons × 3 pairs =
**24 cells**, not 300.

**Result: REJECTED.** Exactly **1 of 24** cells cleared cost, against ~1.2 expected
by chance at 5%. It did not replicate: EURUSD `signed_flow` at 60m went from 13.35
points (1.21x cost, t = 3.35) on design to 4.73 points (t = 1.44) on validation —
same sign, but below cost and not significant.

**What the design window does show, and why it settles the question.** The effect
is unmistakably real, with a clean monotone gradient in horizon on EURUSD:

| Horizon | 5m | 15m | 30m | 60m |
|---|---|---|---|---|
| Edge (points) | 1.59 | 3.37 | 5.71 | **13.35** |
| t | 4.56 | 4.03 | 3.44 | 3.35 |
| Multiple of cost | 0.14 | 0.31 | 0.52 | **1.21** |

A consistent, highly significant, monotonically growing effect — measured in the
single most favourable regime available (liquidity stress), on the cheapest major,
charged the broker's fixed cost rather than the true one. It still only reaches
1.21x cost at its best, and then fails to replicate.

That is the strongest available statement of this lane's conclusion. It is not
that no signal exists in FX — signal demonstrably exists, at t > 4. It is that
after stacking every advantage in its favour, the signal is roughly the same size
as the cost of acting on it, and what little exceeds it does not persist.

Evidence: `outputs/SPREAD_DISLOCATION_TEST.json`.

## R9 — Synthetic crosses, including the one candidate that reached validation (2026-07-26)

**The last gap, now closed.** EURGBP / EURJPY / GBPJPY are tradeable on the
account, are less efficient than USD majors, and have genuinely different
dynamics — the JPY crosses trend, EURGBP ranges. R1–R8 never touched them because
the terminal holds no tick history for them, so `build_crosses.py` constructs them
arbitrage-exactly from the majors (747k M5 bars each, zero negative spreads).
Costs are the legs' summed measured spreads, which is pessimistic versus a direct
broker quote: EURGBP 24, EURJPY 23, GBPJPY 29 points round trip.

Ran the identical R1 family grid (3 families × 48 points), each best point also
rerun at zero cost, plus a multi-day momentum census.

**Result: REJECTED.** Of nine cross/family combinations, one survived the design
screen — and it was the best-looking candidate this entire lane produced:

**GBPJPY `donchian_h4`**, design PF **1.483** costed and **1.470** at zero cost,
242 trades, 55.8% win rate, 1790-point stops. Cost is only ~1.6% of risk, so it
was not a cost artefact, and trend-following working on the highest-volatility
trending cross while failing on range-bound EURGBP is mechanistically coherent
rather than arbitrary. It looked like the system.

Frozen parameters, then every check that killed earlier candidates:

| Window | Trades | WR | PF | ex-top-5% PF |
|---|---|---|---|---|
| Design 2016-07 .. 2022-01 | 242 | 55.8% | **1.483** | 1.223 |
| Validation 2022-01 .. 2024-07 | 112 | 47.3% | **0.903** | 0.740 |
| Final exam 2024-07 .. 2026-07 | 77 | 42.9% | **0.916** | 0.761 |
| **Pooled out-of-sample** | 189 | 45.5% | **0.908** | **0.749** |

Five of six criteria failed: validation PF, final-exam PF, pooled OOS PF, pooled
ex-top-5%, and survival at 2x cost.

**The one criterion it passed is the instructive part.** The *plateau* test passed
cleanly — neighbouring grid points also worked (rr 1.2/1.5/2.0 → PF
1.483/1.353/1.281; atr_mult 1.5/2.0/3.0 → 1.272/1.274/1.483). It was a genuine
broad plateau in-sample, not a spike. And it still collapsed out-of-sample.

So in-sample robustness checks do **not** predict out-of-sample validity. A
plateau shows a result is not a numerical accident; it says nothing about whether
the relationship persists. Only untouched data answers that. This is worth pairing
with R8: neither effect size, nor t-statistic, nor parameter-plateau breadth
substitutes for a holdout.

Multi-day momentum on crosses was also negative (t = −2.79 / −2.15 / −2.69, i.e.
mildly *anti*-predictive), matching the majors in R5.

Evidence: `outputs/CROSS_SEARCH.json`, `outputs/CROSS_GRID.csv`,
`outputs/GBPJPY_DONCHIAN_VALIDATION.json`, `outputs/CROSSES_MANIFEST.json`.

## R8 — Volatility-conditioned microstructure (2026-07-26)

**The most seductive false positive in this lane. Worth reading before proposing
anything else.**

The hypothesis was well motivated, not fishing: the broker's spread is *fixed*
(EURUSD 0.70 pips at every hour), while the size of predictable moves scales with
volatility. R7 measured effects averaged over all conditions, which mixes calm
hours where cost dominates with volatile hours where it might not. So volatility
should buy affordability.

Searched 4 signals × 5 horizons × 3 symbols × 5 volatility quintiles = **300
cells**, scoring each against measured round-trip cost.

**It appeared to work.** 8 cells cleared cost with |t| > 2, all at the 4h horizon,
with edges of 24–63 points against 11–17 points of cost — 2.2x to 4.8x cost. On a
naive reading that is a tradeable system.

**Four things said otherwise before any further data was touched:**

1. 8 hits from 300 cells is *below* the ~15 expected at a 5% false-positive rate;
2. the winning volatility quintiles were scattered (Q2, Q3, Q4, Q5) with no
   monotone relationship to volatility — the opposite of a mechanism;
3. the sign flipped between pairs;
4. a 50-point edge is an implausibly large fraction of a 4h EURUSD move.

**Replication test.** The identical measurement was re-run on validation and each
cell checked for the same sign, still clearing cost, still |t| > 2 — a
replication, not a new search, so it cannot manufacture a result.

| Result | Count |
|---|---|
| Cells selected on design | 8 |
| **Replicated on validation** | **0** |
| Sign flipped entirely | 5 |
| Reached \|t\| > 2 | 0 (best 1.67) |

**Result: REJECTED as multiple-testing noise.**

**The lesson, which is the durable output.** An edge of 4.8x cost with t = 2.8 was
available to ship, and it was worthless. What killed it was not a better idea but
a cheap procedural habit: count the cells searched, compare the hit rate to chance,
distrust scattered parameters and flipped signs, and re-run the same measurement on
new data before believing anything. This repo's four prior reversals
(PF 1.99 → 0.82, claimed 2.03 → 1.20, EURUSD 1.3075 → 1.019 ex-top-5%, and R4's
6-of-6 years → sign reversal) are all the same error. Any future FX or XAU
candidate should face this replication step before it is written up, let alone
deployed.

Evidence: `outputs/VOL_CONDITIONED_CENSUS.json`, `outputs/VOL_REPLICATION_TEST.json`.

## R6a — Carry re-tested with measured broker swap (2026-07-26)

R6 rejected carry on the assumption that retail swap markup destroys the
accrual. Measuring the account's real swap rates refines that: the broker skims
**asymmetrically**, paying close to fair on one side of each pair and gouging the
other (GBPJPY long ~96% pass-through, USDJPY long ~91%, EURUSD long ~0%). Taking
only the favourable side is therefore genuinely positive-expectancy.

Quantified on the four best-paying sides (long USDJPY, long USDCHF, short
USDMXN, short USDZAR), equal-weight, 0.01 lot, 6,905 daily observations:

| Quantity | Value |
|---|---|
| Expected accrual (today's measured swap) | **+2.10%/yr** |
| Historical spot drift | **−1.61%/yr** |
| **Net expectancy** | **≈ +0.5%/yr** |
| Historical spot volatility | 6.69%/yr |
| Historical spot max drawdown | **68.6%** |

**Result: REJECTED as deployable.** Diversification works — leg volatility of
10–16% falls to 6.69% at the basket level, with leg correlations of −0.29 to
+0.50 — but the accrual is simply too small. Roughly half a percent a year of net
expectancy against a 68.6% historical drawdown is not a system, and the entry
spread on USDZAR alone takes 8 days of accrual to repay.

Evidence: `outputs/CARRY_SLEEVE.json`, `outputs/BROKER_COSTS.json`.

## R2 — Inherited EURUSD M30 RSI/Bollinger fade at retail cost (2026-07-26)

**Result: REJECTED as a deployable candidate.** PF 1.083 at Dukascopy raw
spread (0.3 pips) falls to 0.990 at a 1.0-pip retail spread and 0.850 at 2.3
pips. The mechanism is its 0.8R target: breakeven win rate is 55.5% before cost
and 60.8% after, against an actual 57.5%.

This also means the inherited MT5 figure of PF 1.20 was measured at an
optimistically tight tester spread and should not be treated as a retail-
achievable result.

Evidence: `outputs/REFERENCE_SPREAD_STRESS.json`.
