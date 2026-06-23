# A3 ML Fail-Closed Handoff Rehearsal Status

Overall status: PUBLISHED_FAIL_CLOSED_REHEARSAL
Dataset version: xauusd_c02_multiacct_202606211503_geffebb6d_c9221d066
Readiness status: NO_GO

## Authorization

- Training authorized: false
- Python demo predictions authorized: false
- EA consumption authorized: false
- MT5 file publish requested: true
- MT5 file publish attempted: true
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
| expected_accounts_configured | true | configured=1025742,1033030,1033669 |
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
- EA file drop authorized: true.
- Broker action authorized: false.

## Next

The passive observer can read fail-closed ABSTAIN handoff rows from all three MT5 Files roots. Real Python prediction authorization still requires C03 PASS, C05 TRAINED_SHADOW_ONLY, C04 READY_SHADOW_ONLY, and C06 publish.
