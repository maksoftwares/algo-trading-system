# V43 Historical Core Drawdown-Control Audit Preregistration

## Status

This is an explicitly retrospective risk diagnostic. The USD 889.69 closed
drawdown was already known before V43 was written. V43 does not claim an
untouched holdout.

## Frozen Question

Does the R1 box exposure policy that was frozen before this audit materially
reduce the observed Core drawdown without removing another specialist, and can
the resulting risk fit the current Capital demo account?

## Frozen Control

- Apply only to `R1_UPTREND` source `h4_d1_long_best_box2_atr80`.
- Permit at most two concurrent R1 box positions.
- Permit at most one new R1 box position per UTC day.
- Leave every other Core trade unchanged.
- Search no thresholds and make no same-version adjustment after results.

The independent R1 replay must use the already-frozen
`PORTFOLIO_CONSTRAINED_PRIMARY` policy with the same limits.

## Measurements

1. Attribute the original one-year closed drawdown episode by specialist and
   source strategy.
2. Compare original and capped trade count, weekday frequency, net P&L, PF, and
   closed drawdown over fixed 1Y, 2Y, 5Y, and 10Y windows ending before
   2026-07-01 UTC.
3. Mark the frozen R1 policy over the complete Dukascopy M5 bid path.
4. Verify the global M5 peak and trough against exact delta-decoded Dukascopy
   quotes from the identified source hours.
5. Apply the V42 15% account drawdown ceiling and a fixed 25% capital buffer.

## Fail-Closed Rule

The current account is not ready if either:

- buffered stress drawdown exceeds 15% of current equity; or
- the broker minimum lot exceeds the maximum lot that can express the buffered
  risk.

The whole Core remains governed by the legacy USD 1,733.37 floating-equity
evidence until V42 produces a complete same-period shared-account replacement.

## Authority

V43 may audit historical files and publish risk requirements. It may not train
a model, produce a Python execution prediction, alter an EA, attach an EA,
place a demo order, place a live order, or authorize broker action.
