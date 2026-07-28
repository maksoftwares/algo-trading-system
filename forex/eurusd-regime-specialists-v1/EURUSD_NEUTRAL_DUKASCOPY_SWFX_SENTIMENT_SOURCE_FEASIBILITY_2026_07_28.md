# EURUSD Neutral Dukascopy SWFX sentiment source feasibility

## Verdict

`FEASIBLE_FOR_SEPARATELY_LOCKED_PROSPECTIVE_CAPTURE_ONLY`

The official Dukascopy SWFX sentiment source is reachable without a login and
contains one EUR/USD record. It is genuinely different information from the
price, CFTC, exchange-flow, options, macro-surprise, cross-asset, and GDELT
inputs already tested.

This audit does not preregister a trading rule, direction mapping, threshold,
clock, lifecycle, or historical backtest. It does not authorize demo or broker
action.

## Official provenance

Dukascopy describes the Sentiment Index as transaction-flow information showing
long and short ratios consolidated separately for liquidity consumers and
providers. Its official documentation says the current index is updated every
30 minutes and that `getIndexTime()` is the settlement time when accessed
through JForex:

- https://www.dukascopy.com/swiss/english/marketwatch/sentiment/
- https://www.dukascopy.com/wiki/en/development/strategy-api/indicators/sentiment-index/
- https://www.dukascopy.com/client/javadoc/com/dukascopy/api/IFXSentimentIndex.html

The official public historical widget declares this data endpoint:

`https://freeserv.dukascopy.com/2.0/index.php?path=historical_sentiment_index/data`

The endpoint returned HTTP 403 to an unreferenced plain request. A normal
browser-compatible request with an official Dukascopy widget referer and no
cookie, login, token, or account returned HTTP 200.

## One diagnostic observation

The diagnostic request used only:

- `path=historical_sentiment_index/data`;
- `liquidity=consumers`;
- `type=swfx`;
- a browser user agent; and
- the official Dukascopy widget as the HTTP referer.

Observed result:

| Field | Value |
|---|---|
| Local observation UTC | 2026-07-28 20:24:55.0511867 |
| HTTP `Date` | Tue, 28 Jul 2026 20:25:04 GMT |
| HTTP status | 200 |
| Content type | `text/javascript; charset=UTF-8` |
| Response bytes | 344,590 |
| Response SHA-256 | `7c63d05c98acd2de8f9c9d4a43456ab33c1a94bd453996ee19e1b2d252ab181b` |
| JSONP rows | 1,360 |
| Exact `EUR/USD` rows | 1 |

The exact EUR/USD row was:

```json
{
  "name": "EUR/USD",
  "last_long": "-12.399999618530273",
  "last_short": "12.4",
  "sixhours_long": "-12.65999984741211",
  "sixhours_short": "12.66",
  "oneday_long": "-16.639999389648438",
  "oneday_short": "16.64",
  "fivedays_long": "-14.220000267028809",
  "fivedays_short": "14.22"
}
```

No EURUSD price, return, hindsight-oracle row, trade outcome, or P&L was loaded
for this observation. The raw 344,590-byte response was not preserved, so the
hash is diagnostic provenance rather than a complete immutable evidence chain.

## Limitations that must fail closed

1. The public JSONP payload has no explicit settlement timestamp. The local
   observation time and HTTP `Date` prove when the response was seen, not the
   precise time at which Dukascopy settled each value.
2. The `*_long` and `*_short` fields are exact opposites in the observed row.
   The public JForex documentation distinguishes percentage-long index value
   from long-minus-short tendency, but it does not formally bind those concepts
   to this JSONP schema. No trading interpretation is allowed until that mapping
   is independently verified.
3. Six-hour, one-day, and five-day values are delivered in the current
   response without explicit timestamps or revision guarantees. They cannot be
   treated as a point-in-time historical archive.
4. Query-side instrument filtering is a widget display setting; the endpoint
   still returned 1,360 rows. A capture implementation must select exactly one
   case-sensitive `EUR/USD` row and reject missing or duplicate rows.
5. Public web endpoints can change or deny automated access. A prospective
   implementation must preserve the raw body, headers, local request/response
   times, endpoint, referer policy, and hashes, and must stay in cash on any
   schema or access failure.

## Legitimate next step

A later iteration may separately preregister a source-only prospective capture
census. It should capture at fixed UTC clocks for several weeks without
loading EURUSD outcomes, establish update cadence and value semantics, compare
the public row with a visible official widget or timestamped JForex observation,
and freeze capacity/schema gates before any strategy mapping.

Only after that source-only census passes may a prospective Neutral specialist
be designed. Historical July-2026-or-earlier P&L remains prohibited, frequency
is not a gate, and any resulting strategy begins a new prospective clock.
