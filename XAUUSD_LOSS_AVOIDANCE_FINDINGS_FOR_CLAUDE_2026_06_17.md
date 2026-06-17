# XAUUSD Loss-Avoidance Findings For Claude Review - 2026-06-17

## Purpose

We want to reduce losing trades across all demo accounts without cutting the trades that are actually carrying profit.

This document is for independent review. It is analysis only. It does not request or imply any live/runtime EA change.

## Current Evidence Base

Primary files used:

| Artifact | Purpose |
| --- | --- |
| `xau-usd/xauusd-phase1/outputs/reports/XAUUSD_DEDUPED_REAL_FILL_EVIDENCE_2026_06_16.md` | XAUUSD real broker fills, deduped signal analysis, protected breakout impact |
| `xau-usd/xauusd-phase1/outputs/reports/COST_GATE_VERIFICATION_REPORT_2026_06_16.md` | Cost-R buckets and cutoff behavior from real broker fills |
| `xau-usd/xauusd-phase1/outputs/reports/PHASE2_EA_WEAKNESS_SHADOW_REPORT.md` | Duplicate-hidden view, EA quarantine counterfactuals, session filters |
| `xau-usd/xauusd-phase1/outputs/reports/OBSERVER_SHADOW_POLICY_SCOREBOARD.md` | Broker-joined observer scoreboard for shadow policy groups |
| `GOLD_DAILY_TRACKING_WEEK_2026_06_15.md` | Day-by-day gold tracking and regime warnings |

## Main Finding

The losing trades are not random. They are concentrated in repeatable clusters:

1. Round-family EAs are the main persistent drain.
2. XAUUSD afternoon is repeatedly weak.
3. Duplicate same-family stacking inflates exposure.
4. High cost-R trades are dangerous, especially above roughly `0.11` to `0.12R`.
5. The profitable cluster is breakout-family, especially evening/night.

The goal should be to block the bad clusters while explicitly protecting the profitable breakout evening/night cluster.

## Key Numbers

From `XAUUSD_DEDUPED_REAL_FILL_EVIDENCE_2026_06_16.md`:

| Scenario | Rows | Win Rate | PnL AED |
| --- | ---: | ---: | ---: |
| Raw closed XAUUSD fills | 1163 | 39.29% | +649.74 |
| Deduped selected unique signals | 586 | 37.80% | -554.52 |
| Dedup remove round selected | 154 | 41.18% | +804.89 |
| Dedup breakout core only | 112 | 47.75% | +1059.34 |
| Dedup breakout evening/night only | 79 | 52.56% | +1027.32 |
| Dedup no afternoon | 504 | 39.40% | -31.49 |
| Dedup no morning/afternoon | 368 | 40.66% | +179.47 |

Important interpretation:

- Raw PnL looks better because duplicate stacking multiplies some winning trades.
- Deduped rows are better for judging signal quality.
- Removing round-family converts the deduped book from negative to positive.
- Breakout core alone is the best current XAUUSD evidence.
- Breakout evening/night almost preserves the whole breakout-core PnL with fewer trades.

## Candidate And Family Evidence

From the deduped XAUUSD evidence:

| Family / Candidate | Deduped Rows | Win Rate | PnL AED | Interpretation |
| --- | ---: | ---: | ---: | --- |
| `breakout_core` | 112 | 47.75% | +1059.34 | Strongest protected cluster |
| `breakout_retest` | 101 | 47.00% | +892.89 | Main positive candidate |
| `swing_breakout_retest_v0` | 11 | 54.55% | +166.45 | Positive but smaller sample |
| `round_family` | 432 | 36.60% | -1359.41 | Main damage source |
| `symbol_normalized_round_retest_v0` | 410 | 36.61% | -1270.55 | Largest repeat loser |
| `round_number_retest_v0` | 22 | 36.36% | -88.86 | Also weak |
| `session_extreme_retest_v0` | 38 | 26.32% | -143.78 | Weak, but less central than round family |

## Session Evidence

From the deduped XAUUSD session view:

| Session | Rows | Win Rate | PnL AED | Interpretation |
| --- | ---: | ---: | ---: | --- |
| Evening 16:00-19:59 | 127 | 43.55% | +339.46 | Best broad session |
| Night 20:00-05:59 | 241 | 39.17% | -159.99 | Mixed overall, but breakout core performs well here |
| Morning 06:00-11:59 | 136 | 36.03% | -210.96 | Weak |
| Afternoon 12:00-15:59 | 82 | 28.05% | -523.03 | Clearly weakest |

