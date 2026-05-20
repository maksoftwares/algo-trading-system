# XAUUSD Master EA Plan v0.3 — Phase 0 Edge Validation First

**Document status:** Review-ready planning document  
**Version:** v0.3  
**Date:** 2026-05-20  
**Prepared for:** Second external review before any EA coding  
**Primary platform assumption:** MT5 / MQL5  
**Primary symbol:** XAUUSD  
**Core decision:** Phase 0 statistical edge validation must be completed before expert coding begins.

---

## Source Documents Integrated

This v0.3 plan incorporates and supersedes the prior planning direction from:

1. `xauusd_master_ea_plan_v0_2_review_ready.md`
2. `PLAN_V01_REVIEW_FINDINGS.md`
3. `PATH_TO_10.md`
4. `PHASE0_STATISTICAL_STUDY_SPEC.md`

The biggest change from v0.2 is that **Phase 0 is now mandatory before Phase 1 EA coding**. The project should not begin with a live-trading EA shell. It should begin with an evidence package proving that the proposed expert behaviors have positive expectancy before they are coded into the production architecture.

---

# 0. Executive Summary

The architecture from v0.2 remains broadly correct:

```text
Regime first.
Risk second.
Signal third.
Execution last.
Default state = NO_TRADE.
```

However, the latest review identifies a critical remaining weakness: the proposed v1 experts are still **candidate categories**, not yet **validated trading behaviors**.

The three proposed v1 experts are:

```text
1. Trend Pullback Expert
2. Breakout-Retest Expert
3. Range Mean-Reversion Expert
```

These experts should **not** be coded yet.

Before any expert code is written, each behavior must pass Phase 0 statistical validation:

```text
Pre-register the expert hypothesis.
Lock the mechanical definition.
Run the 9-cell test matrix.
Run the decile persistence test.
Run adversarial counter-example review.
Run multi-symbol sanity check.
Produce PHASE0_RESULTS.md per expert.
Produce consolidated PHASE0_VERDICT.md.
```

Only after Phase 0 confirms at least one defensible edge should Phase 1 begin.

The revised roadmap is:

```text
Phase 0A: Plan finalization and hypothesis registration
Phase 0B: Statistical edge validation
Phase 0C: Passive spread/cost logger in parallel
Phase 0D: Phase 0 verdict and review
Phase 1: Dry-run Master EA infrastructure only
Phase 2: Safety, lifecycle, logging, magic numbers, router audit
Phase 3: Regime Router validation
Phase 4: Approved expert implementation, one expert at a time
Phase 5: Full backtest, walk-forward, stress, and holdout validation
Phase 6: Demo forward test
Phase 7: Small live pilot
Phase 8: Production scaling only after live survival gates
```

The most important project rule is:

```text
No expert code before Phase 0.
No live OrderSend before dry-run infrastructure proves stable.
No live trading before backtest, walk-forward, stress, holdout, and demo gates pass.
```

---

# 1. Current Project Decision

## 1.1 What is approved

The following are approved as strategic direction:

```text
One Master EA
MT5/MQL5 implementation
Internal class-based modules
Centralized Regime Router
Centralized Risk Manager
Centralized Execution Guard
Centralized Position Manager
Centralized Logger
One active expert at a time in v1
No martingale, no unlimited grid, no recovery mode
No news trading in v1
Default state = NO_TRADE
```

## 1.2 What is not approved yet

The following are **not** approved for coding yet:

```text
Trend Pullback trading logic
Breakout-Retest trading logic
Range Mean-Reversion trading logic
Any live order placement
Any news trading expert
Any fakeout/liquidity-sweep expert
Any reversal expert
Any spike-fade expert
Any machine-learning component
Any multi-symbol production deployment
```

## 1.3 What must happen next

The next deliverable is not `MasterEA.mq5`.

The next deliverable is:

```text
Phase 0 statistical validation package
+
Passive spread/cost measurement package
```

This is the highest-leverage step because if no candidate expert has a measurable edge, then building the EA would only create a well-engineered system around a non-existent edge.

---

# 2. Non-Negotiable Principles

These principles must remain fixed throughout the project.

## 2.1 Evidence before code

No expert is coded until its behavior passes Phase 0.

The system must not assume that a strategy category has edge simply because it is commonly discussed by traders. A strategy must demonstrate positive expectancy under locked definitions and realistic costs.

## 2.2 No tuning after results

During Phase 0, the expert definition is locked before testing.

Forbidden behavior:

```text
Run test → see failure → add filter → rerun → call it validated
```

Allowed behavior:

```text
Run test → see failure → document failure → reject candidate or register a new candidate version from scratch
```

## 2.3 No trade is the default

The system should not search for reasons to trade.

The default state is:

```text
NO_TRADE
```

A trade is allowed only when:

```text
Regime is clear
Expert is approved
Risk state is acceptable
Execution state is acceptable
News state is safe
Position rules allow entry
Lifecycle status is ACTIVE
Router allows that expert
```

## 2.4 Risk is centralized

No expert decides lot size.

Lot sizing belongs only to the Risk Manager.

## 2.5 Execution is centralized

No expert sends orders directly.

Experts return trade proposals. The Order Gateway executes only if Risk Manager, Execution Guard, Lifecycle Manager, and Router approve.

## 2.6 Router is an overfitting surface

The Regime Router is not harmless infrastructure. It is a major source of curve-fit risk because it contains thresholds and filters.

Therefore:

```text
Router must be versioned independently.
Router thresholds must be distribution-based, not optimized per expert.
Router decisions must be logged.
Router changes require revalidation.
```

## 2.7 Retirement is code-enforced

An expert that fails performance gates must be suspended or retired by code.

A `.set` file must not be able to reactivate a retired expert.

## 2.8 Logs are part of the product

A trade that cannot be explained from logs is a system failure.

Every decision must be auditable.

## 2.9 Dedicated account for the new EA

The new EA should eventually run on a dedicated account, not shared with V85, manual trading, or other automation.

During dry-run, coexistence with existing systems is acceptable only if no order placement exists in the new EA.

## 2.10 No martingale, grid recovery, or no-stop-loss logic

The following are forbidden in v1:

```text
Martingale
Unlimited grid
Doubling after loss
Averaging down without hard invalidation
Moving stop loss farther away
No-stop-loss entries
Hedge-and-pray logic
Recovery mode
```

---

# 3. Project Goals and Non-Goals

## 3.1 Goals

The project aims to build a modular, auditable XAUUSD trading system that:

```text
Validates edge before coding experts
Classifies market regime before selecting strategy
Allows only one expert to trade at a time in v1
Uses centralized risk and execution controls
Blocks unsafe conditions by default
Measures actual cost behavior before live deployment
Logs every decision
Supports dry-run operation
Supports automatic expert suspension and retirement
Can be reviewed and reproduced by another team
```

## 3.2 Non-goals for v1

The first production version will not attempt to:

```text
Trade news events
Trade every session
Trade every market condition
Run multiple experts simultaneously
Use machine learning
Optimize parameters aggressively
Scale capital quickly
Use external macro feeds as entry triggers
Trade multiple symbols
Run high-frequency scalping
```

## 3.3 Success definition

The system is successful only if:

```text
At least one expert passes Phase 0.
The EA runs in dry-run without runtime instability.
The router decisions are explainable.
Backtest and walk-forward results are reproducible.
Demo execution does not materially degrade expected results.
Live pilot performance remains inside pre-registered expectations for at least 3 months.
Six-month live survival confirms no immediate edge collapse.
```

---

# 4. Finalized Plan-Tightening Decisions

The latest review identified ten plan-quality tightening items. This plan adopts them as follows.

| ID | Decision | v0.3 Choice |
|---|---|---|
| F1 | Pick one risk-per-trade value | Phase 0 uses fixed 0.50% for test comparability. Live pilot uses fixed 0.25%. |
| F2 | Walk-forward train window | Minimum 24 months. Prefer 36 months if trade count remains sufficient. |
| F3 | Holdout/train PF gate | Release gate = 0.80. Below 0.70 = hard fail. 0.70–0.80 = research-only / no live. |
| F4 | Single-engine concentration | Maximum 35% contribution to portfolio net P&L. |
| F5 | Single-month contribution | Maximum 25% contribution to net P&L. |
| F6 | Stable live pilot definition | At least 30 trades over at least 3 months, PF within ±20% of expected band, no risk-rule breach. |
| F7 | Timestamps | Log broker time, UTC time, and local/VPS time on every decision row. |
| F8 | Asia trading | No Asia entries in v1 unless Phase 0 proves a specific Asia-session edge. Asia levels may be mapped only. |
| F9 | Portfolio backtest | Router-switching aggregate across active approved experts. Not a simple sum of independent expert tests. |
| F10 | Symbol rename / contract change | Add startup detection, alert, and recovery procedure for suffix/contract changes. |

