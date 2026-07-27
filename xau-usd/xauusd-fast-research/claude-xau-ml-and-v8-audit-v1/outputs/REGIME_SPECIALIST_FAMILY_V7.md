# Per-regime specialist family — iterations 3–7

Goal set by the owner: one specialist per gold regime, non-interfering, each
winning on its own, family win rate above 50%, profit factor near 2.00, tightly
controlled drawdown.

Nothing here has demo or live authority. Research artifact only.

---

## What actually moved the needle

Iterations 1–2 varied only exit geometry and could not move win rate and profit
factor together — exits trade one against the other by construction. Three
things did move both:

**1. A fitted per-regime entry ranker (iteration 3).** Ridge, 8 features, fit on
dev only. Ranking entries inside a regime and keeping the best few percent lifts
both metrics at once, because it removes trades that would have hit the stop.

**2. `FADE_POP` — shorting the pop (iterations 4–5).** Every earlier short test
had used the wrong mechanism: trend-following breakdowns, or slow fades of a
stretched EMA. Fading a short-horizon pop (≥1.0 ATR over 2h) with a near first
target is a different trade, and it is the best specialist in BULL, RANGE_QUIET
and CRASH/BEAR. The prior conclusion "gold shorts never work" was wrong, and was
wrong because of an untested mechanism, not because of the data.

**3. Splitting the two exit levers (iteration 6).** `rr1` and `part` set the win
rate — a trade wins iff price reaches the first target before the stop,
regardless of size banked there. `rr2` sets the profit factor. Earlier grids
moved them together and so kept trading one against the other. The productive
corner is a *small* partial at a *near* target with a *far* runner: bank 25% at
0.75R, run 75% to 6R.

## The calibration bug that faked an edge decay

Iteration 3's leaders showed PF 2.18 on test and PF 1.14 on holdout. That looked
like alpha decay. It was not.

The ranker thresholded at a fixed quantile of the 2016–2021 score distribution.
Gold ran ~$2,600 → ~$4,000, ATR grew, and `spread/stop` drifted −1.15 sd while
`activity` drifted +0.75. Since the ranker rewards tight spread, nearly every
2025–26 candidate scored high:

| era | intended admit | actual admit |
|-----|---------------|--------------|
| dev | 5% | 5.1% |
| test | 5% | 4.0% |
| **holdout** | 5% | **24.6%** |

Selectivity collapsed 5×. The edge itself was intact — the *unselected* base rate
improved out of sample (+0.014R holdout vs −0.141R dev). Fix: standardise
features and take the threshold against a trailing window of prior candidates,
so trade rate is constant by construction. Both causal. Holdout admission went
back to 6.3%, and holdout PF recovered 1.09 → 1.40.

Refitting the ranker walk-forward made things *worse* everywhere — it amplifies
noise. Keep the stable weights; recalibrate only the scale.
See `src/regime_drift.py`, `src/regime_frontier5.py`.

## The result, and why the headline number is not the honest one

Best composition on dev+test (`V4_tightest`, K=3): **WR 63.0%, PF 1.99,
maxDD $121, 65.8% green months**, Capital.com confirming at 62.3% / 1.85.

That number should not be used for planning. It was chosen from 24
composition×K cells, its components came from a sweep of ~1,900 configurations,
and the 2025–26 holdout had been inspected across four iterations by the time it
was picked. Selection that intense leaks.

`src/regime_walkforward.py` measures the **procedure** instead of the chosen
configuration: for each year, every candidate is scored on trades closed strictly
before that year, the best per regime is picked on that evidence alone, the
ranker is fit on pre-year data, and the family then trades the year. No
information from year Y touches any decision made for year Y.

| | in-sample claim | walk-forward |
|---|---|---|
| win rate | 63.0% | **51.5%** |
| profit factor | 1.99 | **1.12** |
| max drawdown | $121 | **$277** |
| green months | 65.8% | **49.3%** |
| total (\$9/trade) | +$1,315 | **+$224** |

**The win-rate target survives; the profit-factor target does not.**

## Letting each regime earn its place, causally

Deleting the losing regimes after seeing the walk-forward result would repeat
the exact error the walk-forward exists to expose. So the standdown rule goes
*inside* the procedure: before each year, the chosen specialist for a regime is
scored on its own prior closed trades, and the regime trades that year only if
that record clears a floor. An EA can compute this at runtime — no hindsight.

Preregistered grid (`min_pf` × `lookback`), all cells reported:

| min prior PF | lookback | n | WR | PF | maxDD | green | worst mo | cap WR / PF |
|---|---|---|---|---|---|---|---|---|
| 1.0 (no gate) | all | 363 | 51.8% | 1.12 | $277 | 47.5% | −$80 | 53.4% / 1.08 |
| 1.0 | 3y | 369 | 52.0% | 1.16 | $241 | 50.0% | −$80 | 56.9% / 1.38 |
| 1.3 | all | 333 | 52.6% | 1.20 | $268 | 50.9% | −$80 | 54.1% / 1.14 |
| 1.3 | 3y | 351 | 54.1% | 1.27 | $140 | 54.0% | −$47 | 59.0% / 1.52 |
| 1.5 | all | 281 | 54.8% | 1.42 | $141 | 58.7% | −$61 | 55.9% / 1.32 |
| **1.5** | **3y** | **288** | **54.9%** | **1.45** | **$136** | **61.9%** | **−$46** | **60.1% / 1.74** |

Every metric improves monotonically in both parameters. Extending the grid past
the preregistered range found the turning point, which is what a real mechanism
should have — too strict a gate stands regimes down while they are still fine:

