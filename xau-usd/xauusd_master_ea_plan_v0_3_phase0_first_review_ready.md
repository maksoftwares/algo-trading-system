# XAUUSD Master EA Plan v0.3 — Phase-0-First, Review-Ready Specification

**Project:** XAUUSD Modular Master EA  
**Version:** v0.3  
**Status:** Review-ready planning document; **not yet coding-authorized**  
**Prepared date:** 2026-05-20  
**Platform commitment:** MT5 / MQL5  
**Primary symbol:** XAUUSD  
**Core decision:** Phase 0 statistical validation is mandatory before any trading expert is coded.  
**Recommended first action:** Execute Phase 0 statistical study and passive spread logger in parallel.  

---

## 0. Executive Summary

This v0.3 plan updates the prior XAUUSD Master EA architecture after two review cycles.

The main change is decisive:

> **Do not begin EA trading-system coding until Phase 0 proves that at least one proposed expert behavior has a defensible statistical edge.**

The prior architecture remains directionally correct:

```text
Regime first.
Risk second.
Signal third.
Execution last.
Default state = NO_TRADE.
```

However, the second review correctly identifies that architecture alone is not enough. A modular EA can still fail if the underlying expert behaviors are not real edges. Therefore, v0.3 promotes **Phase 0 Statistical Edge Validation** into the main plan as a mandatory gate before Phase 1.

The revised project is now split into two different types of work:

```text
Research / validation work:
  Phase 0 — Statistical edge study
  Passive spread logger
  Cost model calibration
  Holdout reservation
  Hypothesis registration

Engineering work:
  Phase 1 onward — Master EA dry-run shell, router, risk controls, execution guard, logging, then experts
```

The project should proceed only if Phase 0 confirms at least one candidate expert.

The v1 trading expert candidates are:

```text
1. Trend Pullback Expert
2. Breakout-Retest Expert
3. Range Mean-Reversion Expert
```

The previously proposed **Fakeout / Liquidity Sweep Expert** is deferred to v1.5 because it is harder to define objectively and more prone to subjective tuning.

The v1 regime set is reduced to seven regimes:

```text
TREND_WITH_PULLBACK
RANGE
COMPRESSION
BREAKOUT_RETEST
ABNORMAL_MARKET
NEWS_BLACKOUT
NO_TRADE
```

The v1 build must remain conservative:

```text
No martingale.
No unlimited grid.
No recovery mode.
No no-stop-loss trading.
No news trading.
No partial close in v1.
No trailing stop in v1.
No overnight holding in v1.
No weekend holding in v1.
Only one active expert at a time.
```

The next deliverable is not `MasterEA.mq5`.

The next deliverables are:

```text
hypothesis_trend_pullback.md
hypothesis_breakout_retest.md
hypothesis_range_mr.md
cost_model_measured.csv
phase0_trend_pullback_results.md
phase0_breakout_retest_results.md
phase0_range_mr_results.md
PHASE0_VERDICT.md
```

Only after `PHASE0_VERDICT.md` approves at least one expert should Phase 1 begin.

---

## 1. Source Documents Incorporated

This v0.3 document incorporates the decisions and requirements from the following internal review documents:

```text
1. xauusd_master_ea_plan_v0_2_review_ready.md
2. PLAN_V01_REVIEW_FINDINGS.md
3. PATH_TO_10.md
4. PHASE0_STATISTICAL_STUDY_SPEC.md
```

Key incorporated changes:

```text
- Phase 0 statistical validation is mandatory before Phase 1.
- Passive 4-week spread logger must run in parallel with Phase 0.
- v1 experts are Trend Pullback, Breakout-Retest, and Range MR.
- Fakeout / Liquidity Sweep is deferred to v1.5.
- Regime count is reduced to seven.
- Risk per trade is fixed, not a range.
- Holdout/train PF gate is tightened.
- Router is treated as an overfitting surface.
- Router must be versioned independently.
- MagicNumberAllocator is mandatory.
- ExpertLifecycleManager is mandatory.
- DryRunMode is mandatory.
- ServerTimeValidator is mandatory.
- Logging must include would-have-allowed experts.
- Concentration reporting is required before expert approval.
- The system must use a dedicated account.
- A true holdout set must remain untouched.
- Operational maturity requirements are documented for later phases.
```

---

## 2. Current Project Verdict

### 2.1 Can we code immediately?

**No — not trading logic.**

The architecture is approved directionally, but v0.3 requires Phase 0 edge validation before coding any expert.

### 2.2 Can we build anything immediately?

Yes, but only research and infrastructure-adjacent tools that do not imply strategy approval:

```text
Allowed immediately:
  - Phase 0 research package
  - Hypothesis templates
  - Data conversion scripts
  - Backtest result templates
  - Passive spread logger
  - Cost model aggregation script
  - SHA256 hypothesis-locking utility
  - Result-report generator

Not allowed yet:
  - Expert trading code
  - OrderSend logic
  - Live trading
  - News trading
  - Parameter optimization
  - Router tuning based on expert P&L
```

### 2.3 What must happen before Phase 1?

Phase 1 is authorized only if:

```text
1. At least one expert passes Phase 0.
2. cost_model_measured.csv exists or an approved temporary cost model is signed.
3. true_holdout_period.md is created and locked.
4. magic_numbers.md is drafted.
5. V85 coexistence / replacement decision is answered.
6. dedicated account decision is answered.
7. platform commitment remains MT5/MQL5.
8. PHASE0_VERDICT.md recommends proceeding.
```

---

## 3. Non-Negotiable Principles

These are not optional.

## 3.1 No-trade is the default

The system should block trading unless all of the following are true:

```text
Market regime is objectively classified.
News state allows trading.
Session state allows trading.
Spread is acceptable.
Slippage risk is acceptable.
Risk caps are not breached.
Expert lifecycle status allows trading.
Exactly one expert is active.
The selected expert has a valid setup.
Position Manager can define hard SL and TP.
Execution Guard approves the order.
```

If anything is unclear:

```text
NO_TRADE
```

## 3.2 Evidence before code

No expert is coded until its behavior passes Phase 0.

Architecture is necessary but not sufficient. A beautiful modular EA built around non-existent edges is still a bad system.

## 3.3 Hard gates, not advisory targets

Approval criteria must be implemented as code-readable constants and test reports.

A gate is not a suggestion. It is a blocker.

## 3.4 Router is an overfitting surface

The Regime Router is not harmless infrastructure. It can become the largest curve-fitting mechanism in the system if thresholds are adjusted to rescue weak experts.

Therefore:

```text
Router thresholds are set from objective market distributions.
Router version is logged.
Router changes require revalidation.
Router logs blocked and would-have-allowed experts.
```

## 3.5 One active trading expert in v1

In v1, only one expert can be allowed to trade at any moment.

Multiple experts may score hypothetically in dry-run, but only the router-selected expert may generate an executable signal.

## 3.6 Risk is centralized

No expert may decide lot size independently.

Every trade plan must pass through:

```text
Risk Manager
Execution Guard
Position Manager
Lifecycle Manager
```

## 3.7 No hidden filters

Every filter must be listed in `filter_inventory.md`.

If a filter exists in source code, it must be documented.

If a filter is configurable, the default must be documented.

If a filter can be disabled, the disabled condition must be tested or explicitly marked untested.

## 3.8 No silent retirement bypass

A `.set` file cannot reactivate a retired expert.

Only a new versioned release with revalidated approval evidence can reactivate a retired expert.

## 3.9 Cost realism before profitability claims

Every backtest must be evaluated after modeled costs.

Eventually, every approval gate must be re-run against measured P95 spread and measured slippage.

## 3.10 Dedicated account

The new EA should run on a dedicated account.

It should not share an account with:

```text
V85
manual trades
other EAs
copy-trading tools
experimental scripts
```

If this is not possible during dry-run, the exception must be documented and no live orders may be possible.

---

## 4. Versioned Roadmap

The project is now divided into explicit gates.

```text
Phase 0     Statistical edge validation and spread logging
Phase 1     Dry-run Master EA shell, no experts, no OrderSend
Phase 2     Safety infrastructure, risk, execution, lifecycle, magic numbers
Phase 3     Versioned Regime Router and market-state logging
Phase 4     First approved expert, dry-run only
Phase 5     Single-expert backtest and validation
Phase 6     Multi-expert portfolio router validation
Phase 7     Demo forward test on VPS
Phase 8     Slippage recalibration and revalidation
Phase 9     Small live pilot
Phase 10    Production scale ladder and quarterly review cycle
```

Critical sequence:

```text
Phase 0 must pass before Phase 1.
Phase 1 must run 5 clean trading days before Phase 2/3 expansion.
Each expert must pass research, backtest, walk-forward, and demo gates before live trading.
```

---

# PART A — PHASE 0: STATISTICAL EDGE VALIDATION

---

## 5. Phase 0 Purpose

Phase 0 exists to answer one question:

> Does the proposed expert behavior have positive expectancy on XAUUSD before tuning begins?

Phase 0 must be completed before any expert code is written.

The aim is not to produce a polished EA. The aim is to reject weak ideas early.

A failed Phase 0 is not a failure of the project. It is a success of the process because it prevents months of engineering work around a non-existent edge.

---

## 6. Phase 0 Candidate Experts

The three v1 candidates are:

```text
1. Trend Pullback Expert
2. Breakout-Retest Expert
3. Range Mean-Reversion Expert
```

Each expert must have:

```text
- A pre-registered hypothesis
- A mechanical setup definition
- A fixed stop and target model
- No optimized parameters
- No added filters after results are observed
- A full 9-cell result matrix
- A decile persistence test
- An adversarial failure review
- A multi-symbol consistency check
- A final pass/fail verdict
```

---

## 7. Phase 0 Data Requirements