---

# 5. Revised Roadmap

## 5.1 Roadmap summary

```text
Phase 0: Prove or reject the expert edges.
Phase 1: Build dry-run infrastructure, no experts, no orders.
Phase 2: Build safety, lifecycle, logging, and governance modules.
Phase 3: Build and validate router behavior.
Phase 4: Code only Phase-0-approved experts, one at a time.
Phase 5: Full validation: backtest, walk-forward, stress, holdout.
Phase 6: Demo forward test on VPS.
Phase 7: Small live pilot.
Phase 8: Scale only after live survival gates.
```

## 5.2 Authorization rule

```text
Phase 1 may start only if Phase 0 approves at least one expert.
```

Preferred:

```text
2 or more experts pass Phase 0.
```

Acceptable:

```text
1 expert passes Phase 0; proceed with reduced v1.
```

Stop condition:

```text
0 experts pass Phase 0; do not build the EA.
```

## 5.3 Why this order matters

Coding infrastructure before edge validation creates sunk-cost pressure. Once months have been spent building the EA, it becomes emotionally and operationally harder to reject weak experts.

Phase 0 prevents this failure mode by asking the decisive question first:

```text
Does the behavior have measurable expectancy before optimization?
```

---

# 6. Phase 0 — Statistical Edge Validation

## 6.1 Purpose

Phase 0 exists to confirm or reject the edge thesis for each v1 expert candidate before any expert code is written.

It is not an optimization phase.

It is a falsification phase.

## 6.2 Candidate experts for Phase 0

```text
1. Trend Pullback Expert
2. Breakout-Retest Expert
3. Range Mean-Reversion Expert
```

## 6.3 Phase 0 deliverables

Each expert must produce:

```text
hypothesis_<expert>.md
phase0_<expert>_results.csv
phase0_<expert>_results.md
phase0_<expert>_decile_results.csv
phase0_<expert>_adversarial_review.md
phase0_<expert>_multi_symbol_check.md
```

The consolidated package must produce:

```text
PHASE0_VERDICT.md
PHASE0_DATA_MANIFEST.md
PHASE0_COST_MODEL.md
PHASE0_REPRODUCTION_NOTES.md
```

## 6.4 Phase 0 definition of done

Phase 0 is complete only when:

```text
[ ] hypothesis_trend_pullback.md written and SHA256-locked
[ ] hypothesis_breakout_retest.md written and SHA256-locked
[ ] hypothesis_range_mr.md written and SHA256-locked
[ ] 27 backtest cells executed and saved
[ ] phase0_trend_pullback_results.md written
[ ] phase0_breakout_retest_results.md written
[ ] phase0_range_mr_results.md written
[ ] Decile tests completed for all candidates
[ ] Adversarial searches completed for all candidates
[ ] Multi-symbol checks completed for all candidates
[ ] Cost assumptions documented
[ ] Data manifest documented
[ ] PHASE0_VERDICT.md consolidated and signed
[ ] Review team approves Phase 0 verdict
```

Only after this is Phase 1 authorized.

---

# 7. Phase 0 Data Requirements

## 7.1 Primary data requirements

| Item | Requirement |
|---|---|
| Primary symbol | XAUUSD |
| Timeframes | M1, M5, M15, H1, H4, D1 |
| Date range | 2016-01-01 through 2025-12-31 |
| Tick sources | Capital.com, Pepperstone, Dukascopy |
| Comparison symbols | EURUSD, USDJPY |
| Starting balance per cell | $10,000 |
| Risk per trade in Phase 0 | Fixed 0.50% |
| Logic changes between cells | Forbidden |
| Parameter changes between cells | Forbidden |

## 7.2 Data source notes

Potential sources:

```text
Capital.com MT5 history center
Dukascopy historical tick data
Pepperstone broker data or third-party tick source
```

Data quality must be documented in `PHASE0_DATA_MANIFEST.md`.

The manifest must include:

```text
Broker/source name
Symbol name and suffix
Start date
End date
Time zone
Digit precision
Point size
Missing data periods
Import method
Modeling method
Known limitations
```

## 7.3 Cross-validation requirement

At least one backtest cell per expert must be reproduced outside MT5 using a separate Python backtesting method, such as:

```text
backtrader
vectorbt
custom pandas event simulator
```

Purpose:

```text
Verify that MT5 Strategy Tester behavior is not creating artifacts.
```

Acceptance:

```text
Independent reproduction must match MT5 metrics within 5% on trade count, gross P&L, and PF after costs.
```

---

# 8. Phase 0 Hypothesis Registration

## 8.1 Registration rule

Before testing, every candidate expert must have a pre-registered hypothesis file.

File format:

```text
hypothesis_<expert>.md
```

The file must include:

```text
Expert name
Hypothesis date
Hypothesis version
SHA256 hash
Mechanical definition
Expected trade count per year
Expected PF band
Expected losing-month percentage
Expected worst single month
Expected max consecutive zero-trade months
Expected R-multiple distribution
Underlying XAU market behavior
Failure modes
Falsification criteria
```

## 8.2 SHA256 locking

After writing the hypothesis file, calculate and record the SHA256 hash.

Example command:

```bash
sha256sum hypothesis_trend_pullback.md
```

The hash is copied into:

```text
PHASE0_DATA_MANIFEST.md
PHASE0_VERDICT.md
phase0_<expert>_results.md
```

If the hash changes after testing begins, the candidate is invalid unless a new hypothesis version is formally registered.

## 8.3 Forbidden after registration

After registration, the following are forbidden:

```text
Changing EMA lengths
Changing ATR multipliers
Changing ADX threshold
Adding a session filter
Adding a news filter
Changing entry candle definition
Changing stop/target logic
Removing losing trades
Changing spread assumptions after seeing results
Excluding bad time periods
Changing broker source selection
```

## 8.4 Allowed after registration

Allowed actions:

```text
Fixing code bugs that made the implementation differ from the registered definition
Correcting data import errors
Documenting failure modes
Rejecting the candidate
Registering a new candidate version after the original fails
```

Bug fixes must be documented in:

```text
PHASE0_REPRODUCTION_NOTES.md
```

---

# 9. Phase 0 Candidate Expert Draft Definitions

These are starting drafts. They must be finalized and locked in the hypothesis files before testing.

## 9.1 Trend Pullback Expert — starting definition

### Long setup

```text
H1 trend condition:
  EMA(50) > EMA(200)
  EMA(50) slope over last 20 H1 bars > 0

M15 pullback condition:
  Price retraces to within 0.5 × ATR(14, H1) of EMA(21, M15)

M5 confirmation:
  Bullish engulfing candle
  OR pin bar with lower wick ≥ 2 × body close

Entry:
  Market entry at close of confirmation candle

Stop:
  Pullback low − 0.1 × ATR(14, M15)

Target:
  1.5R

Trade management:
  No scaling
  No trailing
  No partial close
```

### Short setup

Mirror logic:

```text
EMA(50) < EMA(200)
EMA(50) slope over last 20 H1 bars < 0
Price retraces toward EMA(21, M15)
Bearish confirmation on M5
Entry at close
Stop above pullback high
Target 1.5R
```

### Hypothesized behavior

Trend Pullback attempts to capture continuation after XAUUSD trends pause and mean-revert toward short-term value before resuming in the higher-timeframe direction.

### Primary failure modes

```text
Pullback becomes full reversal
Trend filter identifies late-stage trend
Entry candle appears after move is already exhausted
ATR expansion makes stop too tight
Trend exists only on one timeframe but not structurally
```

---

## 9.2 Breakout-Retest Expert — starting definition

### Long setup

```text
Level source:
  Previous day high
  OR weekly high
  OR M5 swing high with 4+ bars on each side

Break condition:
  M5 close > level by ≥ 0.3 × ATR(14, M5)

Retest condition:
  Price returns to within 5 points of broken level within 20 bars after break

Hold condition:
  M5 low does not close below the broken level during retest

Confirmation:
  Bullish M5 candle after retest

Entry:
  Buy stop above retest high

Stop:
  Retest low − 0.1 × ATR(14, M5)

Target:
  1.5R
```

### Short setup

Mirror logic:

```text
Break below previous day low, weekly low, or M5 swing low
Retest broken support as resistance
Sell stop below retest low
Stop above retest high
Target 1.5R
```

### Hypothesized behavior

Breakout-Retest attempts to capture continuation after a meaningful level is broken, the market returns to test whether the level has converted from resistance to support or support to resistance, and continuation resumes.

### Primary failure modes

```text
Breakout is false
Retest holds briefly then collapses
Level definition creates too many weak levels
Retest occurs too late
ATR-based break threshold is too small during noisy sessions
```

