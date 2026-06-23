# A3 ML Research Preview Runtime Verifier Status

Overall status: RESEARCH_PREVIEW_READ_PATH_CONFIRMED_ALL_ACCOUNTS
Dataset version: xauusd_c02_multiacct_202606220547_geffebb6d_c9221d066

## Meaning

This verifies the EA runtime read path for Python-produced research-preview rows. It still does not authorize official Python demo predictions, EA consumption, or broker action.

## Upstream Statuses

- C20 runtime evidence: RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS
- C25 broker shadow manual attach packet: BROKER_SHADOW_RUNTIME_PRESENT_ALL_ACCOUNTS
- C26 research preview handoff rehearsal: PUBLISHED_RESEARCH_PREVIEW_FAIL_CLOSED

## Runtime Evidence

- Handoff research preview ready all accounts: true.
- Broker shadow tap exists all accounts: true.
- Research preview read path confirmed all accounts: true.

## Account State

| Account | Handoff | Tap log | Read path | Rows |
| --- | --- | --- | --- | --- |
| A1 | true | true | true | 97 |
| A2 | true | true | true | 97 |
| A3 | true | true | true | 378 |

## Validations

| Check | Passed | Detail |
| --- | --- | --- |
| c26_research_preview_published | true | PUBLISHED_RESEARCH_PREVIEW_FAIL_CLOSED |
| c26_keeps_authorization_false | true | C26 authorization must remain false |
| A1_files_root_exists | true | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files |
| A1_files_root_safe | true | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files |
| A1_handoff_exists | true | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files\A3_ML_EA_HANDOFF.csv |
| A1_handoff_research_preview_ready | true | matching_rows=207 actions=ABSTAIN broker_auth=false drift=ML_RESEARCH_PREVIEW_FAIL_CLOSED |
| A2_files_root_exists | true | C:\MT5PortableTier1BestEA\MQL5\Files |
| A2_files_root_safe | true | C:\MT5PortableTier1BestEA\MQL5\Files |
| A2_handoff_exists | true | C:\MT5PortableTier1BestEA\MQL5\Files\A3_ML_EA_HANDOFF.csv |
| A2_handoff_research_preview_ready | true | matching_rows=94 actions=ABSTAIN broker_auth=false drift=ML_RESEARCH_PREVIEW_FAIL_CLOSED |
| A3_files_root_exists | true | C:\MT5PortableRepairLane\MQL5\Files |
| A3_files_root_safe | true | C:\MT5PortableRepairLane\MQL5\Files |
| A3_handoff_exists | true | C:\MT5PortableRepairLane\MQL5\Files\A3_ML_EA_HANDOFF.csv |
| A3_handoff_research_preview_ready | true | matching_rows=48 actions=ABSTAIN broker_auth=false drift=ML_RESEARCH_PREVIEW_FAIL_CLOSED |

## Authorization

- Official model training authorized: false.
- Python demo predictions authorized: false.
- EA consumption authorized: false.
- Broker action authorized: false.

## Boundary

- MT5 connection attempted: false.
- Data export attempted: false.
- Terminal runtime launch attempted: false.
- Terminal shutdown attempted: false.
- Profile or chart file write attempted: false.
- EA file drop authorized: false.
- Broker action authorized: false.

## Next

The EA read path is confirmed for Python-produced research-preview rows on all accounts. Continue collecting/exporting data until C03/C05/C04/C06 can authorize official demo-shadow predictions.
