# A1 XAUUSD Authoritative Handoff

Updated: `2026-07-12`

## Repository authority

- Base commit: `006824cde421ea61a0bcdb074804f9ccf95c17a9`
- Current governance branch: `codex/xau-router-entry-hold-audit`
- Scope: A1 XAUUSD repository research, exact-MT5 Strategy Tester evidence, offline analysis, and shadow-only preparation.
- This file replaces the prior oversized handoff. If an older statement conflicts with the documents below, the documents below control.

## Governing documents

1. [Master direction](xau-usd/xauusd-phase1/docs/A1_XAU_PROFITABLE_SYSTEM_MASTER_DIRECTION_2026_07_10.md)
2. [Current research freeze](xau-usd/xauusd-phase1/docs/A1_XAU_CURRENT_RESEARCH_FREEZE_2026_07_10.md)
3. [Router entry/hold-path audit preregistration](xau-usd/xauusd-phase1/docs/A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_PREREG_2026_07_10.md)
4. [Independent-specialist primary direction](xau-usd/xauusd-phase1/docs/A1_XAU_INDEPENDENT_SPECIALIST_PRIMARY_DIRECTION_2026_07_12.md)

Read all four before changing code or generating evidence.

## Exact north star

> Build an automated XAUUSD system that produces positive net returns over rolling 6- and 12-month periods, survives realistic costs and regime changes, limits portfolio equity drawdown, and can eventually support controlled withdrawals from accumulated profits.

Authoritative status: `NO_GO_RESEARCH_ONLY`.

Priority is safety, causal correctness, stressed expectancy, equity-drawdown control, robustness, independence, and forward confirmation. Activity is secondary and must never be forced.

## Frozen research state

### R6 primary independent-specialist lane

- Specialist: `R6_H4_DISTRIBUTION_BREAK_FAILED_RECLAIM_SHORT_V1`.
- Standing: `PRIMARY_INDEPENDENT_SPECIALIST_LANE`.
- Economic mandate: pre-downtrend H4 distribution / first failed-H1-reclaim short
  while Router V1 is `UPTREND` or `CHOP`.
- Immediate action: `NP1-A`, the market-only native Router/contract acquisition
  lock packet.
- NP1 is a mandatory bounded prerequisite within R6, not a second program.
- Historical R6 P/L, census output, MT5 strategy execution, and portfolio evidence
  remain unauthorized at IS1-A.
- No parallel specialist family is authorized. H1/H4 range-box research is backlog
  only if R6 closes and a later owner/reviewer packet selects it.

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
new_specialist_authorized: R6_REPOSITORY_RESEARCH_ONLY
parallel_specialist_lane_authorized: false
```

No demo/live attach or broker order outside the isolated Strategy Tester is allowed.
No real broker/account change, risk-setting change, runtime-state change, or
production-terminal touch is allowed.

## Immediate next task

`R6-NP1-A_MARKET_ONLY_NATIVE_PARITY_ACQUISITION_LOCKS`

Create only the NP1-A acquisition locks after IS1-A passes reviewer audit. NP1-A
freezes the deterministic market-only Router/contract oracle source contract, output
schemas, exact tester boundary, hashes, and zero-action gates. It contains no MQ5,
Python implementation, tests, compiled artifacts, MT5 evidence, census, or P/L.

The old `A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_V1` is now
`DEFERRED_CONTROL_DIAGNOSTIC`. It remains required before the old R1+R2 control can
ever enter an integrated portfolio, but it does not block R6 standalone discovery.

## Immediate sequence

1. IS1-A owner-direction supersession and R6 primary-lane lock.
2. NP1-A market-only native-parity acquisition locks.
3. NP1-B oracle/probe implementation and tests.
4. NP1-C exact zero-action native evidence.
5. C2R5 native-parity and input-attestation closure.
6. C3A exact historical-input lock.
7. C3 outcome-blind incidence and USD 1,000 contract census.
8. If C3 passes, one standalone exact-MT5 preregistration and one result.
9. If standalone passes, sealed independence audit.
10. If independence passes, forward-shadow lock.

Do not start a second specialist family, optimization, threshold neighbor, session or
calendar mask, management variant, portfolio rescue, or historical P/L study outside
this sequence.

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
