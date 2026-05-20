# XAUUSD Master EA Plan v0.2 — Review-Ready Revised Plan

**Version:** v0.2  
**Date:** 2026-05-20  
**Status:** Review-ready, pre-coding  
**Platform commitment:** MT5 / MQL5  
**Primary symbol:** XAUUSD, runtime-read from `_Symbol`  
**Supersedes:** `xauusd_algo_trading_system_plan_v0_1.md`  
**Based on:** v0.1 plan plus `PLAN_V01_REVIEW_FINDINGS.md`

---

## 0. Executive Summary

This revised plan converts the original XAUUSD algo trading strategy design into a stricter, review-ready engineering specification.

The v0.1 architecture was directionally accepted, but the review identified several gaps that must be fixed before coding begins. This v0.2 plan incorporates those changes directly into the system design.

The core direction remains:

```text
Regime first.
Risk second.
Signal third.
Execution last.
Default state = NO_TRADE.
```

The biggest change is that v0.2 is no longer just a modular strategy plan. It is now a defensive build plan with:

```text
- Hard expert approval gates
- Hard expert retirement gates
- Router versioning and freeze discipline
- Magic-number allocation before OrderSend exists
- Dry-run-first development
- Explicit spread/slippage rules
- Equity-based risk caps
- Reduced v1 regime count
- Reduced v1 expert count
- No news trading in v1
- No partial close or trailing stop in v1
```

The first coding milestone must not include live trading logic. It must be dry-run infrastructure only.

---

## 1. v0.2 Decision Summary

| Area | v0.2 decision |
|---|---|
| Platform | Commit to MT5 / MQL5 only |
| Architecture | One Master EA with internal `.mqh` class-based modules |
| Default state | `NO_TRADE` |
| v1 trading experts | Trend Pullback, Breakout-Retest, Range Mean-Reversion |
| Deferred expert | Fakeout / Liquidity Sweep moved to v1.5 |
| Router | Versioned independently, 7 regimes only in v1 |
| News trading | Disabled completely in v1 |
| Order execution | No `OrderSend` in Milestone 1 |
| Risk per trade | 0.25% to 0.50% |
| Daily loss cap | 1% to 2%, equity-based, includes floating drawdown |
| Weekly loss cap | 3% to 5% |
| Monthly loss cap | 6% to 8% |
| Daily cap action | Force-close EA-managed open trades and lock until next trading day |
| Monthly cap action | Switch EA to dry-run for rest of month |
| Position management v1 | Hard SL, ATR/structure TP, BE at +1R, time stop, session exit |
| Disabled in v1 | Martingale, grid, recovery mode, news trading, partial close, trailing stop, overnight holding, weekend holding |
| Testing | Anchored walk-forward, every-fold acceptance, stress tests, 6-week demo minimum |
| First deliverable before coding | Edge Thesis Document |
| First coding milestone | Dry-run Master EA infrastructure only |

---

## 2. What Changed From v0.1

The review found that v0.1 had a good architecture but was not coding-ready. The following changes have been incorporated.

### 2.1 Must-Change Items Added

```text
1. Edge Thesis Document required before expert coding.
2. Expert approval gates changed from review targets to hard blockers.
3. MagicNumberAllocator added before any OrderSend code.
4. Regime Router treated as the highest overfitting risk.
5. ExpertLifecycleManager added for suspension and retirement.
```

### 2.2 Expert Set Revised

Original v0.1 v1 experts:

```text
Trend Pullback
Range Mean-Reversion
Fakeout / Liquidity Sweep
```

Revised v0.2 v1 experts:

```text
Trend Pullback
Breakout-Retest
Range Mean-Reversion
```

Reason:

```text
Fakeout detection is too fuzzy for v1.
Breakout-Retest is more mechanically definable and easier to validate.
```

### 2.3 Regime Count Reduced

Original v0.1 had 21 possible regimes. v0.2 reduces v1 to 7 regimes:

```text
TREND_WITH_PULLBACK
RANGE
COMPRESSION
BREAKOUT_RETEST
ABNORMAL_MARKET
NEWS_BLACKOUT
NO_TRADE
```

### 2.4 v1 Is Now Dry-Run First

Milestone 1 must contain no `OrderSend` calls.

The EA must boot, classify regimes, log decisions, display dashboard status, validate time, and simulate risk states without being able to place a live order.

---

## 3. Project Objective

Build a modular XAUUSD Master EA that classifies the market regime first, then allows only the appropriate expert to suggest a trade, subject to centralized risk, execution, lifecycle, and logging controls.

The objective is not to build a bot that trades every day. The objective is to build a system that can safely determine:

```text
This is a valid XAUUSD condition for Expert A.
This is unsafe.
This is unclear.
This is outside v1 scope.
No trade.
```

The system must be designed so that a weak expert cannot hide behind the rest of the portfolio, and a tuned router cannot silently curve-fit the system.

---

## 4. Core Principles

### 4.1 No Trade Is the Default

The EA should block trading unless every required layer agrees.

```text
Market regime clear?              Yes
Session acceptable?                Yes
News risk acceptable?              Yes
Spread acceptable?                 Yes
Slippage acceptable?               Yes
Risk caps not breached?            Yes
Expert active and approved?        Yes
Expert has valid setup?            Yes
Position Manager accepts trade?    Yes
Execution Guard accepts order?     Yes
```

If any answer is no:

```text
NO_TRADE
```

### 4.2 One Active Expert at a Time in v1

Only one trading expert may be active at any time in v1.

This is non-negotiable for debuggability.

The router may evaluate what other experts would have done, but only the router-selected expert may produce an executable signal.

### 4.3 Centralized Risk

No trading expert can calculate its own lot size.

All lot sizing, risk caps, daily locks, weekly locks, monthly locks, exposure limits, and kill-switch states are controlled by the Risk Manager.

### 4.4 Router Is a Risk Surface

The Regime Router is not neutral plumbing. It is one of the highest overfitting risks in the whole project because it may contain many thresholds.

Therefore:

```text
Router has its own version.
Router thresholds are set from objective distributions.
Router changes require revalidation.
Router logs would-have-allowed experts.
Router is frozen after calibration unless version is bumped.
```

### 4.5 Experts Must Earn Their Slot

No expert is coded simply because it is a common strategy category.

Each expert requires an Edge Thesis Document and must pass hard validation gates before it can move beyond dry-run.

---

## 5. Required Pre-Coding Deliverables

Before Phase 1 coding begins, the following documents must exist.

### 5.1 Edge Thesis Document

Required for each v1 expert:

```text
Trend Pullback Expert
Breakout-Retest Expert
Range Mean-Reversion Expert
```

Template:

