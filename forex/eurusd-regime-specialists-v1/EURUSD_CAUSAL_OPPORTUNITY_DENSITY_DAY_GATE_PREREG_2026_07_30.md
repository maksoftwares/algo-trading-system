# EURUSD causal opportunity-density day gate preregistration

Date: 2026-07-30

Status: **FROZEN BEFORE OUTCOME**

Demo-order authorization: **false**

## Hypothesis

The hindsight density diagnostic found 124 dates containing exactly four
ordinary RSI/Bollinger opportunities. Taking those 496 trades produced PF
1.444, but the final count was unknowable when the first trade arrived.

This experiment asks a causal question instead: can the exact-four day be
forecast at 00:00 UTC using only prior completed-day opportunity counts,
prior EURUSD range/return/realized-volatility/spread, lagged counts by expert,
and calendar cycles?

A fixed random forest with 400 trees, depth four, minimum leaf 20, balanced
subsamples, and a fixed 0.50 probability threshold is used. There is no
threshold or hyperparameter search. Activated days accept ordinary
opportunities in chronological order, with a maximum of four entries and
four concurrent 0.25R positions. No future daily ranking or outcome is used.

## Chronology

The model initially trains on 2019–2021 and predicts 2022. It refits at each
calendar window using only earlier completed dates and labels.

- Development decisions: 2022 and 2023.
- Locked validation, opened only if development passes: 2024, 2025, and
  2026H1.

Development requires at least 100 trades, 0.15 trades per weekday, PF 1.15,
stressed PF 1.05, both years above PF 1.0, winner-removal PF 1.0, and evidence
that the classifier improves exact-four precision above the low base rate.

Validation adds per-window, recent, drawdown, and protected-date independence
gates. Historical success could authorize only a disarmed forward-shadow
candidate.

## Reproduction command

```powershell
uv run --offline --with pandas --with numpy --with pyarrow --with scikit-learn python run_causal_opportunity_density_day_gate.py
```

