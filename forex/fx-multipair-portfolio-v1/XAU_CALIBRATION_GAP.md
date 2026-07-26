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

## VERIFICATION: the runtime evidence does **not** support the consequences above

The check listed first below was run rather than left as a suggestion, and it
came back negative. Recording that plainly, because an untested claim about a
live system is worth less than nothing.

Read from `C:/MT5PortableTier1BestEA/MQL5/Files/v60_canonical_demo_v2`
(read-only): the current `executor_stdout.log` plus both rotated predecessors —
**29,116 status records** in total — and `events.jsonl`.

| Check | Predicted | **Observed** |
|---|---|---|
| Guardian halts | more frequent | **0 of 29,116 records** had an active entry-halt file |
| Order rejections from `deviation_points` | more frequent | **0** requotes, `PRICE_OFF`, `PRICE_CHANGED` or invalid-price events |
| Order fills | — | 3 fills, all `retcode 10009` (success) |
| Status | — | `ACTIVE_DEMO_BROKER_ACTION` on 10,719 of 10,720 current records |

`events.jsonl` shows the system trading normally on 2026-07-22/23: three
`ORDER_FILLED` events from the `V57_BREAK_SWING_H4ADX` and `V7_SWING_HEALTH`
add-on sleeves, all filled successfully, plus one `CANDIDATE_REJECTED` (a
strategy-level decline, not a broker rejection). Balance moved $987.66 → $982.84,
a $4.82 (0.49%) loss.

**Conclusion: consequences 1 and 2 above are refuted for the period observed.**
Nothing is halting and nothing is being rejected.

Two honest qualifications on the negative result itself:

- The **current** log spans 2026-07-26 01:23–16:25 UTC, a Sunday with the market
  closed, so its zero-trade count carries no information. The trading evidence
  comes from `events.jsonl` and the rotated logs.
- Three fills is a small sample. This shows the failure modes are *not currently
  occurring*; it does not prove they cannot occur under stress.

## What survives, and what does not

**Refuted:** the claim that halts and order rejections are happening now.

**Still arithmetically true, but latent:** the breakers are genuinely much tighter
in volatility-adjusted terms than when they were set — the floating-drawdown stop
sits 4.28 daily ranges from a flat book today versus 23.64 in 2023. That has not
bitten because equity is essentially flat (down 0.49%), so nothing has approached
a threshold. The exposure is what happens during a *real* drawdown: the breakers
will bind roughly 5.5x sooner in volatility-adjusted terms than they were designed
to, and they will do it the first time the system has a genuinely bad run.

**Unaffected by the verification:** consequence 3, that per-sleeve
`maximum_risk_usd` of $20–30 is now 0.19–0.29 daily ranges versus 1.05–1.58 in
2023. This is not a failure mode that shows up in logs — it is simply smaller
positions relative to opportunity than intended, visible only as lower profit per
trade.

## Suggested checks, in order

1. ~~Count halts and order rejections~~ — **done, negative.** See above.
2. **Re-express the drawdown breakers in ATR or daily-range units** rather than
   fixed USD, so they hold their intended meaning as volatility moves. This is the
   live exposure: latent, not currently firing.
3. **Re-check per-sleeve `maximum_risk_usd`** against current volatility and the
   account's $983 equity — but note the floating-drawdown stop is already 46% of
   equity, so raising risk without revisiting that breaker would be unsafe.
4. **`deviation_points`** needs no action on this evidence. Revisit only if fills
   start failing.

## Caveats

- The 2026 sample is March + June 2026 only, and a $105 daily range is an
  exceptional regime that may not persist (2021 and 2023 both sat near $19).
  Thresholds should be re-derived on a rolling basis, not re-pinned to today.
- Dukascopy XAUUSD is 3-decimal and the broker quotes 2-decimal; USD figures are
  used throughout to avoid that mismatch.
- Equity of $983 was read once on 2026-07-26 from account 1033030.
- This says nothing about whether the sleeves' *edges* are intact. It is about the
  control layer around them.