```text
Expert: <name>

Underlying market behavior:
<What is gold actually doing when this expert is right?>

Evidence of persistence:
<Pointer to prior validation, statistical study, or new XAUUSD test showing this behavior exists across multiple years.>

Failure modes:
<When does this behavior fail? What regimes invalidate it?>

Why it deserves a slot:
<What does this expert capture that the other two cannot?>

Preliminary codable pattern:
<How the behavior could be expressed mechanically without curve-fitting.>
```

Rule:

```text
If the Edge Thesis cannot be defended, do not code that expert.
```

### 5.2 `magic_numbers.md`

Required before any order-related code is written.

Must include:

```text
- New Master EA magic-number range
- Per-expert subranges
- Existing occupied ranges from V61, V77, V80, V85
- Collision rules
- Owner/source of each range
- Date assigned
```

### 5.3 `filter_inventory.md`

Every filter must be documented.

Required fields:

```text
Filter name
Module
Default state
Default value
Can be disabled?
Has disabled state been tested?
Is it a hard safety filter or strategy filter?
Reason for existence
Data source
Overfitting risk rating
```

This avoids hidden filters shipping as default-on inputs without validation.

### 5.4 `cost_model.md`

Must define the cost assumptions used in all backtests and approval gates.

Required fields:

```text
Broker
Account type
Symbol name
Symbol digits
Typical spread
Median spread
High-volatility spread
Commission per lot, if any
Modeled slippage
Swap handling
Backtest data source
Known data limitations
```

### 5.5 `router_versioning.md`

Must define:

```text
Router version format
Expert version format
When router version must change
When expert version must change
When full revalidation is required
How logs record router/expert versions
```

### 5.6 `release_snapshot_spec.md`

Every release candidate must produce a snapshot bundle containing:

```text
EA binary
Source hash or git commit hash
.set file
Broker ID
Symbol
Magic ranges
Tick/bar data range
Cost model version
Router version
Expert versions
Backtest report
Walk-forward report
Holdout report
Concentration report
Known issues
Approval status
```

---

## 6. System Architecture

### 6.1 Architecture Decision

Use one Master EA with internal class-based modules implemented as `.mqh` include files.

Do not build separate EAs for each expert in v1.

Reason:

```text
Separate EAs make account-level risk coordination harder.
One Master EA allows centralized router, risk, execution, lifecycle, and logging control.
```

### 6.2 v1 Module Tree

```text
XAUUSD_Master_EA.mq5
│
├── Core/
│   ├── MarketDataEngine.mqh
│   ├── FeatureEngine.mqh
│   ├── SessionEngine.mqh
│   ├── ServerTimeValidator.mqh
│   ├── CostModel.mqh
│   └── ConfigManager.mqh
│
├── Governance/
│   ├── RegimeRouter.mqh
│   ├── RiskManager.mqh
│   ├── ExecutionGuard.mqh
│   ├── NewsGuard.mqh
│   ├── PositionManager.mqh
│   ├── MagicNumberAllocator.mqh
│   ├── ExpertLifecycleManager.mqh
│   ├── DryRunMode.mqh
│   └── KillSwitch.mqh
│
├── Experts/
│   ├── IExpert.mqh
│   ├── TrendPullbackExpert.mqh
│   ├── BreakoutRetestExpert.mqh
│   └── RangeMeanReversionExpert.mqh
│
├── Diagnostics/
│   ├── Logger.mqh
│   ├── Dashboard.mqh
│   ├── ConcentrationReporter.mqh
│   └── SnapshotReporter.mqh
│
└── Shared/
    ├── Types.mqh
    ├── Enums.mqh
    ├── Constants.mqh
    └── Utils.mqh
```

### 6.3 Modules Deferred Beyond v1

```text
FakeoutLiquiditySweepExpert.mqh      v1.5
LiveDriftMonitor.mqh                 v1.5 or v2
TrendContinuationExpert.mqh          v2
CompressionBreakoutExpert.mqh        v2
ReversalExpert.mqh                   v2
NewsSpikeContinuationExpert.mqh      v2+
SpikeFadeExpert.mqh                  v2+
GapAbnormalTradingExpert.mqh         v2+
ExternalMacroFeedEngine.mqh          v2+
MachineLearningEngine.mqh            not planned for v1/v1.5
```

Note: `ConcentrationReporter` should exist before any expert approval because the approval gates require concentration metrics. It can be implemented as a reporting tool rather than a live-trading module.

---

## 7. Market Data Engine

### 7.1 Purpose

Collect and normalize broker data.

### 7.2 Responsibilities

```text
Read current Bid / Ask
Read current spread
Read tick volume
Read M1 / M5 / M15 / H1 / H4 / D1 candles
Track previous day high / low
Track previous week high / low
Track session high / low
Track current candle body and wick structure
Track broker server time
Track local terminal time
Expose symbol metadata
Read point size, tick size, contract size, min lot, lot step, stop level, freeze level
```

### 7.3 Symbol Handling

The EA must never hardcode `XAUUSD` for execution.

It must use:

```text
_Symbol
```

and log the actual runtime symbol, such as:

```text
XAUUSD
XAUUSD.
XAUUSDm
GOLD
```

### 7.4 Required Outputs

```text
current_bid
current_ask
current_spread_points
current_spread_price
median_spread_20_bars
symbol_digits
point_size
tick_size
tick_value
contract_size
min_lot
max_lot
lot_step
stops_level
freeze_level
current_candle
previous_candle
session_high
session_low
daily_high
daily_low
weekly_high
weekly_low
```

### 7.5 Data Limitations Flag

The Data Plan must explicitly flag if the broker provides true tick history only from a certain date, and whether older backtests rely on bar data rather than tick data.

This must be written into `cost_model.md` and every release snapshot.

---

## 8. Feature Engine

### 8.1 Purpose

Convert raw market data into reusable features.

The Feature Engine does not generate trade signals.

### 8.2 Core Features

```text
ATR
ATR percentile
ADX
ADX percentile
EMA slope
SMA slope
Swing highs
Swing lows
Market structure
Range width
Candle body percentage
Upper wick percentage
Lower wick percentage
Break of structure
Change of character
Distance from previous daily high
Distance from previous daily low
Distance from session high
Distance from session low
Distance from EMA
Distance from range boundary
Spread percentile
Volatility state
```

### 8.3 Overfitting Control

Feature thresholds used by the router must be derived from objective historical distributions, not optimized separately per expert.

Example:

```text
H1 ADX trend threshold = long-run 70th percentile of H1 ADX distribution
M5 compression threshold = long-run 20th percentile of M5 ATR distribution
```

These percentile decisions must be documented in `router_versioning.md` and `filter_inventory.md`.

---

## 9. Session Engine

### 9.1 Purpose

Classify the trading session and session-specific risk.

