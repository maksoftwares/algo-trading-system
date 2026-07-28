# EURUSD Neutral session-opening-drive preregistration

Date: 2026-07-28

Status: `FROZEN_BEFORE_HISTORICAL_OUTCOME_PASS`

Prospective start: `2026-07-29T00:00:00Z`

## Distinct hypothesis

The failed session OCO rule placed orders beyond the preceding one-hour
range and let the first range break select direction. The failed
micro-breakout family required a completed rolling one-hour extreme with
EMA and tick confirmation.

This campaign tests a different causal geometry: direction is the sign of a
fully completed 30-minute opening drive at four fixed UTC session anchors,
and entry occurs only at the next M5 open. It neither predicts the
midnight oracle side nor repairs the range-OCO boundary.

## Fixed rule

At 00:00, 06:00, 12:00, and 18:00 UTC on weekdays:

1. Use the latest completed cross-market state no later than anchor hour
   minus one hour.
2. Continue only when direction is `NEUTRAL`, shock is false, and DXY plus
   EURUSD are not jointly compressed.
3. Observe exactly the first six M5 bars, covering 30 minutes after the
   anchor.
4. Require the completed bid bar's absolute open-to-close body to be at
   least 4.0 pips.
5. Go long only when the body is positive and the close is in the top 25%
   of the completed bar's high-low range.
6. Go short only when the body is negative and the close is in the bottom
   25% of that range.
7. Enter at the executable next M5 open after the observation window.
8. Use fixed 4-pip risk, 1.50R target, 12-hour maximum hold, a 0.7-pip
   retail spread floor, 0.1-pip adverse slippage per side, and stop-first
   same-bar handling.
9. Permit one open position and no more than four entries per UTC date.

There is no volatility normalization, tick filter, EMA, pending-order
level, direction alternative, or threshold grid.

## Outcome-blind census

The candidate ledger was generated before opening any post-entry path or
oracle match:

| Item | Count |
|---|---:|
| Four-anchor weekday states | 7,785 |
| Neutral anchors | 1,927 |
| Opening-drive signals across all regimes | 2,498 |
| Neutral trade candidates | 593 |
| Long / short | 299 / 294 |
| Development, 2019-2020 | 160 |
| Development, 2021-2022 | 173 |
| Validation, 2023-2024 | 132 |
| Pseudo-OOS, 2025-2026 H1 | 128 |

These are raw candidates before the one-open-position router. The
historical archive has already been inspected by other campaigns, so all
historical results remain research evidence rather than pristine OOS.

## Admission

Each chronological window must retain at least 40 executed trades, win
45%-55%, realize payoff from 1.35 to 1.75, and achieve PF at least 1.10.
Overall drawdown must be no more than 30R. Results must remain positive
after removing the largest 5% of winners and after adding another half pip
per round trip.

Oracle resemblance is evaluation-only and requires same side and date
within 60 minutes.

## Forward-only boundary

No historical result can authorize demo or live use. Prospective
observations begin at 2026-07-29 00:00 UTC, strictly after this contract.
No promotion review may occur before both 100 post-lock executed trades and
six calendar months exist.

Failure closes the exact historical rule without changing body size, close
location, anchor, direction, or subgroup. Passing only starts the frozen
prospective watchlist.
