# EURUSD Neutral Dukascopy event-timing source audit

## Source decision

The public Dukascopy Economic Calendar widget is accepted for one bounded
Regime 1 campaign as a source of scheduled event timestamps and labels only.
It is login-free and the widget states that it covers past economic releases
with actual, forecast, previous, and impact fields:

<https://www.dukascopy.com/trading-tools/widgets/calendars/economic_calendar>

The public widget loads calendar rows from:

`https://freeserv.dukascopy.com/2.0/index.php?path=economic_calendar_new/getNews`

The acquisition uses only public GET requests and requires no account, API
key, OTP, form submission, or browser session.

## Point-in-time failure

The endpoint is a current historical snapshot, not a documented point-in-time
archive. Its numeric surprise fields therefore fail the standard required for
a causal backtest.

The decisive audit example is the U.S. payroll release at 13:30 UTC on
2024-01-05. The current Dukascopy row reports:

- actual: 216K;
- forecast: -29K;
- previous: 199K.

Contemporaneous reporting recorded a 170K consensus and a 173K downwardly
revised previous value. The forecast field is therefore not a trustworthy
record of what the market knew before that release. Present-day `actual`,
`forecast`, `previous`, normalized values, impact, historical-count, and
effect fields are all prohibited from the strategy.

Allowed fields are restricted to:

- event ID;
- scheduled UTC timestamp;
- currency;
- title;
- stable event tag.

The strategy uses a frozen title taxonomy rather than Dukascopy's current
impact rating.

## Acquisition and integrity

Coverage is split into 30 non-overlapping quarterly requests from 2019-01-01
through 2026-06-30.

| Item | Value |
|---|---:|
| Raw quarterly responses | 30 |
| Normalized event rows | 84,305 |
| EUR-labelled rows | 22,484 |
| USD-labelled rows | 19,071 |
| Parquet bytes | 2,233,648 |

Outside-Git root:

`D:/AlgoTradingData/research/eurusd-neutral-dukascopy-event-timing-v1`

Pinned artifacts:

- raw response chain:
  `6d083d561f16add86fc05dd004711209518ddaef489f9e5d32ca440e67724a4a`
- normalized Parquet:
  `805603f819b727a9481f577ff3d2191f80456a4d83d37360e1416a75c6504be1`
- deterministic manifest:
  `441ad058e84055adf773d61a73ab38385ab8d7e1e422b6bce4fb16f4003cc1e3`

A cache-only rebuild reproduced the Parquet and manifest hashes exactly.
Missing events are never inferred or filled.

## Outcome-blind source relationship

The frozen title taxonomy yields 8,587 EUR/USD-relevant event rows in 5,080
timestamp clusters. Against the 642 existing Neutral 00:00 decision dates:

- 439 dates have a qualifying event in the preceding 24 hours and complete
  price bars;
- 197 have no qualifying event;
- 6 lack the exact completed pre-event M5 bar;
- 203 remain in cash;
- candidate frequency is 0.684 per Neutral date and exactly one trade on each
  traded date.

The latest qualifying event cluster is EUR-only on 288 candidates, USD-only
on 145, and mixed EUR/USD on 6. Event age ranges from 30 to 1,170 minutes,
with a 630-minute median.

These counts use only event timestamps/labels and EURUSD prices completed by
the proposed entry. No trade outcome or oracle membership was loaded.

## Limitations

- Event timestamps and labels are provider records, not official agency
  release archives.
- Titles and tags can change across provider maintenance.
- Current numeric calendar values are explicitly unusable for historical
  surprise calculation.
- Historical EURUSD outcomes have been inspected in earlier campaigns, so
  any result remains adaptive research.
- A historical pass cannot authorize demo or live trading without new
  post-lock observations.
