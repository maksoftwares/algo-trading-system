# A1 XAUUSD H4 Cluster High-Water Scaled-Risk Addendum

Date: 2026-07-11
Boundary: one development Strategy Tester iteration; no broker action is authorized.

## Purpose

The fixed 5.00% floating-equity high-water trigger with a 2.00% release produced
USD 7,561.56 over ten years with 22.93% native MT5 relative equity drawdown.  This
addendum tests whether moving the same causal protection mechanism earlier can bring
drawdown near 10% while retaining most of that result.

This is a single predeclared risk-scaling test, not a threshold sweep.  Its result
will be retained whether it passes or fails.  No nearby trigger/release pair will be
tested on these same paths in response to the outcome.

## Locked implementation

- Preserve the exact original H4 long entry, stop, target, fixed 0.01 lot, and
  session-expiry behavior.
- Preserve the compiled cluster high-water hedge source and separate magic number.
- Change only `InpClusterEquityHedgeTriggerPct` from `5.00` to `2.00`.
- Change only `InpClusterEquityHedgeReleasePct` from `2.00` to `0.80`.
- Preserve the prior 40% release-to-trigger ratio.
- Use a USD 1,000 Strategy Tester deposit, native symbol spread/swap, and the same
  frozen five-year and ten-year windows as the prior exact comparison.
- Run both horizons once in the isolated portable MT5 sandbox.

The 2.00% trigger is fixed before the run because it is 40% of the prior trigger and
is intended to scale the observed 22.93% drawdown toward approximately 10%.  This is
a mechanistic approximation, not a claim that drawdown scales linearly.

## Acceptance rule

The ten-year result is the primary economic decision.  It passes only if all of the
following are true:

- total net profit is at least USD 7,000;
- native MT5 maximum relative equity drawdown is no more than 12.00%;
- profit factor is at least 1.30;
- all original primary entries are retained subject only to frozen session expiry;
- order failures and hedge-management failures are both zero;
- every position and hedge volume reconciles and the run finishes flat.

The five-year result is a disclosed stability diagnostic and must also have profit
factor at least 1.30 plus clean execution/reconciliation.  Its profit and drawdown
are reported but do not retroactively change the primary ten-year rule.

## Interpretation

- Passing demonstrates a development candidate near the user's drawdown objective;
  it does not establish holdout or live robustness.
- Failing ends threshold scaling on these paths.  Research then proceeds through a
  genuinely independent contemporaneous specialist rather than another hedge
  threshold adjustment.

## Exact result

Status: `H4_CLUSTER_HIGHWATER_SCALED_RISK_FAILED`

| Horizon | Primary entries | Net USD | PF | Native relative equity DD | Failures |
| --- | ---: | ---: | ---: | ---: | ---: |
| five-year | 156 | 2,373.91 | 1.2320 | 42.48% | 0 |
| ten-year | 307 | 6,466.78 | 1.5878 | 27.86% | 0 |

The ten-year run missed both USD 7,000 and 12%, while the five-year run also failed
PF 1.30.  Threshold scaling is rejected and will not be continued.
