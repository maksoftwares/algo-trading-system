# EURUSD Regime 1: Growth/Risk Consensus Preregistration

Date frozen: 2026-07-28
Family: `N46_NEUTRAL_GROWTH_RISK_CONSENSUS`
Scope: research only; no demo or live order is authorized.

## Hypothesis

On a date classified Neutral using information available at 00:00 UTC, EURUSD may still respond to synchronized global growth/risk repricing. A risk-on move is defined as rising S&P 500 proxy, rising copper, and falling USD/CNH. A risk-off move is the exact sign inverse.

This is one finite family containing three mandatory session specialists. There is no post-outcome session selection.

## Frozen experts and signal

The exact decision clocks are:

1. `ASIA_HANDOFF_0300` at 03:00 UTC;
2. `EUROPE_MORNING_0900` at 09:00 UTC; and
3. `US_RISK_1500` at 15:00 UTC.

At each clock, use only the external M5 bar ending at the decision time and its contiguous completed 60-minute log returns:

- LONG EURUSD only when SPX > 0, copper > 0, and USD/CNH < 0;
- SHORT EURUSD only when SPX < 0, copper < 0, and USD/CNH > 0;
- otherwise cash.

All three source rows must be present at that exact M5 timestamp, available no later than the decision time, derived from source ticks strictly earlier than the decision time, and have non-null 60-minute returns. There is no forward fill or as-of match.

The EURUSD entry is the M5 open at the exact decision time. The entry bar cannot affect the signal.

## Frozen risk and costs

- Structural stop: the side-appropriate extreme of the 12 completed EURUSD M5 bars before entry, plus a 0.5-pip buffer.
- Stop floor: 4 pips.
- Stop ceiling: 20 pips; larger raw risk means cash.
- Target: 1.5R.
- Maximum hold: 6 hours.
- Minimum retail spread: 0.7 pip.
- Additional slippage: 0.1 pip per side.
- Same-bar target/stop ambiguity: stop first.
- One open position.
- Frequency quota: none.

## Sequential outcome firewall

The chronology is immutable:

1. Run an outcome-blind candidate census across 2022–2026 H1.
2. Only if the census passes, load EURUSD bars through 2022 and evaluate `development_2022`.
3. If development fails, reject the exact family and do not open 2023–2026 outcomes.
4. If development passes, hash-lock its result before loading 2023.
5. Evaluate only `confirmation_2023`.
6. If confirmation fails, reject the exact family and do not open 2024–2026 outcomes.
7. If confirmation passes, hash-lock it before loading the forward windows.
8. Evaluate 2024, 2025, and 2026 H1 exactly once, with no retuning.

All thresholds are in the frozen JSON contract. No expert, clock, return window, threshold, direction, stop, target, holding period, month, weekday, season, or forward year may be chosen after outcomes.

## Frequency interpretation

There is no requirement for four trades per day. Cash is the correct decision when the external markets disagree or required data is missing. Profitability and chronological robustness—not activity—determine admission.

## Success interpretation

A pass is only historical research evidence. It does not authorize broker action. Demo promotion would still require an explicitly authorized, prospective shadow sample under a separately frozen operational contract.
