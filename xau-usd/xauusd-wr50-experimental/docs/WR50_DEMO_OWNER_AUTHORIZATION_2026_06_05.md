# WR50 Demo Owner Authorization

Document date: 2026-06-05

This authorization records the user request in this Codex thread to assign the WR50 EAs for demo trading so real-world demo performance can be observed.

```yaml
owner_name: thread_user
authorization_date: 2026-06-05
authorization_token: WR50_DEMO_1025742_20260605
allowed_account_number: 1025742
allowed_server:
  - Capital.ComMena-Demo
  - Capital.com-Demo
allowed_symbol: XAUUSD
allowed_eas:
  - WR50_BreakoutEvening_v0
  - WR50_BreakoutQuality_v0
  - WR50_BreakoutExit1R_v0
max_fixed_lot: 0.01
max_daily_loss: 100.0
max_total_open_positions: 3
acknowledgement_not_canonical_phase2: yes
acknowledgement_demo_only: yes
acknowledgement_no_live_trading: yes
acknowledgement_breakout_retest_remains_cost_suspended: yes
```

Boundary:

```text
WR50 demo trading does not authorize canonical Phase 2.
WR50 demo trading does not authorize live trading.
WR50 demo trading does not reactivate canonical breakout_retest execution.
breakout_retest_family = COST_SUSPENDED_CANONICAL
```