From Day 2 daily scan:

| Session | Trades | Win Rate | PnL AED 0.01 Normalized |
| --- | ---: | ---: | ---: |
| Evening | 28 | 50.00% | +184.99 |
| Afternoon | 16 | 18.75% | -181.26 |

## Cost Evidence

From `COST_GATE_VERIFICATION_REPORT_2026_06_16.md`:

| Cost-R Bucket | Signals | Win Rate | PnL AED 0.01 |
| --- | ---: | ---: | ---: |
| `<=0.05` | 193 | 42.5% | +288.93 |
| `0.05-0.07` | 162 | 43.8% | +198.14 |
| `0.07-0.09` | 131 | 41.2% | +61.65 |
| `0.09-0.11` | 85 | 30.6% | -408.86 |
| `0.11-0.13` | 54 | 37.0% | -147.77 |
| `>0.13` | 79 | 29.1% | -369.34 |

Cost interpretation:

- Cheap trades are not perfect, but expensive trades are clearly dangerous.
- The report says cumulative results are positive through about `0.11R` and non-positive by `0.12R`.
- A cost cap should be treated as a veto layer, not a standalone strategy.

## Proposed Loss-Avoidance Logic

Recommended guard logic to test in shadow first:

```text
IF family = round_family
    BLOCK or observer-only

ELSE IF symbol = XAUUSD
AND family = breakout_core
AND session in Evening or Night
AND estimated_cost_r <= 0.11 or 0.12
AND no same-family duplicate already exists across accounts for the current M5 bar
    ALLOW

ELSE
    OBSERVE / shadow-only
```

## Across-Account Duplicate Control

The current accounts can stack similar trades. The guard should operate across accounts, not only inside each EA.

Suggested duplicate key:

```text
symbol + direction + family + M5 bar
```

Suggested priority:

```text
1. breakout_retest
2. swing_breakout_retest_v0
3. all other experimental lanes remain observer-only unless separately approved
```

This avoids three accounts independently taking the same family idea at the same time.

## Protected Cluster Check

The report explicitly tested whether the proposed broad filters damage the profitable breakout evening/night cluster:

| Rule | Protected Rows Before | Protected Rows After | Protected PnL Before | Protected PnL After |
| --- | ---: | ---: | ---: | ---: |
| round_family_quarantine | 79 | 79 | +1027.32 | +1027.32 |
| no_afternoon | 79 | 79 | +1027.32 | +1027.32 |
| evening_night_only | 79 | 79 | +1027.32 | +1027.32 |

This is why the round-family and afternoon filters look safer than a broad trend or direction filter.

## What We Should Not Overclaim Yet

Do not hard-block shorts yet.

Reason:

- The current tracking week has two up-days so far.
- On up-days, shorts losing may simply mean the market was rising.
- We still need a down-day or range-day to prove whether the losing side flips.

So the current evidence supports:

```text
Round family is weak.
Afternoon is weak.
High cost-R is dangerous.
Breakout evening/night is protected.
```

It does not yet prove:

```text
All shorts are bad.
All counter-trend trades are bad in every regime.
```

## Recommended Promotion Path

1. Keep current rules as analysis/shadow until the week closes.
2. Use deduped real fills as the main decision view.
3. Promote only filters that improve:
   - PnL
   - profit factor
   - win rate or at least do not materially worsen it
   - best-day-removed robustness
   - protected breakout impact
4. If promoted, implement as a fleet-level guard/router, not by changing every EA separately.

## Questions For Claude

Please review and challenge the following:

1. Is the conclusion to quarantine `round_family` justified by the deduped real-fill evidence?
2. Is `breakout_core evening/night only` a valid protected cluster, or is the sample too small?
3. Is `0.11R` to `0.12R` a reasonable cost veto threshold, or should it be lower/higher?
4. Does the proposed across-account duplicate key miss any important duplicate cases?
5. Should the guard use `family + direction + M5 bar`, or should entry price/level proximity also be included?
6. Are we overfitting to recent demo behavior by preferring evening/night?
7. Which rule is safest to promote first if only one can be promoted?
8. What additional evidence would you require before changing runtime EAs?
9. How should we measure whether profitable trades are being accidentally blocked?
10. Should `session_extreme_retest_v0` be quarantined now or kept under shadow observation?

