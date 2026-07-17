# A3 ML A2 Intraday Context Ranker V1 Decision

Date: `2026-07-17`

Classification: `A2_INTRADAY_CONTEXT_RANKER_NO_OOF_SURVIVOR`

## Decision

Reject this A2 candidate stream and feature/model combination. Do not open the
validation, internal-test, or exam outcomes. Do not change the retention fractions,
model complexity, features, or gates and rerun V1.

No model artifact was produced. Python demo prediction, EA consumption, demo
execution, broker action, and live capital remain unauthorized.

## Source And Quality

- exact A2 positions: `7,007`;
- exact successful A2 entry orders: `7,007`;
- exact deals: `14,014`, with one entry and one exit per position;
- one-to-one successful-order join: passed;
- locked research-window source rows: `4,043`;
- rows with every exact causal feature and finite label: `3,113`;
- joined share: `76.9973%`, above the locked `75%` gate;
- train rows: `990`;
- unique purged OOF rows: `899`;
- feature cutoff: the exact completed M5 timestamp five minutes before entry;
- macro quotes: no forward fill, exact observed endpoints, and one-bar-lagged
  volatility scale;
- label stress: source result plus the locked `$0.75` spread floor, `$0.30`
  additional execution charge, and `$0.35` per 24 hours held.

The first OOF fit contained only 90 rows. That weakness was accepted without changing
the preregistered fold or model. Later expanding fits were larger. Every fit label's
actual exit preceded its evaluation start.

## OOF Evidence

Predictive evidence:

- AUC: `0.495689`;
- Spearman rank correlation: `0.035205`.

The AUC failed the locked `0.52` gate. Spearman passed its minimum narrowly, but a
positive rank correlation without positive selected economics is not useful.

| Policy | Trades | Trades/active day | Stress PF | Average stress R | Stress net R | Closed DD R | Positive months | Bootstrap mean-R p025 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Top 75% | 641 | 1.954 | 0.659 | -0.2618 | -167.80 | 167.80 | 11.1% | -0.3527 |
| Top 60% | 596 | 1.817 | 0.663 | -0.2589 | -154.32 | 154.32 | 5.6% | -0.3565 |
| Top 45% | 387 | 1.180 | 0.639 | -0.2839 | -109.88 | 122.53 | 16.7% | -0.4164 |

All policies retained both directions and met the intended frequency range. Every
policy nevertheless failed PF, average-R, month-stability, drawdown,
top-ten-winner-removal, and bootstrap gates.

The full 899-row OOF candidate population was already deeply negative before ranking:

- stress PF: `0.645`;
- average stress result: `-0.2746R`;
- stress net: `-246.83R`.

The model did not merely choose the wrong retention fraction. The A2 stream lacked
positive OOF expectancy, and the model had no out-of-fold discrimination with which
to repair it.

## Chronological Firewall

- validation outcomes opened: `false`;
- internal-test outcomes opened: `false`;
- exam outcomes opened: `false`.

The experiment stopped at OOF exactly as preregistered.

## Reproduction Lock

The run was repeated immediately. The following artifacts reproduced byte for byte:

- dataset Parquet SHA-256:
  `dc98b5b106fc72cc54708f9ca4a3416d91e530bd4ef3abbcb5c7eb4bbb1e29de`;
- OOF predictions SHA-256:
  `18d4077d7e4e1106325ebbe931c739cfd5aad80300eb62dbe800b2eca439f28b`;
- empty selected-predictions SHA-256:
  `5ab73b14b53797094ecea76213296377d91ba0dc3968fbe4a5b4cd8055fdefeb`;
- evaluations SHA-256:
  `a1fd47ec09186adc71b5f6e0d8fd1c16aec459bee84cd3277b6575e497bb6072`.

The final timestamped JSON report SHA-256 is
`f431541c6f73b8d1cb5460edae2a749f1d8fa7bf88db301651d3b6a7a623ffa7`.

## Next Iteration

Do not run another A2 ranker. Iteration 8 will return to a mechanically positive
premise: trend continuation with movement deliberately wide enough relative to gold
spread and execution cost.

The previously audited M5 momentum generator produced about `1.84` raw candidates per
source day, but its old `0.05R` spread-to-stop gate rejected `2,627` of `2,842`
candidates. A new version may therefore test a preregistered, symmetric,
cost-normalized trend geometry with wider structural risk and payoff. It must:

- remain a new family rather than loosen the old result in place;
- use causal H1/H4 trend ownership and executable Dukascopy Bid/Ask paths;
- freeze a small mechanism set before outcomes;
- retain the target-broker stress schedule and account risk ceiling;
- select on an early development period and conditionally open later periods;
- require positive expectancy before any ML ranking;
- report overlap, concurrent risk, frequency, drawdown, and direction stability.

This is a deterministic alpha test first. ML remains downstream and optional.