### 9.2 Session States

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
WEEKEND_CLOSE
WEEKEND_OPEN
HOLIDAY_THIN_LIQUIDITY
```

### 9.3 Required Outputs

```text
current_session
session_start_time
session_end_time
session_high
session_low
session_range
time_to_next_session
is_rollover_window
is_weekend_close_window
is_weekend_open_window
is_fix_window
is_holiday_thin_liquidity
```

### 9.4 v1 Session Rules

```text
Do not open new trades during rollover window.
Close all EA-managed positions 30 minutes before broker daily rollover.
Do not hold overnight in v1.
Do not hold over weekend in v1.
Friday late session is exit-only.
Asia can be used for range construction, but trading permission must be reviewed by router.
```

---

## 10. News Guard

### 10.1 Purpose

Prevent the EA from trading through high-impact USD events in v1.

### 10.2 v1 News Decision

```text
No news trading in v1.
No News Spike Expert in v1.
No Spike Fade Expert in v1.
All high-impact USD news is a blocker.
```

### 10.3 Events to Block

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
Fed speeches marked high impact
Major manually flagged geopolitical events
```

### 10.4 News States

```text
NO_NEWS_RISK
PRE_NEWS_BLACKOUT
NEWS_RELEASE_ACTIVE
POST_NEWS_COOLDOWN
MANUAL_NEWS_LOCKDOWN
CALENDAR_UNAVAILABLE_FALLBACK_ACTIVE
```

### 10.5 v1 News Rules

```text
Pre-news blackout: 30 minutes
Post-news cooldown: 30 minutes
Close EA-managed open trades before CPI / NFP / FOMC
Block all new trades during blackout and cooldown
Log source of news block
```

### 10.6 Calendar Source

Primary:

```text
MT5 built-in economic calendar, if reliable and available
```

Fallback:

```text
Hardcoded known event windows or manually maintained schedule
```

Fallback examples:

```text
NFP: first Friday of month, 12:25–13:30 UTC, unless calendar says otherwise
CPI: scheduled release dates, 12:25–13:30 UTC
FOMC decision: scheduled FOMC dates, 17:55–19:30 UTC
```

The fallback is a safety net, not a replacement for a real calendar.

---

## 11. Regime Router

### 11.1 Purpose

Classify the current market state and decide which expert, if any, is allowed to operate.

### 11.2 v1 Regime Set

The v1 router uses only 7 regimes:

```text
TREND_WITH_PULLBACK
RANGE
COMPRESSION
BREAKOUT_RETEST
ABNORMAL_MARKET
NEWS_BLACKOUT
NO_TRADE
```

### 11.3 Regimes Deferred Beyond v1

```text
REVERSAL
NEWS_SPIKE_CONTINUATION
SPIKE_FADE
FAKEOUT
GAP_TRADING
TREND_CONTINUATION
COMPRESSION_BREAKOUT
```

### 11.4 Router Versioning

Router version must be logged independently:

```text
router_version = router_v1.0
experts_version = experts_v1.0
```

Every backtest, forward test, dry-run, and live run must log:

```text
router_version
expert_version
cost_model_version
set_file_version
```

### 11.5 Router Freeze Rule

After Phase 4 calibration, the router is frozen.

If any router logic changes:

```text
1. Router version must increment.
2. Every expert calibrated against the previous router must be revalidated.
3. Release snapshot must show old vs new router version.
```

No silent router threshold changes are allowed.

### 11.6 Router Inputs

```text
Session state
News state
Spread state
Volatility state
HTF trend features
LTF structure features
Range validity features
Breakout-retest features
Abnormal market flags
Risk state
Lifecycle state of experts
Open positions
```

### 11.7 Router Outputs

```text
active_regime
allowed_expert
blocked_experts
would_have_allowed_experts
trade_permission
router_confidence_score
block_reason_code
human_readable_reason
```

### 11.8 `would_have_allowed_experts`

This field is mandatory.

For every decision bar, the router must log which experts would have been allowed if the router had not selected or blocked a regime.

Example:

```text
active_regime = NO_TRADE
allowed_expert = NONE
would_have_allowed_experts = TrendPullback:score_61, BreakoutRetest:score_48, RangeMR:score_0
block_reason_code = NEWS_BLACKOUT
```

This allows reviewers to see whether the router is correctly protecting the system or strangling good setups.

### 11.9 Draft v1 Regime Definitions

These are starting definitions for review. Final values must be set from distribution analysis, not optimization.

#### TREND_WITH_PULLBACK

Candidate conditions:

```text
H1 ADX >= objective trend threshold
H1 EMA50 slope and H1 EMA200 slope aligned
Price location agrees with trend direction
M5/M15 pullback into structure or moving-average zone
No news blackout
Spread acceptable
Not abnormal market
```

#### RANGE

Candidate conditions:

```text
H1 trend strength below threshold
M5/M15 range boundaries identifiable
Range width >= N × current spread
At least M touches of upper/lower boundary
No strong breakout close outside range
No news blackout
Spread acceptable
```

#### COMPRESSION

Candidate conditions:

```text
M5 ATR percentile below compression threshold
Range narrowing over recent bars
Inside-bar or low-body cluster present
No active breakout-retest confirmation yet
```

In v1, COMPRESSION is mostly a watch/no-trade state unless Breakout-Retest activates later.

#### BREAKOUT_RETEST

Candidate conditions:

```text
Known level broken by close
Retest occurs within K bars
Retest returns within N points of broken level
Level holds on closing basis
Continuation candle confirms direction
Spread acceptable
No news blackout
```

#### ABNORMAL_MARKET

Candidate conditions:

```text
Weekend gap
Extreme spread
Bad tick
One-candle shock
Broker feed anomaly
Symbol disabled
Unexpected price jump
Rollover instability
Calendar failure during major-event window
```

#### NEWS_BLACKOUT

Candidate conditions:

```text
High-impact USD news within pre-news blackout window
News release currently active
Post-news cooldown active
Manual news lockdown active
```

#### NO_TRADE

Default state when:

```text
No clean regime
Regime conflict
Risk locked
Lifecycle locked
Execution unsafe
Session unsafe
Expert inactive
```

---

## 12. Expert Interface

Every expert must implement the same interface.

```text
DetectSetup()
ValidateRegime()
ScoreSignal()
BuildTradePlan()
ReturnSignal()
ExplainDecision()
```

### 12.1 Standard Signal Object

```text
Signal {
    expert_name
    expert_version
    symbol
    direction
    confidence_score
    entry_type
    entry_price
    stop_loss
    take_profit
    invalidation_level
    risk_reward
    setup_type
    regime
    reason_code
    reason_text
    timestamp
}
```

### 12.2 Direction Values

```text
BUY
SELL
NONE
```

### 12.3 Entry Type Values

```text
MARKET
LIMIT
STOP
NO_ORDER
```

### 12.4 Expert Rule

Experts suggest trades. They do not execute trades.

Execution path:

```text
Expert signal
    ↓
Regime Router approval
    ↓
ExpertLifecycleManager approval
    ↓
Risk Manager approval
    ↓
Execution Guard approval
    ↓
Position Manager approval
    ↓
DryRunMode or OrderSend
```

