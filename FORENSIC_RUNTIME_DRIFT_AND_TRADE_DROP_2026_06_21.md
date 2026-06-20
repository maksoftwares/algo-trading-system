# Forensic Runtime Drift And Trade Drop - 2026-06-21

Owner question: after many changes, trade count dropped, profitability dropped, the best strategy performs badly on other accounts, and it feels like we broke something.

Verdict: **yes, we broke comparability, and we also let weak lanes trade too much before the later safeguards arrived.** The account-to-account comparison is not valid right now because A1, A2, and A3 are not running the same rule. The strongest concrete runtime defect is that the profitable A1 XAU `breakout_retest` standard executor is not present in the currently inspected A1 profile, while A2 is running a stricter XAU version and A3 is paused after a failed repair experiment.

Boundary: this report is read-only/offline analysis. No MT5 chart, EA, preset, order, position, profile, or broker setting was changed.

## Executive Finding

The drop is not caused by one clean bug. It is a sequence of mistakes:

1. We expanded too broadly into unproven lanes and symbols. The portfolio volume exploded from 179 deduped trades in week 1 to 601 in week 2, and week 2 lost `-2327.71 AED`.
2. The worst bleed came from weak lanes, especially `symbol_normalized_round_retest_v0`, not from the one profitable A1 XAU evening lane.
3. We then added session gates, kill switches, mutexes, and account-specific controls. Those were reasonable safeguards, but they changed the live rules.
4. The A1 XAU `920101` lane that produced the strongest evidence is missing from the current A1 standard profile inspection. A1 currently shows standard executor charts for EURUSD and GBPUSD, but not XAUUSD.
5. A2 is not a replica of old A1. It is a stricter clean account: XAU-only, evening-only, one open position, cost cap, spread cap, separate terminal/account. Its `-55.09 AED` result is a small, different-window, different-rule sample.
6. A3 was a separate repair experiment, not the same EA. It lost `-738.38 AED`, with `a3_breakout_plain` alone at `14 losses / 0 wins / -510.44 AED`, and is now correctly paused.

Plain English: **we started comparing different machines as if they were the same strategy. They were not.**

## Evidence Files Read

| Evidence | Path |
| --- | --- |
| Actual broker fills | `docs/review_exports/FRIDAY_DEMO_ACCOUNT_OBSERVER_REVIEW_2026_06_19/csv/PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv` |
| A2 direct history | `docs/review_exports/FRIDAY_DEMO_ACCOUNT_OBSERVER_REVIEW_2026_06_19/csv/A2_TIER1_ACCOUNT_HISTORY_2026_06_19_ROWS.csv` |
| Runtime chart inventory | `xau-usd/xauusd-phase1/outputs/reports/RUNTIME_CHART_INVENTORY_FORENSIC_2026_06_21.csv` |
| A1/A2 rule identity | `xau-usd/xauusd-phase1/outputs/reports/A1_A2_920101_RULE_IDENTITY_RECONCILIATION_2026_06_20.md` |
| A1 goal/session guard update | `xau-usd/xauusd-phase1/outputs/reports/A1_GOAL_LOCK_AND_SESSION_GUARD_UPDATE_2026_06_18.md` |
| A1 daily guardian attachment | `xau-usd/xauusd-phase1/outputs/reports/A1_DAILY_PROFIT_FLOOR_GUARDIAN_ATTACHMENT_2026_06_18.md` |
| A3 reconciliation | `xau-usd/xauusd-phase1/outputs/reports/A3_RUNTIME_AUTH_RECONCILIATION_2026_06_19.md` |
| A3 account history | `xau-usd/xauusd-phase1/outputs/reports/A3_REPAIR_LANE_ACCOUNT_HISTORY_2026_06_19.md` |
| Standard executor source | `xau-usd/xauusd-phase1/mt5/Experts/Phase2ExperimentalDemoExecutor.mq5` |
| Repair executor source | `xau-usd/xauusd-phase1/mt5/Experts/Phase2ExperimentalDemoRepairExecutor.mq5` |

## Timeline Of What Actually Happened

| Period | Deduped trades | PnL AED | Win rate | Interpretation |
| --- | ---: | ---: | ---: | --- |
| Jun 1-7 | 179 | `+44.77` | 39.1% | Nearly flat. The system was not strongly profitable at total portfolio level. |
| Jun 8-14 | 601 | `-2327.71` | 33.8% | Volume exploded and weak lanes flooded the book. This is where most damage happened. |
| Jun 15-19 | 467 | `-858.82` | 33.0% | Still negative, but later guardrails started cutting activity. |

The owner's feeling that trade count later dropped is true, but the big loss was not caused by the drop. The largest loss came after trade count expanded.

## Where The Losses Came From

Deduped actual broker fills by candidate:

