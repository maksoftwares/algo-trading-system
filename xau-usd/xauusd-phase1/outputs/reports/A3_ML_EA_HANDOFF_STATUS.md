# A3 ML EA Handoff Status

Overall status: REFUSED_NOT_READY

## Authorization

- Python demo predictions authorized: false
- EA consumption authorized: false
- MT5 file publish requested: false
- MT5 file publish attempted: false
- Broker action authorized: false

## Accounts

| Account | Login | Files roots |
| --- | --- | --- |
| A1 | 1025742 | C:/Users/ZHAO ZHU INFORMATION/AppData/Roaming/MetaQuotes/Terminal/D0E8209F77C8CF37AD8BF550E51FF075/MQL5/Files |
| A2 | 1033030 | C:/MT5PortableTier1BestEA/MQL5/Files |
| A3 | 1033669 | C:/MT5PortableRepairLane/MQL5/Files |

## Validations

| Check | Passed | Detail |
| --- | --- | --- |
| shadow_bridge_ready | false | observed=DISABLED_FAIL_CLOSED required=READY_SHADOW_ONLY |
| bridge_authorizes_ea_consumption | false | observed=False required=true |
| bridge_blocks_broker_action | true | observed=False required=false |
| predictions_file_exists | true | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_ML_SHADOW_PREDICTIONS.csv |
| predictions_hash_matches_bridge | true | observed=ef4560a069ee9a280e133251b331208b3f8d681a973694ebe032bb3ac3f1eed7 expected=ef4560a069ee9a280e133251b331208b3f8d681a973694ebe032bb3ac3f1eed7 |
| predictions_not_empty | true | rows=349 |
| prediction_actions_allowed | true | observed=ABSTAIN |
| prediction_accounts_allowed | true | observed=1025742,1033030,1033669 |
| all_allowed_accounts_configured | true | configured=1025742,1033030,1033669 |
| all_accounts_have_files_roots | true | A1=C:/Users/ZHAO ZHU INFORMATION/AppData/Roaming/MetaQuotes/Terminal/D0E8209F77C8CF37AD8BF550E51FF075/MQL5/Files; A2=C:/MT5PortableTier1BestEA/MQL5/Files; A3=C:/MT5PortableRepairLane/MQL5/Files |
| terminal_file_name_safe | true | A3_ML_EA_HANDOFF.csv |

## Published Files

- none

## Boundary

- MT5 connection attempted: false.
- Terminal runtime change authorized: false.
- EA file drop authorized: false.
- Broker action authorized: false.

## Next

Wait for C03 PASS, C05 TRAINED_SHADOW_ONLY, and C04 READY_SHADOW_ONLY, then rerun C06.