---

## 13. v1 Trading Experts

## 13.1 Trend Pullback Expert

### Purpose

Trade pullbacks inside an established directional regime.

### Why v1

This is the clearest first expert because it can be tied to observable structure:

```text
Higher-timeframe trend exists.
Lower-timeframe price pulls back.
Support/resistance or moving-average zone holds.
Continuation signal appears.
```

### Candidate Long Setup

```text
Router regime = TREND_WITH_PULLBACK
H1 trend bullish
M5/M15 pulls back toward structure / EMA / prior breakout zone
Pullback low holds
Bullish confirmation candle or structure shift appears
Spread and slippage acceptable
Risk-reward acceptable
```

### Candidate Short Setup

```text
Router regime = TREND_WITH_PULLBACK
H1 trend bearish
M5/M15 rallies toward structure / EMA / prior breakdown zone
Pullback high holds
Bearish confirmation candle or structure shift appears
Spread and slippage acceptable
Risk-reward acceptable
```

### Entry Mode

```text
Market order allowed in v1, subject to Execution Guard.
```

### Invalidation

```text
Long invalidated below pullback low or structure level.
Short invalidated above pullback high or structure level.
```

### Avoid

```text
Late entry after trend extension
Trading in range middle
Trading directly before news
Trading during abnormal spread
Trading if HTF trend is unclear
```

---

## 13.2 Breakout-Retest Expert

### Purpose

Trade a confirmed break of a meaningful level followed by a retest that holds.

### Why v1

Breakout-Retest replaces Fakeout in v1 because it is more mechanically definable.

### Candidate Long Setup

```text
Router regime = BREAKOUT_RETEST
Known resistance level broken by close
Price retests broken resistance as support within K bars
Retest remains within N points of level
No close back below level after retest confirmation
Bullish continuation candle appears
```

### Candidate Short Setup

```text
Router regime = BREAKOUT_RETEST
Known support level broken by close
Price retests broken support as resistance within K bars
Retest remains within N points of level
No close back above level after retest confirmation
Bearish continuation candle appears
```

### Level Sources

```text
Previous day high / low
Session high / low
Range high / low
Weekly high / low
Round-number zone, if defined mechanically
Prior swing high / low
```

### Entry Mode

```text
Prefer stop/limit order logic.
Market order only if explicitly approved after execution testing.
```

### Invalidation

```text
Long invalidated by close back below broken level.
Short invalidated by close back above broken level.
```

### Avoid

```text
Breakouts during news blackout
Breakouts with extreme spread
Breakouts without retest
Retests that occur too late
Retests where range width is too small versus spread
```

---

## 13.3 Range Mean-Reversion Expert

### Purpose

Trade range edges only when the market is demonstrably range-bound.

### Why v1

Range MR is useful for gold, but only if the range-validity gate is strict.

### Candidate Long Setup

```text
Router regime = RANGE
Clear range boundaries exist
Range width >= N × spread
Price reaches lower range boundary
Rejection or hold signal appears
No clean breakdown close
Reward-to-risk acceptable
```

### Candidate Short Setup

```text
Router regime = RANGE
Clear range boundaries exist
Range width >= N × spread
Price reaches upper range boundary
Rejection or hold signal appears
No clean breakout close
Reward-to-risk acceptable
```

### Entry Mode

```text
Prefer limit orders at/near range boundary.
No market chasing in range middle.
```

### Invalidation

```text
Long invalidated by range support breakdown.
Short invalidated by range resistance breakout.
```

### Avoid

```text
Strong trend days
News windows
Range middle
Low range width relative to spread
Recent high-volatility expansion
Unclear range boundaries
```

---

## 14. Deferred Experts

### 14.1 Fakeout / Liquidity Sweep Expert — v1.5

Deferred because sweep/fakeout detection can become subjective and overfit-prone.

It can be reconsidered only after:

```text
Demo spread/slippage behavior is measured.
Breakout-Retest infrastructure is stable.
Router logs show enough rejected fakeout candidates for study.
Edge Thesis Document is defensible.
```

### 14.2 News Spike / Spike Fade Experts — v2+

Deferred because v1 blocks news completely.

### 14.3 Trend Continuation / Compression Breakout / Reversal — v2+

Deferred until v1 proves infrastructure and validation pipeline.

---

## 15. Risk Manager

### 15.1 Purpose

Centralize all account, exposure, and position-sizing controls.

No expert may determine lot size.

### 15.2 v1 Risk Limits

| Risk item | v1 value |
|---|---:|
| Risk per trade | 0.25% to 0.50% |
| Max daily loss | 1% to 2% |
| Max weekly loss | 3% to 5% |
| Max monthly loss | 6% to 8% |
| Max open XAUUSD trades | 1 to 2 |
| Max trades per session | 2 to 4 |
| Max consecutive losses before risk reduction | 3 |
| Max consecutive losses before lockout | 5 |

### 15.3 Daily Loss Accounting

Daily loss must be equity-based and include floating drawdown.

```text
DayStartEquity = equity at start of broker trading day
CurrentEquity = current floating equity
DailyEquityDrawdown = DayStartEquity - CurrentEquity
```

If:

```text
DailyEquityDrawdown >= MaxDailyLoss
```

Then:

```text
Close all EA-managed positions
Block new trades
Set risk_mode = LOCKED_UNTIL_NEXT_DAY
Log reason
Display dashboard lock state
```

### 15.4 Monthly Loss Accounting

Monthly loss is based on starting-of-month equity.

If:

```text
MonthlyEquityDrawdown >= MaxMonthlyLoss
```

Then:

```text
Close all EA-managed positions
Switch to DRY_RUN_ONLY for rest of month
Block all live orders
Require new month or manual governance approval to resume
```

### 15.5 Risk Modes

```text
NORMAL_RISK
REDUCED_RISK
DEFENSIVE_MODE
LOCKED_UNTIL_NEXT_DAY
LOCKED_UNTIL_NEXT_WEEK
DRY_RUN_UNTIL_NEXT_MONTH
MANUAL_LOCKED
```

### 15.6 Forbidden Behavior

The system must not include:

```text
Martingale
Unlimited grid
Doubling after loss
Averaging down without hard invalidation
Moving stop loss farther away
No-stop-loss entries
Recovery mode
Hedge-and-pray logic
Hidden lot multiplier after drawdown
```

---

## 16. Execution Guard

### 16.1 Purpose

Prevent orders during unsafe execution conditions.

### 16.2 Required Checks

```text
Current spread
Spread relative to median spread
Slippage / quote jump
Minimum stop distance
Freeze level
Margin availability
Order rejection frequency
Symbol trading permission
Bad tick detection
Market open state
Rollover state
Broker connection state
```

### 16.3 v1 Spread Rule

Block trading if:

