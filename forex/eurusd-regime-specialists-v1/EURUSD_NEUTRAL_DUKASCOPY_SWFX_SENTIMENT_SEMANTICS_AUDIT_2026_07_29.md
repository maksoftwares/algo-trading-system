# EURUSD Neutral Dukascopy SWFX sentiment semantics audit

## Verdict

`GENERIC_INDEX_SEMANTICS_VERIFIED_JSONP_FIELD_BINDING_STILL_UNVERIFIED`

The official Dukascopy page now provides enough information to define the
generic SWFX consumer-sentiment index. It does not provide enough information
to declare the public historical JSONP field names semantically proven.

This audit adds no trading direction, threshold, EURUSD price, outcome, oracle
row, or P&L.

## Official page inspected

- Page:
  `https://www.dukascopy.com/swiss/english/marketwatch/sentiment/`
- Observed at: `2026-07-29T05:33:30.8276123Z`
- Provider: Dukascopy Bank SA
- Access: public, no login

The official page states, in substance:

1. consumer sentiment is the percentage of long or short positions in open
   trades;
2. the index value is the percentage-point difference between the long and
   short shares;
3. a positive index means the long share is larger and a negative index means
   the short share is larger; and
4. the index is updated every 30 minutes.

Therefore, if an index value `x` is independently proven to be the
long-minus-short value, the implied shares are:

- long share: `(100 + x) / 2`;
- short share: `(100 - x) / 2`.

This formula is documented here only as source semantics. It is not a strategy
or contrarian direction rule.

## Embedded-widget result

The official page declares both real-time and historical sentiment iframe
URLs. The page and explanatory text loaded successfully in both available
browser surfaces. The embedded real-time widget did not publish instrument
rows: one surface remained at `Loading......`, while direct widget navigation
returned an HTTP response-code failure. The second surface exposed an empty
iframe and the same direct-widget failure.

No visible EUR/USD value was therefore available for comparison at this
observation. This occasion does not count toward the frozen requirement for
three value comparisons.

## Remaining field-level ambiguity

The prospective endpoint exposes antipodal pairs such as `last_long` and
`last_short`. It is plausible that these are respectively long-minus-short and
short-minus-long signed tendencies, but that is an inference. The official
explanatory page does not bind those exact JSONP property names to that
meaning.

Accordingly:

- generic index formula: verified;
- update claim: verified as every 30 minutes;
- exact `*_long`/`*_short` JSONP mapping: not yet verified;
- visible-value comparison occasions: `0 / 3`;
- strategy design remains prohibited.

The source-only prospective census remains the correct next evidence source.