| Candidate | Trades | PnL AED | What it means |
| --- | ---: | ---: | --- |
| `symbol_normalized_round_retest_v0` | 595 | `-2115.57` | Main portfolio bleed. This lane should not have been allowed to trade at this scale. |
| `swing_breakout_retest_v0` | 88 | `-358.31` | Same-family variant did not diversify. |
| `breakout_retest` | 385 | `-357.32` | Overall negative across all symbols/sessions, despite one strong XAU evening pocket. |
| `session_extreme_retest_v0` | 130 | `-184.15` | Weak lane, later repair/quarantine focus was justified. |
| `round_number_retest_v0` | 40 | `+16.86` | Near flat, not enough to carry the book. |

Worst lane/symbol combinations:

| Lane | Trades | PnL AED |
| --- | ---: | ---: |
| `920301 / symbol_normalized_round_retest_v0 / XAUUSD` | 458 | `-1381.11` |
| `920304 / symbol_normalized_round_retest_v0 / GBPUSD` | 54 | `-586.43` |
| `920104 / breakout_retest / GBPUSD` | 108 | `-584.07` |
| `920102 / breakout_retest / EURUSD` | 120 | `-447.49` |
| `920201 / swing_breakout_retest_v0 / XAUUSD` | 28 | `-141.92` |

The one genuinely positive slice was narrow:

| Slice | Trades | PnL AED | Win rate | PF |
| --- | ---: | ---: | ---: | ---: |
| A1 `920101 / breakout_retest / XAUUSD`, all sessions | 113 | `+708.59` | 46.02% | 1.45 |
| A1 `920101 / breakout_retest / XAUUSD`, evening | 27 | `+701.86` | 66.67% | 3.75 |

So the profitable thing was not "all breakout", not "all XAU", not "all accounts", and not "all sessions". It was **A1 XAU breakout in the evening**.

## What Is Broken Right Now

### 1. A1's profitable XAU standard executor is missing from the inspected current profile

Current read-only runtime inventory shows A1 standard broker-action charts:

| Account lane | Chart | Symbol | EA | Candidate | Broker action | Session hours |
| --- | --- | --- | --- | --- | --- | --- |
| A1 standard | `chart01.chr` | EURUSD | `Phase2ExperimentalDemoExecutor` | `breakout_retest` | true | `12 -> 1` |
| A1 standard | `chart02.chr` | GBPUSD | `Phase2ExperimentalDemoExecutor` | `breakout_retest` | true | `12 -> 1` |
| A1 standard | `chart18.chr` | XAUUSD | `Phase2ExperimentalDemoRepairExecutor` | `symbol_normalized_round_retest_v0_repair_v1` | true | `12 -> 1` |
| A1 standard | `chart19.chr` | XAUUSD | `Phase2ExperimentalDemoRepairExecutor` | `session_extreme_retest_v0_repair_v1` | true | `12 -> 1` |
| A1 standard | `chart26.chr` | XAUUSD | `Account1DailyProfitFloorGuardian` | close-only guardian | false/no entries | n/a |

No active A1 `Phase2ExperimentalDemoExecutor` chart was found for `InpTargetSymbol=XAUUSD` and account `1025742`.

This directly explains why the exact A1 XAU `920101` lane that made the money is not currently behaving like it did before: **it does not appear to be attached in the current inspected A1 profile.**

### 2. The June 18 maintenance report confirms the same gap

`A1_GOAL_LOCK_AND_SESSION_GUARD_UPDATE_2026_06_18.md` says the standard executor restore brought back only:

- `chart01.chr` EURUSD standard executor
- `chart02.chr` GBPUSD standard executor

It updated XAU repair charts and WR50/guardian charts, but not an XAU standard `Phase2ExperimentalDemoExecutor` chart.

This is the strongest evidence of a concrete operational mistake: the script/report declared the standard executor charts "present or restored", but the restored standard chart was GBPUSD, not the profitable A1 XAU standard executor.

### 3. A2 is not old A1

A2 clean account currently has:

| Account lane | Chart | Symbol | EA | Candidate | Broker action | Session hours | Max open | Cost cap | Spread cap |
| --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| A2 Tier1 | `chart02.chr` | XAUUSD | `Phase2ExperimentalDemoExecutor` | `breakout_retest` | true | `12 -> 15` | 1 | 0.30R | 75 points |

A2's order log confirms the stricter rule:

| A2 guard reason | Count |
| --- | ---: |
| `server_hour_session_gate` | 63 |
| `pass` | 12 |
| `open_instance_exposure_exists` | 9 |
| `terminal_or_account_trading_disabled` | 7 |

A2 took only 12 broker trades and lost `-55.09 AED`. That does not disprove A1's old profitable lane because A2 did not run the same chart set, the same calendar window, or the same guard set.

### 4. A3 was not the same strategy either

A3 was a repair/variant account. Its direct account-history report shows:

| A3 candidate | Trades | Result |
| --- | ---: | --- |
| `a3_breakout_plain` | 14 | `0W / 14L / -510.44 AED` |
| `a3_breakout_improved` | 8 | `1W / 7L / -156.04 AED` |
| `a3_round_retest_guarded_v1` | 26 | `10W / 16L / -38.20 AED` |
| `a3_round_retest_structured_v1` | 25 | `10W / 15L / +34.97 AED` |

A3 is now paused, which is correct. But its bad performance should not be used to judge the original A1 `920101` evening core.

## Why Trade Count Dropped