```text
current_spread_points > max(MaxSpreadAbsolutePoints, MaxSpreadMedianMultiplier × median_spread_20_bars)
```

Default review values:

```text
MaxSpreadAbsolutePoints = 30
MaxSpreadMedianMultiplier = 1.5
Median window = 20 bars
```

Important:

```text
The actual point meaning must be validated against the broker's XAUUSD symbol digits.
```

### 16.4 v1 Quote-Jump / Slippage Rule

For market orders, block if:

```text
current_ask - last_quote_ask > MaxMarketOrderJumpPoints
```

Default review value:

```text
MaxMarketOrderJumpPoints = 5
```

For Breakout-Retest and Range MR order types:

```text
Prefer limit/stop logic.
Default MaxDeviationPoints = 3.
```

### 16.5 OrderSend Failure Rule

If there are 3 consecutive order-send failures:

```text
Enter LOCKED_MODE
Block new orders
Log errors
Require manual or configured reset
```

### 16.6 v1 Order Type Rules

| Expert | v1 order type |
|---|---|
| Trend Pullback | Market allowed, guarded strictly |
| Breakout-Retest | Prefer stop/limit order logic |
| Range MR | Prefer limit orders |

---

## 17. MagicNumberAllocator

### 17.1 Purpose

Prevent magic-number collisions with existing or future EAs.

No expert may choose its own magic number.

Every order must request a magic number from `MagicNumberAllocator`.

### 17.2 Proposed Range

```text
Master EA reserved range:   920000 – 929999

Trend Pullback Expert:      920000 – 920099
Range MR Expert:            920100 – 920199
Breakout-Retest Expert:     920200 – 920299
Fakeout Expert:             920300 – 920399  deferred to v1.5
Reserved future experts:    920400 – 929999
```

### 17.3 Occupied Ranges To Fill Before Coding

```text
V85 production:             <fill actual range>
V61 archive:                <fill actual range>
V77/V80:                    <fill actual range>
Other deployed EAs:         <fill actual range>
```

### 17.4 Startup Validation

On EA startup:

```text
Read magic_numbers.md or compiled constants
Validate no duplicate ranges
Validate active expert has assigned range
Validate current EA range does not collide with occupied ranges
Abort startup if collision risk exists
```

### 17.5 Order Rule

```text
No OrderSend may occur without MagicNumberAllocator approval.
```

Milestone 1 has no `OrderSend`, but the allocator can still be built and tested.

---

## 18. ExpertLifecycleManager

### 18.1 Purpose

Automatically suspend or retire experts that fail validation or live-performance gates.

This turns retirement from a human discipline problem into a code-enforced rule.

### 18.2 Expert States

```text
ACTIVE
DRY_RUN_ONLY
SUSPENDED
RETIRED
DISABLED_BY_CONFIG
DISABLED_BY_GOVERNOR
NOT_APPROVED
```

### 18.3 Startup Behavior

On EA startup:

```text
For each expert:
    Read configured status
    Read approval status
    Read last-N-months performance logs
    Read concentration report
    Apply lifecycle gates
    Override .set file if required
    Log lifecycle decision
    Display expert state on dashboard
```

### 18.4 Retirement Gates

An expert is forced to `RETIRED` if:

```text
Holdout / train PF ratio < 0.70
Concentration exceeds hard threshold
Single trade contribution > 10%
Single month contribution > 30%
Single engine contribution > 40%
Max consecutive zero-trade months > 3
Validation failed and expert was not reapproved
```

### 18.5 Suspension Gates

An expert is forced to `SUSPENDED` or `DRY_RUN_ONLY` if:

```text
3 consecutive losing months
Live 7-day rolling PF < 0.8 × backtest PF, if LiveDriftMonitor is enabled
Execution degradation exceeds allowed threshold
Data-quality warning persists
```

### 18.6 Retirement Enforcement

If retired:

```text
EnableExpert = false
Ignore .set file attempt to enable it
Run no live trades
Log reason
Require new versioned release to reactivate
```

Runtime should not physically move source files. Source movement to `_retired/` or `#ifdef` exclusion should be part of build/release governance.

---

## 19. DryRunMode

### 19.1 Purpose

Allow the full decision pipeline to run without placing real orders.

### 19.2 Behavior

In dry-run:

```text
Router runs normally
Risk Manager runs normally
Execution Guard runs normally
Experts score normally
Position Manager simulates plan
OrderSend is a no-op
would_have_traded rows are logged
No broker order is sent
```

### 19.3 Required Dry-Run Logs

```text
would_have_traded
simulated_entry_price
simulated_stop_loss
simulated_take_profit
simulated_lot_size
simulated_risk
reason_for_trade
reason_for_block
expert_state
router_state
execution_state
risk_state
```

### 19.4 v1 Rule

Milestone 1 must be dry-run only and must contain no live order capability.

---

## 20. Position Manager

### 20.1 Purpose

Centralize trade management after approval.

### 20.2 v1 Exit Model

```text
Hard stop loss: mandatory
ATR-based or structure-based take profit: allowed
Break-even: at +1R
Partial close: disabled in v1
Trailing stop: disabled in v1
Time stop: close if not at +0.5R within 4 hours
Session exit: close all positions 30 minutes before broker daily rollover
Overnight holding: disabled in v1
Weekend holding: disabled in v1
```

### 20.3 Centralized Mechanism, Expert Parameters

The Position Manager owns the mechanism.

Experts may provide parameters, such as:

```text
preferred ATR multiplier
preferred invalidation level
preferred maximum holding time
preferred TP method
```

But the Position Manager enforces:

```text
No missing SL
No widening SL
No holding past session rule
No holding through major news if forbidden
No unauthorized exit logic
```

---

## 21. Logger and Diagnostics

### 21.1 Purpose

Make every decision auditable.

The logger must record both trades and non-trades.

### 21.2 Required Log Files

```text
decision_log.csv
trade_log.csv
risk_log.csv
execution_log.csv
lifecycle_log.csv
router_log.csv
error_log.csv
concentration_report.csv
snapshot_manifest.csv
```

### 21.3 Required Fields — Decision Log

```text
timestamp_broker
timestamp_utc
symbol
broker
account_id_hash
router_version
experts_version
cost_model_version
session
regime
allowed_expert
blocked_experts
would_have_allowed_experts
news_state
risk_state
execution_state
spread_points
median_spread_20_bars
ATR
ADX
HTF_bias
LTF_structure
entry_signal
entry_direction
entry_reason_code
no_trade_reason_code
expert_confidence_score
router_confidence_score
lifecycle_state
open_positions_count
daily_equity_drawdown
weekly_equity_drawdown
monthly_equity_drawdown
```

### 21.4 Required Fields — Trade Log

