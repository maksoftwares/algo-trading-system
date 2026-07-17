# COMEX Futures Foundation V1

This campaign establishes a primary intraday COMEX gold futures data lane. It does not produce a strategy, authorize Python predictions, or interact with a broker.

## Why this lane exists

The completed spot-only specialist campaigns found that higher trade frequency is mechanically possible, but the tested edges did not survive costs or untouched periods. Public daily macro series and spot cross-asset proxies also failed to add enough independent information. Primary futures trades and top-of-book data are the next materially different evidence class.

The frozen first-choice schema is `tbbo`: every futures trade plus the best bid and offer immediately before the trade. That is sufficient to research causal aggressor flow, trade intensity, spread, top-of-book imbalance, and futures-to-spot lead/lag without paying for the full order book initially.

## Locked request

- Dataset: `GLBX.MDP3`
- Symbol: `GC.v.0`
- Symbology: volume-based continuous futures
- Window: 2016-07-01 through 2026-07-01
- Estimates: `ohlcv-1s`, `trades`, `bbo-1s`, `tbbo`, and `mbp-1`
- Preferred first acquisition: `tbbo`

Continuous prices remain unadjusted across contract rolls. Any later feature builder must retain the source instrument mapping and must not treat roll jumps as market returns.

## Frozen feature contract

`config/futures_flow_feature_contract_v1.json` freezes two first-pass mechanisms before the data is inspected:

- `flow_continuation`: unusually concentrated aggressive flow, matching short-window price impulse, and matching top-of-book pressure.
- `absorption_reversal`: unusually concentrated one-sided flow that fails to move price while the top-of-book queue opposes the aggressor.

`src/tbbo_features.py` converts TBBO events into completed one-second feature rows. Rolling features are isolated by raw futures instrument ID, so a continuous-contract roll cannot create a false impulse. A five-minute warm-up follows each instrument transition, and candidate timestamps are restricted to 08:20-13:30 New York time with daylight-saving conversion.

## Estimate without spending

Set `DATABENTO_API_KEY` in the environment, then run:

```powershell
uv run --with-requirements requirements.txt python estimate_or_acquire.py
```

This calls only the historical metadata cost endpoint and writes a manifest under `C:/ComexGoldFuturesFoundationV1/manifests`. It cannot submit a batch job.

## Explicitly authorize an acquisition

After reviewing the estimate, a batch job can be submitted only with both `--execute` and a positive cost cap:

```powershell
uv run --with-requirements requirements.txt python estimate_or_acquire.py --config config/zero_payment_trades_v1.json --execute --schema trades --max-cost-usd 121 --verified-free-credit-usd 125
```

The exact request is re-priced immediately before submission. The command refuses the job when its estimated price is above the cap, when the cap is above the currently verified free-credit balance, or when payment authority is absent. Submission does not automatically download data.

Inspect the submitted job without downloading:

```powershell
uv run --with-requirements requirements.txt python inspect_or_download.py --job-id JOB_ID
```

After the job reaches `done`, explicitly download and hash every raw file:

```powershell
uv run --with-requirements requirements.txt python inspect_or_download.py --job-id JOB_ID --execute-download
```

The downloader refuses unfinished jobs and nonempty destination directories. Its manifest records the vendor job metadata, file list, byte sizes, and SHA-256 digests.

Never put the API key in a command, config file, commit, or chat message.

## Verification

```powershell
uv run --with pytest pytest -q
```
