# XAUUSD Dynamic Profit-Lock Proposal - 2026-06-17

Status: `ANALYSIS_ONLY_PROPOSAL`

No MT5 terminal, chart, EA, preset, order, position, lot, guard, or runtime setting was changed.

## Problem

Several XAUUSD trades moved meaningfully into profit, then reversed and closed at SL. This is not just one visible trade. The current 10-second position-path evidence shows a repeating "green then lost" pattern.

Source evidence:

- Actual broker history: `xau-usd/xauusd-phase1/outputs/reports/PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv`
- Position path snapshots: `C:/MT5PortablePositionPathObserver/MQL5/Files/position_path_log_202606*.csv`
- MFE/MAE report: `xau-usd/xauusd-phase1/outputs/reports/MFE_MAE_2026_06_16.md`

## Evidence Summary

The refreshed MFE/MAE report covers `356` closed XAUUSD trades that had matching 10-second path snapshots.

| Measure | Value |
| --- | ---: |
| Covered closed XAUUSD trades | 356 |
| Control PnL on covered rows | -1638.80 AED |
| Control win rate | 35.67% |
| Losers that reached at least +0.50R first | 73 / 229 losers = 31.88% |
| Losers that reached at least +0.75R first | 52 / 229 losers = 22.71% |
| Losers that reached at least +1.00R first | 29 / 229 losers = 12.66% |
| Losers that reached at least +1.25R first | 9 / 229 losers = 3.93% |

Interpretation: enough losing trades first went green that exit management is worth testing. This is not proof to deploy immediately; it is proof to run a shadow profit-lock experiment.

## Exact 10-Second Path Replay

These results replay each proposed rule through the actual 10-second unrealized-R path, so winners that would have been cut early are counted as affected.

| Rule | Covered trades | Win rate | Replay PnL AED | Delta vs control | Changed trades | Comment |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Control / current behavior | 356 | 35.67% | -1638.80 | 0.00 | 0 | Existing broker outcomes |
| BE after +1.00R | 356 | 32.30% | -1058.55 | +580.25 | 41 | Saves some losses but can turn later winners into flat exits |
| Lock +0.50R after +1.00R | 356 | 43.82% | -742.95 | +895.85 | 55 | Stronger than BE; keeps real profit after a strong move |
| Lock +0.25R after +0.75R | 356 | 50.28% | -525.64 | +1113.16 | 89 | Best path replay result, but affects many trades and needs fresh forward proof |
| Lock +0.80R after +1.25R | 356 | 38.20% | -1136.87 | +501.93 | 23 | Targets the exact near-TP reversal pattern, less invasive |
| Full exit at +1.00R | 356 | 43.82% | -1130.85 | +507.95 | 156 | Caps too many winners; not preferred |
| 50% partial at +1.00R + runner BE | 356 | 43.82% | -1094.70 | +544.10 | 156 | Operationally awkward at 0.01 lot and drags winners |

## June 17 Flip Cases

These are examples from 2026-06-17 where the trade went above +1R but finished as a loss.

| Ticket | EA | Side | Entry | Actual PnL | Max green | BE at +1R | +0.50R lock | +0.80R near-TP lock |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 4125120 | swing_breakout_retest_v0 | BUY | 2026-06-17 18:55 | -92.42 | +1.3377R | 0.00 | +46.08 | +73.73 |
| 4125122 | session_extreme_retest_v0 | BUY | 2026-06-17 18:55 | -92.53 | +1.3349R | 0.00 | +46.14 | +73.82 |
| 4115557 | breakout_retest | BUY | 2026-06-17 09:45 | -11.17 | +1.0030R | 0.00 | +6.08 | n/a |
| 4119012 | symbol_normalized_round_retest_v0 | SELL | 2026-06-17 13:40 | -28.55 | +1.0420R | 0.00 | +14.44 | n/a |

For the visible 18:55 evening flip, a near-TP lock at +0.80R after +1.25R would have changed roughly `-185 AED` across the two covered A1 clone trades into about `+148 AED`, a swing of about `+333 AED`. A +0.50R lock after +1.00R would have changed them into about `+92 AED`, a swing of about `+277 AED`.

## What We Should Not Do

Do not jump straight to partial close.

Reasons:

- 0.01 lot partial close can be broker-volume awkward.
- Prior exact-path work already showed partial close dragged winners.
- The new exact path replay again shows full/partial early exits change many trades.

Do not blindly reduce TP to +1R.

Reason: full exit at +1R improved this losing sample, but it caps the exact winners that make the system worth running. It is a blunt tool.

## Best Candidate Fix

The best next fix is a shadow-only dynamic profit-lock ladder:

```text
Arm 1: if unrealized profit reaches +0.75R, virtual protected floor = +0.25R
Arm 2: if unrealized profit reaches +1.00R, virtual protected floor = +0.50R
Arm 3: if unrealized profit reaches +1.25R, virtual protected floor = +0.80R
Keep original TP at +1.50R
Keep original SL until a floor is armed
Never widen risk
Apply one shared family-level lock to duplicate/co-fired trades
```

The rule is designed to solve the exact pain:

- It does not interfere with trades that never move in our favor.
- It keeps the original 1.5R target alive.
- It converts strong green-then-lost trades into smaller wins.
- It is less destructive than full exit at +1R.
- It can be shadow-tested from position-path logs before touching live/demo EAs.

## Additional Candidate Rule

A second, more conservative rule can be tracked beside the ladder:

```text
Near-TP fail-safe:
If unrealized profit reaches +1.25R and then gives back to +0.80R, close/lock.
```

This rule is less aggressive. It only affected `23` of `356` covered trades in replay. It directly handles the "almost TP, then reversal to SL" case, but misses many +0.75R to +1.00R givebacks.

## Recommended Implementation Path

1. Add shadow profit-lock scoring to the path observer report.
2. Track control vs virtual exits for one fresh week:
   - current broker result
   - BE after +1R
   - +0.50R lock after +1R
   - +0.25R lock after +0.75R
   - +0.80R near-TP lock after +1.25R
3. Score by account, EA, session, direction, and duplicate family.
4. Only promote if the rule improves net PnL and does not destroy evening winners.
5. If promoted later, implement as a separate guardian/exit-manager EA, not by editing each entry EA.

## Current Recommendation

Use the dynamic profit-lock ladder as the primary shadow candidate.

Do not deploy it to broker-action yet. The evidence is strong enough to test, not strong enough to change live demo behavior immediately.

The trade-off is clear:

- We can reduce the painful "green then lost" cases.
- We may also exit some trades before they eventually recover to TP.
- The exact 10-second path replay suggests the trade-off is favorable, but it must survive a fresh forward week.
