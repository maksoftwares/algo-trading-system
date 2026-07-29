# EURUSD Neutral Dukascopy SWFX sentiment comparison 1

## Verdict

`FIRST_OFFICIAL_WIDGET_COMPARISON_MATCHED`

The successful browser retry resolved the field-level ambiguity left by the
earlier semantics audit. The official visible Dukascopy widget and the
immutable prospective JSONP capture show the same EUR/USD state.

This is the first of the three required comparison occasions. It does not
admit the source for strategy design and does not create a trading signal.

## Evidence compared

- Official page:
  `https://www.dukascopy.com/swiss/english/fx-market-tools/swfx-index/`
- Browser observation: `2026-07-29T08:41:32Z`
- Official widget update: `2026-07-29T08:30:00Z`
- Immutable capture slot: `2026-07-29T08:32:00Z`
- Manifest:
  `manifests/CAPTURE_20260729T083200Z_56e683351bbd911f.json`
- Manifest SHA-256:
  `56e683351bbd911feb07c5955d6814976875ee61a240c7a3d2348cb979a236cd`
- External comparison SHA-256:
  `7a72060c679387201b0d973e28dd7f94df9fa592c84a2ea245d81103ece91c23`

## Exact reconciliation

The visible EUR/USD row reported:

- long share: `55.67%`;
- short share: `44.33%`; and
- long-minus-short index: `+11.34%`.

The immutable normalized capture reported:

- `last_short = +11.34`; and
- `last_long = -11.34000015258789`.

Therefore the public JSONP names do not describe the visible share columns.
For this matched observation, `last_short` is the visible long-minus-short
index and `last_long` is its antipode. Applying the already documented source
identity to `last_short` gives:

- `(100 + 11.34) / 2 = 55.67%` long; and
- `(100 - 11.34) / 2 = 44.33%` short.

Both visible shares and the signed index match exactly at displayed precision.

## Independent replay after recording

The network-free validator accepted the comparison and reported:

- `5 / 5` immutable captures valid;
- schedule coverage `1.0`;
- valid-capture ratio `1.0`;
- five distinct EUR/USD source states;
- zero consecutive failures; and
- one manual official-widget comparison occasion.

The census remains `ACCUMULATING_PROSPECTIVE_SOURCE_EVIDENCE`. It cannot be
evaluated before 27 calendar days and 20 weekdays, and it still requires at
least 800 valid captures, 18 valid days, 30 distinct states, and two more
official comparisons on distinct UTC dates.

## Research boundary

No EURUSD price, return, oracle row, outcome, P&L, strategy direction,
threshold, signal, trade, or broker action was loaded or created.
