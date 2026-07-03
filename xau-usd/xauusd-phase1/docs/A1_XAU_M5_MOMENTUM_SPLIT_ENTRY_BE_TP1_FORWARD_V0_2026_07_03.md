# A1 XAU M5 Momentum Split-Entry BE-on-TP1 Forward Test V0

Date: 2026-07-03
Status: APPROVED_FOR_A1_SMALL_DEMO_ATTACH
Scope: A1 demo-only experimental lane. No live trading. No canonical Phase 2 approval.

## Purpose

This spec freezes the repaired A1 XAU M5 Momentum split-entry candidate after the BE-on-TP1 fix. The goal is to test the exact candidate on fresh demo data without fitting to May or any other known losing pocket.

The standing anti-overfit rule is part of this spec:

- Do not add a May-only filter.
- Do not tune hours, thresholds, direction rules, target R, stop rules, or risk rules after seeing the recent 3-month ledger.
- Do not promote this lane because of a single recent window.
- Judge the lane on fresh forward evidence and the pre-registered gates below.

## Candidate Identity

EA: `A1XauM5MomentumContinuationExecutor.mq5`

Symbol/timeframe: `XAUUSD`, M5

Forward lane type: split-entry, two minimum-lot tickets per signal:

- `_TP1`: first ticket targets `0.70R`
- `_RUN`: runner ticket targets `2.00R`
- Runner SL moves to breakeven when TP1 closes at TP, with the threshold-based BE rule retained as backup.

Dedicated proposed forward-test magic: `932280`

Dedicated proposed order comment prefix: `A1_XAU_M5_MOM_SPLIT_BE`

Dedicated proposed kill-switch file: `a1_xau_m5_momentum_split_be_tp1_kill_switch.txt`

These identifiers must not be reused by any other lane.

## Component Priority

The forward signal set is a fixed priority stack. If multiple components would fire, keep only the first component in this order:

1. `risk_norm_split20_v6_max2_all8`
2. `risk_norm_split20_freq_weak_hours_all8`
3. `risk_norm_split20_v13_rr0p7_all8_22`

This tie-break priority is frozen. It must not be changed after owner acceptance.

Runtime enforcement is required. The three component charts must use the shared MT5 GlobalVariable signal-claim guard:

```text
InpSignalClaimEnabled=true
InpSignalClaimNamespace=A1MOM_SPLIT_BE
InpSignalClaimWindowMinutes=4
InpSignalClaimGraceSeconds=2
```

Component priority mapping:

```text
risk_norm_split20_v6_max2_all8: priority 1
risk_norm_split20_freq_weak_hours_all8: priority 2
risk_norm_split20_v13_rr0p7_all8_22: priority 3
```

If multiple components signal the same symbol, direction, and M5 signal bar inside the four-minute claim window, only the highest-priority component may send the split-entry order pair. Lower-priority components must log `signal_claimed_by_higher_priority` and skip. Without this runtime claim guard, the live/demo lane would not match the reviewed offline book.

## Frozen Component Inputs

### `risk_norm_split20_v6_max2_all8`

```text
InpDirectionMode=1
InpUseH1TrendFilter=true
InpH1TrendMinSlopePoints=0
InpUseH4TrendFilter=true
InpH4TrendMinSlopePoints=0
InpRiskReward=0.70
InpMaxEstimatedCostR=0.05
InpBlockedEntryHoursCsv=2,8,9,10,11,12,13,17,19,21,23
InpOnePositionPerMagic=false
InpMaxOpenPositionsPerMagic=4
InpMaxTradesPerDay=20
InpCooldownMinutes=3
InpUseRiskNormalizedLots=true
InpRiskAmountUsd=10.00
InpMaxRiskLots=0.05
InpSplitEntryEnabled=true
InpSplitEntryShadowOnly=false
InpSplitEntryFirstTargetR=0.70
InpSplitEntryRunnerTargetR=2.00
InpSplitEntryMoveRunnerSLToBE=true
InpSplitEntryUseMinLotPair=true
InpSignalClaimEnabled=true
InpSignalClaimNamespace=A1MOM_SPLIT_BE
InpSignalClaimPriority=1
InpSignalClaimWindowMinutes=4
InpSignalClaimGraceSeconds=2
```

### `risk_norm_split20_freq_weak_hours_all8`

