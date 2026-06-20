# A1/A2 920101 Maintenance Packet - 2026-06-21

Status: `OWNER_REVIEW_REQUIRED_BEFORE_RUNTIME`

Boundary: this packet is a proposed maintenance plan only. It does **not** authorize or perform any MT5 terminal, EA, preset, chart, order, position, profile, or broker setting change.

Purpose: restore runtime identity before any next-week forward test. The profitable historical slice is A1 `920101 / breakout_retest / XAUUSD / Dubai evening`, but the currently inspected A1 profile does not contain the corresponding XAU standard executor chart. A2 has an XAU breakout chart, but it is a stricter clean setup and not currently identical to the locked forward-test spec.

## Source Reports

| Item | Path |
| --- | --- |
| Runtime drift forensic | `FORENSIC_RUNTIME_DRIFT_AND_TRADE_DROP_2026_06_21.md` |
| A1/A2 rule identity reconciliation | `xau-usd/xauusd-phase1/outputs/reports/A1_A2_920101_RULE_IDENTITY_RECONCILIATION_2026_06_20.md` |
| Locked forward spec | `xau-usd/xauusd-phase1/docs/A1_XAU_920101_EVENING_CORE_FORWARD_V0_SPEC_2026_06_20.md` |
| Runtime chart inventory | `xau-usd/xauusd-phase1/outputs/reports/RUNTIME_CHART_INVENTORY_FORENSIC_2026_06_21.csv` |

## Current Runtime Snapshot

### A1 Standard Account `1025742`

| Chart | Symbol | EA | Candidate | Broker action | Dry-run | Session | Max open | Cost cap | Spread cap | Decision |
| --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- |
| `chart01.chr` | EURUSD | `Phase2ExperimentalDemoExecutor` | `breakout_retest` | true | false | `12 -> 1` | 0 | 0.00 | 0.0 | Disable broker action; losing non-spec symbol. |
| `chart02.chr` | GBPUSD | `Phase2ExperimentalDemoExecutor` | `breakout_retest` | true | false | `12 -> 1` | 0 | 0.00 | 0.0 | Disable broker action; losing non-spec symbol. |
| `chart18.chr` | XAUUSD | `Phase2ExperimentalDemoRepairExecutor` | `symbol_normalized_round_retest_v0_repair_v1` | true | false | `12 -> 1` | 0 | 0.00 | 0.0 | Disable broker action; repair lane outside forward spec. |
| `chart19.chr` | XAUUSD | `Phase2ExperimentalDemoRepairExecutor` | `session_extreme_retest_v0_repair_v1` | true | false | `12 -> 1` | 0 | 0.00 | 0.0 | Disable broker action; repair lane outside forward spec. |
| `chart20.chr` | EURUSD | `Phase2ExperimentalDemoRepairExecutor` | `session_extreme_retest_v0_repair_v1` | true | false | `12 -> 1` | 0 | 0.00 | 0.0 | Disable broker action; non-spec symbol. |
| `chart21.chr` | XAUUSD | `WR50_BreakoutWideStop_v0` | WR50 | not parsed | not parsed | `12 -> 1` | n/a | n/a | n/a | Disable broker action if enabled; outside forward spec. |
| `chart26.chr` | XAUUSD | `Account1DailyProfitFloorGuardian` | close-only guardian | n/a | false | n/a | n/a | n/a | n/a | Keep, but confirm it matches locked daily stop/lock behavior. |

Missing from A1: `Phase2ExperimentalDemoExecutor` on `XAUUSD` / `breakout_retest` / account `1025742`.

### A2 Clean Account `1033030`

| Chart | Symbol | EA | Candidate | Broker action | Dry-run | Session | Max open | Cost cap | Spread cap | Decision |
| --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- |
| `chart01.chr` | XAUUSD | `AccountEquityGuardianShadow` | guardian shadow | n/a | n/a | n/a | n/a | n/a | n/a | Not equivalent to A1 active daily lock. Needs decision. |
| `chart02.chr` | XAUUSD | `Phase2ExperimentalDemoExecutor` | `breakout_retest` | true | false | `12 -> 15` | 1 | 0.30 | 75.0 | Keep only if A1 is aligned to the same rule and daily lock parity is resolved. |

### A3 Repair Account

A3 must remain paused. Current reconciliation shows A3 entry charts are dry-run / broker-action disabled. Do not reactivate A3 in this maintenance window.

## Proposed Forward-Test Runtime Rule

If the owner approves execution later, A1 and A2 should be aligned to this shared rule:

| Field | Required value |
| --- | --- |
| Account scope | A1 `1025742` and A2 `1033030` only |
| Server | `Capital.ComMena-Demo` only |
| Symbol | `XAUUSD` only |
| Candidate | `breakout_retest` only |
| Derived magic | `920101` only |
| Lot | `0.01` fixed |
| Broker action | true only on the approved XAU breakout chart per account |
| Dry-run | false only on the approved XAU breakout chart per account |
| Session gate | true |
| Broker-action session | Dubai `16:00:00` through `19:59:59` only, represented by server hours `12 -> 15` in the current A2 profile |
| Blocked sessions | Dubai morning, afternoon, and night |
| Max open positions per instance | `1` on both accounts, unless owner explicitly chooses old A1 unlimited behavior and records that the rules are no longer identical |
| Cost cap | `0.30R` on both accounts, or explicit owner-approved revision |
| Spread cap | `75` points on both accounts, or explicit owner-approved revision |
| Duplicate/family mutex | enabled through current `Phase2ExperimentalDemoExecutor` source |
| Daily profit lock | `+100 AED` per account/day |
| Daily loss stop | `-100 AED` per account/day |
| Other broker-action lanes | disabled or observer-only |
| Canonical Phase 2 | unchanged; still not approved |
| Live capital | not authorized |

## Important Open Parity Gap

The locked forward spec requires daily profit and daily loss controls on both accounts.

Current evidence:

- A1 has `Account1DailyProfitFloorGuardian`.
- A2 inventory shows `AccountEquityGuardianShadow`, not an active equivalent close/entry-halt guardian.

Before execution, choose one:

1. **Strict identity option:** add/authorize an A2 active guardian equivalent to A1, including `+100 AED` daily profit lock and `-100 AED` daily loss stop.
2. **Simplified forward-test option:** disable daily-lock enforcement from the pass/fail rule and use it only as an emergency control, then relock the forward spec.

Do not pretend the accounts are identical until this is resolved.

## Proposed Runtime Changes If Owner Approves

### A1 Changes

| Change | Reason |
| --- | --- |
| Restore or attach `Phase2ExperimentalDemoExecutor` on XAUUSD for account `1025742`, candidate `breakout_retest`, lot `0.01`, session `12 -> 15`, max open `1`, cost cap `0.30R`, spread cap `75`. | Restores the only evidenced profitable lane and aligns it to A2. |
| Disable broker action on A1 EURUSD `breakout_retest`. | Losing non-spec lane. |
| Disable broker action on A1 GBPUSD `breakout_retest`. | Losing non-spec lane. |
| Disable broker action on A1 XAU repair lanes. | Repair lanes are outside the locked forward test and have not earned broker-action continuation. |
| Disable broker action on A1 EUR repair lane. | Non-spec lane. |
| Disable WR50 broker action if enabled. | Outside the locked forward test. |
| Keep A1 guardian only if it matches the final shared daily-lock decision. | Avoid hidden account-rule mismatch. |

### A2 Changes

| Change | Reason |
| --- | --- |
| Keep A2 XAU `breakout_retest` chart if it remains `12 -> 15`, lot `0.01`, max open `1`, cost cap `0.30R`, spread cap `75`. | This is already close to the locked forward-test rule. |
| Add/authorize equivalent active daily lock/loss control, or relock the spec without daily-lock parity. | Current A2 shadow guardian is not equivalent to A1 active guardian. |
| Confirm no other A2 broker-action chart exists. | Preserve clean account evidence. |

### A3 Changes

| Change | Reason |
| --- | --- |
| No broker-action changes except confirming paused state. | A3 remains paused due failed repair evidence and prior drift. |

## Required Before/After Evidence If Executed

The execution report must include:

- profile backup paths for A1 and A2;
- before/after chart inventory table;
- source SHA256 for every deployed EA source;
- compiled `0 errors / 0 warnings` logs;
- startup log proof from A1 XAU and A2 XAU;
- order/log file names for A1 XAU and A2 XAU;
- confirmation that disabled lanes are dry-run or broker-action false;
- confirmation that A3 remains paused;
- confirmation that no open positions are unexpectedly closed unless the owner explicitly authorizes close-only cleanup;
- confirmation that no live/real account is touched.

## Review Questions For Owner / Reviewer

1. Approve restoring A1 XAU `920101` and disabling the losing non-spec A1 lanes?
2. Should A1 and A2 both use max open position `1`, cost cap `0.30R`, spread cap `75`, and server session `12 -> 15`?
3. Should A2 receive an active daily lock/loss guardian equivalent to A1, or should the forward spec be relocked without daily-lock parity?
4. Should disabled lanes be detached from charts or left attached as dry-run/observer-only?
5. Confirm A3 remains paused.

## Current Decision

Do not execute runtime changes yet.

Recommended next step: send this packet for review, resolve the A2 daily-lock parity question, then execute one tightly scoped owner-approved maintenance window with before/after evidence.
