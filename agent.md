# A1 XAUUSD Authoritative Handoff

Updated: `2026-07-10`

## Repository authority

- Base commit: `006824cde421ea61a0bcdb074804f9ccf95c17a9`
- Current governance branch: `codex/xau-profitable-system-governance`
- Scope: A1 XAUUSD repository research, exact-MT5 Strategy Tester evidence, offline analysis, and shadow-only preparation.
- This file replaces the prior oversized handoff. If an older statement conflicts with the documents below, the documents below control.

## Governing documents

1. [Master direction](xau-usd/xauusd-phase1/docs/A1_XAU_PROFITABLE_SYSTEM_MASTER_DIRECTION_2026_07_10.md)
2. [Current research freeze](xau-usd/xauusd-phase1/docs/A1_XAU_CURRENT_RESEARCH_FREEZE_2026_07_10.md)
3. [Router entry/hold-path audit preregistration](xau-usd/xauusd-phase1/docs/A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_PREREG_2026_07_10.md)

Read all three before changing code or generating evidence.

## Exact north star

> Build an automated XAUUSD system that produces positive net returns over rolling 6- and 12-month periods, survives realistic costs and regime changes, limits portfolio equity drawdown, and can eventually support controlled withdrawals from accumulated profits.

Priority is safety, causal correctness, stressed expectancy, equity-drawdown control, robustness, independence, and forward confirmation. Activity is secondary and must never be forced.

## Frozen research state

### R1+R2

- `current_r1_r2_baseline` is the only current research control.
- It is an offline/component-exact historical control, not an integrated portfolio pass and not deployment evidence.
- R1 is the primary bullish/uptrend profit engine.
- R2 is the strict downtrend hedge and secondary profit source.

The four frozen sources also preserve legacy rules: a now-forbidden previous-month
P/L health gate, two now-forbidden directional session gates, and a source-local
daily-loss stop that cannot be reused as standalone alpha evidence. They remain only
to keep the 678-trade audit identity unchanged. Any future containment must be the
shared preregistered integrated risk policy, not a source-local historical rescue.
They cannot enter an integrated candidate unless a later reviewed packet resolves
rule admissibility and each source independently passes the master standalone gates.

Rule-admission status: `BLOCKED_LEGACY_RULE_ADMISSIBILITY`.

The legacy upstream trade parser also FIFO-paired exits by direction rather than by
native MT5 position ID: `388/678` rows have a non-native exit deal and `387/678` a
non-native individual P/L assignment, although the exit/P&L multiset and all
source/aggregate totals remain correct. The router audit must first reconstruct the
same 678 entries by native position ID and publish exact reconciliation; no path
classification may use the legacy FIFO pair.

Attribution status: `REPAIR_REQUIRED_NATIVE_POSITION_JOIN`.

Frozen metrics: `678` trades; `51.03%` win rate; `2.6082` realized W/L; `2.7182` profit factor; `+$9,640.05` net; `+$9,436.65` stress net at `-$0.30/ticket`; `+$764.92` recent-three-month net; `$889.69` maximum closed drawdown; `26` positive months; approximately `21.28%` active weekdays.

Frozen ledger: [current R1+R2 baseline](xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_current_r1_best_r2_pullback_plus_r2_impulse_body45_atr45_daily_loss10_KEPT.csv)

Ledger SHA256: `47cbe6a562ba2874d93a97255affbde613566ed06340a149ed2795d69a5dae52`

### R3

- Standing: `STANDALONE_SHADOW_ONLY`.
- Portfolio use is killed by the drawdown gate.
- Evidence: `139` R3 trades, `110` same-opportunity R1-box overlaps, and `29` non-overlaps.
- Do not retest source priority, tune R3, add a drawdown governor, or call it diversification.

### R4

- No R4/chop specialist survived.
- Default chop action is `NO_TRADE`.
- Do not create activity filler or another micro-reclaim repair.

## Evidence boundary

