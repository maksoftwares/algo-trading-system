# EURUSD Neutral prospective actual capture

## State

`ACTIVE_NO_MATURE_PRE_RELEASE_FORECASTS`

The post-release half of the public TradingView evidence pipeline is complete.
It is evidence collection only and cannot place demo or live orders.

## Causal linkage

The collector first reads the immutable pre-release forecast ledger. It makes
no network request unless at least one captured event is 60 seconds past its
scheduled release. A post-release actual is admitted only when:

1. the captured forecast was observed at least 60 seconds before release;
2. the actual is observed at least 60 seconds after release;
3. event id, ticker, and scheduled UTC timestamp match exactly;
4. the actual exists; and
5. the raw pre- and post-release snapshot hashes remain linked in the
   normalized row.

The signal-side convention is frozen: actual above forecast is SHORT EURUSD,
actual below forecast is LONG, and equality is cash.

## Immutable artifacts

Every eligible request appends separate raw, metadata, normalized, and
manifest files beneath:

`D:/AlgoTradingData/prospective/eurusd-neutral-tradingview-consensus-v1`

The post-release evidence has its own deterministic SHA-256 chain. Repeating
identical bytes is idempotent. A changed provider response creates another
snapshot and cannot overwrite the earlier one.

## Initial run

At 2026-07-28 12:48:19 UTC:

- admissible pre-release forecasts: 0;
- mature forecasts: 0;
- network request made: no;
- linked actuals: 0; and
- broker action allowed: no.

This is the correct not-yet-eligible state. The known 7 August NFP, 12 August
CPI, and 13 August PPI rows still lacked forecasts in the first capture, so
there is nothing to poll or trade.

Run after a captured forecast has passed its scheduled release:

```powershell
uv run --with pandas --with pyarrow python capture_prospective_tradingview_actuals.py capture
```