| Item | Requirement |
|---|---|
| Primary symbol | XAUUSD |
| Timeframes | M1, M5, M15, H1, H4, D1 |
| Date range | 2016-01-01 through 2025-12-31 |
| Tick sources | Capital.com, Pepperstone, Dukascopy |
| Comparison symbols | EURUSD, USDJPY |
| Cost assumptions | Best-case, median, P95 spread |
| Starting balance | $10,000 per cell |
| Phase 0 risk per trade | 0.50% fixed |
| Parameter changes across cells | Forbidden |
| Post-result filter additions | Forbidden |

Important:

```text
Phase 0 uses 0.50% fixed risk per trade only for research comparability.
v1 live pilot uses 0.25% risk per trade.
```

---

## 8. Phase 0 Pre-Registered Hypotheses

Before testing, create one file per candidate:

```text
hypothesis_trend_pullback.md
hypothesis_breakout_retest.md
hypothesis_range_mr.md
```

Each file must be SHA256 locked.

Template:

```text
# Hypothesis: <Expert Name>

Expert:
Hypothesis date:
Hypothesis version:
Author:
SHA256 at registration:

## Mechanical definition

<unambiguous entry and exit rules>

## Expected behavior

Expected trade count per year:        <N> ± 20%
Expected cost-adjusted PF:            <X> ± 0.3
Expected losing-month percentage:     <Y%> ± 10%
Expected worst single month:          $<-N>
Expected max consecutive zero months: <Z>
Expected R-multiple distribution:     <description>

## Why this behavior should exist

<2–3 paragraphs describing the market behavior being exploited>

## What would falsify it

Examples:
- Fails fewer than 7 of 9 cells
- Trade count below 40 in any cell
- Cost sensitivity collapses under P95 spread
- One trade contributes more than 10% of P&L
- More than 3 consecutive zero-trade months
- Decile test fails
- Multi-symbol check fails without a defensible XAU-specific explanation

## Forbidden after registration

- Parameter changes
- New filters
- Session restrictions
- News exclusions
- Level-strength rules
- Cherry-picking
- Removing outliers
```

The SHA256 must be recorded in both:

```text
hypothesis_<expert>.md
PHASE0_VERDICT.md
```

---

## 9. Phase 0 Candidate Mechanical Definitions

These are starting definitions. The team may refine wording before registration, but once registered, the logic is locked.

## 9.1 Trend Pullback Expert — Phase 0 Draft

### Long setup

```text
H1 trend:
  EMA(50) > EMA(200)
  EMA(50) slope over last 20 H1 bars > 0

M15 pullback:
  Price retraces to within 0.5 × ATR(14, H1) of EMA(21, M15)

M5 confirmation:
  Bullish engulfing candle
  OR pin bar with lower wick ≥ 2 × candle body

Entry:
  Market entry at close of confirmation candle

Stop:
  Pullback low − 0.1 × ATR(14, M15)

Target:
  1.5R

Management:
  No scaling
  No trailing
  No break-even in Phase 0
```

### Short setup

Mirror logic:

```text
H1 trend:
  EMA(50) < EMA(200)
  EMA(50) slope over last 20 H1 bars < 0

M15 pullback:
  Price retraces to within 0.5 × ATR(14, H1) of EMA(21, M15)

M5 confirmation:
  Bearish engulfing candle
  OR pin bar with upper wick ≥ 2 × candle body

Entry:
  Market entry at close of confirmation candle

Stop:
  Pullback high + 0.1 × ATR(14, M15)

Target:
  1.5R
```

### Forbidden in Phase 0

```text
No session filter
No news filter
No spread filter beyond cost model
No ADX filter
No RSI filter
No parameter tuning
No EMA replacement
No target optimization
```

---

## 9.2 Breakout-Retest Expert — Phase 0 Draft

### Long setup

```text
Level:
  Previous day high
  OR weekly high
  OR M5 swing high with 4+ bars on each side

Break:
  M5 candle closes above level by ≥ 0.3 × ATR(14, M5)

Retest:
  Price returns to within 5 points of broken level within 20 M5 bars after break

Hold condition:
  M5 retest candle low does not close below broken level

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
Level:
  Previous day low
  OR weekly low
  OR M5 swing low with 4+ bars on each side

Break:
  M5 candle closes below level by ≥ 0.3 × ATR(14, M5)

Retest:
  Price returns to within 5 points of broken level within 20 M5 bars after break

Hold condition:
  M5 retest candle high does not close above broken level

Confirmation:
  Bearish M5 candle after retest

Entry:
  Sell stop below retest low

Stop:
  Retest high + 0.1 × ATR(14, M5)

Target:
  1.5R
```

### Forbidden in Phase 0

```text
No round-number filter
No session filter
No level-strength score
No volume filter
No news filter
No retest-depth optimization
No adding "clean break" subjective language
```

---

## 9.3 Range Mean-Reversion Expert — Phase 0 Draft

### Long setup

```text
H1 condition:
  ADX(14) < 20 for last 20 H1 bars

Range identification:
  At least 3 touches of upper boundary
  At least 3 touches of lower boundary
  Touches must occur within last 50 M15 bars

Range width:
  Range width ≥ 2 × ATR(14, M15)

Location:
  Price reaches lower boundary ± 0.2 × ATR(14, M15)

Confirmation:
  Rejection candle with lower wick ≥ 2 × candle body

Entry:
  Limit order at lower boundary

Stop:
  Range low − 0.3 × ATR(14, M15)

Target:
  Opposite range boundary
```

### Short setup

Mirror logic:

```text
H1 condition:
  ADX(14) < 20 for last 20 H1 bars

Range identification:
  At least 3 touches of upper boundary
  At least 3 touches of lower boundary
  Touches must occur within last 50 M15 bars

Range width:
  Range width ≥ 2 × ATR(14, M15)

Location:
  Price reaches upper boundary ± 0.2 × ATR(14, M15)

Confirmation:
  Rejection candle with upper wick ≥ 2 × candle body

Entry:
  Limit order at upper boundary

Stop:
  Range high + 0.3 × ATR(14, M15)

Target:
  Opposite range boundary
```

### Forbidden in Phase 0

```text
No Asia-only filter
No discretionary range validation
No "clean range" subjective condition
No news filter
No spread-width filter
No support/resistance strength filter
No post-failure rescue filter
```

---

## 10. Phase 0 9-Cell Test Matrix

For each expert, run all nine cells:

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

Rules:

```text
Same logic in every cell.
Same parameters in every cell.
Same starting balance in every cell.
Same risk-per-trade in every cell.
No result-driven filter changes.
No excluding outliers.
No switching brokers to rescue results.
No optimizing by cell.
```

---

## 11. Phase 0 Per-Cell Metrics

Each cell must produce the following CSV columns:

```text
cell_id
expert_name
time_window
tick_source
cost_model
starting_balance
risk_per_trade
trade_count
win_rate
profit_factor
total_return_pct
total_pnl_usd
avg_trade_R
median_trade_R
max_drawdown_pct
max_drawdown_usd
worst_month_usd
best_month_usd
losing_month_pct
max_consecutive_zero_trade_months
max_consecutive_losing_months
largest_single_trade_pct_of_pnl
top5_trades_pct_of_pnl
p95_cost_pf_to_best_case_pf_ratio
notes
```

---

## 12. Phase 0 Hard Gates

An expert passes Phase 0 only if all gates pass.

| Gate | Requirement | Result Type |
|---|---|---|
| Multi-cell survival | PF ≥ 1.30 in at least 7 of 9 cells | Hard pass/fail |
| Sample size | Trade count ≥ 40 in every cell | Hard pass/fail |
| Catastrophic failure | No cell DD > 30%; no cell return < -25% | Hard pass/fail |
| Single-trade concentration | Largest single trade ≤ 10% of net P&L | Hard pass/fail |
| Top-5 concentration | Top 5 trades ≤ 40% of net P&L | Hard pass/fail |
| Activity | Max zero-trade months ≤ 3 in every cell | Hard pass/fail |
| Cost sensitivity | P95-cost PF / best-case PF ≥ 0.50 per window | Hard pass/fail |
| Decile persistence | PF > 1.0 in at least 8 of 10 deciles | Hard pass/fail |
| Decile dominance | No decile PF > 2 × median PF | Hard pass/fail |
| Multi-symbol check | EURUSD and USDJPY PF ≥ 0.90, or XAU-specific reason documented | Hard pass/fail or justified exception |
| Adversarial review | Logic-gap failures ≤ 25% of losing trades | Hard pass/fail |
| Hypothesis match | Results reasonably match pre-registered expectations | Review gate |

If a gate fails:

```text
The expert is rejected from v1.
Do not add filters to rescue it.
Do not tune parameters to rescue it.
Do not reframe failure as "close enough."
```

The only acceptable next steps after failure are:

```text
1. Accept rejection.
2. Research a new candidate behavior.
3. Write a new hypothesis.
4. Restart Phase 0 for that new behavior.
```

---

## 13. Phase 0 Decile Test

After the 9-cell matrix passes, split the 2016–2025 Capital.com dataset into ten equal-time deciles.

For each expert:

```text
Run locked logic on each decile independently.
Record PF, trade count, drawdown, and P&L.
```

Acceptance:

```text
PF > 1.0 in at least 8 of 10 deciles.
No decile PF > 2.0 × median PF.
No decile trade count < 10.
```

If a decile fails, create:

```text
phase0_<expert>_decile_failures.md
```

Required contents:

```text
Failed decile period
Market context
Failure type
Trade count
PF
Drawdown
Whether failure suggests router opportunity or strategy fragility
```

---

## 14. Phase 0 Adversarial Counter-Example Search

For each expert, dedicate one full working day to trying to break the idea.

Procedure:

```text
1. Extract losing trades from the 9-cell result set.
2. Manually inspect each losing trade.
3. Label each loss:
   - Acceptable market loss
   - Router-opportunity failure
   - Logic-gap failure
   - Execution-cost failure
   - Ambiguous / needs review
4. Count failure modes.
5. Document chart examples.
```

