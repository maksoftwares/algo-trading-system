# A3 ML Deterministic Benchmark Protocol V1

Status: PRELOCK_CONTRACT

This contract owns deterministic rule grids and fair selection.

Deterministic benchmarks receive the same nested chronological treatment as ML models.

Use the same inner and outer folds, retention gate, calibration/test separation where applicable, and untouched outer-test discipline.

## Raw Baseline

Always report raw breakout_retest.

## Loose Counter-Trend Veto

Pre-register H1 aligned-slope threshold grid:

- 0.05 ATR;
- 0.10 ATR;
- 0.15 ATR.

Block only when slope is at least the threshold against direction.

## H1 Alignment

Pre-register minimum aligned H1 slope grid:

- 0.00 ATR;
- 0.05 ATR;
- 0.10 ATR.

## Light Retest

Pre-register:

- R1: confirmation body ratio >= 0.35, aligned close location >= 0.60, retest window <= 10 bars;
- R2: confirmation body ratio >= 0.45, aligned close location >= 0.65, retest window <= 10 bars;
- R3: confirmation body ratio >= 0.55, aligned close location >= 0.70, retest window <= 5 bars.

All require:

- break distance >= 0.30 ATR;
- no invalidating close before confirmation.

## Eligibility And Selection

Eligibility:

- retention >= 40 percent;
- expectancy per raw signal > 0;
- PF >= 1.10.

Select highest expectancy per raw signal.

Tie-break:

- higher retention;
- less restrictive configuration.

Outer-fold results are untouched until the selected deterministic rule is fixed.