Some of the drop was intentional and some was accidental.

Intentional blockers:

| Change | Effect |
| --- | --- |
| Session gates | Block morning/afternoon or non-evening windows. |
| Daily profit-floor guardian | After +100 AED day lock, writes shared kill switch and keeps A1 flat for the day. |
| Duplicate/family mutex | Blocks same-family stacked entries. |
| A2 max one open position | Blocks signals while a prior A2 exposure is open. |
| Repair filters | Block direction/time buckets in repair EAs. |

Accidental or bad comparability blockers:

| Issue | Effect |
| --- | --- |
| A1 XAU standard executor missing | The historical best A1 XAU lane is not currently active in inspected A1 profile. |
| A1 and A2 different session windows | A1 current standard charts use `12 -> 1`, A2 uses `12 -> 15`; not identical. |
| A2 cost/spread/open-position caps | A2 blocks trades A1 would have taken. |
| Magic reused across accounts | `920101` alone is not enough to identify A1 vs A2; account/terminal/file source must be included. |
| Status pages can lag runtime truth | Old "attached candidates" summaries can look valid while actual chart profiles differ. Runtime inventory must be the authority. |

## What We Did Wrong

1. **We treated labels as identity.** Same candidate name or same magic number does not mean same runtime rule. Account, terminal, chart profile, session window, cost cap, spread cap, kill switch, max-open rules, and source hash all matter.
2. **We let weak lanes trade too much.** The main loss was not mysterious: `symbol_normalized_round_retest_v0` alone lost `-2115.57 AED` deduped.
3. **We changed too many things at once.** Session gates, repair lanes, mutexes, profit floors, A2 clean account, and A3 variants all arrived close together. That destroyed clean attribution.
4. **We allowed runtime drift.** A3 had unauthorized/paused-but-trading behavior before it was fixed. Current reconciliation now catches this, but it came after losses.
5. **We did not require rule-identity before comparing accounts.** A2 was judged against A1's old profitable sample despite not being the same runtime configuration.
6. **A maintenance restore missed the important chart.** Current evidence indicates A1 XAU standard `breakout_retest` was not restored/active after the A1 goal/session maintenance.
7. **We let the dashboard become softer than runtime truth.** The real authority must be current MT5 profile inventory plus broker fills, not historical candidate lists.

## What We Did Not Do Wrong

1. The later guardrails were not stupid. They reduced a real bleed. The problem is that they were applied after the damage and then compared against older, less-restricted behavior.
2. Pausing A3 is correct. A3 had real evidence of failure and drift.
3. Cutting morning/afternoon was directionally justified by realized results. But if we use those filters, we must explicitly call the new system a different rule.
4. The A1 profit-floor guardian does what it was asked to do: protect a daily gain. It also censors later trades, so it should not be used during pure edge-measurement unless we accept that tradeoff.

## Corrective Actions Before Any More Runtime Experiments

1. **Do a no-trade runtime identity audit before every Monday start.**
   - Account, terminal path, chart file, symbol, EA, candidate, magic, lot, broker-action flag, dry-run flag, session gate, spread/cost caps, max-open caps, kill-switch file, source hash.

2. **Restore/attach A1 XAU `920101` only through an owner-approved maintenance packet.**
   - Do not silently edit it.
   - Produce before/after chart tables.
   - Prove startup logs after attach.
   - Confirm it is exactly the shared forward-test rule.

3. **Do not compare A1 and A2 until they run the same shared rule.**
   - Same symbol: XAUUSD.
   - Same candidate: `breakout_retest`.
   - Same session: Dubai evening only if that is the locked test.
   - Same max-open rule.
   - Same spread/cost rule.
   - Same duplicate mutex behavior.
   - Same daily profit/loss lock logic, or explicitly document the difference.

4. **Keep A3 paused.**
   - A3 should not resume broker action until a new, pre-registered, reviewer-approved rule exists.

5. **Stop all non-core bleeding lanes unless they are observer-only.**
   - Especially `symbol_normalized_round_retest_v0` and broad GBP/EUR breakout variants, which were major realized losses.

6. **Make runtime inventory the dashboard source of truth.**
   - If status says an EA is attached but the profile scan cannot find the chart, status must show `MISSING_RUNTIME_CHART`.

7. **Separate profit-protection from edge measurement.**
   - If we use the +100 AED guardian, we are testing a daily-lock trading plan, not raw strategy edge. That is fine, but it must be declared.

## Recommended Next Move

Do not make more strategy changes first. The next move should be a controlled maintenance prep report:

1. Generate a current A1/A2 profile inventory.
2. Draft the exact shared XAU evening `920101` rule.
3. Show what will be changed before touching MT5.
4. After owner approval, restore A1 XAU and align A2 only if both are meant to run the same forward test.
5. Start next week with only that clean test active, and leave all other lanes observer-only or paused.

The shortest honest answer: **we did not just lose because the market changed. We also lost because we expanded weak lanes, then changed runtime rules piecemeal, and the exact A1 XAU chart that made the money is now missing from the inspected active profile. Fix runtime identity before touching strategy logic again.**