---

## 9.3 Range Mean-Reversion Expert — starting definition

### Long setup

```text
H1 range condition:
  ADX(14) < 20 for last 20 H1 bars

Range identification:
  At least 3 touches of upper boundary
  At least 3 touches of lower boundary
  Touches occur within last 50 M15 bars

Range width:
  Width ≥ 2 × ATR(14, M15)

Entry zone:
  Price reaches lower boundary ± 0.2 × ATR(14, M15)

Confirmation:
  Rejection candle with lower wick ≥ 2 × body close

Entry:
  Limit at or near range boundary

Stop:
  Range low − 0.3 × ATR(14, M15)

Target:
  Opposite range boundary
```

### Short setup

Mirror logic:

```text
Price reaches upper boundary
Upper wick rejection
Entry at boundary
Stop above range high
Target opposite range boundary
```

### Hypothesized behavior

Range MR attempts to capture XAUUSD auction behavior when directional conviction is low and price repeatedly rotates between accepted support and resistance areas.

### Primary failure modes

```text
Range breaks immediately after entry
Range definition is too loose
Apparent range is actually compression before expansion
Trend day misclassified as range
Range width too small after costs
```

---

# 10. Phase 0 Nine-Cell Test Matrix

For each expert, run the same mechanical logic across all nine cells.

| Cell | Time Window | Tick Source | Cost Model |
|---:|---|---|---|
| 1 | 2016–2018 | Capital.com | Best-case spread |
| 2 | 2016–2018 | Capital.com | Median spread |
| 3 | 2016–2018 | Capital.com | P95 spread |
| 4 | 2019–2021 | Pepperstone | Best-case spread |
| 5 | 2019–2021 | Pepperstone | Median spread |
| 6 | 2019–2021 | Pepperstone | P95 spread |
| 7 | 2022–2024 | Dukascopy | Best-case spread |
| 8 | 2022–2024 | Dukascopy | Median spread |
| 9 | 2022–2024 | Dukascopy | P95 spread |

## 10.1 Per-cell metrics

Each cell must record:

```text
cell_id
time_window
tick_source
cost_model
trade_count
win_rate
profit_factor
total_return_pct
total_pnl_usd
avg_trade_R
max_drawdown_pct
max_drawdown_usd
worst_month_usd
best_month_usd
losing_month_pct
max_consecutive_zero_trade_months
max_consecutive_losing_months
largest_single_trade_pct_of_pnl
top5_trades_pct_of_pnl
```

## 10.2 Cell rules

```text
Same mechanical logic in all cells
Same risk-per-trade in all cells
Same starting balance in all cells
No filter additions between cells
No parameter changes between cells
No excluding bad trades or months
No cherry-picking broker source
```

---

# 11. Phase 0 Hard Gates

An expert passes Phase 0 only if all gates pass.

## Gate 1 — Multi-cell survival

```text
Cost-adjusted PF ≥ 1.30 in at least 7 of 9 cells
```

## Gate 2 — Sample size

```text
Trade count ≥ 40 in every cell
```

## Gate 3 — No catastrophic failure

```text
No cell max_drawdown_pct > 30%
No cell total_return_pct < -25%
```

## Gate 4 — Concentration

```text
Largest single trade contribution ≤ 10% of net P&L in every cell
Top 5 trades contribution ≤ 40% of net P&L in every cell
```

## Gate 5 — Activity

```text
Max consecutive zero-trade months ≤ 3 in every cell
```

## Gate 6 — Cost sensitivity

For each time window:

```text
P95-cost PF / best-case PF ≥ 0.50
```

## Gate 7 — Decile persistence

On full 2016–2025 Capital.com data:

```text
PF > 1.0 in at least 8 of 10 deciles
No decile PF > 2.0 × median PF
No decile trade count < 10
```

## Gate 8 — Adversarial review

```text
Logic-gap failures ≤ 25% of reviewed losing trades
```

## Gate 9 — Multi-symbol sanity check

Run identical logic on EURUSD and USDJPY.

Acceptance:

```text
EURUSD PF ≥ 0.90
USDJPY PF ≥ 0.90
```

If this fails, the expert can still pass only if a specific XAU mechanism is documented and defended.

## Gate 10 — Hypothesis match

The expert should broadly match its pre-registered expectations:

```text
Actual trade count within expected count ±20%, or documented explanation
Actual PF within expected PF ±0.3, or documented explanation
Losing-month percentage within expected band, or documented explanation
Worst month within expected risk band, or documented explanation
```

Wildly better-than-expected results are a curve-fit warning, not automatic good news.

---

# 12. Phase 0 Decision Tree

```text
                  ┌─────────────────────────┐
                  │  Phase 0 Verdict        │
                  └────────────┬────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
        3 experts        1–2 experts       0 experts
        approved         approved          approved
              │                │                │
              ▼                ▼                ▼
       Proceed to        Proceed to        STOP.
       Phase 1 with      Phase 1 with      Do not begin
       3-expert v1.      reduced v1.       Phase 1.
                         Defer empty
                         slots until        Research new
                         new candidates     candidate
                         pass Phase 0.      behaviors.
```

## 12.1 If all three experts pass

Proceed to Phase 1 with:

```text
Trend Pullback
Breakout-Retest
Range MR
```

## 12.2 If one or two experts pass

Proceed with only the approved expert(s). Do not force a three-expert design.

Example:

```text
Trend Pullback passes
Breakout-Retest fails
Range MR fails
```

Then v1 becomes:

```text
Single-expert Trend Pullback system
```

## 12.3 If no experts pass

Stop the project.

This is a successful outcome if it prevents months of coding around non-existent edge.

---

# 13. Passive Spread and Cost Logger

## 13.1 Purpose

The cost model must be measured, not assumed.

A passive spread logger must run for four weeks in parallel with Phase 0.

## 13.2 Output file

```text
cost_model_measured.csv
```

## 13.3 Required measurements

The logger must capture:

```text
Timestamp broker time
Timestamp UTC
Timestamp local/VPS time
Symbol
Bid
Ask
Spread in points
Spread in price units
Session
Day of week
Hour of day
News window flag
Rollover window flag
Weekend open/close flag
Maximum spread since last sample
Median spread bucket
P95 spread bucket
```

## 13.4 Required summary outputs

At the end of four weeks, generate:

```text
Median spread by hour of day
P95 spread by hour of day
Median spread by day of week
P95 spread by day of week
Spread distribution during rollover ±30 minutes
Spread distribution around high-impact USD news ±10 minutes
Maximum spread by session
Median and P95 spread by session
```

## 13.5 Approval rule

All expert approval gates must be run against P95 measured cost.

An expert that passes only under median spread but fails under P95 spread is not approved for live trading.

## 13.6 Multi-broker cost scenarios

Each candidate must also be modeled under:

```text
Capital.com spread + zero commission
Raw spread + $3 per lot commission
Raw spread + $7 per lot commission
P95 spread + measured slippage after demo data is available
```

The point at which each expert fails must be documented.

---

# 14. Edge Thesis Documents

## 14.1 Purpose

The Edge Thesis Document explains why an expert deserves to exist.

It is not a backtest report.

It answers:

```text
What XAUUSD behavior is this expert exploiting?
Why should the behavior persist?
What evidence supports it?
When does it fail?
Why does this expert deserve a slot over alternatives?
```

## 14.2 Required template

```text
# Edge Thesis: <Expert Name>

Version:
Date:
Author:
Status: Draft / Registered / Phase0-Passed / Rejected

## 1. Underlying Market Behavior
<One paragraph explaining what gold is doing when this setup works.>

## 2. Why This Behavior Should Persist
<Microstructure, session, liquidity, macro, or behavioral reason.>

## 3. Mechanical Definition
<Exact rules. Must match hypothesis file.>

## 4. Evidence of Persistence
<Phase 0 results or prior verified work.>

## 5. Failure Modes
<When the behavior breaks.>

## 6. Router Implications
<Which regimes should allow/block this expert.>

## 7. Cost Sensitivity
<How spread, slippage, and commission affect it.>

## 8. Why It Deserves a Slot
<What it captures that other experts do not.>

## 9. Falsification Conditions
<What result would make us reject the expert.>
```

## 14.3 Approval rule

No expert can enter implementation unless its Edge Thesis is:

```text
Written
SHA256-locked
Phase-0-supported
Reviewed
Approved
```

---

# 15. System Architecture After Phase 0

## 15.1 Architecture style

The EA should be one MT5/MQL5 Master EA with internal modules implemented as class-based `.mqh` include files.

Do not build separate EAs for each expert in v1.

Reason:

```text
Separate EAs create cross-EA risk coordination problems.
A single master controller centralizes router, risk, execution, and lifecycle state.
```