Expert-specific adversarial questions:

### Trend Pullback

```text
How many pullbacks were actually trend reversals?
How often did EMA trend bias lag too far behind?
How often did confirmation candle appear after the good entry was gone?
How often was 1.5R unrealistic before structure resistance/support?
```

### Breakout-Retest

```text
How often did retest appear to hold but fail within 24 hours?
How often did the break become a bull trap or bear trap?
How often did buy-stop/sell-stop trigger after the move had already exhausted?
How often did level selection create duplicate or clustered signals?
```

### Range MR

```text
How often did valid ranges break immediately after entry?
How often did ADX remain low before a major expansion?
How often did range width look acceptable but reward after costs was poor?
How often did "three touches" identify noisy chop rather than a tradable range?
```

Acceptance:

```text
Logic-gap failures ≤ 25% of total losing trades.
Router-opportunity failures documented for later router design.
```

If logic gaps exceed 25%, the mechanical definition is too loose.

---

## 15. Phase 0 Multi-Symbol Consistency Check

Run the identical mechanical logic on:

```text
EURUSD
USDJPY
```

Same period:

```text
2016-01-01 through 2025-12-31
```

Acceptance:

```text
EURUSD PF ≥ 0.90
USDJPY PF ≥ 0.90
```

If either is below 0.70, the edge is treated as XAU-specific and must be defended.

Acceptable XAU-specific explanations:

```text
Gold-specific benchmark/fix behavior
COMEX futures price-discovery behavior
Gold safe-haven flows
Gold's relationship to real yields
Gold's correlation breakdown during USD stress regimes
Gold-specific liquidity behavior around London/New York overlap
```

Unacceptable explanations:

```text
"Gold is more volatile."
"It looked better on XAU."
"We tuned it for XAU."
"Gold respects technical levels better."
```

---

## 16. Phase 0 Deliverables

Per expert:

```text
hypothesis_<expert>.md
phase0_<expert>_results.csv
phase0_<expert>_results.md
phase0_<expert>_decile_results.csv
phase0_<expert>_adversarial_review.md
phase0_<expert>_multi_symbol_check.md
```

Consolidated:

```text
PHASE0_VERDICT.md
cost_model_initial.md
data_source_inventory.md
true_holdout_period.md
```

`PHASE0_VERDICT.md` must include:

```text
| Expert | 9-cell | Decile | Adversarial | Multi-symbol | Hypothesis match | Final |
|---|---|---|---|---|---|---|
| Trend Pullback | PASS/FAIL | PASS/FAIL | PASS/FAIL | PASS/FAIL | PASS/FAIL | PASS/FAIL |
| Breakout-Retest | PASS/FAIL | PASS/FAIL | PASS/FAIL | PASS/FAIL | PASS/FAIL | PASS/FAIL |
| Range MR | PASS/FAIL | PASS/FAIL | PASS/FAIL | PASS/FAIL | PASS/FAIL | PASS/FAIL |
```

Decision tree:

```text
3 experts pass:
  Proceed to Phase 1 with 3-expert v1.

1–2 experts pass:
  Proceed to Phase 1 with reduced v1.
  Empty expert slots remain disabled.

0 experts pass:
  Stop.
  Do not build the EA.
  Research replacement behaviors.
```

---

## 17. Phase 0 Timeline

Focused estimate:

| Week | Work |
|---:|---|
| 1 | Data acquisition, data normalization, hypothesis registration, SHA locking |
| 2 | 27 backtest cells: 3 experts × 9 cells |
| 3 | Decile tests, multi-symbol checks, adversarial review |
| 4 | Result write-up, gate evaluation, consolidated verdict |

Part-time estimate:

```text
6–8 weeks
```

Approximate cash cost:

```text
Capital.com data: $0 if available through existing demo/history
Dukascopy data: $0
Pepperstone data: $0–$100 depending on source
Python tooling: $0
Time: 80–120 focused hours
```

---

# PART B — COST MODEL AND SPREAD LOGGER

---

## 18. Passive 4-Week Spread Logger

The passive spread logger runs in parallel with Phase 0.

It does not trade.

It records:

```text
timestamp_broker
timestamp_utc
timestamp_local
symbol
bid
ask
spread_points
spread_money_per_lot
session
day_of_week
hour_of_day
is_rollover_window
is_news_window
calendar_source
terminal_connected
broker_trade_allowed
```

Frequency:

```text
At least once per M1 bar
Optionally every tick if storage allows
```

Output:

```text
spread_log_raw.csv
cost_model_measured.csv
cost_model_summary.md
```

---

## 19. Required Cost Model Statistics

The logger must produce:

```text
Median spread by hour of day
P75 spread by hour of day
P95 spread by hour of day
Median spread by day of week
P95 spread by day of week
Rollover spread distribution
News-window spread distribution
Session-level spread distribution
Maximum observed spread per session
Spread abnormality frequency
```

Session buckets:

```text
Asia
Pre-London
London Open
London Main
London Fix Window
New York Pre-Data
New York Open
New York Main
New York Afternoon
Rollover
Friday Close
Monday Open
```

---

## 20. Cost Model Usage

Approval gates should eventually use:

```text
measured P95 spread
measured slippage
commission scenario
broker-specific contract size
symbol point size
tick value
```

Until measured spread exists, use a temporary signed cost model:

```text
cost_model_initial.md
```

It must state:

```text
Broker
Account type
Symbol name
Digits
Point size
Contract size
Typical spread assumption
Median spread assumption
P95 spread assumption
Commission assumption
Slippage assumption
Source of assumptions
Expiration date of assumptions
```

Temporary assumptions must be replaced by measured costs before live pilot.

---

## 21. Multi-Broker Cost Scenarios

Even if Capital.com is the planned first demo broker, every expert must be evaluated under:

```text
Capital.com zero-commission model
Raw-spread + $3/lot commission model
Raw-spread + $7/lot commission model
P95 spread stress model
```

Required output:

```text
cost_floor_report_<expert>.md
```

This report answers:

```text
At what cost level does the expert fail?
Is the expert viable only under one broker model?
Does the expert survive if broker costs worsen?
```

---

# PART C — PROJECT DECISIONS NOW LOCKED IN v0.3

---

## 22. Platform Decision

The project is now committed to:

```text
MT5 / MQL5
```

The plan should no longer hedge between MT4, Python live execution, cTrader, NinjaTrader, or TradingView execution.

Python is allowed for:

```text
research
statistical analysis
backtest cross-checking
report generation
cost model aggregation
```

But live trading implementation is:

```text
MT5 Expert Advisor
MQL5
class-based .mqh modules
one master .mq5 shell
```

---

## 23. v1 Expert Decision

v1 candidates:

```text
Trend Pullback
Breakout-Retest
Range MR
```

v1.5 candidate:

```text
Fakeout / Liquidity Sweep
```

v2+ candidates:

```text
Trend Continuation
Compression Breakout
Reversal
News Spike Continuation
Spike Fade
Gap / Abnormal Market Trading
Multi-symbol experts
External macro-filter experts
Machine-learning modules
```

Important:

```text
A candidate is not an approved expert.
Only Phase 0 passing candidates become approved for Phase 1.
```

---

## 24. v1 Risk Decision

v1 live pilot base risk:

```text
RiskPerTrade = 0.25%
```

Not a range.

Phase 0 research risk:

```text
ResearchRiskPerTrade = 0.50%
```

Reason:

```text
Phase 0 uses fixed 0.50% risk for comparability across cells.
Live pilot uses 0.25% to limit execution uncertainty and drawdown.
```

Initial risk caps:

```text
MaxDailyLoss = 1.00% of start-of-day equity
MaxWeeklyLoss = 3.00% of start-of-week equity
MaxMonthlyLoss = 6.00% of start-of-month equity
MaxOpenTrades = 1 in v1
MaxTradesPerDay = 4
MaxTradesPerSession = 2
MaxConsecutiveLossesBeforeReducedRisk = 3
MaxConsecutiveLossesBeforeLock = 5
```

Risk accounting:

```text
Daily loss is equity-based and includes floating drawdown.
Weekly loss is equity-based and includes floating drawdown.
Monthly loss is equity-based and includes floating drawdown.
```

Daily cap action:

```text
Close all EA-managed positions.
Block new trades until next trading day.
Log event.
Dashboard shows LOCKED_DAILY_LOSS.
```

Monthly cap action:

```text
Close all EA-managed positions.
Switch EA to dry-run for rest of month.
Manual review required.
```

---

## 25. Walk-Forward Gate Decision

Use two thresholds:

```text
Hard fail threshold:
  Holdout / train PF < 0.70

Preferred approval threshold:
  Holdout / train PF ≥ 0.80
```

Interpretation:

```text
PF ratio < 0.70:
  Reject.

0.70 ≤ PF ratio < 0.80:
  Conditional review only.
  Must pass all other gates strongly.
  Cannot go live without reviewer approval.

PF ratio ≥ 0.80:
  Pass this specific gate, assuming all other gates pass.
```

Initial train window:

```text
24 months minimum
36 months preferred
```

Validation window:

```text
3 months
```

Step:

```text
3 months
```

Every fold must pass; averages cannot hide a catastrophic fold.

---

## 26. Concentration Gate Decision

Updated concentration gates:

```text
Largest single trade contribution ≤ 10%
Top 5 trades contribution ≤ 40%
Single expert contribution to portfolio P&L ≤ 35%
Single month contribution to net P&L ≤ 25%
Max consecutive zero-trade months ≤ 3
```

If concentration fails:

```text
Expert remains dry-run only or is rejected.
```

---

## 27. Asia Trading Decision

v1 default:

```text
Asia entries disabled.
Asia is used for mapping levels only.
```

Allowed Asia uses:

```text
Asian high
Asian low
Asian range width
Pre-London compression state
Liquidity reference levels
```

Not allowed in v1 unless Phase 0 explicitly proves it:

```text
Opening new trades during Asia session
Asia-only range scalping
Asia fakeout trading
```

This closes a major curve-fit pathway.

---

## 28. Portfolio Backtest Definition

Portfolio backtest means:

```text
The router-selected aggregate of all approved experts,
using the same router logic,
with only one active expert allowed at a time,
with centralized risk caps,
centralized position management,
centralized execution assumptions,
and real trade conflicts resolved exactly as live code would resolve them.
```

It does **not** mean:

```text
Adding independent expert backtest results together.
Selecting the best expert per period after the fact.
Averaging equity curves.
Ignoring overlapping signals.
Ignoring risk caps.
```

Portfolio backtest output must include:

```text
per-expert P&L share
per-regime P&L share
per-month P&L share
single-largest-trade contribution
top-5-trade contribution
router-blocked signals
would-have-allowed experts
risk-lock events
```

---

## 29. Stable Live Pilot Definition

A live pilot is considered stable only if all are true:

```text
At least 30 live trades
At least 3 calendar months
PF within ±20% of pre-registered expected band
Drawdown within expected band
No unauthorized orders
No magic-number collision
No risk-cap breach
No repeated execution failures
No unexplained router behavior
No expert manually reactivated after lifecycle block
```

If fewer than 30 trades occur within 3 months:

```text
Continue pilot until either 30 trades occur or 6 months pass.
```

If 6 months pass with insufficient trades:

```text
Review activity gate and edge viability.
Do not scale.
```

---

# PART D — SYSTEM ARCHITECTURE

---

## 30. Master EA Architecture

The system is one master EA with internal class-based modules.

```text
XAUUSD_MasterEA.mq5
│
├── /include/core/
│   ├── MarketDataEngine.mqh
│   ├── FeatureEngine.mqh
│   ├── SessionEngine.mqh
│   ├── NewsGuard.mqh
│   ├── RegimeRouter.mqh
│   ├── RiskManager.mqh
│   ├── ExecutionGuard.mqh
│   ├── PositionManager.mqh
│   ├── Logger.mqh
│   ├── Dashboard.mqh
│   ├── DryRunMode.mqh
│   ├── MagicNumberAllocator.mqh
│   ├── ExpertLifecycleManager.mqh
│   ├── ServerTimeValidator.mqh
│   ├── ConcentrationReporter.mqh
│   └── ConfigValidator.mqh
│
├── /include/experts/
│   ├── IExpert.mqh
│   ├── TrendPullbackExpert.mqh
│   ├── BreakoutRetestExpert.mqh
│   └── RangeMRExpert.mqh
│
├── /include/utils/
│   ├── TimeUtils.mqh
│   ├── MathUtils.mqh
│   ├── SymbolUtils.mqh
│   ├── FileUtils.mqh
│   └── HashUtils.mqh
│
├── /config/
│   ├── xauusd_master_v1.set
│   ├── magic_numbers.md
│   ├── filter_inventory.md
│   ├── router_thresholds.md
│   └── cost_model_initial.md
│
├── /logs/
│   ├── decision_log.csv
│   ├── trade_log.csv
│   ├── risk_log.csv
│   ├── execution_log.csv
│   ├── lifecycle_log.csv
│   ├── router_log.csv
│   ├── spread_log_raw.csv
│   └── error_log.csv
│
└── /tools/
    ├── phase0_runner.py
    ├── spread_aggregator.py
    ├── concentration_reporter.py
    ├── snapshot.ps1
    ├── release_check.ps1
    └── hash_hypothesis.py
```

---

## 31. Runtime Decision Flow

```text
OnTick()
  ↓
MarketDataEngine.Update()
  ↓
New-bar detection
  ↓
FeatureEngine.Update()
  ↓
SessionEngine.Update()
  ↓
NewsGuard.Update()
  ↓
ServerTimeValidator.Check()
  ↓
RiskManager.Update()
  ↓
ExpertLifecycleManager.Update()
  ↓
RegimeRouter.Classify()
  ↓
Experts.ScoreDryRun()
  ↓
RegimeRouter.SelectAllowedExpert()
  ↓
SelectedExpert.BuildSignal()
  ↓
RiskManager.Approve()
  ↓
ExecutionGuard.Approve()
  ↓
PositionManager.BuildTradePlan()
  ↓
DryRunMode / Order Layer
  ↓
Logger.WriteDecision()
  ↓
Dashboard.Update()
```

In Phase 1:

```text
No OrderSend exists.
All orders are would-have-traded rows only.
```

In later phases:

```text
OrderSend is wrapped behind ExecutionGuard and DryRunMode.
No expert calls OrderSend directly.
```

---

## 32. Standard Expert Interface

Every expert implements:

```text
class IExpert {
  string Name();
  string Version();

  bool IsEnabledByConfig();
  bool IsAllowedByLifecycle();
  bool IsCompatibleWithRegime(RegimeState regime);

  ExpertScore ScoreSetup(MarketContext ctx);
  TradeSignal BuildSignal(MarketContext ctx);

  string ExplainSetup();
  string ExplainNoTrade();
}
```

Standard signal object:

```text
TradeSignal {
  string expert_name;
  string expert_version;
  string symbol;
  ENUM_ORDER_TYPE direction;
  EntryType entry_type;
  double entry_price;
  double stop_loss;
  double take_profit;
  double invalidation_level;
  double risk_reward;
  double confidence_score;
  string setup_type;
  string regime;
  string reason_code;
  string human_reason;
  datetime signal_time_broker;
  datetime signal_time_utc;
}
```

Experts suggest trades.

They do not:

```text
Place orders.
Calculate lot size.
Override risk caps.
Override execution rules.
Override lifecycle status.
Override router selection.
```

---

## 33. Module Specifications

---

## 33.1 MarketDataEngine

Purpose:

```text
Collect and normalize all broker, tick, candle, and symbol data.
```

Responsibilities:

```text
Read Bid and Ask.
Read spread.
Read tick volume.
Read M1, M5, M15, H1, H4, D1 candles.
Track previous day high/low.
Track previous week high/low.
Track current session high/low.
Track broker server time.
Track UTC time.
Track local machine time.
Read symbol digits, point size, tick value, contract size.
Detect symbol rename/suffix.
Detect missing candles.
Detect abnormal candles.
```

Outputs:

```text
MarketSnapshot
CandleSeries
SymbolMetadata
TimeSnapshot
SpreadSnapshot
```

Required checks:

```text
_symbol_exists
_symbol_trade_allowed
_symbol_digits_valid
_tick_value_valid
_contract_size_valid
_time_available
_candles_available
```

---

## 33.2 FeatureEngine

Purpose:

```text
Convert raw market data into reusable features.
```

Features:

```text
ATR by timeframe
ADX by timeframe
EMA values
EMA slope
Swing highs/lows
Break of structure
Change of character
Candle body size
Candle wick ratios
Range width
Distance from prior high/low
Distance from EMA
Compression state
Volatility percentile
Spread percentile
Session range statistics
```

Rule:

```text
FeatureEngine does not produce trade signals.
```

It only produces inputs for router and experts.

---

## 33.3 SessionEngine

Sessions:

```text
ASIA
PRE_LONDON
LONDON_OPEN
LONDON_MAIN
LONDON_FIX_WINDOW
NEW_YORK_PRE_DATA
NEW_YORK_OPEN
NEW_YORK_MAIN
NEW_YORK_AFTERNOON
ROLLOVER
FRIDAY_CLOSE
MONDAY_OPEN
HOLIDAY_THIN_LIQUIDITY
UNKNOWN
```

Outputs:

```text
current_session
session_start_time
session_end_time
session_high
session_low
session_range
time_to_next_session
is_rollover_window
is_friday_close_window
is_monday_open_window
is_london_fix_window
asia_high
asia_low
asia_range
```

v1 decision:

```text
Asia entries disabled.
Asia levels may be used.
```

---

## 33.4 NewsGuard

v1 rule:

```text
No news trading.
High-impact USD news blocks new entries.
CPI, NFP, and FOMC require exposure closure.
```

News states:

```text
NO_NEWS_RISK
PRE_NEWS_BLACKOUT
NEWS_RELEASE_ACTIVE
POST_NEWS_COOLDOWN
MANUAL_NEWS_LOCKDOWN
CALENDAR_SOURCE_DOWN
FALLBACK_SCHEDULE_ACTIVE
```

Default timing:

```text
Pre-news blackout: 30 minutes
Post-news cooldown: 30 minutes
```

Forced close events:

```text
CPI
NFP
FOMC rate decision
FOMC press conference
```

Calendar sources:

```text
Primary: MT5 economic calendar if reliable
Fallback: manually maintained high-impact USD schedule
Manual override: user-defined lockdown windows
```

Required log field:

```text
news_block_source = API / FALLBACK / MANUAL / NONE
```

---

## 33.5 RegimeRouter

Purpose:

```text
Classify market state and select exactly one allowed expert.
```

v1 regimes:

```text
TREND_WITH_PULLBACK
RANGE
COMPRESSION
BREAKOUT_RETEST
ABNORMAL_MARKET
NEWS_BLACKOUT
NO_TRADE
```

Router must output:

```text
router_version
active_regime
allowed_expert
blocked_experts
would_have_allowed_experts
trade_permission
block_reason
confidence_score
threshold_set_version
```

Router rules:

```text
Only one active expert may trade in v1.
Router thresholds are set from objective distribution stats.
Router version is independent from expert versions.
Router logs every decision.
Router changes require revalidation.
Router cannot be silently tuned to improve an expert's backtest.
```

Example decision hierarchy:

```text
If server time invalid:
  NO_TRADE

Else if risk locked:
  NO_TRADE

Else if news blackout:
  NEWS_BLACKOUT

Else if spread extreme:
  NO_TRADE

Else if abnormal tick/gap:
  ABNORMAL_MARKET

Else if trend pullback conditions:
  TREND_WITH_PULLBACK

Else if breakout-retest conditions:
  BREAKOUT_RETEST

Else if range conditions:
  RANGE

Else if compression:
  COMPRESSION

Else:
  NO_TRADE
```

---

## 33.6 RiskManager

Purpose:

```text
Centralize risk and account protection.
```

Controls:

```text
Risk per trade
Daily loss
Weekly loss
Monthly loss
Total drawdown
Open positions
Trades per day
Trades per session
Risk reduction after losing streak
Risk lock after loss streak
Exposure cap
Minimum and maximum stop distance
Minimum reward-to-risk
```

v1 risk constants:

```text
kRiskPerTrade = 0.0025
kMaxDailyLoss = 0.0100
kMaxWeeklyLoss = 0.0300
kMaxMonthlyLoss = 0.0600
kMaxOpenTrades = 1
kMaxTradesPerDay = 4
kMaxTradesPerSession = 2
kMaxConsecutiveLossesReducedRisk = 3
kMaxConsecutiveLossesLock = 5
```

Risk modes:

```text
NORMAL
REDUCED
DEFENSIVE
LOCKED_DAILY_LOSS
LOCKED_WEEKLY_LOSS
LOCKED_MONTHLY_LOSS
LOCKED_MANUAL
LOCKED_EXECUTION_FAILURE
```

Lot sizing inputs:

```text
Account equity
Risk percent
Stop distance
Tick value
Tick size
Contract size
Minimum lot
Maximum lot
Lot step
Margin requirement
```

No expert may override the lot size.

---

## 33.7 ExecutionGuard

Purpose:

```text
Block bad orders before they reach broker.
```

Checks:

```text
Spread
Dynamic spread vs median
Slippage / price jump
Minimum stop distance
Freeze level
Margin availability
Symbol trade mode
Broker connection
Order rejection count
Bad tick status
Rollover window
News state
```

Initial v1 spread rule:

```text
Block if current_spread > max(30 points, 1.5 × 20-bar median spread)
```

Important:

```text
The absolute 30-point threshold must be validated against broker symbol digits before live use.
```

Initial slippage rule:

```text
Block market orders if current Ask - lastQuote.Ask > 5 points for buys.
Block market orders if lastQuote.Bid - current Bid > 5 points for sells.
```

Order type policy:

```text
Trend Pullback:
  Market entry allowed, subject to slippage guard.

Breakout-Retest:
  Stop order preferred.

Range MR:
  Limit order preferred.
```

Execution failure lock:

```text
If 3 consecutive OrderSend failures:
  Enter LOCKED_EXECUTION_FAILURE.
  Block new trades.
  Require manual review or timed reset based on failure type.
```

---

## 33.8 PositionManager

v1 allowed:

```text
Hard stop loss
Take profit
Break-even at +1R
Time stop
Session exit
Emergency exit
News forced close
Weekend forced close
```

v1 disabled:

```text
Partial close
Trailing stop
Overnight holding
Weekend holding
```

Default exit model:

```text
Hard SL:
  Required for every trade.

TP:
  1.5R default unless expert-specific validated parameter exists.

Break-even:
  Move SL to entry at +1R.

Time stop:
  Close if not at +0.5R within 4 hours.

Session exit:
  Close all positions 30 minutes before broker daily rollover.

News exit:
  Close before CPI, NFP, FOMC.

Weekend exit:
  Close before Friday cutoff.
```

Rule:

```text
Stop loss may never be moved farther away from entry.
```

---

## 33.9 Logger

Required log files:

```text
decision_log.csv
trade_log.csv
risk_log.csv
execution_log.csv
router_log.csv
lifecycle_log.csv
spread_log_raw.csv
error_log.csv
```

Every decision row must include:

```text
timestamp_broker
timestamp_utc
timestamp_local
symbol
bid
ask
spread_points
session
news_state
regime
router_version
expert_versions
allowed_expert
blocked_experts
would_have_allowed_experts
risk_mode
lifecycle_status_by_expert
entry_signal
entry_reason_code
no_trade_reason_code
lot_size
sl_price
tp_price
risk_reward
execution_state
order_result
slippage
position_id
magic_number
balance
equity
daily_pnl
weekly_pnl
monthly_pnl
drawdown_pct
```

Logging principle:

```text
A blocked trade is as important as an executed trade.
```

---

## 33.10 Dashboard

Dashboard fields:

```text
Symbol
Broker time
UTC time
Local time
Session
Regime
Router version
Allowed expert
Would-have-allowed experts
Risk mode
News state
Spread
Execution state
Open positions
Daily P/L
Weekly P/L
Monthly P/L
Lifecycle status
Trade permission
Block reason
Dry-run status
```

Dashboard examples:

```text
XAUUSD
Session: London Main
Regime: TREND_WITH_PULLBACK
Allowed Expert: TrendPullback
Risk Mode: NORMAL
News State: NO_NEWS_RISK
Spread: OK
Trade Permission: DRY_RUN_ONLY
```

```text
XAUUSD
Session: New York Pre-Data
Regime: NEWS_BLACKOUT
Allowed Expert: None
Risk Mode: DEFENSIVE
News State: PRE_NEWS_BLACKOUT
Trade Permission: BLOCKED
Reason: CPI in 22 minutes
```

---

## 33.11 MagicNumberAllocator

Reserved namespace:

```text
Master EA reserved range: 920000–929999

Trend Pullback Expert:    920000–920099
Range MR Expert:          920100–920199
Breakout-Retest Expert:   920200–920299
Fakeout Expert:           920300–920399  deferred
Future experts:           920400–929999
```

Required file:

```text
magic_numbers.md
```

It must include:

```text
New EA reserved ranges
V85 production range
V61 archive range
V77/V80 ranges
Any other deployed EA ranges
Account numbers where ranges are active
Date verified
Verified by
```

Rules:

```text
No expert chooses its own magic number.
Every order request calls MagicNumberAllocator.
EA refuses startup if magic_numbers.md is missing.
EA refuses startup if range collision is detected.
EA logs assigned magic on every trade.
```

---

## 33.12 ExpertLifecycleManager

Lifecycle states:

```text
ACTIVE
DRY_RUN_ONLY
SUSPENDED
RETIRED
DISABLED_BY_CONFIG
DISABLED_BY_GOVERNOR
PENDING_PHASE0_APPROVAL
PENDING_WALK_FORWARD_APPROVAL
PENDING_DEMO_APPROVAL
```

Startup behavior:

```text
Read expert lifecycle file.
Read latest approval status.
Read performance logs.
Apply gates.
Force disable any expert that is not approved.
Ignore .set activation if lifecycle state blocks trading.
Log final status.
Display status on dashboard.
```

Retirement rules:

```text
If holdout/train PF ratio < 0.70:
  RETIRED

If concentration threshold breached:
  RETIRED

If 3 consecutive losing months:
  SUSPENDED

If 90-day rolling PF < 1.1:
  SUSPENDED

If 90-day losing-month percentage > 50%:
  SUSPENDED

If live PF / expected PF < 0.5:
  RETIRED
```

Runtime behavior:

```text
ACTIVE:
  May trade if router, risk, and execution approve.

DRY_RUN_ONLY:
  Logs would-have-traded signals only.

SUSPENDED:
  Dry-run only until review date.

RETIRED:
  Cannot be reactivated by .set file.
  Requires new versioned release and full validation.
```

Runtime should not physically move source files. Retirement in source control is handled by release process.

---

## 33.13 DryRunMode

Purpose:

```text
Run full pipeline without live orders.
```

Dry-run behavior:

```text
Expert signals are generated.
Risk sizing is calculated.
Execution approval is simulated.
Position management is simulated.
No OrderSend is called.
Would-have-traded rows are logged.
```

Required in:

```text
Phase 1
Phase 2
Phase 3
First month of any new expert
Suspended expert observation
Retired expert audit, if compiled
```

---

## 33.14 ServerTimeValidator

Purpose:

```text
Prevent time-zone, broker-clock, and calendar misalignment.
```

Checks:

```text
TimeCurrent()
TimeTradeServer()
TimeLocal()
Expected broker offset
UTC conversion
Calendar timestamp alignment
Session mapping
```

If external NTP is unavailable:

```text
Use internal comparisons.
Log reduced confidence.
Block trading if mismatch exceeds configured threshold.
```

Startup behavior:

```text
If drift > 60 seconds:
  Abort trading.
  Dry-run allowed only if configured.
```

---

## 33.15 ConcentrationReporter

This should be available before expert approval, not deferred.

It produces:

```text
concentration_report.csv
concentration_report.md
```

Metrics:

```text
Single-largest-trade contribution
Top-5-trade contribution
Per-expert P&L share
Per-month P&L share
Per-session P&L share
Per-regime P&L share
Largest drawdown contributor
Dead-month analysis
Zero-trade-month analysis
```

Required after:

```text
Every Phase 0 run
Every backtest
Every walk-forward cycle
Every portfolio backtest
Every demo-forward review
```

---

## 33.16 LiveDriftMonitor

v1.5 or later for live monitoring, but its design should be documented now.

Inputs:

```text
Live trade log
Expected PF band
Expected drawdown band
Expected trade frequency
Expected losing-month percentage
Expected zero-trade-month frequency
```

Alerts:

```text
7-day rolling PF < 0.8 × expected PF
30-day rolling PF < 0.8 × expected PF
90-day rolling PF < 1.1
Trade frequency below expected band
Drawdown exceeds expected band
Execution slippage exceeds backtest model
Spread regime worsens vs cost_model_measured.csv
```

---

# PART E — REGIME DEFINITIONS

---

## 34. v1 Regime Set

v1 has seven regimes.

