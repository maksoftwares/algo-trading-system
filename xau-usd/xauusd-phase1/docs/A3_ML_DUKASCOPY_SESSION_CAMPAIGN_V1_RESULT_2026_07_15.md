# A3 ML Dukascopy Session Campaign V1 Result

Date: `2026-07-15`

Classification: `DUKASCOPY_SESSION_CAMPAIGN_INVALID`

## Decision

Reject all eight session profiles. None passed the train-only screen, so no profile was selected and validation/test outcome metrics remained suppressed.

Do not repair an individual threshold, target, session, direction, or lookback against this result. A new experiment must use a separately preregistered premise.

## Population

- Verified source months: `72`.
- H1 bars: `35,459`.
- Candidates: `3,400`.
- Resolved labels: `3,363` (`98.91%`).
- Active source days: `774` train, `517` validation, and `257` test.

The frozen `99%` resolution gate failed because `37` Friday positions reached their eight-hour timeout before the market weekend and had no quote inside the frozen 24-hour timeout grace. This is a protocol-quality failure. It is not why the profiles were rejected: their resolved train evidence was already negative.

## Train-Only Screen

| Profile | Trades | Trades/source day | Stress PF | Average stress R | Max DD R | Positive months |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Breakout LB4 1.5R | 370 | 0.478 | 0.7812 | -0.1769 | 72.01 | 10/36 |
| Breakout LB8 1.5R | 308 | 0.398 | 0.7629 | -0.1843 | 61.94 | 12/36 |
| Breakout LB4 2.0R | 368 | 0.475 | 0.8848 | -0.1275 | 57.73 | 12/36 |
| Breakout LB8 2.0R | 306 | 0.395 | 0.8521 | -0.1471 | 53.82 | 14/36 |
| Sweep LB4 1.5R | 128 | 0.165 | 0.8543 | -0.1891 | 26.52 | 12/35 |
| Sweep LB8 1.5R | 75 | 0.097 | 0.8509 | -0.1257 | 12.90 | 10/31 |
| Sweep LB4 2.0R | 127 | 0.164 | 0.9437 | -0.1412 | 23.39 | 13/35 |
| Sweep LB8 2.0R | 74 | 0.096 | 0.8847 | -0.1060 | 15.94 | 13/31 |

Every profile had negative average R and PF below one. The most frequent profile remained below half a trade per active source day, far short of the target.

## Holdout Protection

No profile passed all train-selection gates. Therefore:

- selected family: none;
- validation metrics: suppressed;
- test metrics: suppressed;
- profile promotion: prohibited.

## Next Research Direction

Independently port the already frozen exact-MT5 high-frequency M5 momentum portfolio to Dukascopy. That experiment is a cross-feed portability test of an existing candidate, not a threshold repair of this failed H1 session family. It must reproduce the M5 trigger, H1/H4 trend gates, server-hour masks, spread-to-stop cost gate, cooldown, position occupancy, and daily caps before its historical P&L is read.

No demo prediction, EA consumption, broker action, or deployment authorization is granted.
