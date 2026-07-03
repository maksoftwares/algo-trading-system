# A3 ML Research Preview Handoff Rehearsal Status

Overall status: PUBLISHED_RESEARCH_PREVIEW_FAIL_CLOSED
Dataset version: xauusd_c02_multiacct_202606242335_g0a9823b0_c9221d066

## Meaning

This publishes only research-preview ABSTAIN rows. It is not the official model handoff and it does not authorize Python demo predictions, EA consumption, or broker action.

## Authorization

- Official model training authorized: false.
- Python demo predictions authorized: false.
- EA consumption authorized: false.
- MT5 file publish requested: true.
- MT5 file publish attempted: true.
- Broker action authorized: false.

## Accounts

| Account | Login | Files roots |
| --- | --- | --- |
| A1 | 1025742 | C:/Users/ZHAO ZHU INFORMATION/AppData/Roaming/MetaQuotes/Terminal/D0E8209F77C8CF37AD8BF550E51FF075/MQL5/Files |
| A2 | 1033030 | C:/MT5PortableTier1BestEA/MQL5/Files |
| A3 | 1033669 | C:/MT5PortableRepairLane/MQL5/Files |

## Validations

| Check | Passed | Detail |
| --- | --- | --- |
| c18_rehearsed_research_only | true | REHEARSED_RESEARCH_ONLY |
| c18_keeps_demo_authorization_false | true | C18 authorization must remain false |
| artifact_exists | true | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_ML_EXPLORATORY_MODEL_REHEARSAL_ARTIFACT.json |
| artifact_is_research_only | true | REHEARSED_RESEARCH_ONLY |
| preview_csv_exists | true | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_ML_EXPLORATORY_SHADOW_PREVIEW.csv |
| preview_rows_not_empty | true | rows=512 |
| preview_rows_force_abstain | true | observed=ABSTAIN required=ABSTAIN |
| preview_broker_action_false | true | observed=false required=false |
| expected_accounts_configured | true | configured=1025742,1033030,1033669 |
| preview_accounts_allowed | true | observed=1025742,1033030,1033669 allowed=1025742,1033030,1033669 |
| preview_covers_all_accounts | true | observed=1025742,1033030,1033669 required=1025742,1033030,1033669 |
| all_accounts_have_files_roots | true | A1=C:/Users/ZHAO ZHU INFORMATION/AppData/Roaming/MetaQuotes/Terminal/D0E8209F77C8CF37AD8BF550E51FF075/MQL5/Files; A2=C:/MT5PortableTier1BestEA/MQL5/Files; A3=C:/MT5PortableRepairLane/MQL5/Files |
| files_roots_are_mql5_files | true | A1=C:/Users/ZHAO ZHU INFORMATION/AppData/Roaming/MetaQuotes/Terminal/D0E8209F77C8CF37AD8BF550E51FF075/MQL5/Files; A2=C:/MT5PortableTier1BestEA/MQL5/Files; A3=C:/MT5PortableRepairLane/MQL5/Files |
| terminal_file_name_safe | true | A3_ML_EA_HANDOFF.csv |

## Published Files

- C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files\A3_ML_EA_HANDOFF.csv
- C:\MT5PortableTier1BestEA\MQL5\Files\A3_ML_EA_HANDOFF.csv
- C:\MT5PortableRepairLane\MQL5\Files\A3_ML_EA_HANDOFF.csv

## Boundary

- MT5 connection attempted: false.
- Terminal runtime change authorized: false.
- Profile or chart file write attempted: false.
- EA file drop authorized: true.
- Broker action authorized: false.

## Next

Attach or reload the dry-run broker shadow consumers on XAUUSD M5. They should log ml_available=true with ABSTAIN research-preview rows; official Python demo prediction authority remains closed.
