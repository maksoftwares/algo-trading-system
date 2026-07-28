# EURUSD Neutral two-stage opportunity audit

## Verdict

`REJECTED_IN_DEVELOPMENT_FORWARD_FORBIDDEN`

The low-frequency two-stage oracle imitator failed entirely inside the
2021-2022 development block. No 2023, 2024, 2025, or 2026 H1 row or return
was loaded for this family, and no threshold was selected.

This closes the idea that the prior forced-side failure can be repaired merely
by separately predicting whether a target opportunity exists and abstaining
at low scores.

## Causal formulation

The model decomposed each Neutral 00:00, 00:15, 00:30, and 00:45 clock into:

1. an opportunity model estimating whether exactly one side would reach its
   1.5R target first; and
2. a side model estimating LONG versus SHORT, trained only on historical
   one-winner pairs.

The success score was:

`P(one target-first side) * max(P(LONG), P(SHORT))`

Both stages used standardized L2 logistic regression with fixed `C=0.1`.
The opportunity model used eleven shared, non-directional volatility,
spread, range, and tick-activity features. The side model used the existing
sixteen LONG-minus-SHORT price, DXY, Treasury, room, and quote-imbalance
contrasts.

There was no feature, interaction, calibration, clock, model, or
hyperparameter search.

## Strict data boundary

- Training labels: 2019-2020 only.
- Development selection: 2021-2022 only.
- Forward boundary: entry strictly before 2023-01-01.
- Maximum row actually admitted: 2022-12-30 00:45 UTC.
- Forward returns loaded: `false`.

The filtered source supplied 1,532 paired first-hour decisions on 383 Neutral
dates. Training contained 836 pairs, of which 528 had exactly one winning
side. Development contained 696 pairs on 174 dates.

The opportunity rate was stable—63.16% in training and 63.51% in
development. The missing edge was choosing the side, not recognizing that
some side would move.

## Development threshold ladder

The descending ladder was fixed at 0.45, 0.43, and 0.41. A threshold had to
retain at least 50 trades, at least 20 in both 2021 and 2022, win 45-55%,
reach PF 1.15, remain positive after another 0.5 pip, and remain positive
after removing the top 5% of winners.

| Score threshold | Trades | Active dates | Win rate | Payoff | PF | Net |
|---:|---:|---:|---:|---:|---:|---:|
| 0.45 | 112 | 76 | 33.93% | 1.439 | 0.739 | -19.80R |
| 0.43 | 158 | 97 | 33.54% | 1.439 | 0.726 | -29.45R |
| 0.41 | 222 | 117 | 34.68% | 1.439 | 0.764 | -35.05R |

The strictest and most selective threshold still lost in both development
years:

| Year | Trades | Win rate | PF | Net |
|---|---:|---:|---:|---:|
| 2021 | 59 | 30.51% | 0.632 | -15.48R |
| 2022 | 53 | 37.74% | 0.872 | -4.33R |

At threshold 0.45, the extra-half-pip PF was 0.603 and best-5%-removed PF was
0.622. Lower thresholds did not improve either diagnostic.

## Interpretation

The opportunity model generated scores as high as 0.685, so this was not a
structural zero-trade outcome. It selected many timestamps where the market
was likely to produce a 1.5R move on one side. The side model still chose the
actual winning side only about one third of the time after no-winner clocks
were included.

This directly explains why the forced four-clock strategy failed despite
approximately 52-54% conditional side accuracy: causal volatility and
activity features can identify movement, but the available price,
cross-asset, and quote features cannot identify its future EURUSD direction
with adequate precision.

Lowering the threshold, changing probability calibration, selecting 2022,
or opening later outcomes would be development repair after a decisive
failure. The forward archive remains unopened for N41.

## Integrity

- Result SHA-256:
  `b7f62edf0cfe4ddc8d812e1b3a83afc706fad69416fd0ebf855f48899e9424ff`
- Scored development ledger SHA-256:
  `a4621bcf3d25999e2f482e05851c60d2ab45be8a4407a1f2633ebc96038fe086`
- Coefficient ledger SHA-256:
  `f2e27c535712a469bb750f9154858d5dca966207cf525f184e69a0abd09ad833`
