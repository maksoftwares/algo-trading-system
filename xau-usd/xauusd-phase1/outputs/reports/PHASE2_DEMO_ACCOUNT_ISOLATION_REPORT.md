# Phase 2 Demo Account Isolation Report

This report verifies demo-account isolation evidence only. It does not authorize Phase 2 readiness, paper-mode implementation, live capital, or broker-side execution.

Overall status: PASS

## Authority

| Field | Value |
| --- | --- |
| Paper mode authorized | false |
| Demo trading authorized | false |
| Live trading authorized | false |
| Broker execution authorized | false |
| Canonical Phase 2 authorized | false |

## Account Evidence

| Field | Value |
| --- | --- |
| account_server | Capital.ComMena-Demo |
| account_type_or_label | DEMO_OR_PRACTICE |
| evidence_source | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_EXPERIMENTAL_DEMO_TERMINAL.json |
| positions_count | 0 |
| orders_count | 0 |
| terminal_path | C:\Program Files\MetaTrader 5\terminal64.exe |
| data_path | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075 |
| latest_decision_row_path | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\DEMO_OBSERVER_WOULD_SIGNALS_2026_06_01.csv |
| live_server_marker_present | False |

## Checks

| name | status | evidence |
| --- | --- | --- |
| experimental_demo_terminal_report | PASS | `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_EXPERIMENTAL_DEMO_TERMINAL.json` status is DEMO_TERMINAL_VERIFIED_EXPERIMENTAL_OBSERVERS_ATTACHED. |
| demo_server | PASS | Account server `Capital.ComMena-Demo` is demo/practice context. |
| zero_positions_orders | PASS | `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_EXPERIMENTAL_DEMO_TERMINAL.json` proves 0 positions and 0 orders. |
| authority_boundary | PASS | `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_EXPERIMENTAL_DEMO_TERMINAL.json` keeps Phase 2/demo/live authorization false. |
| runtime_isolation | PASS | Terminal path is distinct from known Phase 1 dry-run and spread-logger portable runtimes. |
| experimental_demo_attachments | PASS | `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_EXPERIMENTAL_DEMO_ATTACHMENTS.json` keeps attachment evidence non-authorizing. |

## Source Reports

| Field | Value |
| --- | --- |
| experimental_demo_terminal | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_EXPERIMENTAL_DEMO_TERMINAL.json |
| experimental_demo_attachments | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_EXPERIMENTAL_DEMO_ATTACHMENTS.json |
| latest_demo_observer_signal_csv | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\DEMO_OBSERVER_WOULD_SIGNALS_2026_06_01.csv |
