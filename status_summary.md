# A1 XAUUSD Current Governance Status

Status: `NO_GO_RESEARCH_ONLY`
Schema: `a1_xau_governance_status_v1`
Generated UTC: `2026-07-10T15:11:59.001734Z`
Branch: `codex/xau-router-entry-hold-audit`
Base commit: `c12f024802135bdb61e817db4fe4f8e10ba0a683`

This is the only authoritative current status surface. Historical phase/runtime summaries are non-authorizing.

## North star

> Build an automated XAUUSD system that produces positive net returns over rolling 6- and 12-month periods, survives realistic costs and regime changes, limits portfolio equity drawdown, and can eventually support controlled withdrawals from accumulated profits.

## Required current statements

```text
R1+R2 = current research control
R3 = standalone shadow only
R3 portfolio use = killed by DD gate
R4 = no survivor
no demo/live authorization
next task = router entry/hold path audit
```

## Current research control

Control: `current_r1_r2_baseline`
Standing: `CURRENT_RESEARCH_CONTROL`; `RESEARCH_CONTROL_NOT_DEPLOYMENT_AUTHORIZED`
Ledger SHA256: `47cbe6a562ba2874d93a97255affbde613566ed06340a149ed2795d69a5dae52`

| Metric | Value |
| --- | ---: |
| Trades | `678` |
| Win rate | `51.03%` |
| Realized W/L | `2.6082` |
| Profit factor | `2.7182` |
| Net | `+$9,640.05` |
| Stress net at -$0.30/ticket | `+$9,436.65` |
| Recent-three-month net | `+$764.92` |
| Maximum closed drawdown | `$889.69` |
| Positive months | `26` |
| Active weekdays | `approximately 21.28%` |

## Specialist ownership

| Specialist | Current standing | Role / default |
| --- | --- | --- |
| R1 | `CURRENT_RESEARCH_CONTROL_COMPONENT` | Primary bullish/uptrend profit engine |
| R2 | `CURRENT_RESEARCH_CONTROL_COMPONENT` | Strict downtrend hedge and secondary profit source |
| R3 | `STANDALONE_SHADOW_ONLY`; `KILLED_BY_DD_GATE` | Portfolio use killed by DD gate |
| R4 | `NO_SURVIVOR` | Chop default `NO_TRADE` |

## Post-audit rule admissibility

Status: `BLOCKED_LEGACY_RULE_ADMISSIBILITY`
Identity scope: `PRESERVES_678_ROW_AUDIT_IDENTITY_ONLY`

The four retained rules below preserve the 678-row audit identity only; they are not endorsed for integration.
The first three are forbidden selection rules. The R2 $10 daily-loss stop is source-local containment, not standalone alpha/admission evidence, and cannot be reused as such.
Future containment must be a shared preregistered integrated risk policy.
Integrated admission requires independently qualified rule-clean sources or later reviewed governance.
Otherwise the result is `NO_GO`. The router audit cannot remove or repair these rules.

| Frozen source | Admissibility issue | Retained rule type | Retained rule |
| --- | --- | --- | --- |
| `h4_d1_long_best_box2_atr80` | `FORBIDDEN_SELECTION_RULE` | `PREVIOUS_MONTH_PNL_HEALTH_GATE` | Previous-month P/L health gate (enabled; minimum net -$50) |
| `r1_h1_pullback_long_v1` | `FORBIDDEN_SELECTION_RULE` | `R1_DIRECTIONAL_SESSION_GATE` | R1 directional session 09 <= hour < 15 |
| `r2_pullback_rejection_short_v1` | `FORBIDDEN_SELECTION_RULE` | `R2_DIRECTIONAL_SESSION_GATE` | R2 directional session 05 <= hour < 19 |
| `r2_continuation_short_v1` | `SOURCE_LOCAL_CONTAINMENT_NOT_ADMISSION_EVIDENCE` | `R2_DAILY_LOSS_STOP` | R2 $10 daily-loss stop |

## Native-position attribution repair

Attribution status: `REPAIR_REQUIRED_NATIVE_POSITION_JOIN`

The legacy direction-FIFO parser assigned a non-native exit deal to `388/678` rows and non-native individual P/L to `387/678` rows.
The aggregate exit/P&L multiset and source/portfolio totals remain exact, and all 678 native positions are recoverable.
The audit must complete the outcome-blind native position join and reconcile it before any router classification.
FIFO fallback is prohibited. This is evidence-attribution repair only; no strategy change is authorized.

## Evidence and authorization boundary

All inspected history through `2026-06-30` is `DEVELOPMENT_DATA`.
It is not an untouched holdout.

| Authorization fact | Value |
| --- | ---: |
| Demo authorized | `false` |
| Live authorized | `false` |
| Broker action authorized | `false` |
| Runtime touched | `false` |

## Immediate next task

Next task: `A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_V1`
Status: `PREREGISTERED_NOT_RUN`
Strategy change authorized: `false`
EA trading-logic change: `NONE`

## Governing documents

| Document | SHA256 |
| --- | --- |
| [master_direction](xau-usd/xauusd-phase1/docs/A1_XAU_PROFITABLE_SYSTEM_MASTER_DIRECTION_2026_07_10.md) | `d17285d1056c07342bbd4e3ef0d84c5a0999ff9067313076414d66a9b7b90bfb` |
| [current_research_freeze](xau-usd/xauusd-phase1/docs/A1_XAU_CURRENT_RESEARCH_FREEZE_2026_07_10.md) | `e3a7ec680a35bc81b08fbeaf56d12f8b9b3b23cdb068ad41a18aad88f7f060c8` |
| [router_entry_hold_path_audit_prereg](xau-usd/xauusd-phase1/docs/A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_PREREG_2026_07_10.md) | `cc42e7942ae04956c6b94cefa59e3277e4b0db167a02826eb05156e758f92541` |