```text
InpDirectionMode=1
InpUseH1TrendFilter=true
InpH1TrendMinSlopePoints=0
InpUseH4TrendFilter=true
InpH4TrendMinSlopePoints=0
InpRiskReward=0.70
InpMaxEstimatedCostR=0.05
InpBlockedEntryHoursCsv=2,8,9,10,11,12,17,22,23
InpMaxTradesPerDay=12
InpCooldownMinutes=5
InpUseRiskNormalizedLots=true
InpRiskAmountUsd=10.00
InpMaxRiskLots=0.05
InpSplitEntryEnabled=true
InpSplitEntryShadowOnly=false
InpSplitEntryFirstTargetR=0.70
InpSplitEntryRunnerTargetR=2.00
InpSplitEntryMoveRunnerSLToBE=true
InpSplitEntryUseMinLotPair=true
InpSignalClaimEnabled=true
InpSignalClaimNamespace=A1MOM_SPLIT_BE
InpSignalClaimPriority=2
InpSignalClaimWindowMinutes=4
InpSignalClaimGraceSeconds=2
```

### `risk_norm_split20_v13_rr0p7_all8_22`

```text
InpSignalMode=5
InpDirectionMode=0
InpUseH1TrendFilter=true
InpH1TrendMinSlopePoints=0
InpUseH4TrendFilter=true
InpH4TrendMinSlopePoints=0
InpRiskReward=0.70
InpMaxEstimatedCostR=0.05
InpBlockedEntryHoursCsv=0,2,4,8,9,10,11,12,16,19,20,22
InpBlockedShortEntryHoursCsv=13,14,15,17,18
InpM5TrendEmaFastPeriod=8
InpM5TrendEmaSlowPeriod=21
InpM5TrendSlopeBars=3
InpM5TrendMinSlopeAtr=0.03
InpM5TrendMaxDistanceAtr=1.20
InpMinRangeAtr=0.35
InpMinBodyFraction=0.30
InpLongCloseLocation=0.58
InpShortCloseLocation=0.42
InpMinThreeBarMoveAtr=0.10
InpMaxTradesPerDay=24
InpCooldownMinutes=0
InpUseRiskNormalizedLots=true
InpRiskAmountUsd=10.00
InpMaxRiskLots=0.05
InpSplitEntryEnabled=true
InpSplitEntryShadowOnly=false
InpSplitEntryFirstTargetR=0.70
InpSplitEntryRunnerTargetR=2.00
InpSplitEntryMoveRunnerSLToBE=true
InpSplitEntryUseMinLotPair=true
InpSignalClaimEnabled=true
InpSignalClaimNamespace=A1MOM_SPLIT_BE
InpSignalClaimPriority=3
InpSignalClaimWindowMinutes=4
InpSignalClaimGraceSeconds=2
```

## Evidence Before Forward Test

Recent exact MT5 Strategy Tester window: 2026-04-01 to 2026-06-30

Report: `outputs/reports/A1_XAU_M5_MOMENTUM_SPLIT_ENTRY_BE_TP1_RECENT3M_REVIEW_2026_07_03.md`

Signal-level result:

```text
Signals: 64
Win rate: 65.62%
Net: +345.78 USD
Profit factor: 1.58
Average win: +22.42 USD
Average loss: -28.37 USD
```

Ticket-level result:

```text
Tickets: 128
Win rate: 48.44%
Net: +345.78 USD
Profit factor: 1.58
Average win: +15.19 USD
Average loss: -9.94 USD
```

Month-level result:

```text
April 2026: +192.16 USD, 58.62% signal WR, PF 1.67
May 2026: -100.75 USD, 56.25% signal WR, PF 0.54
June 2026: +210.50 USD, 83.33% signal WR, PF 3.33
```

Interpretation:

- Recent evidence is test-worthy, not proof.
- May warns that win rate alone is insufficient; payoff shape must be monitored.
- May must not be separately optimized.
- The repaired BE-on-TP1 logic removed the recent `TP1 win / runner giveback / net-negative` bucket in the tested window.

## Long-Window Debt

The full 2022-07 to 2026-06 fixed rerun timed out on the V6/max2 component at 900 seconds because transaction-management logging makes that component slower. This is not treated as a pre-attach blocker, but it is required evidence debt.

Requirement:

- Re-run with timeout at least 3600 seconds and/or reduced per-transaction logging.
- Complete within the first 4 weeks of any forward test.
- If the repaired BE-on-TP1 version degrades the long-window book by more than 15% versus the unfixed split-entry baseline, pause the forward lane for review.

