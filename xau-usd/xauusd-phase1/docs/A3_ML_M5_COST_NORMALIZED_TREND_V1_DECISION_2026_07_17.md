# A3 ML M5 Cost-Normalized Trend V1 Decision

Date: `2026-07-17`

Classification: `M5_COST_NORMALIZED_TREND_NO_DEVELOPMENT_SURVIVOR`

## Decision

Reject all three cost-normalized M5 trend geometries. Do not open validation,
internal-test, or exam outcomes. Do not alter the stop, target, timeout, cost ceiling,
portfolio occupancy, or gates and rerun V1.

No geometry qualifies for ML ranking, target-broker replay, shared-account
composition, Python demo prediction, EA consumption, demo execution, broker action,
or live capital.

## Source And Correctness

- verified Dukascopy XAUUSD Bid/Ask months: `96/96`;
- source period: July 2018 through June 2026;
- causal M5 rows: `567,104`;
- frozen base momentum candidates: `3,908`;
- profiled candidates: `11,685`;
- development source days: `625`;
- all source hashes, month counts, candidate uniqueness, resolved-share, risk, and
  cost-reconciliation checks passed;
- long entries used Ask and long exits Bid;
- short entries used Bid and short exits Ask;
- exact ticks resolved stop/target ordering;
- the `$0.75` spread floor, `$0.30` execution charge, and time-proportional holding
  cost were included;
- initial risk was capped at `$50` per 0.01 lot;
- no later chronological stage was replayed.

## Development Evidence

| Profile | Candidates | Selected trades | Trades/source day | Stress PF | Average stress R | Stress net R | Stress net USD | Closed DD R | Positive months | Bootstrap mean-R p025 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 4 ATR / 1R / 12h | 853 | 352 | 0.563 | 0.567 | -0.1915 | -67.42 | -480.26 | 67.42 | 20.8% | -0.2836 |
| 6 ATR / 1.5R / 24h | 853 | 285 | 0.456 | 0.637 | -0.2018 | -57.52 | -426.64 | 60.86 | 16.7% | -0.3458 |
| 8 ATR / 2R / 48h | 852 | 210 | 0.336 | 0.700 | -0.1810 | -38.01 | -371.48 | 42.88 | 25.0% | -0.3455 |

Every profile retained both directions, but every profile failed PF, average-R,
month-stability, drawdown, winner-removal, and bootstrap gates. None reached the
minimum `0.75` trades per source day. The two wider profiles also failed the 300-trade
minimum.

## Mechanism Diagnosis

The new geometry did what it was designed to do operationally:

- only 15, 7, and 2 development entries respectively failed the `0.15R` immediate
  cost ceiling;
- stop width increased PF monotonically from `0.567` to `0.700`;
- all label-quality checks passed.

It did not create positive expectancy. Longer holds also increased same-direction
occupancy rejections from `472` to `623`, reducing selected frequency as the geometry
widened. The result is therefore an alpha and occupancy failure, not a market-data,
spread-admission, or software failure.

Widening the same trigger further after observing this monotonic pattern would be an
outcome-driven sibling test. It is not authorized.

## Chronological Firewall

- validation opened: `false`;
- internal test opened: `false`;
- exam opened: `false`.

## Reproduction Lock

An immediate warm-cache rerun reused all 96 H1 and M5 months. The core artifacts
reproduced byte for byte:

- candidates SHA-256:
  `91f5402e3b570157d9243911ad90b5a36e6c41e919ce4b404f59c7b6e290075b`;
- labels SHA-256:
  `411ddfd91fb11201752d2d3268a4b45981d3fc692993e7dd7278cc04b0072d99`;
- selected trades SHA-256:
  `11de71d3c650b0c3ba1be501154fb75a5a57ab03f1718ab3bf6fe64451bcba10`;
- evaluations SHA-256:
  `b57fbb40d92a122d782808b679cbf3b34c4eb0659dbf22db1727dec805e7c420`.

The final timestamped JSON report SHA-256 is
`c545599671fdcf5df3267fbc037e5dc43c49732103a31aaad2142692bc077611`.

## Next Research Direction

Do not perform Iteration 9 as another stop/target, retention, or model variant on the
same M5 trigger. Two consecutive experiments now show:

1. A2 high-frequency candidates are deeply negative and not rankable.
2. Frozen M5 momentum candidates remain deeply negative after cost geometry is fixed.

The next iteration must change the information or market mechanism. The defensible
options are:

- acquire causal COMEX gold futures trades/depth and macro-surprise data, then test a
  futures-led spot specialist;
- or accept the verified low-frequency R1 research sleeve and build a strictly
  controlled demo shadow for data collection without claiming it meets the requested
  frequency or qualification standard.

The current Dukascopy spot price, spread, tick-pressure, cross-FX, dollar-index, and
bond-proxy set has not supported a profitable high-frequency specialist under the
frozen tests. Continuing to search the same information with nearby thresholds would
increase overfitting risk rather than increase evidence.
