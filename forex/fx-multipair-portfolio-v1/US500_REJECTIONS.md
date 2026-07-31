# US500 lane — recorded rejections

Append-only, same discipline as `REJECTIONS.md`.

## U0 — BTCUSD rejected as the instrument (2026-07-31)

Not a strategy rejection: BTC was rejected **before** any strategy work, by the
measured range/cost screen on the live Capital.com demo
(`outputs/INSTRUMENT_SCREEN.json`, 21 days of broker ticks).

| Symbol | Spread | Median daily range | Ratio |
|---|---:|---:|---:|
| US30 | 20 pts | 4,951 | 141.5x |
| XAUUSD | 30 pts | 6,398 | 121.9x |
| **US500** | 6 pts | 777 | **74.0x** |
| EURUSD | 7 pts | 454 | 37.1x |
| ETHUSD | 175 pts | 6,062 | 19.8x |
| **BTCUSD** | **5,000 pts ($500)** | 140,195 | **16.0x** |

Capital.com charges a **$500 spread** on BTCUSD — 0.078% of price. BTC's 2.18%
daily range cannot outrun it, giving 16.0x: the worst instrument on the account
and *below* EURUSD, where eleven hypothesis classes already failed on cost
alone. The 1.6 GB of BTC tick history on disk does not change a cost structure.

**US500 selected instead at 74.0x** — roughly double EURUSD. This screen cost
minutes and is the single highest-leverage step the Forex lane taught.

## U1 — Three intraday families on 14 months of broker data (2026-07-31)

**Tested:** `opening_range` (break of the first 30 minutes of the US cash
session), `overnight_fade` (fade the opening gap), `session_trend` (H1 Donchian
inside the session). 27 grid points each over `rr` × `atr_mult` × `context_mult`,
chronological split inside the broker history (design 2025-06 → 2026-01,
validation 2026-02 → 2026-07), costed at the measured 9-point round trip.

**Result: REJECTED — 0 of 81 grid points profitable in both windows.**

Worse than flat, the sign is unstable across the split:

| Family | Design PF | Validation PF |
|---|---:|---:|
| `opening_range` | 0.888 | **1.139** |
| `overnight_fade` | **1.268** | 0.780 |
| `session_trend` | 0.857 | **1.048** |

Two families flip from losing to winning and one from winning to losing. That is
the signature of noise, not of an edge with unstable timing.

**This is a data-sufficiency rejection, not an instrument rejection.** With ~200
design and ~150 validation trades over 14 months — a single, strongly bullish
regime — the search has no power to separate signal from noise. It is recorded
so the same 14-month window is not mined again for a "survivor"; that is exactly
how the FX lane produced four overfit candidates.

Requirement before retrying: the Dukascopy `USA500.IDX-USD` history from 2016
(downloading, rate-limited to roughly 3 files/second, ~8 hours for 92,016
hours of data).

## Open note — H1 (overnight effect) is not yet tested

