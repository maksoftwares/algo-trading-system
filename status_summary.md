# A1 XAUUSD Current Governance Status

Status: `NO_GO_RESEARCH_ONLY`
Schema: `a1_xau_governance_status_v1`
Generated UTC: `2026-07-12T06:42:24.698893Z`
Branch: `codex/xau-router-entry-hold-audit`
Base commit: `d26c19736a0672a2c74a3062263cd9732a46bb13`

This is the only authoritative current status surface. Historical phase/runtime summaries are non-authorizing.

## North star

> Build an automated XAUUSD system that produces positive net returns over rolling 6- and 12-month periods, survives realistic costs and regime changes, limits portfolio equity drawdown, and can eventually support controlled withdrawals from accumulated profits.

## Required current statements

```text
R6 = primary independent specialist lane
NP1-A = next action
R1+R2 = research control only
R3 = excluded
R4 = no survivor
router entry/hold audit = deferred control diagnostic
parallel specialist lane = false
all history through 2026-06-30 = DEVELOPMENT_DATA
no demo/live/broker authorization
```

## Primary independent-specialist lane

Primary lane: `R6_H4_DISTRIBUTION_BREAK_FAILED_RECLAIM_SHORT_V1`
Standing: `PRIMARY_INDEPENDENT_SPECIALIST_LANE`
Next action: `NP1-A` — market-only native Router/contract acquisition locks
NP1 standing: `MANDATORY_PREREQUISITE_WITHIN_R6`
Parallel specialist lane authorized: `false`
Historical R6 P/L authorized: `false`

R6 owns the pre-downtrend distribution / failed-reclaim transition while Router V1 is `UPTREND` or `CHOP`.
The H1/H4 objective range-box family is backlog only if R6 closes and a later owner/reviewer packet selects it.

## Machine-readable authority

Authoritative task key: `primary_next_task`
Authoritative statements key: `required_current_statements`
Compatibility task key: `control_diagnostic_task`

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

| Specialist | Primary-program standing | Frozen compatibility standing | Role / default |
| --- | --- | --- | --- |
| R1 | `RESEARCH_CONTROL_ONLY` | `CURRENT_RESEARCH_CONTROL_COMPONENT` | Primary bullish/uptrend profit engine |
| R2 | `RESEARCH_CONTROL_ONLY` | `CURRENT_RESEARCH_CONTROL_COMPONENT` | Strict downtrend hedge and secondary profit source |
| R3 | `EXCLUDED` | `STANDALONE_SHADOW_ONLY`; `KILLED_BY_DD_GATE` | Not independent; excluded from portfolio use |
| R4 | `NO_SURVIVOR` | `NO_SURVIVOR` | Chop default `NO_TRADE` |

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

Next task: `R6-NP1-A_MARKET_ONLY_NATIVE_PARITY_ACQUISITION_LOCKS`
Status: `AUTHORIZED_NOT_STARTED`
Strategy change authorized: `false`
EA trading-logic change: `NONE`

## Deferred control diagnostic

Control task: `A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_V1`
Status: `DEFERRED_CONTROL_DIAGNOSTIC`
Authoritative for primary program: `false`
It remains required before the old R1+R2 control can enter an integrated portfolio, but it does not block R6 standalone discovery.

### Frozen compatibility statements

```text
R1+R2 = current research control
R3 = standalone shadow only
R3 portfolio use = killed by DD gate
R4 = no survivor
no demo/live authorization
router entry/hold path audit preregistration remains frozen
```

## Governing documents

| Document | SHA256 |
| --- | --- |
| [master_direction](xau-usd/xauusd-phase1/docs/A1_XAU_PROFITABLE_SYSTEM_MASTER_DIRECTION_2026_07_10.md) | `d17285d1056c07342bbd4e3ef0d84c5a0999ff9067313076414d66a9b7b90bfb` |
| [current_research_freeze](xau-usd/xauusd-phase1/docs/A1_XAU_CURRENT_RESEARCH_FREEZE_2026_07_10.md) | `e3a7ec680a35bc81b08fbeaf56d12f8b9b3b23cdb068ad41a18aad88f7f060c8` |
| [router_entry_hold_path_audit_prereg](xau-usd/xauusd-phase1/docs/A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_PREREG_2026_07_10.md) | `cc42e7942ae04956c6b94cefa59e3277e4b0db167a02826eb05156e758f92541` |
| [independent_specialist_primary_direction](xau-usd/xauusd-phase1/docs/A1_XAU_INDEPENDENT_SPECIALIST_PRIMARY_DIRECTION_2026_07_12.md) | `c68a669f160b7469f8204101d05d38c36cf46f0501ca1f11c77ff3f91659b9af` |
