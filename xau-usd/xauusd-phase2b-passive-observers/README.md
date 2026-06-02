# XAUUSD Phase 2B Passive Observers

This lane contains passive MT5 observers for separate Phase 0R candidates. These are not current canonical EAs and are not execution-authorized.

Runtime rules:

- Observe XAUUSD only by default.
- Refuse startup on other symbols unless a research override is explicitly enabled.
- Never send broker-side actions.
- Write decision and would-signal telemetry only.
- Include `dry_run=true`, `trade_permission=false`, `broker_action_allowed=false`, and `phase2_execution_authorized=false` on every observer row.

Observers:

| EA | candidate_id | status |
| --- | --- | --- |
| Phase2B_D1CompressionH4Expansion_Observer.mq5 | d1_compression_h4_expansion_v0 | DRAFT observer |
| Phase2B_H4TrendPullbackD1Bias_Observer.mq5 | h4_trend_pullback_d1_bias_v0 | DRAFT observer |
| Phase2B_WeeklyLevelH4Rejection_Observer.mq5 | weekly_level_h4_rejection_v0 | DRAFT observer |

Run the lane safety audit from the repository root:

```powershell
python xau-usd\xauusd-phase2b-passive-observers\scripts\audit_phase2b_observer_safety.py
```
