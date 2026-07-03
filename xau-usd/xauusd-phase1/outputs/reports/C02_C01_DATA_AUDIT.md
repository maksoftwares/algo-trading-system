# A3 ML C01 Data Audit

Overall status: PIPELINE_ONLY

## Boundary

C01 Python ML pipeline bootstrap only for configured A1/A2/A3 account scopes. It reads frozen local data and writes offline shadow artifacts. It does not touch MT5 runtime, orders, positions, profiles, charts, presets, or running EAs.

## Scope

- Accounts: 1025742, 1033030, 1033669
- Symbol: XAUUSD
- Family: breakout_retest
- Allowed families: breakout_retest
- Contract scope: breakout_retest_only
- Candidate source: B0_RAW_ALL_SESSION
- Label promotion: label_promotion_locked
- Label promotion active: false
- Label promotion slippage status: INSUFFICIENT

## Per-Account Counts

- A1 1025742: snapshot_rows=299, setup_groups=246, positive=76, negative=223
- A2 1033030: snapshot_rows=186, setup_groups=154, positive=63, negative=123
- A3 1033669: snapshot_rows=148, setup_groups=119, positive=40, negative=108

## Counts

- decisions_rows: 1087
- trades_rows: 0
- scoped_raw_rows: 1087
- rejected_rows: 0
- parse_errors: 0
- exact_unique_signals: 633
- snapshot_rows: 633

## Training Gate

- supervised_training_allowed: false
- reason: global_feature_budget=0 is below the contract minimum of 5
- global_feature_budget: 0
- budget_binding_fold_id: outer_1
- slippage_model_status: INSUFFICIENT

## Outputs

- data_audit_json: C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\C02_C01_DATA_AUDIT.json
- data_audit_md: C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\C02_C01_DATA_AUDIT.md
- snapshot_csv: C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_ML_C01_SNAPSHOT_ROWS.csv
- feature_matrix_csv: C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_ML_C01_FEATURE_MATRIX.csv
- offline_report_json: C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_ML_OFFLINE_REPORT.json
- offline_report_md: C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_ML_OFFLINE_REPORT.md
- offline_scores_csv: C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\a3_ml_offline_scores.csv
