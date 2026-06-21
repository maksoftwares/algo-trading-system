# A3 ML Slippage Model Contract V1

Status: PRELOCK_CONTRACT

This contract owns fill observations, slippage definitions, sample adequacy, session/spread buckets, P50/P95 distributions, fold-causal fitting, and slippage artifact hashes.

## Artifact

The fitted slippage artifact is:

```text
A3_ML_SLIPPAGE_MODEL_V1.json
```

The fitted artifact is not part of the contract lock. It is hashed as a generated artifact later.

## Measurements

Measure adverse slippage for:

- entry: request price versus actual entry fill;
- SL exit: active stop level versus actual SL fill;
- TP exit: target level versus actual TP fill;
- timeout or market exit: observed executable quote versus actual market exit where available.

Spread is embedded through executable bid/ask quotes. Additional broker slippage is modeled separately.

## Buckets

Primary buckets:

- global;
- Dubai session;
- spread tercile.

Use a session or spread bucket only when bucket rows >= 50. Otherwise use global.

## Candidate Adequacy

Candidate evaluation requires:

- entry fills >= 200;
- SL exits >= 100;
- TP exits >= 50.

If any requirement is unmet:

```text
slippage_model_status = INSUFFICIENT
dataset cannot exceed EXPLORATORY_MODEL
```

## Label Scenarios

Expected labels use adverse P50.

P95-stress labels use adverse P95.

For TP, do not grant favorable slippage beyond zero improvement.

## Leakage Control

For each outer fold, fit the slippage distribution only from fills before the test start and freeze it for that test fold.

The final forward window uses the last locked pre-forward slippage model.

If the empirical slippage model is unavailable, base executable labels may be built only as OPTIMISTIC_DIAGNOSTIC_ONLY.
