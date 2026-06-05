# WR50 EA Registry

Document date: 2026-06-04

Default status for all new EAs is `DEMO_EXPERIMENT_ONLY`. No WR50 EA is live-authorized or canonical-Phase-2-authorized.

| ea_id | ea_name | version | magic_start | magic_end | active_magic | strategy_family | experiment_status | allowed_account | symbol | entry_timeframe | risk_profile | comment_prefix | owner_authorized | live_authorized | canonical_phase2_authorized | max_fixed_lot |
| --- | --- | --- | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: |
| wr50_bev0 | WR50_BreakoutEvening_v0 | v0 | 930000 | 930099 | 930000 | breakout_retest_wr50_experimental | DEMO_EXPERIMENT_ONLY | OWNER_AUTHORIZATION_REQUIRED | XAUUSD | M5 | fixed_or_min_lot_no_compounding | WR50\|BEV0 | false | false | false | 0.01 |
| wr50_bqv0 | WR50_BreakoutQuality_v0 | v0 | 930100 | 930199 | 930100 | breakout_retest_wr50_experimental | DEMO_EXPERIMENT_ONLY | OWNER_AUTHORIZATION_REQUIRED | XAUUSD | M5 | fixed_or_min_lot_no_compounding | WR50\|BQV0 | false | false | false | 0.01 |
| wr50_e1r0 | WR50_BreakoutExit1R_v0 | v0 | 930200 | 930299 | 930200 | breakout_retest_wr50_experimental | DEMO_EXPERIMENT_ONLY | OWNER_AUTHORIZATION_REQUIRED | XAUUSD | M5 | fixed_or_min_lot_no_compounding | WR50\|E1R0 | false | false | false | 0.01 |

## Interpretation

- `owner_authorized=false` means the EA must not be enabled until an owner authorization file is filled outside this repo template and copied into the operating evidence package.
- `live_authorized=false` is mandatory.
- `canonical_phase2_authorized=false` is mandatory.
- `allowed_account=OWNER_AUTHORIZATION_REQUIRED` means the runtime account must match the filled owner authorization and optional allowlist before demo trading is enabled.