## 15.2 High-level flow

```text
Tick / Bar Event
    ↓
Market Data Engine
    ↓
Feature Engine
    ↓
Session Engine
    ↓
News Guard
    ↓
Server Time Validator
    ↓
Regime Router
    ↓
Expert Registry / Lifecycle Manager
    ↓
Allowed Expert Generates Proposal
    ↓
Risk Manager
    ↓
Execution Guard
    ↓
Order Gateway / DryRunMode
    ↓
Position Manager
    ↓
Logger / Dashboard / Reports
```

## 15.3 Module list

```text
1. MasterEA.mq5
2. GlobalConfig.mqh
3. MarketDataEngine.mqh
4. FeatureEngine.mqh
5. SessionEngine.mqh
6. NewsGuard.mqh
7. ServerTimeValidator.mqh
8. RegimeRouter.mqh
9. ExpertRegistry.mqh
10. ExpertLifecycleManager.mqh
11. RiskManager.mqh
12. PortfolioGovernor.mqh
13. ExecutionGuard.mqh
14. MagicNumberAllocator.mqh
15. OrderGateway.mqh
16. DryRunMode.mqh
17. PositionManager.mqh
18. Logger.mqh
19. Dashboard.mqh
20. ConcentrationReporter.py or .mqh/reporting script
21. SnapshotBuilder.ps1
22. ReleaseCheck.ps1
```

## 15.4 Trading experts after Phase 0

Only Phase-0-approved experts are implemented.

Possible v1 experts:

```text
TrendPullbackExpert.mqh
BreakoutRetestExpert.mqh
RangeMRExpert.mqh
```

Deferred:

```text
FakeoutLiquiditySweepExpert.mqh
TrendContinuationExpert.mqh
CompressionBreakoutExpert.mqh
ReversalExpert.mqh
NewsSpikeExpert.mqh
SpikeFadeExpert.mqh
GapAbnormalTradingExpert.mqh
```

---

# 16. Core Module Specifications

## 16.1 MasterEA.mq5

Responsibilities:

```text
Initialize all modules
Validate configuration
Validate magic number registry
Validate server time
Validate symbol
Validate account mode
Route OnTick and OnTimer events
Trigger bar-close processing
Call dry-run or live order gateway depending on approved mode
Display dashboard
Handle shutdown safely
```

Startup must fail if:

```text
Magic number ranges are missing or duplicated
Symbol precision cannot be resolved
Time validation fails beyond allowed drift
Config file is incomplete
Logger cannot write files
Risk limits are invalid
Lifecycle file is missing
Live trading is enabled without release approval
```

## 16.2 MarketDataEngine

Responsibilities:

```text
Read Bid and Ask
Read spread
Build or retrieve candles for M1, M5, M15, H1, H4, D1
Track previous day high/low
Track previous week high/low
Track session high/low
Track current candle body and wick structure
Detect bad ticks
Detect gaps
Normalize symbol precision
```

Outputs:

```text
bid
ask
spread_points
spread_price
point_size
digits
current_bar_time
prev_day_high
prev_day_low
prev_week_high
prev_week_low
session_high
session_low
bad_tick_flag
gap_flag
```

## 16.3 FeatureEngine

Calculates reusable features only. It does not generate signals.

Features:

```text
ATR values
ADX values
EMA values
EMA slope
Swing highs/lows
Range width
Candle body percentage
Upper wick percentage
Lower wick percentage
Distance from EMA
Distance from session high/low
Distance from daily high/low
Volatility percentile
Spread percentile
Compression score
```

## 16.4 SessionEngine

Classifies current session.

Session states:

```text
ASIA_MAPPING_ONLY
PRE_LONDON
LONDON_OPEN
LONDON_MAIN
LONDON_FIX_WINDOW
NEW_YORK_PRE_DATA
NEW_YORK_OPEN
NEW_YORK_MAIN
NEW_YORK_AFTERNOON
ROLLOVER
FRIDAY_CLOSE_WINDOW
WEEKEND_CLOSED
MONDAY_OPEN_WINDOW
HOLIDAY_THIN_LIQUIDITY
```

v1 Asia rule:

```text
Asia levels may be mapped.
No Asia entries unless Phase 0 proves a specific Asia edge.
```

## 16.5 NewsGuard

v1 rule:

```text
No news trading.
```

News states:

```text
NO_NEWS_RISK
PRE_NEWS_BLACKOUT
NEWS_RELEASE_ACTIVE
POST_NEWS_COOLDOWN
MANUAL_NEWS_LOCKDOWN
CALENDAR_UNAVAILABLE_FALLBACK_ACTIVE
```

High-impact USD events:

```text
CPI
PPI
NFP
Unemployment rate
Average hourly earnings
FOMC rate decision
FOMC press conference
FOMC minutes
PCE inflation
GDP
Retail sales
ISM Manufacturing
ISM Services
Major Fed speeches
```

Rules:

```text
Block new trades 30 minutes before high-impact USD news.
Block new trades 30 minutes after high-impact USD news.
Close EA-managed open positions before CPI, NFP, and FOMC.
Use MT5 calendar as primary.
Use hardcoded fallback schedule when calendar unavailable.
Log calendar source for every block.
```

## 16.6 ServerTimeValidator

Responsibilities:

```text
Compare broker time, trade server time, local/VPS time, and expected UTC offset.
Detect time drift.
Log broker time + UTC + local time.
Block startup if drift exceeds threshold.
```

Initial rule:

```text
If time drift > 60 seconds and cannot be explained by known broker offset, abort startup or enter DRY_RUN_ONLY.
```

If external NTP is not available inside MQL5, use an approved external helper process or validated VPS clock sync.

## 16.7 RegimeRouter

The router determines the current regime and active expert permission.

Inputs:

```text
Features
Session state
News state
Risk state
Spread state
Volatility state
Lifecycle state
Open positions
```

Outputs:

```text
router_version
active_regime
allowed_expert
blocked_experts
would_have_allowed_experts
trade_permission
block_reason
confidence_score
```

## 16.8 ExpertLifecycleManager

Manages expert status.

Possible states:

```text
CANDIDATE
PHASE0_APPROVED
DRY_RUN_ONLY
BACKTEST_APPROVED
DEMO_APPROVED
ACTIVE
SUSPENDED
RETIRED
DISABLED_BY_CONFIG
DISABLED_BY_GOVERNOR
```

Startup behavior:

```text
Read lifecycle_status.json or equivalent file.
Read recent performance metrics.
Apply suspension and retirement rules.
Override .set file if necessary.
Log status and reason.
Display status on dashboard.
```

Important rule:

```text
A retired expert cannot be reactivated by .set file.
Only a new versioned release can reactivate it.
```

## 16.9 RiskManager

Controls all lot sizing and risk limits.

Responsibilities:

```text
Calculate lot size
Enforce risk per trade
Enforce daily loss cap
Enforce weekly loss cap
Enforce monthly loss cap
Enforce max open trades
Enforce max trades per day
Enforce max trades per session
Enforce losing-streak risk reduction
Enforce equity drawdown cap
```

No expert may bypass this module.

## 16.10 ExecutionGuard

Protects against broker execution risk.

Checks:

```text
Spread
Slippage
Price jump
Minimum stop distance
Freeze level
Margin availability
Order rejection frequency
Trading permissions
Bad tick flag
Symbol availability
Market open/closed status
```

## 16.11 MagicNumberAllocator

Single source of truth for magic-number assignment.

No expert may choose magic numbers independently.

## 16.12 OrderGateway and DryRunMode

OrderGateway is the only module allowed to call live order functions.

DryRunMode must support:

```text
Full signal generation
Full router path
Full risk calculation
Full execution checks
No actual OrderSend
Write would_have_traded rows
```

Milestone 1 must contain no live `OrderSend` capability.

## 16.13 PositionManager

Manages all open trades.

v1 rules:

```text
Hard SL required
Take profit required unless exit model explicitly approved
Break-even at +1R
No partial close
No trailing stop
Time stop if trade not at +0.5R within 4 hours
Session exit 30 minutes before rollover
No overnight hold in v1
No weekend hold in v1
```

## 16.14 Logger

Logs all decisions, not only trades.

Required log files:

```text
decision_log.csv
trade_log.csv
risk_log.csv
execution_log.csv
router_audit_log.csv
lifecycle_log.csv
error_log.csv
spread_log.csv
news_log.csv
```

## 16.15 Dashboard

Dashboard fields:

```text
Symbol
Broker time
UTC time
Local/VPS time
Current spread
Current session
Current regime
Router version
Allowed expert
Would-have-allowed experts
Lifecycle state per expert
Risk mode
News state
Execution state
Open trades
Daily P/L
Weekly P/L
Monthly P/L
Trade permission
Block reason
Dry-run/live mode
```

