# EURUSD Neutral session OCO verdict

Date: 2026-07-28

Decision: `REJECTED_NEUTRAL_SESSION_OCO_V1`

## Purpose

CME account OTP delivery prevented completion of the zero-cost DataMine
licence. The former anonymous SPAN archive still exposes directory
indexes, but its binary files are no longer retrievable anonymously.
CME CVOL history also requires authentication and entitlement.

This experiment therefore tested a price-only causal alternative without
using option data or predicting direction: at four fixed UTC session
anchors, a two-sided OCO order let the first executable breakout select
the side. The complete rule, costs, gates, and chronology were frozen and
hash-locked before the historical outcome pass.

## Frozen result

| Window | Trades | Win rate | Payoff | PF | Net R |
|---|---:|---:|---:|---:|---:|
| 2019-2020 | 598 | 24.92% | 1.346 | 0.447 | -268.35 |
| 2021-2022 | 454 | 22.25% | 1.249 | 0.357 | -263.00 |
| 2023-2024 | 378 | 26.72% | 1.348 | 0.492 | -152.60 |
| 2025-2026 H1 | 360 | 23.06% | 1.222 | 0.366 | -212.03 |
| Full archive | 1,790 | 24.25% | 1.293 | 0.414 | -895.98 |
| Latest six months | 122 | 23.77% | 1.326 | 0.414 | -60.65 |

The latest-six-month frequency was 0.946 trades per weekday. Full-history
maximum drawdown was 897.90R.

Removing the largest 5% of winners reduced PF to 0.327 and net return to
-1,028.73R. Adding another half-pip round-trip cost reduced PF to 0.341
and net return to -1,119.73R.

## Oracle resemblance

The fixed rule matched 409 of 2,615 Neutral oracle entries:

- exact-entry precision: 22.85%;
- oracle recall: 15.64%;
- median absolute timing difference among matches: 0 minutes.

The timing agreement is real, but the rule cannot identify the
future-winning side. Its 1.50R target does not compensate for the 24.25%
win rate after conservative retail execution costs.

## Decision

The exact price-only OCO rule failed every frozen return gate and is
closed without repair. It is not a Regime 1 specialist and must remain
cash.

The account/OTP problem is no longer an operational blocker for the
repository: the system can continue without CME data. It is, however, an
evidence limitation. After the repeated historical failures already
recorded in this package, another post-outcome price-rule revision would
be adaptive overfitting rather than an independent test.

The next defensible lane is prospective evidence: append untouched
future EURUSD observations and any lawfully obtained option/CVOL
snapshots, freeze a rule before those outcomes exist, and judge it only
after a sufficient sample accumulates.

## Reproduction

```powershell
uv run --with pandas --with numpy --with pyarrow python run_neutral_session_oco.py
```

Machine-readable result:

```text
outputs/neutral_session_oco/RESULT.json
```
