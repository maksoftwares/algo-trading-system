# Phase 2X Owner Authorization Status

Overall status: PASS

Phase 2X owner authorization status. The generated preset is local/private demo-only and non-canonical.

Created at UTC: `2026-06-08T11:24:38.649359Z`

## Boundary

- Phase 2X can approve only quarantined experimental demo execution.
- Phase 2X cannot approve canonical Phase 2.
- Phase 2X cannot approve live trading or real capital.
- Phase 2X cannot unsuspend the cost-suspended breakout-retest family.
- Phase 2X cannot create same-family diversification claims.

## Owner Authorization

- Owner JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\local\phase2x_owner_authorization.local.json`
- Local preset written: `True`
- Local preset SHA256: `c85299972f4a9449dccaddd63e69dafe8a2e843c063a62a22fb7f02f6a8ee84c`
- Masked account: `****742`

## Checks

| Check | Status | Evidence |
|---|---|---|
| owner_json_present | PASS | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\local\phase2x_owner_authorization.local.json |
| authorization_status | PASS | authorization_status='APPROVED_FOR_EXPERIMENTAL_DEMO_ONLY' |
| authorized_account_login_present | PASS | account login must be nonblank |
| server_marker_demo_or_practice | PASS | server_marker='Capital.ComMena-Demo' |
| authorized_symbol_xauusd | PASS | authorized_symbol='XAUUSD' |
| authorized_candidate | PASS | authorized_candidate='P2WEAKNESS_BR_V1' |
| authorized_magic_931000 | PASS | authorized_magic=931000 |
| fixed_lot_lte_0_01 | PASS | fixed_lot=0.01 |
| max_orders_per_day_lte_3 | PASS | max_orders_per_day=2 |
| max_account_orders_per_day_lte_3 | PASS | max_account_orders_per_day=3 |
| max_family_open_positions_eq_1 | PASS | max_family_open_positions=1 |
| max_estimated_cost_r_lte_0_15 | PASS | max_estimated_cost_r=0.15 |
| max_measured_spread_points_lte_75 | PASS | max_measured_spread_points=75.0 |
| experimental_authorization_token | PASS | required token must match exactly |
| cost_suspension_acknowledgement_token | PASS | required acknowledgement token must match exactly |
| authorization_not_expired | PASS | expires_at_utc=2026-06-15T11:18:36+00:00 |
| local_output_path | PASS | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\local\Phase2WeaknessBreakoutRetestExecutor.owner_authorized_demo_xauusd.local.set |
