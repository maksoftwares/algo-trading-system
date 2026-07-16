# A3 ML Broker Cost Calibration V1 Decision

Date: 2026-07-16

Classification: `BROKER_COST_CALIBRATION_VALID`

## Decision

Accept V1 as the cost lock for the next higher-timescale research iteration. Continue
to use native historical Dukascopy Bid/Ask quotes, but stress entry spread to at least
$0.75 and add $0.30 per 0.01 lot. Reject any later candidate whose total stressed entry
cost exceeds 0.15 of initial risk.

This result does not establish strategy expectancy and does not authorize model
training, Python predictions, EA consumption, demo orders, or live orders.

## Source And Correctness

- canonical broker feed: Capital.ComMena-Demo A3 / account `1033669`;
- canonical raw ticks: 7,616,882;
- active UTC date files: 18;
- observed interval: 2026-06-05 00:00:00.248 through 2026-06-25 23:59:59.967;
- canonical active file hashes: all matched the C02 manifest;
- invalid or negative Bid/Ask rows: 0;
- maximum Ask-minus-Bid versus stated-spread error: approximately 1.11e-16;
- chronological non-decreasing timestamps: pass;
- exact duplicated timestamp/Bid/Ask rows: 739, or about 0.0097%;
- matched broker/Dukascopy M5 bars: 4,092;
- all source, identity, quality, and overlap gates: pass.

The 739 duplicate quote rows are reported rather than silently removed. They are too
few to change the distribution materially and are retained because the source export
is immutable.

## Account Independence

A1, A2, and A3 each contained the same 7,616,882 tick count on the same 18 active dates
from `Capital.ComMena-Demo`. Their first and last market quote tuples matched in all 72
cross-account boundary comparisons.

This supports treating them as mirrors of one broker feed. It does not provide three
independent samples, and V1 makes no such claim.

## Broker Spread Result

Canonical tick-level absolute XAUUSD spread:

- median: $0.50;
- 75th percentile: $0.50;
- 90th percentile: $0.75;
- 95th percentile: $0.75;
- 99th percentile: $0.75;
- maximum: $1.80;
- mean: approximately $0.5477.

The spread was discrete rather than smoothly distributed. Most quotes were $0.50 or
$0.75. Sunday/opening periods had the clearest $1.80 tail; UTC hour 22 had a 99th
percentile and maximum of $1.80.

## Dukascopy Comparison

Across the 4,092 matched M5 bars:

- broker M5 median-spread median: $0.50;
- broker M5 p90-spread median: $0.75;
- Dukascopy tick-mean-spread median: approximately $0.6053;
- Dukascopy open-spread median: approximately $0.6100;
- broker M5 p90 spread exceeded Dukascopy mean spread in 3,028 bars;
- Dukascopy mean spread exceeded broker M5 p90 in 1,064 bars;
- broker p90 spread/ATR median: approximately 0.1233ATR;
- Dukascopy open spread/ATR median: approximately 0.1059ATR.

Dukascopy was neither uniformly cheaper nor uniformly more expensive. Native
Dukascopy Bid/Ask therefore remains the historical execution path, while the target
broker p90 becomes a minimum stress floor.

## Locked Cost Geometry

For a reference 0.01 lot, one ounce of XAUUSD exposure:

- broker spread floor: $0.75;
- additional execution stress: $0.30;
- total stressed entry friction: $1.05;
- maximum allowed friction: 0.15R;
- minimum initial stop distance: $7.00.

Any strategy with a smaller stop is structurally ineligible under the next campaign,
regardless of its gross backtest. Wider risk geometry is not permission to increase lot
size; the fixed $50 maximum initial risk still applies.

## Implication For Iteration 5

The next specialist campaign should use M15/H1 decisions and structural stops that are
at least $7.00 after rounding. It should target movements large enough for the spread
to be a modest part of risk, use four-hour to multi-day holding logic, and test separate
trend, reversal, compression, and shock regimes.

The campaign must still:

- enter long at Ask and exit/mark at Bid;
- enter short at Bid and exit/mark at Ask;
- use native Dukascopy spread or the $0.75 floor, whichever is worse;
- add $0.30 stress per 0.01 lot plus holding costs;
- reject cost above 0.15R and initial risk above $50;
- pass train, validation, internal test, exam, exact-tick, and shared-account gates in
  sequence.

## Limitations

The target-broker sample covers one June 2026 interval. It cannot prove that Capital.com
had the same spread in earlier years or will keep it in the future. The $0.75 floor is a
current-demo stress assumption, not a historical broker-spread portability claim.

## Artifact Lock

- contract SHA256:
  `9f6e7abca318036c87519afff9375cf045c17d249748f5f6be87277aab14a7c6`
- daily metrics SHA256:
  `d431cec02cfe3010d9cc24c7babc17ce534b2a88a5037fdce05e20f8668dbfcc`
- hourly metrics SHA256:
  `2c92a749cd3e71083426e96fcc3db21a92d6446f4d7b4904b4d5a42ce3286270`
- overlap M5 SHA256:
  `f40c4563002810b3345ef168350a99f69fd0159b02e7f3958654fc31f89cca8c`
- JSON report SHA256:
  `72f4180d518f494dce2f664c6852df0af881edc81b77ab2608d60ec2d86ae7bb`
- Markdown report SHA256:
  `0e3c94a1f9227530dba8e49481c4da9b60cf58d20e7595f95b2ad150180220bd`

## Authorization

- cost calibration accepted: yes;
- strategy authorization: no;
- model training authorization: no;
- Python demo predictions: no;
- EA consumption: no;
- demo authorization: no;
- live authorization: no.