```text
TREND_WITH_PULLBACK
RANGE
COMPRESSION
BREAKOUT_RETEST
ABNORMAL_MARKET
NEWS_BLACKOUT
NO_TRADE
```

No other regime may trade in v1.

---

## 35. TREND_WITH_PULLBACK

Candidate objective definition:

```text
H1 trend exists:
  EMA(50) and EMA(200) aligned.
  EMA(50) slope consistent with direction.
  ADX or trend-strength percentile above objective threshold.

M15 pullback exists:
  Price retraces toward EMA(21), structure support/resistance, or prior breakout level.

M5 confirmation:
  Rejection or engulfing pattern appears.
```

Allowed expert:

```text
Trend Pullback Expert
```

Risks:

```text
Trend reversal mistaken as pullback.
Late trend entry.
Overlapping with range regime.
```

---

## 36. RANGE

Candidate objective definition:

```text
H1 ADX below threshold.
Range boundaries identified mechanically.
At least 3 upper and 3 lower touches.
Range width sufficient relative to ATR and cost.
Price near boundary, not middle.
```

Allowed expert:

```text
Range MR Expert
```

Risks:

```text
Low ADX before expansion.
False range boundary.
Breakout through range edge.
Spread consuming range edge.
```

---

## 37. COMPRESSION

Candidate objective definition:

```text
ATR percentile below threshold.
Narrowing range.
Inside-bar cluster or Donchian contraction.
No active breakout-retest confirmation.
```

Allowed expert:

```text
None in v1 by default.
```

Use in v1:

```text
Map levels.
Prepare for possible Breakout-Retest.
Do not trade compression directly.
```

---

## 38. BREAKOUT_RETEST

Candidate objective definition:

```text
Objective level broken.
Retest occurs within defined bar count.
Broken level holds.
Confirmation candle appears.
```

Allowed expert:

```text
Breakout-Retest Expert
```

Risks:

```text
Fake breakout.
Late entry after retest.
Stop too close after volatility expansion.
Multiple overlapping levels.
```

---

## 39. ABNORMAL_MARKET

Triggers:

```text
Weekend gap
Monday open gap
Broker feed anomaly
Bad tick
Extreme spread
Unexpected symbol state
Flash spike
Order rejection cluster
Server time invalid
```

Allowed expert:

```text
None in v1.
```

Actions:

```text
Block trading.
Log abnormality.
Possibly close positions if risk requires.
Require manual review for severe cases.
```

---

## 40. NEWS_BLACKOUT

Triggers:

```text
High-impact USD news within blackout window.
Manual news lockdown.
Calendar source failure during high-risk window.
Fallback news schedule active.
```

Allowed expert:

```text
None in v1.
```

Actions:

```text
Block new trades.
Close positions before CPI, NFP, FOMC.
Cooldown after release.
```

---

## 41. NO_TRADE

Default regime.

Used when:

```text
No valid regime.
Conflicting signals.
Spread too high.
Risk locked.
Lifecycle blocks experts.
Session disabled.
Price in range middle.
Router confidence too low.
```

---

# PART F — RISK MANAGEMENT

---

## 42. Risk Constants

```text
kRiskPerTradeLive = 0.0025
kRiskPerTradePhase0 = 0.0050
kMaxDailyLoss = 0.0100
kMaxWeeklyLoss = 0.0300
kMaxMonthlyLoss = 0.0600
kMaxTotalDrawdownBeforeManualReview = configurable
kMaxOpenTrades = 1
kMaxTradesPerDay = 4
kMaxTradesPerSession = 2
kMinRewardRisk = 1.20
kPreferredRewardRisk = 1.50
```

---

## 43. Equity-Based Loss Accounting

Daily, weekly, and monthly losses are calculated from equity, not only realized P&L.

```text
DailyDrawdown = DayStartEquity - CurrentEquity
WeeklyDrawdown = WeekStartEquity - CurrentEquity
MonthlyDrawdown = MonthStartEquity - CurrentEquity
```

If cap breached:

```text
Close EA-managed positions.
Block new trades.
Log event.
Update dashboard.
```

---

## 44. Risk Reduction

If losing streak reaches 3:

```text
Risk mode = REDUCED
RiskPerTrade = 0.125%
```

If losing streak reaches 5:

```text
Risk mode = LOCKED
No new trades.
Manual review required.
```

If execution conditions degrade:

```text
Risk mode = DEFENSIVE
Block market orders.
Allow dry-run only.
```

---

## 45. Position Sizing Formula

Concept:

```text
RiskMoney = AccountEquity × RiskPerTrade
StopMoneyPerLot = StopDistanceInPoints × PointValuePerLot
LotSize = RiskMoney / StopMoneyPerLot
```

Then normalize:

```text
LotSize >= MinLot
LotSize <= MaxLot
LotSize rounded to LotStep
Margin requirement passes
Exposure cap passes
```

If normalized lot size violates risk:

```text
Block trade.
```

---

# PART G — EXECUTION AND BROKER REALISM

---

## 46. Execution Policy by Expert

| Expert | Entry Type | Reason |
|---|---|---|
| Trend Pullback | Market allowed | Confirmation often requires immediacy |
| Breakout-Retest | Stop order preferred | Entry after continuation confirmation |
| Range MR | Limit order preferred | Entry at predefined boundary |
| Fakeout | Deferred | Needs live execution data |

---

## 47. Spread Rule

Initial rule:

```text
Block if current_spread > max(30 points, 1.5 × 20-bar median spread)
```

This must be broker-validated because XAUUSD digits and point values can vary.

After spread logger completes:

```text
Replace static assumptions with measured P95 session-specific thresholds.
```

---

## 48. Slippage Rule

Initial rule:

```text
Market buy blocked if Ask - lastQuote.Ask > 5 points.
Market sell blocked if lastQuote.Bid - Bid > 5 points.
```

Order deviation:

```text
MaxDeviation = 3 points for stop/limit orders where applicable.
```

After demo forward test:

```text
Measured slippage replaces planned slippage.
All gates re-run against measured slippage.
```

---

## 49. Execution Failure Handling

If order fails:

```text
Log error code.
Log symbol state.
Log spread.
Log price.
Log freeze level.
Log stop distance.
Log margin state.
```

If 3 consecutive failures:

```text
LOCKED_EXECUTION_FAILURE
No new trades.
Manual review or scheduled recovery depending on error type.
```

---

## 50. Symbol Rename / Contract Change Recovery

At startup:

```text
Read _Symbol.
Read symbol digits.
Read point size.
Read tick value.
Read contract size.
Read margin settings.
Compare against previous known metadata.
```

If changed:

```text
Block trading.
Log SYMBOL_CONTRACT_CHANGED.
Notify operator.
Require cost model revalidation.
Require .set review.
```

Examples:

```text
XAUUSD
XAUUSD.
XAUUSDm
GOLD
```

No hardcoded symbol assumptions may be used without validation.

---

# PART H — NEWS AND SESSION RULES

---

## 51. News Policy

v1:

```text
No news trading.
No News Spike Expert.
No Spike Fade Expert.
No holding through CPI/NFP/FOMC.
```

Block windows:

```text
30 minutes before high-impact USD news
30 minutes after high-impact USD news
```

Forced-close windows:

```text
CPI
NFP
FOMC rate decision
FOMC press conference
```

---

## 52. Fallback News Schedule

Fallback schedule must exist for:

```text
NFP
CPI
FOMC
PCE
PPI
major Fed events
```

Fallback is not the source of truth. It is a safety net.

If calendar API fails during a known high-risk period:

```text
Use fallback.
Log fallback usage.
```

---

## 53. Session Rules

v1 default trading sessions:

```text
London Main
New York Main
London/New York overlap
```

v1 no-entry periods:

```text
Asia
Rollover
Friday close
Monday open
High-impact news blackout
Holiday thin liquidity
```

Asia use:

```text
Level mapping only.
No entries unless Phase 0 proves Asia edge.
```

---

# PART I — TESTING AND VALIDATION AFTER PHASE 0

---

## 54. Testing Ladder

After Phase 0, approved experts move through:

```text
1. Unit tests
2. Visual backtests
3. Single-expert backtests
4. Router-integrated backtests
5. Portfolio backtests
6. Walk-forward validation
7. CPCV or equivalent, if resources allow
8. True holdout
9. Demo forward test
10. Slippage/cost revalidation
11. Small live pilot
```

---

## 55. Historical Stress Periods

Required XAU-specific tests:

```text
2020-03 to 2020-04 — COVID volatility crash/rally
2022-09 to 2022-11 — strong USD trend / DXY peak
2023-03 — banking crisis / SVB volatility
2024-04 — geopolitical spike
2025 full year — most recent forward-like regime
Continuous 5-year M5 backtest
```

---

## 56. Walk-Forward

Specification:

```text
Method: Anchored walk-forward
Initial train: 24 months minimum, 36 months preferred
Validation: 3 months
Step: 3 months
Acceptance: every fold passes
```

Fold gate:

```text
Holdout/train PF ≥ 0.80 preferred
Holdout/train PF < 0.70 hard fail
```

One catastrophic fold cannot be hidden by average results.

---

## 57. True Holdout

Reserve six months of recent data.

Rules:

```text
No development use.
No parameter tuning on this period.
No repeated peeking.
Opened only at final pre-live approval.
```

Required file:

```text
true_holdout_period.md
```

Contents:

```text
Start date
End date
Data source
Date locked
Locked by
Reason selected
Confirmation that team will not use it before final review
```

---

## 58. Advanced Validation

If resources permit:

```text
Combinatorial Purged Cross-Validation
White's Reality Check
Hansen SPA test
Independent reproduction by non-build team member
```

Acceptance:

```text
CPCV median holdout/train PF ≥ 0.70
Data-mining bias p-value < 0.05 where applicable
Independent reproduction within 5% of stated metrics
```

---

## 59. Stress Tests

Mandatory:

```text
Normal spread
2× spread
3× spread
P95 measured spread
High slippage
Delayed execution
Rollover spread expansion
VPS restart mid-position
Symbol disabled mid-session
Broker disconnect
Order rejection cluster
Calendar API failure
Server time skew
Negative balance / margin-call simulation
Friday close
Monday open
```

---

# PART J — DEVELOPMENT PHASES

---

## 60. Phase 0 — Statistical Edge Validation

Status:

```text
Mandatory before Phase 1.
```

Deliverables:

```text
hypothesis files
9-cell matrix results
decile tests
adversarial reviews
multi-symbol checks
cost model files
PHASE0_VERDICT.md
```

Acceptance:

```text
At least one expert passes all gates.
```

---

## 61. Phase 1 — Dry-Run Master EA Shell

Purpose:

```text
Build the non-trading skeleton.
```

Build:

```text
XAUUSD_MasterEA.mq5
MarketDataEngine
FeatureEngine basic
SessionEngine basic
Logger
Dashboard
DryRunMode
ConfigValidator
ServerTimeValidator basic
```

Forbidden:

```text
No experts enabled.
No OrderSend calls.
No trade execution code.
No live orders possible.
```

Acceptance:

```text
Runs 5 trading days continuously.
decision_log.csv has one row per M5 bar.
Dashboard updates correctly.
ServerTimeValidator catches injected skew.
Risk caps can be simulated.
No runtime crashes.
```

---

## 62. Phase 2 — Safety Infrastructure

Build:

```text
RiskManager
ExecutionGuard
MagicNumberAllocator
ExpertLifecycleManager
NewsGuard
Spread logger integration
Kill switch
Daily/weekly/monthly caps
```

Acceptance:

```text
Risk caps trigger under simulation.
Magic number collision blocks startup.
News blackout blocks entries.
Spread rule blocks entries.
Execution failure lock works in simulation.
Lifecycle state overrides .set file.
```

---

## 63. Phase 3 — Versioned Regime Router

Build:

```text
7-regime classifier
router_v1.0
router_thresholds.md
would_have_allowed_experts logging
blocked expert logging
router dashboard status
```

Acceptance:

```text
Router classifies every M5 bar.
NO_TRADE is default.
Router logs reasons.
Thresholds are derived from objective market distributions.
Router changes require version bump.
```

---

## 64. Phase 4 — First Approved Expert Dry-Run

Only after Phase 0 approves an expert.

Build first approved expert only.

Recommended order if all pass:

```text
1. Trend Pullback
2. Breakout-Retest
3. Range MR
```

Phase 4 status:

```text
Dry-run only.
No live orders.
```

Acceptance:

```text
Expert implements standard interface.
Expert returns signal object.
Expert logs setup and no-setup reasons.
Router controls activation.
Risk and execution approval simulated.
```

---

## 65. Phase 5 — Single-Expert Validation

For each approved expert:

```text
Single-expert backtest
Walk-forward validation
Stress testing
Concentration report
True holdout
Dry-run forward observation
```

An expert can advance only if it passes all gates.

---

## 66. Phase 6 — Portfolio Router Validation

Build aggregate system with multiple approved experts.

Requirements:

```text
One active expert at a time.
Router resolves conflicts.
Risk caps apply globally.
Position Manager applies globally.
Portfolio backtest is router-selected aggregate.
```

Acceptance:

```text
No expert conflict.
No duplicate orders.
No hidden overexposure.
Concentration gates pass.
Single-engine contribution ≤ 35%.
Single-month contribution ≤ 25%.
```

---

## 67. Phase 7 — Demo Forward Test on VPS

Requirements:

```text
Dedicated demo account
VPS deployment
External health monitor
Same .set file as intended pilot
No manual intervention except documented incidents
Minimum 6 weeks
At least one high-impact USD news event observed
```

Acceptance:

```text
No unauthorized trades.
No risk cap violations.
No repeated execution failures.
Logs complete.
Slippage measured.
Spread measured.
Router behavior explainable.
```

---

## 68. Phase 8 — Slippage Revalidation

After demo forward test:

```text
Measure actual slippage.
Measure actual rejected orders.
Measure actual spread.
Update cost model.
Re-run approval gates.
```

If PF drops below gate under measured slippage:

```text
Expert rejected or returned to research.
```

Backtest approval does not grandfather an expert past live execution evidence.

---

## 69. Phase 9 — Small Live Pilot

Rules:

```text
Minimum lot size
0.25% risk per trade maximum
No news trading
No overnight holding
No weekend holding
Daily log review
Weekly performance review
Manual emergency exit process ready
```

Stable pilot requires:

```text
At least 30 trades
At least 3 months
PF within expected band
Drawdown within expected band
No critical operational failure
```

---

## 70. Phase 10 — Production and Long-Term Survival

Production only after stable live pilot.

Requirements:

```text
Capital ladder
Quarterly review calendar
LiveDriftMonitor active
Next-expert research pipeline
Disaster recovery runbook
Tax/accounting process
Broker backup plan
```

---

# PART K — OPERATIONAL MATURITY

---

## 71. CI/CD

Repository branches:

```text
develop
release-candidate
production
```

Required tools:

```text
release_check.ps1
snapshot.ps1
hash_hypothesis.py
concentration_reporter.py
spread_aggregator.py
```

`release_check.ps1` blocks live trading unless:

```text
Unit tests pass.
Snapshot bundle exists.
magic_numbers.md validated.
filter_inventory.md complete.
Edge Thesis / Phase 0 verdict signed.
Walk-forward report exists.
Concentration report passes.
No retired expert enabled.
Router version matches validation report.
```

---

## 72. Snapshot Bundle

Every release bundle contains:

```text
EA source
EA compiled binary
.set file
Git commit hash
Router version
Expert versions
Magic-number map
Filter inventory
Cost model
Backtest report
Walk-forward report
Concentration report
Holdout report
Known issues
Approval status
```

---

## 73. VPS Plan

Required file:

```text
vps_plan.md
```

Contents:

```text
Provider
Region
Latency to broker
Operating system
MT5 version
Auto-restart policy
Backup schedule
Log backup location
Monitoring method
Access control
2FA status
Disaster recovery process
```

---

## 74. External Health Monitor

Separate from EA.

Checks every 5 minutes:

```text
EA heartbeat
MT5 terminal status
Broker connection
Log update frequency
Margin level
Unexpected state
Dry-run/live mode status
```

Alerts if:

```text
No heartbeat > 10 minutes
Broker connection lost
Margin warning
Unexpected live mode
Log activity spike
EA stopped
```

---

## 75. Disaster Recovery Runbook

Required file:

```text
dr_runbook.md
```

Scenarios:

```text
VPS dies mid-trade
MT5 crashes
Broker connection lost
Capital.com account closed or unavailable
All EA-managed positions need manual exit
Magic-number confusion
Calendar API failure
Symbol contract changes
EA logs corrupt or unavailable
```

Each scenario must include:

```text
Detection method
Immediate action
Manual close procedure
Responsible person
Recovery procedure
Post-incident review requirement
```

---

## 76. Account Isolation

Recommended:

```text
Dedicated account for the new EA.
```

If V85 remains active elsewhere:

```text
Separate account preferred.
If same account during dry-run, new EA must have no OrderSend capability.
If trading enabled, V85 and new EA cannot share account unless portfolio-level governor is built and approved.
```

---

# PART L — CONFIGURATION AND FILE INVENTORY

---

## 77. Required Configuration Files

```text
xauusd_master_v1.set
magic_numbers.md
filter_inventory.md
router_thresholds.md
cost_model_initial.md
cost_model_measured.csv
expert_lifecycle_status.json
true_holdout_period.md
release_manifest.md
```

---

## 78. filter_inventory.md Template

```text
# Filter Inventory

| Filter ID | Module | Description | Default | Can Disable? | Tested Disabled? | Version Added |
|---|---|---|---|---|---|---|
| F001 | NewsGuard | High-impact USD blackout | ON | No | N/A | v1.0 |
| F002 | ExecutionGuard | Spread threshold | ON | No | N/A | v1.0 |
| F003 | Router | ADX range threshold | ON | No | N/A | v1.0 |
```

Rules:

```text
No undocumented filter may exist in source.
No filter may default ON unless documented.
Any disabled-state behavior must be tested or marked untested.
```

---

## 79. router_thresholds.md Template

```text
# Router Thresholds

Router version:
Date locked:
Data period used:
Method:
Author:

| Threshold | Value | Source | Reason |
|---|---:|---|---|
| ADX trend cutoff | <value> | XAU long-run ADX percentile | objective distribution |
| ATR compression cutoff | <value> | XAU ATR percentile | objective distribution |
| Range width minimum | <value> | Phase 0 definition | pre-registered |
```

Rules:

```text
Thresholds are not optimized per expert.
Threshold changes require router version bump.
Expert revalidation required after router threshold changes.
```

---

## 80. expert_lifecycle_status.json Template

```json
{
  "TrendPullback": {
    "status": "PENDING_PHASE0_APPROVAL",
    "version": "0.0",
    "last_review": "2026-05-20",
    "reason": "Phase 0 not complete"
  },
  "BreakoutRetest": {
    "status": "PENDING_PHASE0_APPROVAL",
    "version": "0.0",
    "last_review": "2026-05-20",
    "reason": "Phase 0 not complete"
  },
  "RangeMR": {
    "status": "PENDING_PHASE0_APPROVAL",
    "version": "0.0",
    "last_review": "2026-05-20",
    "reason": "Phase 0 not complete"
  }
}
```

---

# PART M — EXPERT APPROVAL AND RETIREMENT

---

## 81. Expert Approval Gates

Before an expert can trade beyond dry-run:

```text
Phase 0 pass
Minimum train trades ≥ 40
Cost-adjusted train PF ≥ 1.50
Holdout/train PF ≥ 0.80 preferred
Holdout/train PF ≥ 0.70 absolute minimum
Holdout losing months ≤ 35%
Largest single trade ≤ 10% of P&L
Top 5 trades ≤ 40% of P&L
Single expert portfolio contribution ≤ 35%
Single month contribution ≤ 25%
Max zero-trade months ≤ 3
Walk-forward all folds pass
True holdout pass
Demo forward no critical execution failure
Measured slippage revalidation pass
```

---

## 82. Expert Retirement Gates

Automatic retirement:

```text
Holdout/train PF < 0.70
Live PF / expected PF < 0.50
Concentration threshold breached materially
Unauthorized order from expert
Repeated risk rule violation
```

Automatic suspension:

```text
3 consecutive losing months
90-day rolling PF < 1.1
90-day losing-month percentage > 50%
Execution slippage materially worse than model
Trade frequency outside expected band
```

Suspended experts:

```text
Run dry-run only.
Re-evaluate monthly.
Cannot trade until lifecycle manager approves.
```

Retired experts:

```text
Cannot be enabled by .set file.
Require new versioned release and full validation.
```

---

# PART N — REVIEW CHECKLIST FOR NEXT REVIEW TEAM

---

## 83. Review Questions

Please review this v0.3 plan against these questions:

```text
1. Is Phase 0 sufficiently strict before Phase 1?
2. Are the Phase 0 gates too strict, too loose, or appropriate?
3. Are the three candidate expert definitions objective enough?
4. Should Phase 0 use 0.50% fixed research risk, or another value?
5. Is v1 live risk of 0.25% appropriate?
6. Are Trend Pullback, Breakout-Retest, and Range MR still the correct candidates?
7. Is Fakeout correctly deferred?
8. Are seven regimes enough for v1?
9. Are any v1 modules missing?
10. Should ConcentrationReporter be part of v1 rather than v1.5?
11. Is the spread logger specification sufficient?
12. Are the cost model assumptions adequate before measured data?
13. Are the execution rules realistic for the intended broker?
14. Is the router freeze/versioning rule strict enough?
15. Are lifecycle retirement rules strict enough?
16. Is the walk-forward acceptance threshold appropriate?
17. Is the true holdout rule practical?
18. Is dedicated account isolation mandatory or optional?
19. What must be changed before Phase 0 starts?
20. What must be changed before Phase 1 starts?
```

---

## 84. Requested Review Output Format

```text
Overall verdict:
  Approved / Approved with changes / Needs major revision / Not recommended

Phase 0 verdict:
  Approved / Needs changes / Too strict / Too loose

Top 10 must-change items:
1.
2.
3.
4.
5.
6.
7.
8.
9.
10.

Top 10 nice-to-have improvements:
1.
2.
3.
4.
5.
6.
7.
8.
9.
10.

Expert candidate verdict:
  Trend Pullback:
  Breakout-Retest:
  Range MR:
  Fakeout deferment:

Risk model verdict:

Execution model verdict:

Router model verdict:

Lifecycle model verdict:

Operational model verdict:

Recommended Phase 0 start conditions:

Recommended Phase 1 start conditions:

Final recommendation:
```

---

# PART O — OPEN ITEMS BEFORE PHASE 0

---

## 85. Open Decisions

The following decisions remain open:

```text
1. Actual V85 magic-number range.
2. Actual V61, V77, V80 magic-number ranges.
3. Whether new EA gets a dedicated account immediately.
4. Exact Capital.com demo account to use for spread logger.
5. Pepperstone tick data source.
6. Whether true holdout is 2025-H2 or the latest six months before final review.
7. Who signs hypothesis files.
8. Who runs independent reproduction.
9. Whether Phase 0 is MT5-only or MT5 + Python cross-check for every expert.
10. Which VPS provider will be used later.
11. Which external health monitor mechanism will be used.
12. Whether operational Categories C, D, E are deferred until Phase 0 pass or partially started now.
```

---

## 86. Open Files to Create

Before Phase 0 starts:

```text
data_source_inventory.md
cost_model_initial.md
hypothesis_trend_pullback.md
hypothesis_breakout_retest.md
hypothesis_range_mr.md
true_holdout_period.md
phase0_execution_log.md
```

Before Phase 1 starts:

```text
magic_numbers.md
filter_inventory.md
router_thresholds.md
vps_plan.md
dr_runbook.md
release_manifest.md
expert_lifecycle_status.json
```

---

# PART P — FINAL RECOMMENDED NEXT ACTIONS

---

## 87. Immediate Next Actions

Do these in order:

```text
1. Approve or edit this v0.3 plan.
2. Create Phase 0 repository folder.
3. Create hypothesis templates.
4. Decide true holdout period.
5. Lock data sources.
6. Start passive 4-week spread logger.
7. Register and SHA-lock the three hypotheses.
8. Run 27 Phase 0 backtest cells.
9. Complete decile tests.
10. Complete adversarial reviews.
11. Complete multi-symbol checks.
12. Produce PHASE0_VERDICT.md.
```

---

## 88. Go / No-Go Rule

```text
If at least one expert passes Phase 0:
  Proceed to Phase 1 dry-run Master EA shell.

If no expert passes Phase 0:
  Stop.
  Do not build the EA.
  Research replacement candidate behaviors.
```

This is the most important discipline rule in the entire plan.

---

## 89. Final Position

The project should continue, but not by coding trading experts immediately.

The correct next phase is:

```text
Phase 0 statistical validation
+
passive spread logging
+
cost model calibration
+
locked hypotheses
```

Only after this evidence exists should engineering work begin.

The purpose of v0.3 is to prevent the project from becoming:

```text
A beautiful EA around an unproven edge.
```

The desired outcome is:

```text
A defensive, evidence-driven, modular XAUUSD system whose experts earn their right to be coded.
```

---

## Appendix A — Phase 0 Definition of Done

```text
[ ] data_source_inventory.md completed
[ ] cost_model_initial.md completed
[ ] passive spread logger started
[ ] true_holdout_period.md created
[ ] hypothesis_trend_pullback.md written and SHA256-locked
[ ] hypothesis_breakout_retest.md written and SHA256-locked
[ ] hypothesis_range_mr.md written and SHA256-locked
[ ] 27 backtest cells executed
[ ] phase0_trend_pullback_results.md written
[ ] phase0_breakout_retest_results.md written
[ ] phase0_range_mr_results.md written
[ ] Decile tests completed
[ ] Adversarial searches completed
[ ] Multi-symbol checks completed
[ ] Concentration reports completed
[ ] PHASE0_VERDICT.md written and signed
[ ] Decision communicated: proceed with N experts or stop
```

---

## Appendix B — Phase 1 Definition of Done

```text
[ ] XAUUSD_MasterEA.mq5 boots
[ ] No OrderSend calls in codebase
[ ] DryRunMode active
[ ] MarketDataEngine working
[ ] FeatureEngine basic features working
[ ] SessionEngine working
[ ] Logger writes decision_log.csv
[ ] Dashboard displays status
[ ] ServerTimeValidator catches simulated skew
[ ] Risk cap simulation works
[ ] EA runs 5 trading days continuously
[ ] One decision_log.csv row per M5 bar
[ ] No runtime crashes
[ ] No live orders possible
```

---

## Appendix C — v1 Build Scope

Build for v1 if Phase 0 passes:

```text
Master EA shell
Market Data Engine
Feature Engine
Session Engine
News Guard with fallback
Regime Router with 7 regimes
Risk Manager with monthly hard stop and equity-based caps
Execution Guard with explicit spread/slippage rules
Position Manager without partial close/trailing
Logger with would-have-allowed experts
Dashboard
MagicNumberAllocator
ExpertLifecycleManager
DryRunMode
ServerTimeValidator
ConcentrationReporter
Approved Phase 0 experts only
```

Defer to v1.5:

```text
Fakeout / Liquidity Sweep Expert
LiveDriftMonitor full implementation
Advanced trailing or partial exits
```

Defer to v2+:

```text
Trend Continuation
Compression Breakout
Reversal
News Spike
Spike Fade
Gap trading
Multi-symbol trading
External macro feeds
Machine learning
```

---

## Appendix D — Prohibited First-Version Features

```text
Martingale
Unlimited grid
Doubling after loss
Averaging down without hard invalidation
Moving stop loss farther away
No-stop-loss trading
Recovery mode
Hedge-and-pray logic
News trading
Spike fading
Fakeout trading
Overnight holding
Weekend holding
Manual override of lifecycle retirement
Manual override of risk caps
Unlogged filters
Undocumented magic numbers
```

---

## Appendix E — Key File Naming Convention

```text
/xauusd_master_ea/
  /phase0/
    hypothesis_trend_pullback.md
    hypothesis_breakout_retest.md
    hypothesis_range_mr.md
    phase0_trend_pullback_results.csv
    phase0_breakout_retest_results.csv
    phase0_range_mr_results.csv
    PHASE0_VERDICT.md

  /docs/
    xauusd_master_ea_plan_v0_3.md
    magic_numbers.md
    filter_inventory.md
    router_thresholds.md
    true_holdout_period.md
    vps_plan.md
    dr_runbook.md

  /src/
    XAUUSD_MasterEA.mq5
    /include/core/
    /include/experts/
    /include/utils/

  /tools/
    phase0_runner.py
    spread_aggregator.py
    concentration_reporter.py
    release_check.ps1
    snapshot.ps1

  /logs/
    decision_log.csv
    spread_log_raw.csv
    trade_log.csv
    risk_log.csv
    execution_log.csv
```

---

## Appendix F — Review Status

This document is ready for second review.

Recommended reviewer focus:

```text
Phase 0 strictness
Candidate expert objectivity
Cost model realism
Router overfitting controls
Lifecycle enforcement
Magic-number enforcement
Dedicated account requirement
Operational maturity sequence
Definition of Phase 1 start conditions
```