---

# 17. Regime Router v1 Specification

## 17.1 v1 regime set

The original plan had too many regimes. v1 uses seven regimes:

```text
TREND_WITH_PULLBACK
RANGE
COMPRESSION
BREAKOUT_RETEST
ABNORMAL_MARKET
NEWS_BLACKOUT
NO_TRADE
```

## 17.2 Regime definitions

Definitions must be finalized after Phase 0 but before Phase 3.

Starting concepts:

### TREND_WITH_PULLBACK

```text
Higher timeframe trend exists.
Lower timeframe retraces into defined pullback zone.
Volatility not extreme.
News not active.
```

Possible objective components:

```text
H1 EMA alignment
H1 EMA slope
ADX percentile
M15 retracement distance
M5 confirmation candle
```

### RANGE

```text
Trend strength low.
Clear upper/lower boundaries.
Sufficient touches.
Range width sufficient after costs.
Price near edge, not middle.
```

### COMPRESSION

```text
ATR percentile low.
Range narrowing.
Inside-bar or low-range behavior.
No trade in v1 unless Breakout-Retest condition appears later.
```

### BREAKOUT_RETEST

```text
Known level broken.
Retest occurs within allowed bar count.
Level holds.
Continuation confirmation appears.
```

### ABNORMAL_MARKET

```text
Gap
Bad tick
Extreme spread
Extreme volatility
Broker abnormality
Unscheduled shock
Symbol issue
```

### NEWS_BLACKOUT

```text
Scheduled high-impact USD news blackout or cooldown active.
```

### NO_TRADE

```text
Default state.
Used when no approved regime is valid.
```

## 17.3 Router safeguards

The router must follow these controls:

```text
Router has independent version number.
Every decision logs router version.
Thresholds are chosen from distribution statistics, not per-expert optimization.
Every blocked expert is logged in would_have_allowed_experts.
Router is frozen after Phase 3.
Any router change requires full revalidation of affected experts.
```

## 17.4 Router pseudocode

```text
If NewsGuard.state in [PRE_NEWS_BLACKOUT, NEWS_RELEASE_ACTIVE, POST_NEWS_COOLDOWN]:
    regime = NEWS_BLACKOUT
    allowed_expert = NONE
    trade_permission = BLOCKED

Else if ExecutionGuard.abnormal_market_detected:
    regime = ABNORMAL_MARKET
    allowed_expert = NONE
    trade_permission = BLOCKED

Else if RiskManager.mode == LOCKED:
    regime = NO_TRADE
    allowed_expert = NONE
    trade_permission = BLOCKED

Else if trend_pullback_regime_valid and TrendPullback.lifecycle_allows:
    regime = TREND_WITH_PULLBACK
    allowed_expert = TREND_PULLBACK

Else if breakout_retest_regime_valid and BreakoutRetest.lifecycle_allows:
    regime = BREAKOUT_RETEST
    allowed_expert = BREAKOUT_RETEST

Else if range_regime_valid and RangeMR.lifecycle_allows:
    regime = RANGE
    allowed_expert = RANGE_MR

Else if compression_valid:
    regime = COMPRESSION
    allowed_expert = NONE
    trade_permission = BLOCKED

Else:
    regime = NO_TRADE
    allowed_expert = NONE
    trade_permission = BLOCKED
```

## 17.5 One active expert rule

v1 allows only one active trading expert at a time.

If multiple experts appear valid, the priority rule must be explicit and logged.

Initial priority:

```text
NEWS_BLACKOUT / ABNORMAL_MARKET blocks all.
TREND_WITH_PULLBACK before RANGE.
BREAKOUT_RETEST before RANGE when level break is recent.
RANGE only if price is near range edge and no breakout/retest condition exists.
```

---

# 18. Risk Management Specification

## 18.1 Risk values

For live pilot v1:

```text
Risk per trade: 0.25%
Max daily equity loss: 1.00%
Max weekly equity loss: 3.00%
Max monthly equity loss: 6.00%
Max open XAUUSD trades: 1 initially
Max trades per day: 4
Max trades per session: 2
Max consecutive losses before defensive mode: 3
Max consecutive losses before lockout: 5
```

For Phase 0 statistical tests:

```text
Risk per trade: fixed 0.50%
Starting account: $10,000 each cell
```

## 18.2 Daily loss accounting

Daily loss is equity-based and includes floating drawdown.

```text
DailyEquityLoss = DayStartEquity - CurrentEquity
```

If:

```text
DailyEquityLoss >= MaxDailyLoss
```

Then:

```text
Close all EA-managed positions
Block new trades
Set mode = LOCKED_UNTIL_NEXT_TRADING_DAY
Log event
Display dashboard warning
```

## 18.3 Weekly and monthly loss rules

Weekly loss:

```text
If weekly equity loss ≥ 3.00%:
    Close all EA-managed positions
    Lock until next week
```

Monthly loss:

```text
If monthly equity loss ≥ 6.00%:
    Close all EA-managed positions
    Switch to DRY_RUN_ONLY for rest of month
    Require manual review before next month reactivation
```

## 18.4 Defensive risk mode

After 3 consecutive losses:

```text
Set risk mode = DEFENSIVE
New trades blocked for rest of session or until next day
```

After 5 consecutive losses:

```text
Set risk mode = LOCKED
Manual review required
```

## 18.5 Risk calculation

Conceptual formula:

```text
AllowedRiskMoney = AccountEquity × RiskPercent
StopLossMoneyPerLot = StopDistance × TickValueAdjusted
LotSize = AllowedRiskMoney / StopLossMoneyPerLot
```

The final lot must be normalized to broker:

```text
Minimum lot
Maximum lot
Lot step
Margin requirement
Stop distance requirement
```

---

# 19. Execution and Broker Realism

## 19.1 Spread rule

Initial rule:

```text
Block if current_spread_points > max(30 points, 1.5 × 20-bar median spread)
```

Important implementation note:

```text
30 points must be normalized by broker _Point and XAUUSD digit precision.
```

The spread rule must be recalibrated after the four-week spread logger produces measured P95 values.

## 19.2 Slippage and price-jump rule

For market orders:

```text
Block if Ask - lastQuote.Ask > 5 points for buy market orders
Block if lastQuote.Bid - Bid > 5 points for sell market orders
```

Initial max deviation:

```text
Trend Pullback market order: configurable but strict
Breakout-Retest stop order: MaxDeviation = 3 points
Range MR limit order: MaxDeviation = 3 points
```

## 19.3 Order type by expert

| Expert | Initial Order Type |
|---|---|
| Trend Pullback | Market entry after confirmation candle, subject to price-jump rule |
| Breakout-Retest | Stop order after retest confirmation |
| Range MR | Limit order at boundary, subject to execution checks |

## 19.4 Order failure rule

If three consecutive order failures occur:

```text
Enter LOCKED_MODE
Block further order attempts
Log failure codes
Require manual review
```

## 19.5 Broker/symbol safeguards

Startup must check:

```text
Symbol exists
Symbol is tradeable
Symbol suffix handled
Digits and point size resolved
Contract size resolved
Tick value resolved
Minimum stop distance resolved
Freeze level resolved
Margin mode resolved
```

If symbol changes from `XAUUSD` to `XAUUSDm`, `XAUUSD.`, or similar:

```text
Abort live trading
Log symbol mismatch
Notify operator
Require documented recovery
```

---

# 20. News and Calendar Policy

## 20.1 v1 rule

```text
No news trading in v1.
```

News events are used only to block trading and manage exposure.

## 20.2 Blackout windows

```text
Pre-news blackout: 30 minutes
Post-news cooldown: 30 minutes
```

## 20.3 Forced close events

EA-managed open positions must be closed before:

```text
CPI
NFP
FOMC rate decision
FOMC press conference
```

The exact closure time must be configurable, with starting value:

```text
Close 30 minutes before event
```

## 20.4 Calendar source hierarchy

```text
Primary: MT5 built-in economic calendar
Secondary: manually maintained event file
Fallback: time-based schedule for known event windows
```

Every news block must log:

```text
Event name
Event time
Calendar source
Block start
Block end
Action taken
```

---

# 21. Position Management v1

## 21.1 Standard exit model

v1 uses a simple exit model to preserve attribution.

```text
Hard SL: mandatory
TP: mandatory or expert-defined R target
Break-even: at +1R
Partial close: disabled
Trailing stop: disabled
Time stop: enabled
Session exit: enabled
Overnight holding: disabled
Weekend holding: disabled
```

## 21.2 Break-even rule

```text
When trade reaches +1R:
    Move stop loss to entry price, adjusted for spread/commission if required
```

## 21.3 Time stop