```text
order_id
position_id
magic_number
expert_name
expert_version
entry_time
entry_price
entry_type
stop_loss
take_profit
lot_size
risk_percent
risk_money
reward_to_risk
slippage_points
spread_at_entry
exit_time
exit_price
exit_reason
pnl_money
pnl_R
holding_time_minutes
```

### 21.5 Dashboard Fields

```text
Symbol
Broker time
UTC time
Current spread
Current session
Current regime
Allowed expert
Would-have-allowed experts
Risk mode
News state
Lifecycle states
Open trades
Daily P/L
Weekly P/L
Monthly P/L
Trade permission
Block reason
Router version
EA version
Dry-run/live mode
```

---

## 22. ConcentrationReporter

### 22.1 Purpose

Detect whether performance depends on too few trades, months, or engines.

### 22.2 Required Report Fields

```text
Total net P&L
Total trades
Per-expert P&L
Per-expert P&L share
Per-month P&L
Per-month P&L share
Largest trade P&L share
Top-5 trades P&L share
Max consecutive zero-trade months
Max consecutive losing months
Holdout/train PF ratio
Holdout losing month percentage
```

### 22.3 Required Output

```text
concentration_report.csv
concentration_report_summary.md
```

### 22.4 Approval Dependency

No expert can be approved beyond dry-run unless the concentration report passes hard gates.

---

## 23. Hard Expert Approval Gates

These gates are hard blockers, not review suggestions.

An expert cannot move beyond dry-run unless all required gates pass.

| Gate | Threshold | Action if failed |
|---|---:|---|
| Minimum train trades | >= 40 | Remain dry-run / reject |
| Cost-adjusted train PF | >= 1.50 | Reject or revise edge |
| Holdout / train PF ratio | >= 0.70 | Reject or revise edge |
| Holdout losing months / total months | <= 35% | Reject or revise edge |
| Single trade contribution to net P&L | <= 10% | Reject or revise edge |
| Single engine contribution to portfolio P&L | <= 40% | Reduce allocation or reject |
| Single month contribution to net P&L | <= 30% | Reject or investigate anomaly |
| Max consecutive zero-trade months | <= 3 | Reject or redefine use case |
| Every-fold walk-forward pass | Required | Reject until explained and revalidated |
| Spread ×2 stress survival | Required | Reject or add execution guard |
| Slippage stress survival | Required | Reject or modify order type |

### 23.1 Constants

The gates must exist in code or configuration as constants.

Example:

```text
kMinTrainTrades = 40
kMinCostAdjustedTrainPF = 1.50
kMinHoldoutTrainPFRatio = 0.70
kMaxHoldoutLosingMonthPct = 0.35
kMaxSingleTradeContributionPct = 0.10
kMaxSingleEngineContributionPct = 0.40
kMaxSingleMonthContributionPct = 0.30
kMaxConsecutiveZeroTradeMonths = 3
```

### 23.2 Preferred vs Hard Threshold

For holdout/train PF ratio:

```text
< 0.70 = fail
0.70 to 0.80 = conditional review
>= 0.80 = preferred pass
```

---

## 24. Testing and Validation Plan

### 24.1 Test Stages

```text
Stage 1: Unit testing
Stage 2: Visual backtesting
Stage 3: Router-only dry-run testing
Stage 4: Single-expert dry-run testing
Stage 5: Single-expert backtesting
Stage 6: Router + expert backtesting
Stage 7: Full v1 system backtesting
Stage 8: Out-of-sample testing
Stage 9: Anchored walk-forward testing
Stage 10: Stress testing
Stage 11: Demo forward testing
Stage 12: Small live pilot
```

### 24.2 Unit Tests

Required unit tests:

```text
ATR calculation
ADX calculation
EMA slope calculation
Spread median calculation
Session detection
News blackout detection
Fallback news schedule
Risk-cap trigger
Monthly loss trigger
Magic-number allocation
Magic-number collision rejection
Router classification
would_have_allowed_experts logging
DryRunMode no-op OrderSend
Lifecycle state override
Execution spread block
Execution slippage block
Time stop
Rollover exit
Server time validation
```

### 24.3 Required Historical Test Periods

```text
2020-03 to 2020-04: COVID volatility crash + rally
2022-09 to 2022-11: strong USD / sustained trend behavior
2023-03: SVB / banking crisis stress window
2024-04: Iran/Israel geopolitical spike window
2025 full year: most recent full-year regime
Continuous 5-year M5 backtest: overall expectancy validation
```

### 24.4 Anchored Walk-Forward Specification

```text
Method: anchored walk-forward
Initial train window: 18 months
Validation window: 3 months
Step: 3 months
Acceptance: holdout PF >= 0.70 × train PF on every fold
```

One bad fold is a mandatory rejection or investigation. Passing average PF is not enough.

### 24.5 Stress Tests

Required stress tests:

```text
Normal spread
2× spread sustained for full session
3× spread shock
Normal slippage
High slippage
Delayed execution
News blackout enabled
News blackout disabled for diagnostic only
Rollover window
Friday close
Monday open
VPS restart at random tick
Symbol disabled mid-session
Broker disconnect
Negative balance / margin-call simulation
OrderSend rejection burst
Calendar unavailable
Server time skew
```

### 24.6 Demo Forward Test

Minimum:

```text
6 weeks demo forward test
At least 2 weeks must include high-impact USD news events
Same broker intended for live pilot
Same VPS intended for live pilot
Same symbol and account type
Same .set file family
Daily log review
Weekly concentration review
```

### 24.7 Live Pilot Criteria

Live pilot can be considered only after:

```text
Milestone 1 dry-run passed
Edge Thesis approved
Expert passed approval gates
Walk-forward passed every fold
Stress tests passed
Demo forward test passed
Magic numbers resolved
VPS plan approved
V85 coexistence/replacement decision resolved
```

---

## 25. Data Plan

### 25.1 Required Data

```text
M1 candles
M5 candles
M15 candles
H1 candles
H4 candles
D1 candles
Spread history
Execution history
Order rejection history
Account equity history
News calendar history
```

### 25.2 Tick Data Limitation

If broker tick history is available only after a certain date, document:

```text
Tick history start date
Which tests use tick data
Which tests use bar data
How spread is modeled before tick history exists
How slippage is modeled before live data exists
```

### 25.3 Optional External Data

Do not add external macro feeds in v1 unless review explicitly approves.

Possible future filters:

```text
DXY / USD proxy
US 10-year yield
US real yield proxy
COMEX gold futures
Gold ETF flow data
COT data
Volatility index
```

These are deferred because they add data-dependency and fragility.

---

## 26. ServerTimeValidator

### 26.1 Purpose

Detect broker/server/local time mismatch before the EA makes time-sensitive decisions.

### 26.2 Required Checks

```text
TimeCurrent()
TimeTradeServer()
TimeLocal()
Expected broker offset
UTC conversion
News calendar time alignment
Session window alignment
```

### 26.3 Optional NTP Check