## Current Preferred Answer

The first runtime rule, if approved later, should be:

```text
Quarantine round-family from broker action, keep it observer-only.
```

Reason:

- It removes the largest losing family.
- It does not touch protected breakout evening/night trades.
- It is less regime-sensitive than direction filters.
- It is easier to explain and audit than a complex trend rule.

Second rule:

```text
Fleet-level duplicate family mutex across all accounts.
```

Third rule:

```text
Cost-R veto around 0.11R to 0.12R, confirmed by forward data.
```

Fourth rule:

```text
XAUUSD afternoon block or severe reduction, but only after the week confirms it across regimes.
```

## Boundary

This document is for review only.

No MT5 runtime changes, EA changes, preset changes, order changes, chart changes, or account changes are authorized by this document.

---

## Post-Claude Canonical Recut - 2026-06-17

After Claude's review, we generated a one-universe report so family, session, duplicate, protected-cluster, and cost evidence are all tied back to the same canonical XAUUSD deduped signal set.

New artifact:

| Artifact | Purpose |
| --- | --- |
| `xau-usd/xauusd-phase1/outputs/reports/XAUUSD_CANONICAL_LOSS_AVOIDANCE_2026_06_17.md` | Canonical 586-row loss-avoidance analysis |
| `xau-usd/xauusd-phase1/outputs/reports/XAUUSD_CANONICAL_LOSS_AVOIDANCE_2026_06_17_ROWS.csv` | Enriched canonical rows with ticket, cost, and guard tags |

### Canonical Universe

| Metric | Value |
| --- | ---: |
| Canonical deduped XAUUSD rows | 586 |
| Broker-ticket matched rows | 586 |
| Cost-matched rows | 586 |
| Cost-known rows | 435 |
| Cost-missing rows | 151 |

### What Stayed Strong

| Scenario | Kept Rows | Kept Win Rate | Kept PnL AED | Delta vs Baseline | Protected Breakout Removed |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline canonical deduped XAUUSD | 586 | 37.80% | -554.52 | n/a | n/a |
| Round-family quarantine | 154 | 41.18% | +804.89 | +1359.41 | 0 |
| Breakout core only | 112 | 47.75% | +1059.34 | +1613.86 | 0 |
| Protected breakout evening/night cluster | 79 | 52.56% | +1027.32 | +1581.84 | 0 |
| No afternoon | 504 | 39.40% | -31.49 | +523.03 | 0 |

Interpretation:

- Round-family quarantine remains the strongest first rule.
- It does not remove the protected breakout evening/night cluster.
- Afternoon remains weak, but still needs regime confirmation before runtime promotion.
- Breakout evening/night should be protected, not used as an overfit "only trade this window" rule yet.

### Cost Correction

The canonical recut confirms Claude's warning: the earlier cost threshold was measured on a different universe.

Cost on the same 586-row universe uses only 435 cost-known rows:

| Cost Bucket | Rows | Win Rate | PnL AED | Notes |
| --- | ---: | ---: | ---: | --- |
| `<=0.05` | 100 | 39.58% | -96.22 | Not cleanly positive on this universe |
| `0.05-0.07` | 101 | 42.57% | +35.73 | Slightly positive |
| `0.07-0.09` | 82 | 42.68% | +128.45 | Best bucket here |
| `0.09-0.11` | 56 | 32.14% | -196.06 | Weak |
| `0.11-0.13` | 32 | 34.38% | -117.51 | Weak |
| `>0.13` | 64 | 28.12% | -315.52 | Clearly bad |

Updated cost conclusion:

```text
Cost is useful as a worst-tier veto, especially >0.13R, but the exact threshold remains fragile.
Do not promote a hard 0.11-0.12R cutoff yet.
```

### Updated Promotion Order

1. **Round-family quarantine** - still strongest; first candidate for owner/reviewer approval.
2. **Cross-account exposure mutex** - use `symbol + direction + bar + level band`; keep family for attribution only.
3. **Afternoon reduction** - promising but requires at least one non-up day before calling it regime-independent.
4. **Worst-tier cost veto** - shadow only for now, likely around `>0.13R`; do not use as primary rule yet.
5. **Session-extreme quarantine** - continue shadowing; not enough evidence to promote before round-family.