```text
If trade is not at +0.5R within 4 hours:
    Close trade or mark for exit at next safe price
```

## 21.4 Session exit

```text
Close all EA-managed positions 30 minutes before broker daily rollover.
Close all EA-managed positions before Friday close window.
```

## 21.5 Stop-loss integrity

Forbidden:

```text
Moving stop farther away from entry
Removing stop loss
Replacing hard stop with mental stop
Averaging down to avoid stop
```

---

# 22. Magic Number Plan

## 22.1 Reserved range

```text
Master EA reserved range:  920000 – 929999
```

## 22.2 Proposed allocation

```text
Trend Pullback Expert:     920000 – 920099
Range MR Expert:           920100 – 920199
Breakout-Retest Expert:    920200 – 920299
Fakeout Expert:            920300 – 920399  (deferred)
Future experts:            920400 – 929999
```

## 22.3 Required documentation

Create:

```text
magic_numbers.md
```

It must include:

```text
New EA reserved ranges
V85 production occupied ranges
V61 archive occupied ranges
V77/V80 occupied ranges
Any manual or other EA ranges
Broker account IDs where ranges are active
```

## 22.4 Startup validation

EA startup must fail if:

```text
Magic range is missing
Magic range overlaps another known range
Expert requests unknown magic number
Magic number is outside reserved namespace
```

## 22.5 No direct expert magic numbers

Experts must request magic numbers through:

```text
MagicNumberAllocator
```

No expert may hardcode its own magic number.

---

# 23. Expert Lifecycle Management

## 23.1 Lifecycle states

```text
CANDIDATE
PHASE0_APPROVED
DRY_RUN_ONLY
BACKTEST_APPROVED
DEMO_APPROVED
ACTIVE
SUSPENDED
RETIRED
DISABLED_BY_CONFIG
DISABLED_BY_GOVERNOR
```

## 23.2 Promotion path

```text
CANDIDATE
  ↓ passes Phase 0
PHASE0_APPROVED
  ↓ coded and dry-run stable
DRY_RUN_ONLY
  ↓ passes backtest/walk-forward/stress
BACKTEST_APPROVED
  ↓ passes demo forward test
DEMO_APPROVED
  ↓ live pilot approval
ACTIVE
```

## 23.3 Suspension rules

Suspend expert if:

```text
3 consecutive losing months
90-day rolling PF < 1.10
90-day losing-month percentage > 50%
Live PF falls below 0.8 × expected PF band
Execution slippage materially exceeds model
```

Suspended expert behavior:

```text
No live trades
Dry-run only
Monthly re-evaluation
```

## 23.4 Retirement rules

Retire expert if:

```text
Holdout/train PF ratio < 0.70
Single-trade concentration > 10%
Top-5-trade concentration > 40%
Single-engine contribution > 35% in portfolio
Single-month contribution > 25%
Repeated suspension without recovery
Post-demo slippage-adjusted PF below approval gate
```

Retired expert behavior:

```text
EnableExpert forced false
.set file cannot override
Order proposals ignored
Lifecycle log records reason
Reactivation requires new versioned release
```

---

# 24. Logging and Diagnostics

## 24.1 Decision log

Every M5 decision event must log:

```text
decision_id
broker_time
utc_time
local_time
symbol
bid
ask
spread_points
session
news_state
risk_state
execution_state
router_version
active_regime
allowed_expert
would_have_allowed_experts
blocked_experts
block_reason
atr_m5
atr_m15
atr_h1
adx_h1
ema_state
volatility_state
open_positions
equity
balance
daily_pnl
weekly_pnl
monthly_pnl
mode_live_or_dryrun
```

## 24.2 Trade log

Every proposed or executed trade must log:

```text
trade_id
expert_name
expert_version
router_version
magic_number
proposal_time
entry_type
direction
entry_price
stop_loss
take_profit
risk_money
risk_pct
lot_size
risk_reward
setup_reason
execution_status
fill_price
slippage
exit_time
exit_reason
pnl_usd
pnl_R
```

## 24.3 Router audit log

Must include:

```text
All regime scores
Which regimes were valid
Which experts would have been allowed
Why final expert was selected
Why each other expert was blocked
Router threshold values
Router version
```

## 24.4 Risk log

Must include:

```text
Day start equity
Week start equity
Month start equity
Current equity
Daily loss percentage
Weekly loss percentage
Monthly loss percentage
Risk mode
Loss streak
Risk lock status
```

## 24.5 Execution log

Must include:

```text
Spread check result
Slippage check result
Min stop distance check
Freeze level check
Margin check
Order result code
Order rejection count
Broker trade permission
Bad tick flag
```

---

# 25. Testing and Validation After Coding

Phase 0 validates behavior. Later phases validate implementation.

## 25.1 Unit testing

Test each module independently:

```text
Risk calculation
Magic number allocation
Spread filter
Session detection
News blackout
Router classification
Lifecycle state transition
Dry-run order suppression
Logger write behavior
Symbol suffix handling
```

## 25.2 Visual backtesting

Every expert must pass visual review on representative periods before metric evaluation.

Purpose:

```text
Confirm trades match registered logic.
Find implementation bugs.
Ensure router state matches visible market behavior.
```

## 25.3 Required historical periods

Use at minimum:

```text
2020-03 to 2020-04: COVID volatility crash/rally
2022-09 to 2022-11: strong USD trend period
2023-03: SVB/banking crisis
2024-04: geopolitical spike period
2025 full year: most recent pre-review regime
Continuous 5-year M5 backtest
Full 2016–2025 dataset where data quality permits
```

## 25.4 Walk-forward validation

Method:

```text
Anchored walk-forward
Initial train window: 24 months minimum
Validation window: 3 months
Step: 3 months
```

Acceptance:

```text
Holdout/train PF ≥ 0.80 on every release-approval fold
Below 0.70 on any fold = hard fail
0.70–0.80 = research-only, not live-approved
```

## 25.5 True holdout

Set aside the most recent six months before final pre-live review.

Rules:

```text
Do not inspect during development.
Do not tune against it.
Open only once at final approval.
If results materially degrade, expert fails release approval.
```

## 25.6 Stress tests

Every approved expert and the full portfolio must pass:

```text
Spread ×2 for a full session
Spread ×3 during rollover simulation
High slippage simulation
Delayed execution simulation
VPS restart at random tick
Symbol disabled mid-session
Broker connection loss
Three consecutive order rejections
Negative balance / margin-call simulation
Calendar API unavailable
Server time skew
Friday close
Monday open gap
```

## 25.7 Concentration report

After every backtest, generate:

```text
concentration_report.csv
```

Fields:

```text
single_trade_contribution
top5_trade_contribution
single_month_contribution
single_engine_contribution
monthly_pnl_distribution
zero_trade_months
losing_month_percentage
```

## 25.8 Independent reproduction

Before live pilot, a person not on the build team must reproduce the backtest from the specification alone.

Acceptance:

```text
Results within 5% of stated trade count, PF, and net P&L after costs.
```

---

# 26. Release Gates

## 26.1 Expert release gate

An expert may move beyond dry-run only if:

```text
Phase 0 passed
Edge Thesis approved
Backtest passed
Walk-forward passed
True holdout passed
Stress tests passed
Concentration gates passed
Cost model passed at P95 spread
Independent reproduction passed
Lifecycle state = BACKTEST_APPROVED or higher
```

## 26.2 Portfolio release gate

The portfolio may enter demo if:

```text
At least one expert is approved
Router-switching aggregate backtest passes
No single expert contributes >35% if multiple experts active
No single month contributes >25%
Portfolio max drawdown within limit
Portfolio passes stress tests
Decision logs are complete
No unexplained trades
No unexplained blocks
```

## 26.3 Demo release gate

Demo may move to small live pilot only if:

```text
Minimum 6 weeks demo forward test
At least 2 weeks include high-impact USD news events
No unauthorized orders
No risk-rule breach
No persistent execution errors
Slippage measured and backtests rerun with measured slippage
At least 30 trades over at least 3 months for stable pilot graduation
```

Note:

```text
If demo does not produce 30 trades in 6 weeks, continue demo until sample size is met or activity gate is reconsidered.
```

---

# 27. CI/CD and Release Discipline

## 27.1 Git branches

```text
develop
release-candidate
production
```

## 27.2 Required release files

Every release candidate must include:

```text
EA source files
Compiled EA binary
.set file
magic_numbers.md
filter_inventory.md
edge thesis files
Phase 0 result files
backtest report
walk-forward report
holdout report
concentration report
cost model file
router version file
expert lifecycle file
snapshot bundle
```

## 27.3 release_check.ps1

A release check script must refuse live trading unless:

```text
Unit tests pass
Magic numbers validated
Filter inventory complete
Edge thesis signed off
Phase 0 verdict exists
Walk-forward all-fold pass exists
Concentration report passes
Cost model exists
Snapshot bundle exists
Router version is documented
No retired expert is enabled
EnableLiveTrading approved
```

## 27.4 Snapshot bundle

Every release must create:

```text
snapshot_<version>_<date>.zip
```

Contents:

```text
EA binary
Source files
.set file
Broker ID
Account ID
Magic ranges
Git commit hash
Tick data range
Backtest report
Holdout report
Concentration report
Cost model
Lifecycle state file
Release checklist
```

---

# 28. Operational Plan

## 28.1 Account isolation

The new EA should have a dedicated account for forward testing and live pilot.

Do not share with:

```text
V85
Manual trading
Other EAs
Experimental scripts
```

## 28.2 VPS requirements

Create:

```text
vps_plan.md
```

Include:

```text
Provider
Location
OS
MT5 terminal version
Auto-restart policy
Remote access method
2FA policy
Backup schedule
Clock sync method
Network monitoring
Log backup path
```

## 28.3 External health monitor

A separate process on another host should ping the EA every 5 minutes.

Alert if:

```text
No heartbeat for >10 minutes
Broker connection lost
Margin warning
EA mode changes unexpectedly
Log activity spike
Order rejection spike
Risk state becomes LOCKED
```

## 28.4 Disaster recovery runbook

Create:

```text
dr_runbook.md
```

Include procedures for:

```text
VPS dies mid-trade
MT5 crashes
Broker account inaccessible
All EA-managed positions need manual close
Magic-number-based position identification
State file recovery
Log backup recovery
```

---

# 29. Live Pilot and Scaling Plan

## 29.1 Capital ladder

| Phase | Duration | Risk Per Trade | Lot Cap | Conditions |
|---|---:|---:|---:|---|
| Demo | Minimum 6 weeks, preferably until 30 trades | 0% live | None | Execution validation |
| Pilot | Months 1–3 | 0.25% | Minimum lot | No major rule breach |
| Probation | Months 4–6 | 0.25%–0.50% | 2× minimum | Stable pilot passed |
| Production | Months 7–12 | Target risk approved by review | 5× minimum | 6-month survival |
| Scale | Month 13+ | Review-approved | Target | Quarterly review pass |

## 29.2 Scale-down triggers

Scale down or suspend if:

```text
90-day rolling PF < 1.10
Drawdown exceeds expected band
Slippage exceeds model
Monthly loss cap hit
Two consecutive months below expected band
Router no-trade rate deviates materially from expected
Expert concentration rises above limits
```

## 29.3 Stable live pilot definition

Stable live pilot requires:

```text
At least 30 live trades
At least 3 calendar months
PF within ±20% of expected band
Drawdown within expected band
No risk-rule breach
No unauthorized order
No repeated execution failure
No unexplainable trade
```

---

# 30. Long-Term Survival Design

## 30.1 Quarterly review calendar

Create:

```text
review_calendar.md
```

Each quarter review:

```text
P&L vs expectation
PF vs expected band
Drawdown vs expected band
Slippage vs model
Regime classification distribution
Router block reasons
Expert lifecycle states
Parameter stability
Drift metrics
```

## 30.2 Pre-committed retirement triggers

```text
90-day rolling PF < 1.10 → suspend
90-day losing-month % > 50% → suspend
Holdout/train degradation below 0.50 → retire
Two monthly hard-stop breaches in six months → retire or rebuild
Slippage-adjusted PF below gate → retire
```

## 30.3 Research pipeline

Retail edges decay. The project must maintain a research backlog for replacement experts.

Candidate future experts:

```text
Fakeout / Liquidity Sweep
Trend Continuation
Compression Breakout
Session Expansion
Spike Exhaustion
Gap Handling
```

No future expert may bypass Phase 0.

---

# 31. Deferred Items

## 31.1 Deferred to v1.5

```text
Fakeout / Liquidity Sweep Expert
LiveDriftMonitor if not required for pilot
Advanced external health monitor
Trailing stop experiments
Partial close experiments
```

## 31.2 Deferred to v2+

```text
News trading
Spike fade trading
Machine learning
Multi-symbol production
External macro factor model
Full portfolio optimizer
Dynamic capital allocation between experts
```

## 31.3 Permanently forbidden unless separately approved

```text
Martingale
Unlimited grid
No-stop-loss systems
Recovery doubling
Broker-latency arbitrage
Unbounded averaging down
```

---

# 32. Updated MVP Scope

## 32.1 Validation MVP — immediate next step

Build/produce:

```text
Phase 0 hypothesis files
Phase 0 test scripts
Phase 0 result templates
Phase 0 data manifest
Passive spread logger
Cost model report
PHASE0_VERDICT.md
```

No EA trading infrastructure required yet.

## 32.2 EA MVP after Phase 0 passes

Build:

```text
Master EA shell
Market Data Engine
Feature Engine
Session Engine
News Guard
Server Time Validator
Regime Router
Risk Manager
Execution Guard
Position Manager
Logger
Dashboard
MagicNumberAllocator
ExpertLifecycleManager
DryRunMode
ConcentrationReporter
```

No live orders in first EA milestone.

## 32.3 First trading expert after infrastructure

Implement only the highest-confidence Phase-0-approved expert first.

Recommended if all pass:

```text
1. Trend Pullback
2. Breakout-Retest
3. Range MR
```

But actual order must be based on Phase 0 results.

---

# 33. Phase-by-Phase Implementation Plan

## Phase 0A — Finalize study setup

Deliverables:

```text
Data manifest draft
Hypothesis templates
Backtest harness plan
Cost logger design
Git repository structure
```

Acceptance:

```text
Review team approves hypothesis locking process.
```

## Phase 0B — Statistical edge study

Deliverables:

```text
27 cell results
Decile tests
Adversarial review
Multi-symbol checks
Per-expert result documents
```

Acceptance:

```text
PHASE0_VERDICT.md completed.
```

## Phase 0C — Passive cost measurement

Deliverables:

```text
4-week spread log
cost_model_measured.csv
P95 spread report
session spread report
news/rollover spread report
```

Acceptance:

```text
P95 cost model approved for validation gates.
```

## Phase 1 — Dry-run infrastructure

Build:

```text
MasterEA shell
Market data
Features
Sessions
Logger
Dashboard
DryRunMode
ServerTimeValidator
```

Strict rule:

```text
No OrderSend calls in the codebase.
```

Acceptance:

```text
Runs 5 trading days continuously.
One decision_log.csv row per M5 bar.
Dashboard updates correctly.
Server time validation works.
No runtime errors.
```

## Phase 2 — Safety and governance modules

Build:

```text
RiskManager
ExecutionGuard
MagicNumberAllocator
ExpertLifecycleManager
NewsGuard
Kill switches
```

Acceptance:

```text
Risk caps trigger under simulated equity injection.
Magic collision test fails startup.
News blackout logs correctly.
Execution blocks on simulated spread/slippage.
Lifecycle manager blocks retired expert.
```

## Phase 3 — Router validation

Build:

```text
RegimeRouter v1.0
Router audit log
would_have_allowed_experts logging
```

Acceptance:

```text
Router classifications visually reviewed.
Router no-trade rate documented.
No silent expert blocking.
Router version logged every decision.
```

## Phase 4 — Expert implementation

Implement one expert at a time, only if Phase 0 approved.

For each expert:

```text
Code expert
Run unit test
Run dry-run
Run visual backtest
Run full validation
Obtain review approval
Only then add next expert
```

## Phase 5 — Full validation

Run:

```text
Full backtest
Walk-forward
True holdout
Stress tests
Concentration report
Independent reproduction
Portfolio router-switching aggregate
```

## Phase 6 — Demo forward test

Run on VPS.

Minimum:

```text
6 weeks
At least 2 high-impact USD news events observed
Preferably until 30 demo trades
```

## Phase 7 — Small live pilot

Rules:

```text
Dedicated account
0.25% risk per trade
Minimum lot if possible
No news trading
No overnight/weekend hold
Daily log review
Weekly review
```

## Phase 8 — Production and scaling

Allowed only after:

```text
Stable live pilot definition met
Quarterly review process active
Disaster recovery runbook tested
External health monitor active
```

---

# 34. Pre-Coding Open Decisions

Before Phase 1 begins, the review team must answer:

## 34.1 V85 coexistence or replacement

Decision needed:

```text
Will V85 remain on the same account during dry-run?
Will the new EA get a dedicated account immediately?
When will V85 be retired, if ever?
```

Recommended:

```text
Dry-run may coexist with V85 only if new EA has no OrderSend capability.
Trading-enabled phases should use dedicated account.
```

## 34.2 Platform commitment

Decision:

```text
Commit to MT5/MQL5.
```

