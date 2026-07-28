# EURUSD Neutral Growth/Risk Selected Portfolio Preregistration

Date frozen: 2026-07-28
Family: `N47_NEUTRAL_GROWTH_RISK_SELECTED`
Status: adaptive after disclosed 2022 development; frozen before any 2023 EURUSD outcome.

## Honest information status

This is not a pre-2022 hypothesis. N46 opened only 2022 and showed:

- Asia 03:00: PF 1.236, +4.544R;
- Europe 09:00: PF 1.640, +5.812R;
- US 15:00: PF 0.692, -2.809R.

N46 remains rejected because its mandatory three-expert portfolio missed its frozen trade-count evidence floor. N47 is a separately named successor that treats 2022 as in-sample development and permanently selects only Asia and Europe before 2023 is opened.

The selected 2022 portfolio had 54 trades, 48.15% wins, 1.471 realized payoff, PF 1.366, +10.356R, and 6.122R maximum drawdown. These are development metrics, not validation.

## Frozen mechanics

N47 inherits N46 mechanics byte-for-byte:

- Neutral date known at 00:00 UTC;
- exact completed-M5 external data with no as-of match or forward fill;
- LONG only when SPX and copper are positive while USD/CNH is negative over the completed prior 60 minutes;
- SHORT only for the exact inverse;
- cash on disagreement, zero, stale, missing, or noncontiguous inputs;
- EURUSD entry at the exact decision-time M5 open;
- prior completed 60-minute EURUSD structure stop, 0.5-pip buffer, 4-pip floor, 20-pip ceiling;
- 1.5R target and six-hour maximum hold;
- 0.7-pip minimum spread, 0.1 pip slippage per side, stop-first ambiguity;
- one open position.

Only two clocks remain:

1. Asia handoff at 03:00 UTC;
2. Europe morning at 09:00 UTC.

The 15:00 US expert is excluded permanently. No frequency quota exists.

## Untouched candidate capacity

Without reading EURUSD outcomes, the selected experts have:

- 71 candidates in 2023 confirmation;
- 40 in 2024;
- 57 in 2025;
- 36 in 2026 H1;
- 204 total, split 107 LONG and 97 SHORT.

## Outcome firewall

1. Commit and push this preregistration before loading 2023 EURUSD.
2. Load only the parquet slice ending `2023-12-31T23:59:59Z`.
3. Apply every confirmation threshold in the frozen JSON.
4. If 2023 fails, reject N47 and do not open 2024–2026.
5. If 2023 passes, hash-lock and commit the confirmation result before opening any later year.
6. Evaluate 2024, 2025, and 2026 H1 exactly once with no retuning.

Success in 2023 or later history does not authorize demo or live orders. Broker action remains false unless the user separately authorizes an operational prospective phase.
