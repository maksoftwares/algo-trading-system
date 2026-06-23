# A3 ML Demo Shadow Collection Health

Overall status: COLLECTING_LIVE_WAITING_FOR_DATA
Dataset version: xauusd_c02_multiacct_202606220547_geffebb6d_c9221d066
Max stale seconds: 86400

## Upstream Status

- C03 readiness: NO_GO.
- C23 demo Python launch controller: WAITING_FOR_DATA.
- C27 runtime verifier: RESEARCH_PREVIEW_READ_PATH_CONFIRMED_ALL_ACCOUNTS.
- C28 demo shadow monitor: DEMO_SHADOW_RUNTIME_CONFIRMED_ALL_ACCOUNTS.

## Accounts

| Account | Handoff rows | Handoff current | Observer rows | Observer age | Broker tap rows | Collecting |
| --- | --- | --- | --- | --- | --- | --- |
| A1 | 207 | yes | 2866 | 0s | 97 | yes |
| A2 | 94 | yes | 2866 | 4s | 97 | yes |
| A3 | 48 | yes | 2866 | 2s | 383 | yes |

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
| observer_prediction_fresh_all_accounts | true |
| broker_shadow_tap_present_all_accounts | true |
| research_preview_read_path_confirmed_all_accounts | true |
| demo_shadow_post_attach_confirmed_all_accounts | true |
| all_accounts_collecting | true |

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

Keep A1/A2/A3 terminals running, continue passive data collection, then rerun C08/C23 after more market data advances.
