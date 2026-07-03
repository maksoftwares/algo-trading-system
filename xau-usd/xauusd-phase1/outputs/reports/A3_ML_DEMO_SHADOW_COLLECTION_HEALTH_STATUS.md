# A3 ML Demo Shadow Collection Health

Overall status: STALE_OR_PARTIAL_COLLECTION
Dataset version: xauusd_c02_multiacct_202606242335_g0a9823b0_c9221d066
Max stale seconds: 86400

## Upstream Status

- C03 readiness: NO_GO.
- C23 demo Python launch controller: WAITING_FOR_DATA.
- C27 runtime verifier: RESEARCH_PREVIEW_READ_PATH_CONFIRMED_ALL_ACCOUNTS.
- C28 demo shadow monitor: DEMO_SHADOW_RUNTIME_CONFIRMED_ALL_ACCOUNTS.

## Accounts

| Account | Handoff rows | Handoff current | Observer rows | Observer age | Broker tap rows | Collecting |
| --- | --- | --- | --- | --- | --- | --- |
| A1 | 259 | yes | 4512 | 218711s | 849 | no |
| A2 | 146 | yes | 4525 | 218584s | 850 | no |
| A3 | 107 | yes | 4538 | 218453s | 3523 | no |

## Collection Checks

| Check | Passed |
| --- | --- |
| files_roots_exist_all_accounts | true |
| files_roots_safe_all_accounts | true |
| handoff_files_exist_all_accounts | true |
| handoff_rows_all_accounts | true |
| handoff_dataset_current_all_accounts | true |
| handoff_unexpired_all_accounts | true |
| observer_startup_present_all_accounts | true |
| observer_prediction_present_all_accounts | true |
| observer_prediction_fresh_all_accounts | false |
| broker_shadow_tap_present_all_accounts | true |
| research_preview_read_path_confirmed_all_accounts | true |
| demo_shadow_post_attach_confirmed_all_accounts | true |
| all_accounts_collecting | false |

## Authorization

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

Observer logs are stale or missing. Reload/attach the observers, wait for fresh rows, then rerun C33 and C23.