## Forward-Test Scope

Account: A1 demo only, unless owner separately approves a different isolated demo account.

Broker action: demo only.

Lot/exposure: this lane opens two minimum-lot tickets per signal. Owner must explicitly accept that one signal can lose both tickets.

Quantified exposure owner must accept before attach:

```text
Worst case per signal: approximately -36 USD at the 1800-point stop ceiling with two 0.01 tickets.
Typical losing signal from recent evidence: approximately -20 to -30 USD.
Recent 3-month average losing signal: -28.37 USD.
Approximately one-third of signals can lose both tickets before TP1.
InpMaxRiskLots=0.05 remains the tested input; because InpSplitEntryUseMinLotPair=true, typical large-stop XAU losses are dominated by the 2 x 0.01 broker-minimum pair rather than the risk-normalized target.
```

No real capital. No live account. No canonical Phase 2 pass.

No sibling variants may be changed or added during this lane's measurement window.

## Pre-Attach Conditions

All must be true before manual attach:

- Owner explicitly accepts 2 x 0.01 minimum-lot ticket exposure per signal.
- Owner explicitly accepts the quantified practical exposure above: worst case approximately -36 USD per failed signal, typical loss approximately -20 to -30 USD, and about one-third of signals may lose both tickets.
- Spec SHA256 is recorded.
- EA source SHA256 is recorded.
- Dedicated magic `932280` is confirmed unused.
- Dedicated comment prefix `A1_XAU_M5_MOM_SPLIT_BE` is confirmed unique.
- Dedicated kill-switch filename `a1_xau_m5_momentum_split_be_tp1_kill_switch.txt` is confirmed unique.
- Previous feature-guard draft use of `932280/932281` is treated as retired/superseded for deployment. It must not be attached while this split-entry lane owns `932280`.
- Runtime signal-claim smoke report is PASS.
- Attach packet renders exactly three components with priorities `1`, `2`, and `3`, all using the shared claim namespace.
- Package guard currency is confirmed as USD for this lane; no AED/USD mismatch.
- Start timestamp is pinned at the first post-attach fill.
- Existing production/demo lanes are not modified by this attach.

## Forward Sample

Minimum sample before judgment:

- At least 150 signals, or
- At least 16 weeks,
- whichever comes later.

Expected cadence from recent regime: about 1 signal per market day, active on roughly 44% of market days. This does not satisfy "multiple trades every day", but it is the current honest cadence of this filtered lane.

## Pass Gates

All required:

- Signal-level win rate >= 55%
- Profit factor >= 1.25
- Net profit > 0 after a 0.20 USD per-signal cost haircut
- Top 2% signal removal remains net-positive
- No single day contributes more than 30% of total net profit
- Signal-level average win / average loss ratio >= 0.70
- No safety, account, magic, or kill-switch violation

## Kill Gates

Any one triggers stop/review:

- Rolling 40-signal PF < 0.90
- Net negative after 80 closed signals
- Signal-level win rate < 45% after 80 closed signals
- Lane drawdown exceeds 2x recent-3M max drawdown until the long-window rerun recalibrates it
- Any wrong account, wrong symbol, wrong magic, wrong comment, or real-capital violation
- Any checksum/config drift after attach

No streak-only kill is allowed. A 3-signal losing day is normal for this lane.

## Review Cadence

Weekly:

- Export closed deals.
- Confirm magic/comment attribution.
- Confirm `_TP1` and `_RUN` comments survive broker records.
- Confirm BE-on-TP1 management events are present when applicable.
- Report signal-level and ticket-level results separately.
- Report month-to-date payoff shape, not just win rate.

Formal review:

- Week 4: health and config integrity only.
- End of sample: pass/kill decision.

## Owner Acceptance

I understand this is experimental demo only.

I understand this is not canonical Phase 2 approval.

I understand this is not live trading and not real capital.

I understand each signal can open two minimum-lot tickets and can lose both tickets.

I understand May 2026 will not be fitted separately.

Owner decision: APPROVE / DECLINE

Owner name:

Date/time Dubai:

Notes:

## Quantified Exposure Acceptance

Owner acceptance recorded from the project thread on 2026-07-03:

```text
I accept the quantified split-entry exposure and approve demo attach on A1
```

This acceptance applies only to the A1 demo split-entry BE-on-TP1 forward-test lane described in this document. It does not authorize live trading, real capital, canonical Phase 2 approval, or any parameter change outside this frozen spec.