- All inspected history through `2026-06-30` is `DEVELOPMENT_DATA`.
- It is not an untouched holdout and may not be relabeled as one.
- Historical exact MT5 can diagnose execution and causal behavior; it cannot remove selection bias.
- Offline recomposition is diagnostic only and cannot authorize portfolio promotion.
- Final confirmation requires locked, genuinely new forward-shadow evidence.

## Authorization flags

```text
demo_authorized: false
live_authorized: false
broker_action_authorized: false
runtime_attach_authorized: false
strategy_tuning_authorized: false
new_specialist_authorized: false
```

No demo/live attach or broker order outside the isolated Strategy Tester is allowed.
No real broker/account change, risk-setting change, runtime-state change, or
production-terminal touch is allowed.

## Immediate next task

`A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_V1`

Audit every frozen R1+R2 trade using EA-side Router V1 as the authoritative classifier. Determine whether each trade is a correct stable-regime entry, a correct entry followed by a later regime change, a stale tactical entry, a wrong-router entry, a transition entry, a data/timestamp error, or a valid loss in its expected regime.

Required hard evidence includes completed-bar-only router states at signal, entry, every completed H1 bar while open, and exit; causal D1/H4/H1/M15 context; signal/order/risk fields; MFE/MAE and final R; and exact trade/P&L reconciliation.

The audit is invalid if any frozen trade is untraced, a timestamp or snapshot is missing, a join reads the future, bar 0 is used for a regime decision, or source counts/P&L do not reconcile exactly. Ambiguous cases fail closed.

Any `WRONG_ROUTER_ENTRY` count above zero is a defect stop. Fix only routing/configuration, then rerun the frozen exact baseline. It is not permission to add a filter or tune a threshold.

## Immediate sequence

1. Finish the governance reset and refresh status artifacts without changing trading logic.
2. Add deterministic router-audit schemas, analyzers, verifiers, and causality/reconciliation/safety tests.
3. Generate immutable read-only exact-MT5 snapshot/path evidence.
4. Produce the router audit reports and assign exactly one preregistered status.
5. Take a conditional router action only if the audit gate justifies it.
6. Requalify the frozen R1 and R2 sources against the master standalone admission
   gates; if no source passes independently, assign `NO_GO` and do not run an
   integrated portfolio.
7. Only after router closure and standalone admission, build one integrated exact-MT5
   portfolio from the independently approved R1/R2 sources, with shared exposure,
   ownership, execution, and equity-DD accounting.
8. Only after an integrated pass, freeze a genuinely new forward-shadow exam.

Do not start a new specialist, optimization, parameter variation, entry/exit repair, session/hour/month filter, portfolio grid, risk governor, or activity filler during this sequence.

## Isolated tester boundary

- Exact runs are allowed only in the isolated Strategy Tester workspace: `C:\MT5A1M5MomentumBacktest`.
- Use local tester agents only; no remote/cloud agents and no visual/runtime attachment.
- Keep account context, terminal profiles, charts, live/demo terminals, positions, and broker state untouched.
- Freeze and hash EA source, EX5, tester INI, compile log, raw logs, reports, and derived artifacts for each evidence run.
- The audit baseline must be derived from base commit `006824cde421ea61a0bcdb074804f9ccf95c17a9`, not from uncommitted campaign EA changes.

## Prior campaign quarantine

- The prior specialist campaign and its uncommitted files are `DEVELOPMENT_DATA` and nonpromotion evidence only.
- Its checkpoint remains `NO_QUALIFIED_STANDALONE_SPECIALIST_NO_PORTFOLIO_TEST_AUTHORIZED`.
- The previously completed mode-27 five-control reconstruction is quarantined as development-only diagnostics.
- It did not authorize mode-27 candidate implementation or execution, does not enter the router-audit decision, and is not forward evidence.
- Do not continue mode-27 or merge prior campaign trading-logic changes into the governance/audit baseline.

## Terminal rule

The valid outcomes include `NO_GO`, `CONTINUE_EVIDENCE`, `NO_TRADE`, and `FREEZE_CURRENT_BASELINE`. Never weaken a gate to avoid one of them. Build only the smallest integrated system whose expectancy, regime ownership, independence, equity risk, and forward survival can be demonstrated without changing rules after seeing results.
