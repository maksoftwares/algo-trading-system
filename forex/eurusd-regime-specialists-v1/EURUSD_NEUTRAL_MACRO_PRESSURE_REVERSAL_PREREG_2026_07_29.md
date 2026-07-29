# EURUSD Regime 1 Macro-Pressure Reversal Preregistration

Frozen at UTC: 2026-07-29T13:04:43.4586588Z

Status: FROZEN_BEFORE_TEN_YEAR_EXACT_REPLAY

Boundary: RESEARCH_ONLY; no broker, terminal, account, order, or position access is authorized.

## Question

Can the strongest earlier EURUSD macro lead survive a higher-fidelity ten-year Dukascopy bid/ask replay, and does its predeclared `chop + compression` subset qualify as a causal Regime 1 / neutral specialist?

This is not pristine out-of-sample evidence. The original rule and archived EURUSD history were inspected previously. It is an exact-rule transfer and chronological stability audit. No result-dependent parameter, direction, regime, year, or session selection is permitted.

## Frozen Signal

- Bars: complete EURUSD H4 mid-price bars derived from the frozen M5 bid/ask source.
- Macro inputs: official FRED `DFII10` and `DTWEXBGS`, forward-filled only after each observation date plus one calendar day.
- Macro pressure: `20-day real-yield change / 0.20 + 20-day broad-dollar percentage change / 1.50`.
- Prior extreme: preceding 24 complete H4 bars, excluding the signal bar.
- Long: pressure at least `+1.75`, real-yield change greater than `+0.10`, dollar change greater than `+0.75%`, then a break below the prior low by `0.08 ATR` that closes back above it with a bullish body.
- Short: exact inverse.
- ATR: original 14-bar simple moving average of H4 true range.
- Stop: signal extreme plus/minus `0.45 ATR`.
- Entry: next complete H4 open.
- Target: `1.25R`.
- Maximum hold: 12 available complete H4 bars.
- One open position.

## Frozen Execution

- Observed M5 bid/ask path.
- Minimum retail spread floor: `0.7 pip`.
- Maximum entry spread: `2.0 pips`.
- Adverse slippage: `0.1 pip` per side.
- Stress: another `0.5 pip` round trip.
- Stop wins any unresolved same-M5-bar stop/target collision.
- October 2024 suspect interval is cash if an entry-to-exit path overlaps it.

## Frozen Ownership

- `ALL_REGIMES_REPLICATION` is diagnostic only.
- The only promotion scope is `REGIME_1_NEUTRAL_OWNED = chop + compression`, using the already-frozen causal H4 classifier.
- All six classifier labels will be reported. No label may be selected after results.

## Frozen Gates

Regime 1 must have at least 60 full-audit trades; 45%-55% wins; realized payoff 1.35-1.75; PF at least 1.30; stressed PF at least 1.15; every chronological block PF above 1.0; latest-12-month PF at least 1.15 and positive net R; at least 55% positive active months; PF at least 1.0 after removing the best 5% of winners; and maximum closed-trade drawdown no more than 15R.

A historical pass cannot authorize demo or live trading. It would still require separate prospective confirmation.

## Mechanical Amendment 1

At 2026-07-29T13:12Z, the first execution completed trade generation but failed before writing `RESULT.json`: strict JSON rejected an infinite PF from a window with no gross losses. The trade ledger was not opened or inspected. Serialization now maps positive/negative infinity to the strings `Infinity`/`-Infinity` and NaN to JSON null. No signal, threshold, direction, ownership rule, execution rule, metric calculation, or gate changed. The implementation lock records both hashes.