If external NTP access is available and approved, compare broker/server time against NTP-derived UTC.

If NTP is unavailable:

```text
Log warning
Use internal consistency checks
Run in reduced confidence mode if time mapping is uncertain
```

### 26.4 Hard Abort Rule

If confirmed time drift exceeds 60 seconds and cannot be resolved:

```text
Abort live trading startup
Allow dry-run only
Log reason
Display dashboard warning
```

---

## 27. Development Phases

## Phase 0 — Final Pre-Coding Specification

Deliverables:

```text
Plan v0.2 reviewed
Edge Thesis Document
magic_numbers.md
filter_inventory.md
cost_model.md
router_versioning.md
release_snapshot_spec.md
Open decisions answered
```

Exit criteria:

```text
Review team approves revised plan
At least one expert has defensible Edge Thesis
MT5/MQL5 commitment confirmed
V85 coexistence/replacement decision resolved
VPS plan approved
```

---

## Phase 1 — Dry-Run Core Infrastructure

Build:

```text
Master EA shell
MarketDataEngine
FeatureEngine
SessionEngine
ServerTimeValidator
ConfigManager
Logger
Dashboard
DryRunMode
```

No trading experts enabled.

No `OrderSend` calls in the codebase.

Exit criteria:

```text
EA boots
EA logs one decision row per M5 bar
Dashboard displays state
Server time validator works
DryRunMode is active
No live orders are possible
```

---

## Phase 2 — Governance and Safety Infrastructure

Build:

```text
RiskManager
ExecutionGuard
NewsGuard
MagicNumberAllocator
ExpertLifecycleManager
KillSwitch
CostModel
```

Exit criteria:

```text
Daily/weekly/monthly risk caps simulate correctly
Spread/slippage blocks simulate correctly
News blackout works
Fallback news schedule works
Magic-number collision check works
Lifecycle states apply correctly
Kill switch works
```

---

## Phase 3 — Regime Router v1.0

Build:

```text
7-regime router
Router version logging
would_have_allowed_experts logging
Objective threshold loading
Router dashboard state
```

Exit criteria:

```text
Router classifies every M5 bar
NO_TRADE is default when unclear
Router logs active regime and reason codes
Router does not activate more than one expert
Router thresholds are documented
```

---

## Phase 4 — Expert 1: Trend Pullback

Build Trend Pullback Expert in dry-run first.

Exit criteria:

```text
Edge Thesis approved
Expert returns standardized Signal
Expert respects router
Expert respects lifecycle state
Expert respects risk manager
Expert respects execution guard
Dry-run logs would-have-traded rows
Backtest gates pass before live order capability
```

---

## Phase 5 — Expert 2: Breakout-Retest

Build Breakout-Retest Expert in dry-run first.

Exit criteria:

```text
Edge Thesis approved
Stop/limit order infrastructure validated
Expert returns standardized Signal
Breakout-retest definitions are mechanical
Backtest gates pass before live order capability
```

---

## Phase 6 — Expert 3: Range Mean-Reversion

Build Range MR Expert in dry-run first.

Exit criteria:

```text
Edge Thesis approved
Range-validity gate documented
Range width vs spread rule enforced
No trading in range middle
Backtest gates pass before live order capability
```

---

## Phase 7 — Full v1 Backtesting and Walk-Forward

Tasks:

```text
Single-expert backtests
Router + expert backtests
Full v1 portfolio backtest
Anchored walk-forward
Concentration report
Stress tests
Snapshot bundle
```

Exit criteria:

```text
Every expert passes hard gates
Full system passes hard gates
No unexplained trade
No unexplained block
No missing log field
No concentration breach
```

---

## Phase 8 — Demo Forward Test

Tasks:

```text
Deploy to VPS demo
Run 6 weeks minimum
Monitor logs daily
Run alongside V85 only if dry-run or risk allocation resolved
Record spread/slippage behavior
Capture news-event behavior
Generate weekly reports
```

Exit criteria:

```text
No unauthorized orders
No risk rule violations
No time sync failure
No unresolved lifecycle override
Execution behavior matches assumptions
Router does not starve experts unexpectedly
```

---

## Phase 9 — Small Live Pilot

Only after review approval.

Rules:

```text
Minimum lot size
Reduced risk
Strict daily/monthly lock
No news trading
No overnight holding
No weekend holding
Daily log review
Weekly concentration review
Manual kill switch available
```

Exit criteria:

```text
Live execution stable
Risk controls function correctly
No unauthorized trades
No unexplained behavior
No degradation beyond lifecycle thresholds
```

---

## 28. Recommended First Coding Milestone

Milestone 1 must be extremely strict.

### 28.1 Milestone 1 Scope

```text
Master EA boots on demo account
Dry-run mode only
No expert enabled
No OrderSend calls in codebase
Classifies regime on every M5 bar
Logs decision_log.csv with one row per M5 bar
Displays dashboard
Tracks daily/weekly/monthly risk caps
Validates server/broker time
```

### 28.2 Milestone 1 Acceptance Criteria

```text
EA runs for 5 trading days continuously without runtime errors
One decision_log.csv row per M5 bar
Dashboard updates correctly
ServerTimeValidator catches deliberately injected time skew
Risk caps trigger under simulated equity-curve injection
Router version logged
would_have_allowed_experts field present
DryRunMode prevents all order placement
No OrderSend exists in codebase
```

Milestone 2 cannot begin until Milestone 1 has run 5 clean trading days.

---

## 29. Open Pre-Coding Decisions

These must be answered before Phase 1 starts.

### 29.1 V85 Coexistence vs Replacement

Decision needed:

```text
Will V85 remain running on Capital.com-Demo while the new EA is developed?
```

Recommended answer:

```text
New EA may run beside V85 only in dry-run mode.
No trading-enabled coexistence until magic-number ranges and portfolio risk allocation are resolved.
```

### 29.2 Magic Ranges for Existing EAs

Need actual values:

```text
V85 production magic range
V61 archive magic range
V77/V80 magic ranges
Any other deployed EA ranges
```

### 29.3 VPS / Hosting

Decision needed:

```text
Where will demo forward testing run?
```

Recommended answer:

```text
Dedicated VPS, not local desktop.
```

### 29.4 Walk-Forward Threshold

Decision needed:

```text
Use 0.70 or 0.80 for holdout/train PF threshold?
```

Recommended answer:

```text
0.70 hard minimum
0.80 preferred pass
0.70–0.80 conditional review
```

### 29.5 Build Cadence

Decision needed:

```text
Accept staged build timeline, or reduce scope further?
```

Recommended answer:

```text
Commit only to Milestone 1 first.
Do not promise live pilot date until Milestone 1 and Edge Thesis are approved.
```

---

## 30. Failure Modes and Mitigations

