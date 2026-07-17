# COMEX Futures Foundation V1 Preregistration

## Status

This document freezes acquisition controls and the research sequence before any COMEX data is inspected. This campaign is data infrastructure only.

## Hypothesis

Primary COMEX gold futures trades and top-of-book state may contain short-horizon information that is absent from broker spot bars. The first research target is not raw next-candle prediction. It is whether futures flow can improve the ranking or vetoing of mechanically generated spot specialist candidates after realistic costs.

## Acquisition sequence

1. Estimate the full locked window for all frozen schemas without submitting a job.
2. Prefer `tbbo` if its cost is explicitly approved because it combines trade events with pre-trade top-of-book state.
3. Use `trades`, `bbo-1s`, or `ohlcv-1s` only if a lower-cost feasibility lane is required and record that decision before download.
4. Do not acquire `mbp-1` unless TBBO evidence justifies the additional depth and cost.
5. Record the Databento job metadata, request parameters, raw-file hashes, and instrument definitions before analysis.

## Frozen first-pass mechanisms

The exact thresholds and session rules are stored in `config/futures_flow_feature_contract_v1.json` and must not be changed after inspecting acquired events.

1. `flow_continuation` tests whether concentrated buyer- or seller-initiated volume continues when short-window futures price impulse and top-of-book imbalance agree.
2. `absorption_reversal` tests whether concentrated one-sided flow reverses when price makes little progress and the opposing top-of-book queue remains stronger.

Events are aggregated into completed UTC seconds. Features never cross raw instrument IDs, candidates are disabled during the first five minutes of each mapped contract, and the liquid-session clock is expressed in `America/New_York` so daylight-saving changes are causal and explicit.

## Research sequence after acquisition

1. Decode DBN without converting timestamps or prices through lossy text formats.
2. Preserve event time, receive time, publisher, instrument ID, action, side, price, size, sequence, and symbol mappings where present.
3. Build causal 1-second and 5-second features from completed windows only.
4. Map each futures event to the contemporaneous Dukascopy spot quote without backward-looking timestamp repair.
5. Run a futures-led event census before defining entries.
6. Preregister separate continuation, exhaustion, and compression-release specialist rules.
7. Label candidates with native bid/ask execution, commissions, slippage stress, stop-first ambiguity, and contract-roll exclusions.
8. Use chronological train, validation, and untouched exam periods. Never random-split overlapping events.
9. Permit ML only as a ranker, calibrator, regime router, or veto layer until it passes locked out-of-time gates.

## Required acceptance evidence

- Positive net expectancy and profit factor above 1.25 after baseline costs in validation and exam.
- Profit factor above 1.10 under locked stress costs in validation and exam.
- At least 200 exam trades and at least 0.5 qualified trades per trading day before considering the specialist material.
- No single month contributes more than 25% of full-period net profit.
- Positive expectancy in both long and short directions unless the specialist is explicitly directional and independently justified.
- Maximum shared-account equity drawdown below the portfolio risk budget when combined with other survivors.
- Deterministic candidates, labels, splits, metrics, and artifact hashes.

Failure of any gate rejects the specialist. The frequency target cannot override expectancy or drawdown gates.

## Prohibited uses

- No demo or live order generation.
- No optimization on the untouched exam set.
- No automatic purchase, download, or schema upgrade.
- No API secrets in repository files or manifests.
- No claim that continuous futures prices are roll-adjusted.