| min prior PF | 1.0 | 1.3 | **1.5** | 1.8 |
|---|---|---|---|---|
| PF (3y lookback) | 1.16 | 1.27 | **1.45** | 1.35 |

A gradient that rises to an interior optimum and falls again is much stronger
evidence than a lone peak at the edge of the search, which is what noise
produces.

The gate earns its keep on the worst year without being told about it: it stood
BULL and STRONG_BULL down in 2026, the year that lost $153 ungated. Yearly P&L
becomes +$0, +$107, −$28, +$141, +$198, +$88, +$36 — one negative year in seven.

## Which specialists are real

Walk-forward, by regime:

| regime | mechanism | n | WR | PF | $ | verdict |
|--------|-----------|---|----|----|---|---------|
| BULL | fade pop (short) | 163 | 58.3% | 1.56 | +$348 | holds up |
| RANGE_QUIET | dip buy | 33 | 60.6% | 1.77 | +$92 | holds up |
| CRASH/BEAR | fade pop (short) | 10 | 50.0% | 1.07 | +$3 | too few trades to judge |
| DOWNTREND | mean-rev long | 92 | 47.8% | 0.85 | −$66 | fails |
| STRONG_BULL | mean-rev long | 127 | 43.3% | 0.77 | −$153 | **fails** |

STRONG_BULL is the cautionary one: 62.9% WR / PF 1.31 on holdout, and it loses
money once its configuration is chosen without hindsight. A second tell was
visible without the P&L — the procedure kept changing which STRONG_BULL variant
it preferred (SB_A→SB_A→SB_B→SB_C→SB_A), whereas RANGE_QUIET picked `RNG_C`
every single year and BULL never left the FADE_POP mechanism. **Instability of
the selection is itself evidence of no stable edge.**

## The decisive test: remove my judgement too — and it fails

v1 and v2 walk the *config* choice forward but the candidate pool was still mine.
I chose FADE_POP for BULL and dip-buy for RANGE_QUIET after seeing every era,
then let the procedure pick among variants of my own picks. That is where the
remaining leak lived, and it was the biggest one.

`src/regime_walkforward3.py` removes it: all five mechanisms offered to all five
regimes (675 candidates), nothing pre-filtered by anything I had learned, annual
causal selection choosing the mechanism as well as its parameters.

| | walk-forward v2 (my pool) | **walk-forward v3 (no pre-chosen mechanism)** |
|---|---|---|
| win rate | 54.9% | **48.6–49.4%** |
| profit factor | 1.45 | **0.80–0.82** |
| P&L at \$9/trade | +$542 | **−$435 to −$564** |
| max drawdown | $136 | **$513–611** |

**It loses money.** The pick log shows why: a causal process does not choose
FADE_POP for BULL until **2023** — it picks MR_SHORT and MOM_LONG in 2019–2022.
My "FADE_POP discovery" required seeing the whole sample. And once the procedure
does find it, it still does not pay:

| BULL | n | WR | PF | $ |
|---|---|---|---|---|
| 2019–2022 (pre-FADE_POP picks) | 117 | 47.9% | 0.92 | −$47 |
| 2023–2026 (FADE_POP picks) | 76 | 51.3% | 1.02 | +$7 |
| whole family 2023–2026 | 179 | 54.7% | 1.01 | +$5 |

Break-even, not an edge.

## A flaw in the v2 standdown gate

In v3 the gate makes no difference at all — `min_pf` 1.0 through 1.8 give
identical results. The reason is circularity: the procedure *selects* the
candidate that maximises prior-window score and then the gate *tests* prior-window
PF. With 135 candidates per regime, something always clears the bar, so the gate
never binds. It only appeared to add +0.33 PF in v2 because the pool was 11
hand-picked configs and the best one sometimes still had a weak prior record.

So the v2 result is not "walk-forward plus a useful runtime gate". It is
"hindsight mechanism choice, partially disciplined". The gate is not a validated
mechanism, and the +0.33 PF claim is withdrawn.

## Status — negative

**The per-regime specialist family has no reproducible edge on this data.** Every
version of the target metrics that survives honest testing is at or below
break-even:

| measurement | WR | PF | verdict |
|---|---|---|---|
| in-sample, best of 24 compositions | 63.0% | 1.99 | not evidence |
| walk-forward, my hand-picked pool | 54.9% | 1.45 | leaks mechanism choice |
| walk-forward, no pre-chosen mechanism | 49.1% | 0.82 | **loses** |

What is nonetheless durable and worth keeping:

- The **exit-geometry law** (rr1 and partial size set win rate; rr2 sets profit
  factor) is a structural fact about this trade type, independent of whether any
  particular specialist works.
- The **rolling-calibration fix** is a genuine bug fix that any deployed ranker
  needs, and the diagnosis method (selected fraction per era) generalises.
- The **size of the selection leak** — 63.0%/1.99 in-sample versus 49.1%/0.82
  when nothing is chosen with hindsight — is the most useful number produced
  here. It should be used to discount every other result in this repository that
  was tuned the first way.
- **Selection instability as a tell**: the procedure re-picked the same
  RANGE_QUIET config 8/8 years while churning STRONG_BULL variants annually. The
  churn predicted the failure before any P&L was consulted.

Not deployable. Do not shadow. The honest next step is new information — a
different instrument set, a venue with different microstructure, or a
redefinition of the trade — not further search over this data, which is what
[[second-ea-search-exhausted]] already concluded.

Files: `src/regime_frontier{3,4,5,6}.py`, `src/regime_drift.py`,
`src/regime_family.py`, `src/regime_family_sweep.py`,
`src/regime_walkforward{,2}.py`; results under `outputs/REGIME_*.json`.