| Failure mode | Mitigation |
|---|---|
| Magic-number collision | MagicNumberAllocator, startup collision check, `magic_numbers.md` |
| Router overfit | Versioned router, objective thresholds, freeze rule, revalidation on change |
| Expert overfit | Hard approval gates, walk-forward every-fold pass, holdout/train PF rule |
| Thin-sample expert | Minimum 40 train trades before approval |
| P&L concentration | ConcentrationReporter, single-trade/month/engine gates |
| Dead strategy with long inactivity | Max consecutive zero-trade months gate |
| Hidden filters | `filter_inventory.md` |
| Reported P&L inconsistency | One authoritative tester run per release snapshot |
| Spread/slippage mismatch | Cost model, execution guard, stress tests, demo forward measurement |
| News volatility loss | NewsGuard blocks all high-impact news in v1 |
| Server time mismatch | ServerTimeValidator, dry-run fallback, abort live trading if drift unresolved |
| Broker rejects repeated orders | Lock after 3 consecutive OrderSend failures |
| Strategy degradation | ExpertLifecycleManager, future LiveDriftMonitor |
| VPS restart | Restart stress test and open-state recovery |
| Broker symbol disabled | Symbol-disabled stress test and execution lock |
| Weekend gap | No weekend holding in v1 |
| Rollover spread spike | Rollover exit and spread guard |

---

## 31. Configuration Plan

All major parameters must be configurable but documented.

### 31.1 Config Groups

```text
General settings
Dry-run settings
Risk settings
Session settings
News settings
Execution settings
Router settings
Expert activation settings
Position management settings
Magic-number settings
Lifecycle settings
Logging settings
```

### 31.2 Example Config Values

```text
RunMode = DRY_RUN
EnableLiveTrading = false
EnableTrendPullbackExpert = false
EnableBreakoutRetestExpert = false
EnableRangeMRExpert = false

RiskPerTrade = 0.005
MaxDailyLoss = 0.02
MaxWeeklyLoss = 0.05
MaxMonthlyLoss = 0.08

NewsBlackoutBeforeMinutes = 30
NewsBlackoutAfterMinutes = 30
CloseBeforeCPI = true
CloseBeforeNFP = true
CloseBeforeFOMC = true

MaxSpreadAbsolutePoints = 30
MaxSpreadMedianMultiplier = 1.5
MaxMarketOrderJumpPoints = 5
MaxDeviationPoints = 3

UseBreakEven = true
BreakEvenAtR = 1.0
UsePartialClose = false
UseTrailingStop = false
TimeStopHours = 4
MinProgressBeforeTimeStopR = 0.5
```

### 31.3 Config Rule

Every configurable filter must be in `filter_inventory.md`.

---

## 32. Release and Audit Process

### 32.1 Version Naming

```text
XAU_MasterEA_v0.2_review
XAU_MasterEA_v0.3_dryrun_core
XAU_MasterEA_v0.4_governance
XAU_MasterEA_v0.5_router
XAU_MasterEA_v0.6_trend_pullback_dryrun
XAU_MasterEA_v0.7_breakout_retest_dryrun
XAU_MasterEA_v0.8_range_mr_dryrun
XAU_MasterEA_v1.0_demo_candidate
```

### 32.2 Snapshot Bundle

Every test candidate must create:

```text
snapshot_<version>_<date>.zip
```

Containing:

```text
EA binary
Source files or git commit hash
.set file
magic_numbers.md
filter_inventory.md
cost_model.md
router_versioning.md
decision_log sample
backtest report
walk-forward report
concentration report
holdout report
known issues
approval status
```

---

## 33. Review Team Checklist for v0.2

The next review should focus on these questions.

### 33.1 Architecture

```text
Is one Master EA with `.mqh` class modules still approved?
Are MagicNumberAllocator and ExpertLifecycleManager specified clearly enough?
Is DryRunMode strict enough?
Is Milestone 1 correctly scoped with no OrderSend?
```

### 33.2 Regime Router

```text
Are 7 regimes enough for v1?
Are any regime definitions still too subjective?
Are objective distribution-based thresholds acceptable?
Is the router freeze/revalidation rule strict enough?
```

### 33.3 Experts

```text
Are Trend Pullback, Breakout-Retest, and Range MR the correct v1 experts?
Should Range MR be delayed until after Trend Pullback and Breakout-Retest?
Is Fakeout correctly deferred to v1.5?
Does each expert need a stronger Edge Thesis before coding?
```

### 33.4 Risk

```text
Are the daily, weekly, and monthly caps acceptable?
Should daily cap force-close open positions?
Should monthly cap force dry-run for the rest of the month?
Is 0.25% to 0.50% risk per trade appropriate?
```

### 33.5 Execution

```text
Are 30 absolute points and 1.5× median spread reasonable for the target broker?
Are 5-point quote-jump and 3-point deviation rules reasonable?
Should market orders be allowed only for Trend Pullback?
```

### 33.6 News

```text
Should v1 block all high-impact USD news?
Are 30-minute pre- and post-news windows enough?
Should CPI/NFP/FOMC force-close open trades?
Is the fallback calendar approach acceptable?
```

### 33.7 Testing

```text
Are the hard approval gates strict enough?
Is minimum train trades >= 40 enough?
Should holdout/train PF be hard 0.70 or 0.80?
Are required historical windows sufficient?
Are stress tests sufficient?
Is 6-week demo forward test enough?
```

### 33.8 Deployment

```text
Can the new EA run dry-run beside V85?
What are actual occupied magic-number ranges?
Where will VPS demo forward testing run?
What is the exact broker/symbol/cost model?
```

---

## 34. Final v0.2 Recommendation

Do not begin trading-expert coding yet.

The correct next sequence is:

```text
1. Review and approve Plan v0.2.
2. Produce Edge Thesis Document for Trend Pullback, Breakout-Retest, and Range MR.
3. Fill actual magic-number ranges.
4. Create filter_inventory.md.
5. Create cost_model.md.
6. Create router_versioning.md.
7. Confirm V85 coexistence/replacement decision.
8. Confirm VPS plan.
9. Start Milestone 1 only: dry-run infrastructure, no experts, no OrderSend.
```

The first live-trading-capable code should not exist until the infrastructure, router logging, risk caps, magic-number allocation, and dry-run pipeline are proven.

The system should be built to reject weak experts automatically, not rely on manual discipline.

---

## 35. Final Scope Statement

The v1 system is:

```text
A conservative, MT5/MQL5, XAUUSD-only, regime-routed Master EA with centralized risk, execution protection, lifecycle governance, dry-run validation, and three mechanically defined trading experts.
```

The v1 system is not:

```text
A news bot
A grid bot
A martingale bot
A recovery bot
A high-frequency scalper
A machine-learning system
A multi-symbol portfolio
A discretionary signal wrapper
```

The v1 system should only graduate from review to coding if the review team agrees that the controls are strict enough to avoid repeating prior overfitting, concentration, magic-number, and deployment-failure patterns.