### Updated Non-Negotiables

- Do not hard-block shorts yet.
- Do not route only evening/night yet.
- Do not compose rule expectancies from mixed universes.
- Do not judge a filter by losers blocked alone; always report winners clipped, protected-cluster impact, and best-day-removed PnL.

### Current Best Single Action

If we choose only one practical rule to move toward approval, it remains:

```text
Round-family broker-action quarantine, fleet-wide, reversible, with observer-only logging preserved.
```

This is the cleanest way to avoid many losing trades without affecting the profitable breakout evening/night cluster.

---

## Account-Focus Recut - A1 Lab vs A2/A3 Production-Style

The owner clarified that A1 is a noisy test/lab account and that A2/A3 are the accounts we should focus on for production-style evidence.

New artifact:

| Artifact | Purpose |
| --- | --- |
| `xau-usd/xauusd-phase1/outputs/reports/XAUUSD_ACCOUNT_FOCUS_VIEW_2026_06_17.md` | Separates A1 lab rows from A2/A3 production-style rows |
| `xau-usd/xauusd-phase1/outputs/reports/XAUUSD_ACCOUNT_FOCUS_VIEW_2026_06_17_ROWS.csv` | Normalized account-attributed XAU rows |
| `xau-usd/xauusd-phase1/outputs/reports/A2_TIER1_ACCOUNT_HISTORY_2026_06_17.md` | Fresh read-only A2 MT5 account-history reconciliation |
| `xau-usd/xauusd-phase1/outputs/reports/A3_REPAIR_LANE_ACCOUNT_HISTORY_2026_06_17.md` | Fresh read-only A3 MT5 account-history reconciliation |

### Tracking Summary

This now uses fresh read-only MT5 account-history exports for A2 and A3. The older A3 Day 1 / Day 2 CSV rows remain raw evidence, but they no longer drive the current A3 account verdict.

| View | Rows | Win Rate | PnL AED 0.01 | PF |
| --- | ---: | ---: | ---: | ---: |
| All tracked rows | 203 | 40.39% | +380.63 | 1.15 |
| A1 lab observation | 140 | 41.43% | +350.82 | 1.22 |
| A2+A3 production-style | 63 | 38.10% | +29.81 | 1.03 |
| A2 clean account | 8 | 50.00% | +104.92 | 1.81 |
| A3 experiment account | 55 | 36.36% | -75.11 | 0.91 |

### Production-Style View: A2 + A3

| Slice | Rows | Win Rate | PnL AED 0.01 | PF |
| --- | ---: | ---: | ---: | ---: |
| A2 clean account | 8 | 50.00% | +104.92 | 1.81 |
| A3 experiment account | 55 | 36.36% | -75.11 | 0.91 |
| Breakout core | 12 | 33.33% | +33.04 | 1.16 |
| Round family | 51 | 39.22% | -3.23 | 1.00 |
| Evening | 15 | 46.67% | +128.08 | 1.54 |
| Night | 17 | 52.94% | +126.18 | 1.57 |
| Afternoon | 15 | 13.33% | -217.84 | 0.23 |
| Morning | 16 | 37.50% | -6.61 | 0.97 |

### Updated Interpretation

- A1 remains useful for weakness discovery, but it should not drive production-style approval.
- The long-window canonical report is currently A1-only after account matching, so its round-family quarantine finding is a strong **lab finding**.
- A2 fresh MT5 history is clean and positive so far: 8 closed XAU trades, 4 wins / 4 losses, +104.92 AED closed PnL.
- A3 fresh MT5 history is negative on closed PnL: 55 closed XAU trades, 20 wins / 35 losses, -75.11 AED closed PnL. One open A3 position was present at export time and is tracked separately in the A3 report.
- A3 still contains old retired round-family residuals, but the fresh MT5 export makes that exact instead of relying on stale partial CSVs.
- For A2/A3, the biggest immediate focus is not removing A1 round-family. It is collecting clean A2 breakout-only and A3 breakout A/B rows.

### Current Decision Shift

Because A1 is explicitly a lab account:

```text
Do not rush to remove round-family from A1.
Use A1 to observe bad behavior and stress-test filters.
Use A2/A3 to judge production-style readiness.
```

The practical next evidence target is:

```text
Fresh A2 breakout-only rows + fresh A3 breakout A/B rows, preferably across multiple sessions and at least one non-up gold day.
```
