# A1 XAUUSD H4 Profit-Retention Heat-Guard Preregistration

Date: 2026-07-11  
Scope: development Strategy Tester only; no broker action is authorized.

## Problem

The frozen H4 control produced attractive five- and ten-year net profit but reached
40.55% and 39.49% native MT5 relative equity drawdown.  The episode-identity repair
reduced drawdown to 19.06% and 14.49%, but its single-position/first-cross rule also
reduced net profit too aggressively.  This experiment tests a narrower risk repair:
retain the frozen signal stream and permit controlled pyramiding, while refusing a
new position when the projected loss to all open hard stops would exceed a fixed
share of current equity.

## Frozen causal change

- Preserve the pinned H4 signal condition, including repeated valid state entries.
- Preserve fixed 0.01 lots, legacy entry gates, stops, targets, and source magic.
- Preserve the frozen maximum-open-position setting; the heat guard is controlling.
- Add `InpMaxAggregateStopRiskPct = 6.00`.
- Before each order, calculate in account currency:
  - remaining loss from every same-symbol/same-magic open position's current price
    to its live hard stop;
  - candidate loss from the candidate entry price to its proposed hard stop.
- Reject the candidate, fail closed, if a stop is absent, risk cannot be calculated,
  equity is nonpositive, or projected aggregate risk exceeds 6.00% of current equity.
- A signal observed while the market session is closed expires permanently.

The 6% ceiling is fixed before results: it leaves a two-percentage-point buffer below
the 8% source design limit and four points below the 10% hard rejection gate.  No
calendar, losing-trade, hour, stop, target, or outcome-derived filter is introduced.

## Exact tests

Initial deposit is USD 1,000 with the frozen XAUUSD symbol and exact MT5 every-tick
history:

- five-year: 2021-07-01 through 2026-06-30;
- ten-year: 2016-07-01 through 2026-06-30.

## Locked decision gates

The heat-guard candidate survives only if both horizons have:

- native MT5 maximum relative equity drawdown <= 10.00%;
- positive net profit and profit factor >= 1.30;
- zero order-send failures;
- maximum projected aggregate stop risk at accepted entry <= 6.00%, subject only to
  normal price discretization;
- net profit retention >= 60% of the matched frozen H4 control.

The ten-year run must also retain at least 100 closed trades.  Frozen matched controls:

- five-year net USD 6,823.25, so minimum retained net is USD 4,093.95;
- ten-year net USD 8,159.08, so minimum retained net is USD 4,895.45.

If any gate fails, status is `H4_PROFIT_RETENTION_HEAT_GUARD_FAILED`.  A failed result
does not authorize cap tuning against the observed path; the next causal question is
holding-path regime invalidation.
