# XAUUSD Cross-Asset Residual V1 Review Corrections

**CORRECTION-ONLY EVIDENCE REPLAY**
**NO STRATEGY CHANGES**
**NO PARAMETER CHANGES**
**NO STAGE B ACCESS**
**NOT A NEW STRATEGY EXPERIMENT**
**NOT MT5 PARITY EVIDENCE**
**NOT FORWARD-SHADOW EVIDENCE**
**NOT DEPLOYMENT AUTHORIZATION**

Reviewed commit: `0722a66a41cf7a3d109a4bc129f8f469b80ca022`
Correction branch: `codex/xau-crossasset-residual-v1-review-corrections`
Correction commit: `BOUND_BY_CONTAINING_GIT_COMMIT`
Primary classification: `XAU_CROSSASSET_RESIDUAL_V1_CORRECTIONS_COMPLETE_NO_DIRECTIONAL_SURVIVOR`
Underlying economic classification: `XAU_CROSSASSET_RESIDUAL_V1_NO_DIRECTIONAL_SURVIVOR`

## Corrected defects

- Exact per-tick `(timestamp_msc, source_sequence)` execution ordering.
- MFE/MAE terminate at the selected exit tick, inclusive.
- Old-versus-corrected trade and metric reconciliations.
- Gross-positive-trade denominator for winning-day concentration.
- USD 1,000 account contract: 0.50% risk, 20% margin, 80% free margin.
- Exact positive-path classification strings.
- Both model ledgers bound by Parquet, semantic-row, schema, and canonical hashes.
- Full 144-partition raw provenance, capability profiles, gate audit, and substantive test map.

## Execution reconciliation

- Same-millisecond groups inspected: 0
- Groups containing both stop and target across quotes: 0
- Trades whose exit changed: 0
- Trades whose MFE changed: 0
- Trades whose MAE changed: 0

## Corrected Stage A results

- `XAU_NEGATIVE_RESIDUAL_LONG_SPECIALIST`: 2038 trades, PF 0.609146, expectancy -0.153952R, net -313.753891R; `FAIL` (baseline_profit_factor|baseline_expectancy_R|stress_profit_factor|stress_expectancy_R|broker_profit_factor|maximum_closed_drawdown_R|baseline_net_R|stress_net_R|broker_net_R|broker_expectancy_R).
- `XAU_POSITIVE_RESIDUAL_SHORT_SPECIALIST`: 1974 trades, PF 0.589505, expectancy -0.158844R, net -313.558048R; `FAIL` (baseline_profit_factor|baseline_expectancy_R|stress_profit_factor|stress_expectancy_R|broker_profit_factor|maximum_closed_drawdown_R|baseline_net_R|stress_net_R|broker_net_R|broker_expectancy_R).
- `COMBINED_BIDIRECTIONAL_DIAGNOSTIC`: 4012 trades, PF 0.599570, expectancy -0.156359R, net -627.311939R; `FAIL` (baseline_profit_factor|baseline_expectancy_R|stress_profit_factor|stress_expectancy_R|broker_profit_factor|maximum_closed_drawdown_R|baseline_net_R|stress_net_R|broker_net_R|broker_expectancy_R).

## Evidence status

- Deterministic replay: PASS
- Raw provenance: 144_PARTITIONS_SHA256_VERIFIED (144 partitions)
- Test coverage: PASS
- Stage B access: NONE

The corrected Stage A evidence supports permanent closure of the XAU return-residual mean-reversion direction.

Stage B remains unauthorized.

No new strategy, EA or deployment authorization has been granted.
