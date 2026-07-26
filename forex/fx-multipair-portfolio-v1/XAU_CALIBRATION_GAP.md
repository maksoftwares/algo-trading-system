# XAU V60: absolute risk controls have not scaled with gold's volatility

Status: **evidence for the XAU lane, read-only.** Nothing in the runtime, config,
preset or broker state was modified. Produced by
`audit_gold_calibration.py`; data in `outputs/XAU_CALIBRATION_AUDIT.json`.

This came out of the Forex work: the metric that closed all eleven FX hypotheses
(movement versus cost) also happens to reveal a calibration gap in the system that
already works.

## The fact

Gold's median daily range, measured from the Dukascopy archive (March + June of
each year):

| Year | Price | Daily range |
|---:|---:|---:|
| 2019 | $1,318 | $11.57 |
| 2021 | $1,750 | $19.34 |
| 2023 | $1,942 | $19.03 |
| 2025 | $3,125 | $33.20 |
| **2026** | **$4,464** | **$105.15** |

**5.53x wider than 2023. 9.09x wider than 2019.** The broker's spread is unchanged
at $0.30.

## What is fine

The seven `target_r_default` parameters are **R-multiples** — dimensionless. They
scale automatically with whatever stop distance is chosen, so they need no
revision. That is good design and this document is not a criticism of it.

## What has silently drifted

Every **absolute** control is a fixed number chosen under the old regime. Measured
in units of a current daily range:

| Control | Value | Daily ranges **today** | Daily ranges **in 2023** | % of $983 equity |
|---|---:|---:|---:|---:|
| `closed_drawdown_resume_usd` | $180 | 1.71 | 9.46 | 18% |
| `closed_drawdown_suspend_usd` | $225 | 2.14 | 11.82 | 23% |
| `combined_closed_drawdown_hard_stop_usd` | $300 | 2.85 | 15.77 | 31% |
| `floating_drawdown_hard_stop_usd` | $450 | 4.28 | 23.64 | 46% |
| `account.deviation_points` | 80 (=$0.80) | 0.80% of range | 4.20% of range | — |
| `sources[*].maximum_risk_usd` | $20–30 | 0.19–0.29 | 1.05–1.58 | 2–3% |

## Two consequences, pulling in opposite directions

**1. The guardians bind far sooner than designed.** The floating-drawdown hard
stop used to sit 23.6 daily ranges away from a flat book; it now sits 4.3 away.
The suspend breaker went from ~11.8 daily ranges to 2.1. These thresholds were
chosen so that only a genuine failure would trip them; at current volatility a
routine adverse session can reach them. Expect more halts, and expect them to be
uninformative about whether anything is actually wrong.

**2. `deviation_points = 80` will reject far more orders.** An $0.80 slippage
tolerance was 4.2% of a daily range in 2023 and is 0.80% now. In a market moving
5.5x faster, price will travel outside that window between decision and fill far
more often. Rejected orders are silent: the system simply does not trade, and the
absence shows up as low frequency rather than as an error.

**3. Per-trade risk has shrunk relative to the opportunity.** `maximum_risk_usd`
of $20–30 was 1.05–1.58 daily ranges in 2023 and is 0.19–0.29 now. The sleeves are
taking positions roughly 5x smaller relative to gold's movement than when they
were sized. That caps profit per trade even when the edge is intact.

So the same drift both **increases the halt rate** and **decreases profit per
trade**. Neither shows up as a bug; both show up as "the system trades less and
earns less than expected."

## Suggested checks, in order

1. **Count actual halts and order rejections** in the recent runtime logs and
   compare against the pre-2025 rate. This is the cheapest confirmation, and it
   either supports or kills the whole hypothesis immediately.
2. **Re-express the drawdown breakers in ATR or daily-range units** rather than
   fixed USD, so they hold their intended meaning as volatility moves.
3. **Re-check `deviation_points`** against the current distribution of price
   movement over the decision-to-fill interval.
4. **Re-check per-sleeve `maximum_risk_usd`** against both current volatility and
   the account's $983 equity — note the floating-drawdown stop is already 46% of
   equity, so raising risk without also revisiting that breaker would be unsafe.

## Caveats

- The 2026 sample is March + June 2026 only, and a $105 daily range is an
  exceptional regime that may not persist (2021 and 2023 both sat near $19).
  Thresholds should be re-derived on a rolling basis, not re-pinned to today.
- Dukascopy XAUUSD is 3-decimal and the broker quotes 2-decimal; USD figures are
  used throughout to avoid that mismatch.
- Equity of $983 was read once on 2026-07-26 from account 1033030.
- This says nothing about whether the sleeves' *edges* are intact. It is about the
  control layer around them.