Remove platform hedging from final coding specification.

## 34.3 Build cadence

Realistic timeline:

```text
Phase 0: 3–6 weeks depending on effort
Phase 1–3: 2–3 months
Expert implementation and validation: 3–6 months
Demo/live pilot: 3+ months
```

Total to meaningful live evidence:

```text
9–12 months minimum
```

## 34.4 VPS/hosting plan

Decision needed before demo:

```text
Provider
Location
Monitoring
Backup
Recovery process
```

## 34.5 Holdout threshold

v0.3 decision:

```text
≥0.80 required for release approval.
<0.70 hard fail.
0.70–0.80 research-only.
```

---

# 35. Review Checklist for This v0.3 Plan

The next review should focus on these questions.

## 35.1 Phase 0 review

```text
Are the Phase 0 gates too strict, too loose, or appropriate?
Are the 9 cells correctly designed?
Are the three data sources acceptable?
Should 2016–2025 be the correct full range?
Should Phase 0 use 0.50% risk or another fixed value?
Are the candidate expert definitions objective enough?
Should any candidate be replaced before testing?
```

## 35.2 Cost model review

```text
Is a 4-week spread logger enough?
Should the logger run longer?
Should P95 spread be the approval gate?
What broker cost assumptions should be included?
Should commission scenarios be broader?
```

## 35.3 Architecture review

```text
Is one Master EA still approved?
Are all mandatory modules included?
Should ConcentrationReporter be live-module or research-tool only?
Is DryRunMode specified strongly enough?
Is OrderGateway separation sufficient?
```

## 35.4 Risk review

```text
Is 0.25% live pilot risk appropriate?
Is 1% daily loss too strict or right?
Is 6% monthly loss appropriate?
Should daily cap force-close positions?
Are suspension and retirement gates appropriate?
```

## 35.5 Router review

```text
Are seven regimes enough?
Are any regimes missing for v1?
Is router freeze policy practical?
Is would_have_allowed_experts enough for audit?
```

## 35.6 Deployment review

```text
Should dedicated account be mandatory from demo onward?
Should external health monitor be required before live pilot?
Is disaster recovery detailed enough?
```

## 35.7 Final go/no-go review question

```text
Does this plan now prevent the known failure modes from V61, V77, V80, V85, and GBPUSD-style reviews?
```

---

# 36. Final Recommendation

This v0.3 plan should be reviewed once more before coding.

The recommended next action is:

```text
Approve v0.3 as the architecture and validation baseline.
Then execute Phase 0 statistical study.
Run passive spread logger in parallel.
Do not begin EA coding until PHASE0_VERDICT.md is complete.
```

The strongest possible result from this review would not be “start coding immediately.”

The strongest result would be:

```text
The review team agrees that Phase 0 is the correct next step.
The expert hypotheses are objective enough to test.
The gates are strict enough to prevent weak edges from reaching code.
The project will stop if no candidate expert passes.
```

That discipline is what protects the project from building an impressive system around an unproven edge.

---

# Appendix A — Hypothesis Template

```text
# Hypothesis: <Expert Name>

Expert:
Version:
Date:
Author:
SHA256:

## Mechanical Definition
<Exact rules. No ambiguity.>

## Expected Metrics
Expected trade count per year:        <N> ± 20%
Expected cost-adjusted PF:            <X> ± 0.3
Expected losing-month percentage:     <Y%> ± 10%
Expected worst single month:          <amount>
Expected max consecutive zero months: <Z>
Expected R-multiple distribution:     <description>

## Underlying XAU Behavior
<Why this should work on gold.>

## Failure Modes
<When it breaks.>

## Falsification Criteria
<What result rejects this hypothesis.>
```

---

# Appendix B — Phase 0 Result Template

```text
# Phase 0 Results: <Expert Name>

## Hypothesis
File:
SHA256 at registration:
SHA256 at result writing:

## 9-Cell Matrix
<table or CSV>

## Gate Summary
Gate 1 Multi-cell survival: PASS/FAIL
Gate 2 Sample size: PASS/FAIL
Gate 3 No catastrophic failure: PASS/FAIL
Gate 4 Concentration: PASS/FAIL
Gate 5 Activity: PASS/FAIL
Gate 6 Cost sensitivity: PASS/FAIL
Gate 7 Decile persistence: PASS/FAIL
Gate 8 Adversarial review: PASS/FAIL
Gate 9 Multi-symbol sanity: PASS/FAIL
Gate 10 Hypothesis match: PASS/FAIL

## Decile Test
<results>

## Adversarial Search
<trades reviewed, failure modes, logic-gap percentage>

## Multi-Symbol Check
EURUSD PF:
USDJPY PF:
XAU-specific justification if required:

## Hypothesis vs Reality
<compare expected vs actual>

## Final Verdict
PASS / FAIL

## If Failed
<reason>
```

---

# Appendix C — Consolidated Phase 0 Verdict Template

```text
# Phase 0 Consolidated Verdict

| Expert | 9-cell | Decile | Adversarial | Multi-symbol | Hypothesis Match | Final |
|---|---|---|---|---|---|---|
| Trend Pullback | PASS/FAIL | PASS/FAIL | PASS/FAIL | PASS/FAIL | PASS/FAIL | PASS/FAIL |
| Breakout-Retest | PASS/FAIL | PASS/FAIL | PASS/FAIL | PASS/FAIL | PASS/FAIL | PASS/FAIL |
| Range MR | PASS/FAIL | PASS/FAIL | PASS/FAIL | PASS/FAIL | PASS/FAIL | PASS/FAIL |

## Experts approved for Phase 1
<list>

## Experts rejected
<list with reason>

## Recommended action
Proceed with 3 experts / reduced v1 / stop project.

## Sign-off
Reviewer:
Date:
```

---

# Appendix D — Magic Numbers Template

```text
# magic_numbers.md

## New XAUUSD Master EA
Reserved: 920000–929999

Trend Pullback: 920000–920099
Range MR: 920100–920199
Breakout-Retest: 920200–920299
Fakeout deferred: 920300–920399
Future: 920400–929999

## Existing Occupied Ranges
V85 production: <fill>
V61 archive: <fill>
V77/V80: <fill>
Other EAs: <fill>
Manual reserved: <fill>

## Accounts
Broker:
Account ID:
Environment: Demo / Live
Active ranges:
```

---

# Appendix E — Filter Inventory Template

```text
# filter_inventory.md

| Filter Name | Module | Default | Tunable? | Tested Disabled? | Purpose | Overfit Risk |
|---|---|---|---|---|---|---|
| News blackout | NewsGuard | ON | Yes | No | Avoid news risk | Low |
| Spread guard | ExecutionGuard | ON | Yes | No | Avoid bad fills | Medium |
| ADX trend gate | Router | TBD | No after freeze | Yes | Regime classification | High |
```

Rule:

```text
Every configurable filter must be listed here before release.
```

---

# Appendix F — Release Checklist

```text
[ ] Git commit hash recorded
[ ] Version number updated
[ ] Router version recorded
[ ] Expert versions recorded
[ ] Magic numbers validated
[ ] Filter inventory complete
[ ] Unit tests pass
[ ] Phase 0 files included
[ ] Edge thesis files included
[ ] Backtest report included
[ ] Walk-forward report included
[ ] True holdout report included
[ ] Concentration report included
[ ] Cost model included
[ ] Stress tests passed
[ ] Lifecycle states valid
[ ] No retired expert enabled
[ ] Snapshot bundle created
[ ] EnableLiveTrading approval documented
```

---

# Appendix G — Dry-Run Decision Row Example

```text
2026-06-01 10:15:00 broker_time,
2026-06-01 06:15:00 UTC,
XAUUSD,
spread=18,
session=LONDON_MAIN,
news_state=NO_NEWS_RISK,
risk_state=NORMAL,
router_version=router_v1.0,
regime=TREND_WITH_PULLBACK,
allowed_expert=TREND_PULLBACK,
would_have_allowed_experts=TREND_PULLBACK;BREAKOUT_RETEST,
blocked_experts=RANGE_MR,
block_reason=RANGE_MR_PRICE_NOT_AT_EDGE,
mode=DRY_RUN,
trade_permission=WOULD_TRADE
```

---

# Appendix H — Final Coding Authorization Rule

Coding Phase 1 may begin only after:

```text
[ ] v0.3 plan reviewed
[ ] Phase 0 study approved for execution
[ ] Hypothesis templates approved
[ ] Data sources approved
[ ] Cost logger approved
[ ] Phase 0 verdict completed
[ ] At least one expert passes Phase 0
[ ] Review team signs Phase 1 authorization
```

If no expert passes Phase 0:

```text
Do not code the EA.
Research new candidate behaviors.
```

