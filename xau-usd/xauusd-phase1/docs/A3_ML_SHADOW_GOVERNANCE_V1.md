# A3 ML Shadow Governance V1

Status: PRELOCK_CONTRACT

This contract owns offline/live shadow operation, safety, and runtime authorization boundary.

## Runtime Boundary

C01 may evaluate frozen A1 account 1025742, A2 account 1033030, and A3 account 1033669 data.

The ML layer has no authority to arm, disarm, attach, detach, alter, close, or place broker actions on any account.

A3 account 1033669 remains paused.

A3 lanes 933200, 933300, and 933400 remain paused.

Profit-lock remains DRY_RUN_DISARMED.

No broker action, reactivation, armed EA attach, armed preset, live trading, real capital, account setting change, or runtime state change is authorized by the ML layer.

## Offline Shadow

Python may read frozen data and write:

- a3_ml_offline_scores.csv;
- A3_ML_OFFLINE_REPORT.md.

No MT5 runtime change is allowed.

## Live Python Shadow

Only after offline review, Python may tail passive feature logs and write passive score logs.

It may output only shadow scores, probabilities, threshold, action label TAKE/SKIP/ABSTAIN, drift status, hashes, and explanations.

Python must not import or call broker write functions.

Read-only MT5 use is allowed only for bars, ticks, account verification, and history verification.

## Passive MQL5 Parity

Passive MQL5 feature parity may be built later.

MQL5 passive observers must not include OrderSend, CTrade, TRADE_ACTION_*, position modification, or close logic.

## Export Boundary

Logistic export should be signed JSON with feature order, imputer values, scaler means/scales, coefficients, intercept, threshold, and hashes.

Required parity before any execution discussion:

- probability absolute error <= 1e-6;
- 100 percent action parity on boundary fixtures;
- at least 99.9 percent parity across replay sample.

No future execution design may depend on Python network RPC.

## Drift Response

On schema/hash mismatch, critical drift, or drift lock:

```text
ML_SHADOW_DISABLED
```

A future execution system must fail to deterministic no-trade/paused policy.