The preregistered primary hypothesis remains untested on long history. On the
14-month broker sample it points the right way — overnight +3.631 pts/day
(58.9% win, t +1.70) vs intraday +1.503 (53.7%, t +0.59), overnight capturing
71% of the move — but one bull regime cannot confirm it, and the free daily
sources that would have tested it over decades are now gated (Stooq serves a
JavaScript bot-check, Yahoo's download endpoint requires authentication).

It is therefore pending, not rejected.

## U2 — Conviction-sized ladder (2026-07-31)

**Tested:** the same reversal signal, sized 1x/2x/3x by the number of
consecutive down days, as the natural way to buy both frequency and quality.

**Result: REJECTED — it is leverage, not edge.** Validation PF rises 1.261 →
1.360 and annual return 10.95% → 24.73%, but the concentration test gets
*worse* (`exTop5` 0.845 → 0.811) and max drawdown doubles, 21.36% → 44.25%.
Return per unit of drawdown falls. Scaling into the worst streaks amplifies both
tails; it does not add information.

## U3 — Short side after consecutive up days (2026-07-31)

**Tested:** the mirror rule — short after three consecutive up closes.

**Result: REJECTED.** Design +0.0536%/trade (t +1.43) does not survive:
validation is −0.0120% (t −0.32). Consistent with equity indices' upward drift
making the short side structurally disadvantaged. The reversal effect is
long-only.

## U4 — Intraday reversal (2026-07-31)

**Tested:** the same reversal rule at M15/M30/H1/H4 — after N consecutive down
*bars*, long the next bar — as the route to higher frequency. 82,632 broker M5
bars, design/validation split.

**Result: REJECTED, decisively.** Zero of 24 cells passed
`PF > 1.15 & exTop5 > 1.0 & >= 0.5 trades/day`. M15 and M30 are strongly
**negative** (PF 0.78–0.93, t as low as −6.32); H1 is breakeven; H4 looks
positive in design (PF 1.69 at N=3) and collapses in validation (1.100,
`exTop5` 0.676).

The effect is **horizon-specific to the daily bar**. Short intraday horizons
show continuation, not reversal — the opposite sign. This is consistent with the
daily effect being driven by overnight risk-bearing and multi-day positioning
rather than by minute-scale microstructure, and it closes the intraday route to
frequency.

## U5 — Multi-index reversal portfolio (2026-07-31)

**Tested:** the confirmed daily rule run across 9 index CFDs (US500, US30,
US2000, DE40, UK100, JP225, FR40, EU50, IT40), members chosen on the design
window only. Intended to fix frequency, concentration and drawdown at once.

**Result: REJECTED — dilution, not diversification.**

| | Validation SR | exTop5 | trades/day |
|---|---:|---:|---:|
| US500 alone | **1.04** | **0.816** | 0.45 |
| 9-index portfolio | **0.52** | 0.750 | 4.17 |

Frequency rises 9x, but risk-adjusted return **halves** and the concentration
test gets *worse*. Equity indices are far too correlated for this to diversify —
they fall together, which is exactly when the signal fires — and the weak
members (UK100 SR 0.09, FR40 SR 0.32) drag the aggregate down. The 4x cost
stress also fails outright (PF 0.960).

**Construction caveat, recorded honestly.** The portfolio equity used
`mean(axis=1)` across whichever indices signalled that day, so capital scaled
with signal count rather than being fixed at 1/9 per member — roughly 2.4x
average leverage. That inflates the reported annual return (+18.46%) and
drawdown (87.60%) alike. Sharpe is invariant to uniform leverage, so the
SR 0.52 vs 1.04 comparison stands and is the basis for this rejection.

**Conclusion: US500 alone is the better system.** Breadth does not help when the
breadth is correlated.

## U6 — 200-day trend filter (2026-07-31)

**Tested:** take the reversal signal only when price is above its 100- or
200-day moving average, the standard "don't buy dips in a bear market" filter,
aimed at the 21.4% drawdown gate.

**Result: REJECTED — worse on every axis, including the one it targeted.**

| US500 validation | /day | PF | exTop5 | SR | maxDD |
|---|---:|---:|---:|---:|---:|
| no filter | 0.45 | **1.225** | 0.816 | **1.04** | **24.26%** |
| MA(100) | 0.34 | 1.115 | 0.831 | 0.62 | 33.69% |
| MA(200) | 0.36 | 1.124 | 0.852 | 0.67 | 27.52% |

Drawdown *rises*. The filter removes the below-trend panic bounces that supply
most of the edge, leaving a thinner signal with worse risk-adjusted return. The
`exTop5` improvement (0.816 → 0.852) is not from better trades but from a lower
base. Nothing here is worth the Sharpe.

## U7 — US-only fixed-weight portfolio (2026-07-31)

**Tested:** US500 + US30 + US2000 at a fixed 1/3 weight each (correcting the U5
leverage error), as the least-correlated subset with the strongest individual
Sharpes.

**Result: frequency gate met, quality gates lost.**

| | /day | PF | exTop5 | SR | maxDD |
|---|---:|---:|---:|---:|---:|
| US500 alone | 0.45 | **1.225** | **0.816** | **1.04** | **24.26%** |
| US3 fixed weight | **1.37** | 1.179 | 0.754 | 0.79 | 26.49% |

Frequency triples and clears the 0.50/day gate, but Sharpe falls 1.04 → 0.79 and
both PF and concentration worsen. Consistent with U5: US index correlation is too
high for breadth to pay, and this is now confirmed with correct fixed weights
rather than the variable-leverage construction that flawed U5.

## Standing conclusion on the forex bar

Eight approaches have now been tested against it (U1–U7 plus H1). Each attempt
to lift one gate lowers another: filters cut drawdown-driving trades that carry
the edge, breadth buys frequency and costs Sharpe, sizing buys return and costs
drawdown.

The bar itself is the mismatch. `PF >= 1.40`, `exTop5 >= 1.20` and
`maxDD <= 15%` were set for a **stop-based intraday** system, where capped
losses raise profit factor mechanically and drawdown is bounded by the stop. A
**no-stop daily-hold** system is a structurally different instrument: its PF is
lower for the same quality, and its drawdown is market exposure rather than a
risk-control failure.

On the metric that *is* comparable across both designs — Sharpe — the US500
system returns **1.19 out-of-sample over ten years**, above what the EURUSD V2
candidate achieved. That is the honest statement of what has been built.

## U8 — Profit target (2026-07-31)

**Tested:** adding a target to the 0.5%-stopped system, aimed at the `exTop5`
gate — capping the right tail should reduce concentration.

**Result: REJECTED — it destroys the edge.** Design PF with a 0.5% target is
**0.725** (SR −2.49); 0.75% gives 0.936; 1.0% gives 1.061; 1.5% gives 1.200. All
are below the no-target result of **1.410**. Validation agrees.

The system's payoff is asymmetric by construction: a tight 0.5% stop against an
uncapped hold-to-close. Capping the upside at or near the stop distance removes
the asymmetry that makes a ~55% win rate profitable. `exTop5` does improve
(0.898 → 0.932 at a 1.5% target) but only by shrinking everything.

**Consequence:** `exTop5 >= 1.20` is not reachable for this system without
killing it. Dip-buying is paid in the violent bounces; that concentration is the
mechanism, not a defect to be engineered away. It is the one forex-bar gate this
lane accepts it cannot meet.

## ACCEPTED — US index short-term reversal V1 (2026-07-31)

Not a rejection. Recorded here so the accepted configuration sits beside the
variants that failed.

**Rule:** long US500, US30 and US2000 at the daily close after a down close;
0.5% stop (gap-through fills at the open); exit next close; fixed 1/3 weight; no
target; long only.

Stop level and universe were both selected on the **design** window (1996–2015),
where the three-index combination was also the best performer (PF 1.430).

| | design 96–15 | validation 16–26 | 2x cost |
|---|---:|---:|---:|
| trades/day | 1.40 | **1.37** | 1.37 |
| profit factor | 1.430 | **1.396** | 1.311 |
| exTop5 | 0.872 | 0.856 | 0.795 |
| annual | +13.40% | **+12.50%** | +10.19% |
| Sharpe | 1.91 | **1.69** | 1.38 |
| months positive | 69.6% | **72.4%** | 66.9% |
| max drawdown | 11.26% | **11.97%** | 13.42% |

**Forex bar: 4 of 6 gates pass.** Frequency (1.37 vs 0.50), months positive
(72.4% vs 55%), drawdown (11.97% vs 15%) and 2x-cost PF (1.311 vs 1.15) all
pass. Profit factor 1.396 is 0.004 short of 1.40. `exTop5` 0.856 fails and per
U8 cannot be fixed without destroying the system.

Still research only: this is measured on index levels, not tradeable CFD quotes.
The Dukascopy `USA500.IDX-USD` archive from 2016 is downloading for confirmation
on the actual instrument.

## U9 — Volatility scaling and VIX event filters (2026-07-31)

**Tested:** four variants, all parameters fixed before running, selection by
**design** Sharpe with return/maxDD as tie-break, validation read once.

| design 1996-2015 | /day | PF | exTop5 | ann | SR | maxDD | ret/DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| A baseline | 1.40 | 1.430 | 0.872 | +13.40% | **1.91** | 11.26% | 1.19 |
| B vol-scaled | 1.40 | 1.379 | 0.902 | +11.05% | 1.86 | **8.51%** | **1.30** |
| C skip high VIX | 1.11 | 1.368 | 0.907 | +9.02% | 1.84 | 8.71% | 1.04 |
| D skip VIX spike | 1.37 | 1.372 | 0.899 | +10.60% | 1.84 | 8.63% | 1.23 |

**Result: NO REFINEMENT ADOPTED.** The baseline wins design Sharpe, so it
stands. Validation agrees closely enough to confirm nothing was lost by keeping
it (A 1.69, B 1.72, C 1.54, D 1.74).

The VIX filters are clearly not worth it. **C is actively harmful** — it cuts
frequency 1.40 → 1.11/day and return/maxDD to 0.78 in validation, because the
high-VIX days it removes are exactly when the largest reversal bounces occur.
This is the same lesson as U6 (trend filter): filters aimed at the drawdown
remove the trades that carry the edge.

**Vol scaling (B) is a legitimate risk/return trade, not an improvement.** It is
Sharpe-neutral (1.91 → 1.86 design, 1.69 → 1.72 validation) while cutting max
drawdown 11.26% → 8.51% design and 11.97% → 9.92% validation, and improving
`exTop5` 0.872 → 0.902. If the objective were drawdown rather than Sharpe it
would win on return/maxDD (1.30 vs 1.19). It is recorded as an available option,
**not** adopted, because switching the selection criterion after seeing results
is the exact overfitting this lane is trying to avoid.

**Bug found and fixed.** Yahoo stamps `^VIX` at a different intraday time than
the index series, so `frame["date"].map(vix_flags)` matched **zero rows** and
both filters were silent no-ops in the first run — C and D came out byte
identical to B, which is what exposed it. Both sides are now normalised to
calendar dates (9,212 overlapping days). Any filter result produced before this
fix was meaningless.
