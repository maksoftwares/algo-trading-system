# XAUUSD Algo Trading System Plan v0.1

> **Purpose:** Review-ready planning document for a modular XAUUSD algorithmic trading system.  
> **Status:** Draft for technical and strategy review.  
> **Important note:** This document is for system design and research planning only. It is not financial advice, investment advice, or a guarantee of profitability.

---

## 1. Project Objective

Build a modular XAUUSD trading system where multiple independent strategy experts operate under one centralized master controller.

The goal is **not** to create one signal that trades every condition. The goal is to classify the market regime first, then allow only the expert designed for that condition to act.

XAUUSD needs this structure because gold is not driven only by chart patterns. The World Gold Council identifies the London OTC market, the US futures market, and the Shanghai Gold Exchange as the three most important gold trading centers, together representing more than 90% of global gold trading volumes. CME also describes gold as reacting quickly to political and economic events and notes nearly 24-hour electronic access for gold futures.

Sources:

- World Gold Council — Global gold market structure: <https://www.gold.org/gold-market-structure/global-gold-market>
- CME Group — Gold futures overview: <https://www.cmegroup.com/markets/metals/precious/gold.html>

The system should be built as:

```text
Regime first.
Risk second.
Signal third.
Execution last.
```

Not:

```text
Indicator gives signal.
Bot enters trade.
```

---

## 2. Core Design Principle

The default state of the bot should be:

```text
NO TRADE
```

The bot should only trade when all required conditions are satisfied:

```text
Market regime is clear
Spread is acceptable
Volatility is acceptable
Session is acceptable
News risk is acceptable
Risk limits are not breached
One expert has a valid setup
The router allows that expert
Execution conditions are clean
```

This is especially important for XAUUSD because gold can move cleanly during trends, but it can also produce violent fakeouts, news spikes, liquidity sweeps, and spread expansion.

---

## 3. Recommended System Architecture

The system should be built as **one master EA** with multiple internal modules.

```text
Master XAUUSD EA
│
├── 1. Market Data Engine
├── 2. Feature Engine
├── 3. Session Engine
├── 4. News / Calendar Guard
├── 5. Regime Router
├── 6. Risk Manager
├── 7. Execution Guard
├── 8. Position Manager
├── 9. Logger / Diagnostics Engine
│
├── 10. Trend Pullback Expert
├── 11. Range Expert
├── 12. Fakeout / Liquidity Sweep Expert
│
├── 13. Trend Continuation Expert
├── 14. Compression Breakout Expert
├── 15. Breakout-Retest Expert
├── 16. Reversal Expert
├── 17. News Spike Continuation Expert
├── 18. Spike Fade Expert
└── 19. Gap / Abnormal Market Expert
```

This is **19 internal modules**, but not 19 separate live bots.

Practical breakdown:

```text
9 infrastructure / control modules
10 trading experts
```

For the first coding phase, we should **not build all 19 immediately**. The first version should include:

```text
Master EA
Market Data Engine
Feature Engine
Session Engine
News Guard
Regime Router
Risk Manager
Execution Guard
Position Manager
Logger

Trend Pullback Expert
Range Expert
Fakeout / Liquidity Sweep Expert
```

That gives us a controlled MVP with 3 trading experts and all required safety infrastructure.

---

## 4. Platform Assumption

Initial assumption: **MT5 / MQL5 Expert Advisor**, because the project language refers to “experts,” which usually means Expert Advisors.

In MQL5, `OnTick()` is called when a new quote arrives for the symbol attached to the EA’s chart. This means the main EA should be event-driven, but internally it should avoid making decisions on every random tick. Most strategy decisions should be made on confirmed candle events, such as new M1, M5, M15, or H1 candles.

Source:

- MQL5 documentation — OnTick event: <https://www.mql5.com/en/docs/event_handlers/ontick>

If the final platform is MT4, Python, cTrader, NinjaTrader, or TradingView plus broker API, the same architecture still applies, but implementation details will change.

---

## 5. System-Wide Assumptions for Review

The review team should challenge these assumptions before coding begins.

| Area | Proposed assumption |
|---|---|
| Symbol | XAUUSD |
| Platform | MT5 / MQL5 initially |
| Style | Intraday, not high-frequency |
| Main timeframes | M5 / M15 / H1 |
| Higher-timeframe filter | H1 / H4 / D1 |
| Sessions | Asia, London, New York, rollover, weekend |
| Default state | No trade |
| Risk style | Conservative |
| Initial risk per trade | 0.25% to 0.50% |
| Max daily loss | 1% to 2% |
| Max weekly loss | 3% to 5% |
| News handling | Block or reduce risk around high-impact events |
| First experts to build | Trend Pullback, Range, Fakeout / Liquidity Sweep |
| Forbidden first-version logic | Martingale, unlimited grid, no-stop-loss recovery logic |

---

## 6. Market Situations the System Must Classify

The Regime Router should classify the market into one of these broad regimes:

```text
TREND_UP
TREND_DOWN
PULLBACK_IN_UPTREND
PULLBACK_IN_DOWNTREND
RANGE
COMPRESSION
BREAKOUT_UP
BREAKOUT_DOWN
BREAKOUT_RETEST_UP
BREAKOUT_RETEST_DOWN
FAKEOUT_UP
FAKEOUT_DOWN
REVERSAL_UP
REVERSAL_DOWN
NEWS_SPIKE_UP
NEWS_SPIKE_DOWN
SPIKE_EXHAUSTION_UP
SPIKE_EXHAUSTION_DOWN
GAP_UP
GAP_DOWN
ABNORMAL_MARKET
NO_TRADE
```

The system does not need a separate expert for every state. Many states can be handled by the same expert.

Example:

```text
TREND_UP
PULLBACK_IN_UPTREND
TREND_DOWN
PULLBACK_IN_DOWNTREND
```

can be handled by:

```text
Trend Pullback Expert
Trend Continuation Expert
```

---

# 7. Core Module Specifications

## 7.1 Market Data Engine

Purpose: collect and normalize all price and broker data.

Responsibilities:

```text
Read Bid / Ask
Read spread
Read tick volume
Read candle data
Build M1 / M5 / M15 / H1 / H4 / D1 structures
Track previous day high / low
Track previous week high / low
Track session high / low
Track current candle body / wick structure
Track broker server time
Map broker time to UTC and major sessions
```

Required outputs:

```text
Current bid
Current ask
Current spread
Current ATR values
Current candle structure
Previous candle structure
Session range
Daily range
Weekly range
Broker time
UTC time
```

Review questions:

```text
Will we use broker candles only, or independent data validation?
Do we need external futures data from COMEX as a filter?
Will the EA support only one broker feed at first?
```

---

## 7.2 Feature Engine

Purpose: convert raw price data into reusable features.

Features to calculate:

```text
ATR
ADX
Moving average slope
Swing highs
Swing lows
Market structure
Range width
Candle body percentage
Upper wick percentage
Lower wick percentage
Break of structure
Change of character
Distance from previous high
Distance from previous low
Distance from moving average
Distance from session VWAP if available
Volatility percentile
Spread percentile
```

Possible indicators:

```text
ATR for volatility
ADX for trend strength
EMA or SMA slope for direction
Fractals or swing logic for structure
Donchian channels for breakout range
RSI only as optional exhaustion filter
```

Important rule:

```text
The Feature Engine should not generate trade signals.
```

It should only produce clean, reusable information for the Router and Experts.

---

## 7.3 Session Engine

Purpose: classify trading session and session-specific behavior.

Session states:

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

The LBMA Gold Price is set twice daily at 10:30 and 15:00 UK time, so the system should at minimum be aware of those benchmark windows, even if the first version simply logs or filters around them.

Source:

- LBMA Gold Price: <https://www.lbma.org.uk/prices-and-data/lbma-gold-price/lbma-gold-price>

Session Engine outputs:

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
is_fix_window
```

Review questions:

```text
Should we trade during Asia or only use Asia to define range levels?
Should London open be tradable or treated as high-risk?
Should New York pre-news windows be blocked?
Should Friday late session be disabled?
```

---

## 7.4 News / Calendar Guard

Purpose: prevent the bot from trading blindly into scheduled high-impact events.

Events to track:

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
Fed speeches
Major geopolitical events, if manually flagged
```

News states:

```text
NO_NEWS_RISK
PRE_NEWS_BLACKOUT
NEWS_RELEASE_ACTIVE
POST_NEWS_COOLDOWN
MANUAL_NEWS_LOCKDOWN
```

Suggested initial rules:

```text
Block new trades 30 minutes before red-folder USD news.
Block new trades 15 to 30 minutes after red-folder USD news.
Allow only News Spike Expert if explicitly enabled.
Force wider slippage checks during post-news period.
Do not allow Range Expert during immediate post-news volatility.
```

Review questions:

```text
Which economic calendar API will be used?
Will news filtering be fully automatic or manual in v1?
Should open trades be closed before FOMC / CPI / NFP?
Should the bot reduce risk instead of blocking completely?
```

---

## 7.5 Regime Router

Purpose: decide which expert is allowed to operate.

This is the most important module.

Inputs:

```text
Trend strength
Volatility
Market structure
Session
Spread
News state
Higher-timeframe bias
Current price location
Recent breakout/fakeout state
Open positions
Risk state
```

Outputs:

```text
active_regime
allowed_expert
blocked_experts
trade_permission
reason
confidence_score
```

Example routing logic:

```text
If spread is too high:
    regime = NO_TRADE
    allowed_expert = NONE

Else if daily loss limit hit:
    regime = NO_TRADE
    allowed_expert = NONE

Else if news blackout active:
    regime = NO_TRADE or NEWS_ONLY

Else if abnormal tick or gap detected:
    regime = ABNORMAL_MARKET
    allowed_expert = GAP_ABNORMAL_EXPERT

Else if HTF trend is bullish and LTF pullback is valid:
    regime = PULLBACK_IN_UPTREND
    allowed_expert = TREND_PULLBACK_EXPERT

Else if HTF trend is bearish and LTF pullback is valid:
    regime = PULLBACK_IN_DOWNTREND
    allowed_expert = TREND_PULLBACK_EXPERT

Else if range conditions are valid:
    regime = RANGE
    allowed_expert = RANGE_EXPERT

Else if liquidity sweep detected:
    regime = FAKEOUT
    allowed_expert = FAKEOUT_EXPERT

Else:
    regime = NO_TRADE
    allowed_expert = NONE
```

Review questions:

```text
Should the router allow multiple experts to score signals, then pick the best?
Or should it activate only one expert based on regime?
Should experts be allowed to disagree with the router?
What confidence score is required before trade permission?
```

Recommendation for v1:

```text
Allow only one active trading expert at a time.
```

This reduces conflict and makes debugging easier.

---

## 7.6 Risk Manager

Purpose: centralize all position sizing and account protection.

No expert should decide lot size independently.

Risk Manager controls:

```text
Risk per trade
Maximum daily loss
Maximum weekly loss
Maximum total drawdown
Maximum open positions
Maximum exposure
Maximum trades per day
Maximum trades per session
Risk reduction after losing streak
Risk reduction during high volatility
Risk reduction during news cooldown
Minimum reward-to-risk
Maximum stop-loss distance
Minimum stop-loss distance
```

Suggested initial parameters:

```text
Base risk per trade: 0.25% to 0.50%
Maximum daily loss: 1% to 2%
Maximum weekly loss: 3% to 5%
Maximum open XAUUSD trades: 1 to 2
Maximum trades per session: 2 to 4
Minimum reward-to-risk: 1.2R to 1.5R
Hard emergency drawdown lock: configurable
```

Risk modes:

```text
NORMAL_RISK
REDUCED_RISK
DEFENSIVE_MODE
LOCKED_MODE
```

Example:

```text
If losing streak >= 3:
    risk_mode = REDUCED_RISK

If daily loss limit reached:
    risk_mode = LOCKED_MODE

If volatility extreme:
    risk_mode = DEFENSIVE_MODE
```

Review questions:

```text
Should risk be fixed percentage or volatility-adjusted?
Should risk reduce after a loss or only after multiple losses?
Should open positions be force-closed after daily loss limit?
Should daily loss be based on balance, equity, or realized P/L?
```

---

## 7.7 Execution Guard

Purpose: protect against bad fills, bad spreads, and broker-side execution issues.

Execution Guard checks:

```text
Current spread
Spread relative to recent average
Slippage
Minimum stop distance
Freeze level
Margin availability
Order rejection
Partial fill behavior
Requote behavior
Tick abnormality
Candle abnormality
Broker trading permissions
```

Broker and counterparty risk matter in retail OTC products. The CFTC advises traders to verify registration status and disciplinary history before depositing funds with firms or people selling trading products or strategies. It has also warned specifically about researching OTC forex dealers, including verifying registration and disciplinary history.

Sources:

- CFTC — Check registration and background: <https://www.cftc.gov/check>
- CFTC press release on forex fraud awareness: <https://www.cftc.gov/PressRoom/PressReleases/8566-22>

Execution states:

```text
EXECUTION_OK
SPREAD_TOO_HIGH
SLIPPAGE_TOO_HIGH
MARGIN_INSUFFICIENT
STOP_DISTANCE_INVALID
ORDER_REJECTED
BROKER_LOCKED
BAD_TICK
```

Suggested first-version rule:

```text
No order should be sent unless Execution Guard returns EXECUTION_OK.
```

Review questions:

```text
What is the maximum acceptable spread for XAUUSD?
Should spread thresholds be fixed or ATR-adjusted?
What is the maximum allowed slippage?
Should market orders be allowed during high volatility?
Should limit orders be preferred for some experts?
```

---

## 7.8 Position Manager

Purpose: manage trades after entry.

Position Manager controls:

```text
Stop loss
Take profit
Break-even
Partial close
Trailing stop
Time stop
Session exit
Opposite signal exit
Emergency exit
News exit
Weekend exit
```

Exit types:

```text
FIXED_TP
ATR_TP
STRUCTURE_TP
PARTIAL_CLOSE
TRAILING_STOP
BREAK_EVEN
TIME_EXIT
SESSION_EXIT
MANUAL_KILL
```

Suggested v1 behavior:

```text
Every trade must have a hard stop loss.
No trade should move stop loss farther away.
Break-even only after price has moved meaningfully in favor.
Partial close should be optional, not default.
Time stop should close trades that fail to move after a defined period.
```

Review questions:

```text
Should exits be expert-specific or centralized?
Should trailing be ATR-based or structure-based?
Should the bot hold trades overnight?
Should it hold trades over the weekend?
Should break-even be used, or does it reduce expectancy?
```

---

## 7.9 Logger / Diagnostics Engine

Purpose: make the bot auditable.

The logger should record **every important decision**, not just trades.

Required logs:

```text
Timestamp
Symbol
Broker time
UTC time
Session
Bid
Ask
Spread
ATR
ADX
Market regime
Higher-timeframe bias
Allowed expert
Blocked experts
Entry signal
Entry reason
No-trade reason
Risk mode
Lot size
Stop-loss price
Take-profit price
Stop size in points
Reward-to-risk
Order result
Slippage
Exit reason
P/L
Equity
Balance
Drawdown
```

Minimum log files:

```text
trade_log.csv
decision_log.csv
risk_log.csv
execution_log.csv
error_log.csv
```

This module is essential because without it, we will only know whether the backtest made or lost money. We will not know **why**.

Review questions:

```text
Should logs be CSV only or also database-based?
Should every tick be logged or only decision events?
Should the bot produce screenshots or chart markers?
Should backtest logs and live logs use the same format?
```

---

# 8. Standard Expert Interface

Every trading expert should follow the same structure.

```text
DetectSetup()
ValidateRegime()
ScoreSignal()
BuildTradePlan()
ReturnSignal()
ExplainDecision()
```

Each expert should return a standardized object.

```text
Signal {
    expert_name
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
    reason
    timestamp
}
```

Possible `direction` values:

```text
BUY
SELL
NONE
```

Possible `entry_type` values:

```text
MARKET
LIMIT
STOP
NO_ORDER
```

Important rule:

```text
Experts suggest trades.
The router and risk manager approve or reject trades.
```

---

# 9. Trading Expert Specifications

## 9.1 Trend Pullback Expert — v1 Priority

Purpose: trade pullbacks in established trends.

Activates when:

```text
Higher timeframe trend is clear
Lower timeframe pulls back
Price reaches support/resistance, moving average, prior breakout level, or structure zone
Volatility is normal or moderate
No major news blackout
```

Bullish setup:

```text
HTF bullish
LTF pulls back
Price holds above key support
Bullish rejection candle or structure shift appears
Spread acceptable
```

Bearish setup:

```text
HTF bearish
LTF rallies into resistance
Bearish rejection candle or structure shift appears
Spread acceptable
```

Entry options:

```text
Market entry after confirmation candle
Limit entry at structure level
Stop entry above/below confirmation candle
```

Invalidation:

```text
Bullish trade invalidated below pullback low
Bearish trade invalidated above pullback high
```

Avoid:

```text
Entering after extended move
Trading when trend is unclear
Trading directly before news
Trading in range middle
```

First-version status:

```text
Build in v1.
```

---

## 9.2 Range Mean-Reversion Expert — v1 Priority

Purpose: buy range lows and sell range highs.

Activates when:

```text
Market is sideways
ADX or trend strength is low
Range boundaries are clear
ATR is not extreme
Price is near range edge
```

Bullish setup:

```text
Price reaches range support
Lower wick / rejection appears
No clean breakdown
Reward-to-risk acceptable
```

Bearish setup:

```text
Price reaches range resistance
Upper wick / rejection appears
No clean breakout
Reward-to-risk acceptable
```

Avoid:

```text
Trading middle of range
Trading during volatility expansion
Trading immediately after major news
Trading if range width is too small relative to spread
```

Invalidation:

```text
Range support breaks for long
Range resistance breaks for short
```

First-version status:

```text
Build in v1.
```

---

## 9.3 Fakeout / Liquidity Sweep Expert — v1 Priority

Purpose: trade false breakouts and stop hunts.

Activates when:

```text
Price sweeps a known high or low
Breakout fails
Price closes back inside prior structure
Reversal confirmation appears
```

Bullish fakeout:

```text
Price sweeps below prior low
Sellers get trapped
Price reclaims the level
Buy confirmation appears
```

Bearish fakeout:

```text
Price sweeps above prior high
Buyers get trapped
Price loses the level
Sell confirmation appears
```

Important levels:

```text
Asian high
Asian low
Previous day high
Previous day low
Weekly high
Weekly low
Range high
Range low
Round numbers
```

Avoid:

```text
Trading every wick as a fakeout
Fading strong genuine breakouts
Trading during news without news mode
```

First-version status:

```text
Build in v1.
```

---

## 9.4 Trend Continuation Expert — Later Phase

Purpose: enter strong continuation moves without waiting for deep pullback.

Activates when:

```text
Trend strength is high
Momentum candles are strong
Pullbacks are shallow
HTF and LTF align
```

Risk:

```text
Can easily chase late moves.
```

Status:

```text
Build after v1 proves stable.
```

---

## 9.5 Compression Breakout Expert — Later Phase

Purpose: trade expansion after volatility compression.

Activates when:

```text
ATR contracts
Range narrows
Inside bars or compression candles appear
Price approaches breakout point
```

Needs strong filters because false breakouts are common.

Status:

```text
Build after v1.
```

---

## 9.6 Breakout-Retest Expert — Later Phase

Purpose: trade confirmed breakout retests.

Activates when:

```text
Price breaks support or resistance
Price returns to retest broken level
Retest holds
Continuation signal appears
```

This is safer than raw breakout trading but may miss fast moves.

Status:

```text
Build after v1.
```

---

## 9.7 Reversal Expert — Later Phase

Purpose: trade full market structure changes.

Activates when:

```text
Trend exhaustion appears
Structure breaks
New higher low or lower high forms
Momentum shifts
```

Risk:

```text
Reversal trading is harder than trend continuation.
```

Status:

```text
Build only after data proves useful.
```

---

## 9.8 News Spike Continuation Expert — Advanced Phase

Purpose: trade continuation after high-impact news.

Activates when:

```text
News event occurs
Spread normalizes
First spike has direction
Retest or continuation setup appears
```

This expert should be disabled until execution filters are mature.

Status:

```text
Advanced phase only.
```

---

## 9.9 Spike Fade Expert — Advanced Phase

Purpose: fade exhausted parabolic moves.

Activates when:

```text
One-candle shock appears
ATR is extreme
Long wick forms
Price fails to continue
Reversal confirmation appears
```

Risk:

```text
Can be very dangerous if trying to catch a runaway move.
```

Status:

```text
Advanced phase only.
```

---

## 9.10 Gap / Abnormal Market Expert — Safety Phase

Purpose: handle market open gaps, weekend gaps, broker feed errors, and abnormal candles.

This expert may not trade often. Its main job is to protect the system.

Activates when:

```text
Weekend gap detected
Monday open abnormality detected
Spread extreme
Bad tick detected
Broker feed spike detected
Unexpected price jump detected
```

Actions:

```text
Block trading
Reduce exposure
Close risky positions
Log abnormality
Wait for normalization
```

Status:

```text
Can be built early as a safety module.
```

---

# 10. Signal Conflict Rules

The system must define what happens when experts disagree.

Recommended v1 rule:

```text
Only one expert can be active at a time.
```

Recommended v2 rule:

```text
Multiple experts may score the market,
but only the router-selected expert may trade.
```

Example conflict:

```text
Range Expert wants to sell resistance.
Breakout Expert wants to buy resistance.
Fakeout Expert wants to wait for a failed breakout.
```

Resolution:

```text
Router decides current regime.
Only expert matching regime can trade.
```

No expert should bypass the router.

---

# 11. Risk and Money Management Plan

## 11.1 Position Sizing

Position size should be calculated from:

```text
Account equity
Risk percentage
Stop-loss distance
Symbol contract size
Broker tick value
Broker minimum lot
Broker lot step
```

Formula concept:

```text
Lot size = allowed risk money / stop-loss money per lot
```

Every lot calculation must be validated against broker constraints.

---

## 11.2 Risk Limits

Recommended initial limits:

```text
Risk per trade: 0.25% to 0.50%
Max daily loss: 1% to 2%
Max weekly loss: 3% to 5%
Max open trades: 1 to 2
Max trades per day: 4 to 6
Max trades per session: 2 to 4
Max consecutive losses before risk reduction: 3
Max consecutive losses before lockout: 5
```

---

## 11.3 Forbidden Behavior

The first version should not include:

```text
Martingale
Unlimited grid
Doubling after loss
Averaging down without hard invalidation
Moving stop loss farther away
No-stop-loss entries
Recovery mode
Hedge-and-pray logic
```

These methods can make backtests look attractive while hiding tail risk.

---

# 12. Testing and Validation Plan

MT5’s Strategy Tester allows testing and optimizing Expert Advisors before live trading, and it can run repeated optimization passes over historical data. MetaTrader also describes built-in forward testing as a way to reduce parameter-fitting risk by optimizing on one part of the data and confirming on another part.

Sources:

- MetaTrader 5 Strategy Tester help: <https://www.metatrader5.com/en/terminal/help/algotrading/testing>
- MetaTrader 5 automated trading strategy tester: <https://www.metatrader5.com/en/automated-trading/strategy-tester>

We should use that, but not rely on it blindly.

## 12.1 Test Stages

```text
Stage 1: Unit testing
Stage 2: Visual backtesting
Stage 3: Single-expert backtesting
Stage 4: Router backtesting
Stage 5: Full-system backtesting
Stage 6: Out-of-sample testing
Stage 7: Walk-forward testing
Stage 8: Stress testing
Stage 9: Demo forward testing
Stage 10: Small-size live pilot
```

---

## 12.2 Unit Tests

Test each module independently.

Examples:

```text
Does ATR calculate correctly?
Does spread filter trigger correctly?
Does session detection work correctly?
Does daily loss lock activate correctly?
Does position sizing match expected risk?
Does router block trades during news?
Does fakeout detection correctly identify sweep and reclaim?
```

---

## 12.3 Backtest Periods

The review team should define exact historical periods, but we should include:

```text
Trending gold periods
Ranging gold periods
High-volatility CPI / FOMC / NFP periods
Quiet low-volatility periods
Major geopolitical volatility periods
Strong USD periods
Weak USD periods
Friday close / Monday open periods
```

The goal is not to find one perfect backtest period. The goal is to see where the system works and where it fails.

---

## 12.4 Stress Tests

Each expert must be tested under:

```text
Normal spread
2x spread
3x spread
Normal slippage
High slippage
Delayed execution
Reduced trading hours
News blackout enabled
News blackout disabled
Different ATR settings
Different stop-loss multipliers
Different take-profit multipliers
```

---

## 12.5 Walk-Forward Validation

Process:

```text
Optimize on period A
Validate on period B
Move window forward
Optimize again
Validate again
Repeat
```

We should reject any expert that only works with one exact parameter set.

---

## 12.6 Demo Forward Test

Before live capital:

```text
Run on demo account
Same broker intended for live
Same VPS or hosting environment
Same risk settings as planned
Minimum several weeks of observation
Review logs daily
Compare real execution with backtest assumptions
```

---

# 13. Expert Approval Criteria

Before any expert is allowed into the live system, it should pass minimum standards.

Suggested criteria:

```text
Positive expectancy after spread and commission
Profit factor above minimum threshold
Drawdown within acceptable limit
No single trade explains most profit
No single day explains most profit
No single market phase explains all profit
Stable under parameter changes
Survives 2x spread test
Survives slippage stress test
Does not overtrade
Has clear invalidation
Has clear no-trade conditions
Works with router active
Works with risk manager active
```

Suggested minimum review metrics:

| Metric | Review target |
|---|---|
| Profit factor | Above 1.20 after costs |
| Max drawdown | Within predefined account tolerance |
| Average R per trade | Positive |
| Win rate | Not judged alone |
| Reward-to-risk | Must be structurally reasonable |
| Trade count | Enough to be meaningful |
| Parameter stability | Required |
| Spread sensitivity | Must survive stress test |
| Slippage sensitivity | Must survive stress test |
| Forward-test behavior | Must not materially degrade |

A high win rate alone should not be accepted as proof of quality.

---

# 14. Data Plan

## 14.1 Required Internal Data

```text
Tick data
M1 candles
M5 candles
M15 candles
H1 candles
H4 candles
D1 candles
Spread history
Order execution history
Account balance/equity history
```

## 14.2 Optional External Data

```text
Economic calendar
DXY or USD index proxy
US 10-year yield
US real yield proxy
COMEX gold futures price
Gold ETF flow data
COT data
Volatility index
```

These optional filters should not be added immediately unless the review team agrees they improve the model. Adding too many external dependencies early can make the system fragile.

---

# 15. Development Phases

## Phase 0 — Review and Final Specification

Deliverables:

```text
Final architecture
Final list of modules
Final risk rules
Final session rules
Final news rules
Final expert priority
Final testing criteria
```

Output:

```text
Approved technical specification
```

---

## Phase 1 — Core Infrastructure

Build:

```text
Master EA shell
Market Data Engine
Feature Engine
Session Engine
Logger
Basic dashboard / status panel
```

Acceptance criteria:

```text
EA runs without trading
Logs all market states
Correctly detects sessions
Correctly calculates features
No major runtime errors
```

---

## Phase 2 — Safety Infrastructure

Build:

```text
Risk Manager
Execution Guard
News Guard
Kill switch
Daily loss lock
Spread lock
Abnormal tick lock
```

Acceptance criteria:

```text
EA can block trades correctly
Risk limits trigger correctly
Spread guard works
News lock works
Kill switch works
All blocks are logged with reasons
```

---

## Phase 3 — Regime Router

Build:

```text
Trend detection
Range detection
Compression detection
Fakeout state detection
No-trade classification
Expert permission logic
```

Acceptance criteria:

```text
Router identifies regimes visually correctly
Router blocks unclear markets
Router activates only one expert in v1
Router logs active and blocked experts
```

---

## Phase 4 — First Three Experts

Build:

```text
Trend Pullback Expert
Range Mean-Reversion Expert
Fakeout / Liquidity Sweep Expert
```

Acceptance criteria:

```text
Each expert can detect setup
Each expert can return standardized signal
Each expert can explain decision
Each expert respects router
Each expert respects risk manager
Each expert respects execution guard
```

---

## Phase 5 — Position Management

Build:

```text
Fixed SL/TP
ATR-based SL option
Structure-based SL option
Break-even option
Partial close option
Trailing stop option
Time stop
Session exit
Emergency exit
```

Acceptance criteria:

```text
Every trade has hard SL
Trade management is logged
Exits are explainable
No stop is moved farther away
Emergency exit works
```

---

## Phase 6 — Backtesting and Debugging

Tasks:

```text
Run each expert independently
Run router with each expert
Run full v1 system
Run visual tests
Compare logs against chart behavior
Find false positives
Find missed valid setups
Tune regime filters
```

Acceptance criteria:

```text
No unexplained trades
No unexplained blocked trades
No major logic conflicts
No uncontrolled risk behavior
```

---

## Phase 7 — Stress Testing

Tasks:

```text
Increase spread
Increase slippage
Test news windows
Test volatile sessions
Test low-liquidity hours
Test Friday close
Test Monday open
Test VPS restart simulation
Test broker disconnect simulation
```

Acceptance criteria:

```text
Bot blocks unsafe conditions
No catastrophic behavior
Risk limits remain enforced
Execution failures are handled
Logs remain complete
```

---

## Phase 8 — Demo Forward Testing

Tasks:

```text
Run on demo
Monitor every trade
Compare actual fills with expected fills
Check spread behavior
Check slippage behavior
Check session detection
Check news filter
Check log quality
```

Acceptance criteria:

```text
No technical failures
No unexpected orders
No risk rule violations
No repeated execution errors
Forward behavior reasonably matches backtest behavior
```

---

## Phase 9 — Small Live Pilot

Only after review approval.

Rules:

```text
Minimum lot size
Reduced risk
Strict daily loss cap
No news trading initially
No weekend holding initially
Daily log review
Weekly performance review
```

Acceptance criteria:

```text
Live execution is stable
Risk controls function correctly
No unauthorized trades
No unexplained behavior
```

---

# 16. Deployment Plan

## 16.1 Environments

```text
Development environment
Backtest environment
Demo forward-test environment
Small live pilot environment
Production live environment
```

## 16.2 Version Control

Use versioning:

```text
v0.1 architecture
v0.2 core infrastructure
v0.3 risk/execution
v0.4 router
v0.5 first experts
v0.6 backtest candidate
v0.7 demo candidate
v1.0 live pilot
```

Every version should have:

```text
Change log
Parameter file
Known issues
Test result summary
Approval status
```

---

# 17. Configuration Plan

All important values should be configurable, not hardcoded.

Config groups:

```text
General settings
Risk settings
Session settings
Spread settings
News settings
Expert activation settings
Trend settings
Range settings
Fakeout settings
Exit settings
Logging settings
```

Example:

```text
EnableTrendPullbackExpert = true
EnableRangeExpert = true
EnableFakeoutExpert = true

RiskPerTrade = 0.005
MaxDailyLoss = 0.02
MaxWeeklyLoss = 0.05

MaxSpreadPoints = configurable
NewsBlackoutBeforeMinutes = 30
NewsBlackoutAfterMinutes = 30

UseBreakEven = true
UseTrailingStop = false
UsePartialClose = false
```

---

# 18. Dashboard Plan

The EA should display a simple on-chart dashboard.

Recommended dashboard fields:

```text
Symbol
Current spread
Current session
Current regime
Allowed expert
Risk mode
News state
Open trades
Daily P/L
Weekly P/L
Trade permission
Block reason
```

Example:

```text
XAUUSD
Session: London Main
Regime: Pullback in Uptrend
Allowed Expert: Trend Pullback
Risk Mode: Normal
News State: No News Risk
Spread: OK
Trade Permission: Allowed
```

Or:

```text
XAUUSD
Session: New York Pre-Data
Regime: No Trade
Allowed Expert: None
Risk Mode: Defensive
News State: Pre-News Blackout
Spread: OK
Trade Permission: Blocked
Reason: CPI in 22 minutes
```

---

# 19. Kill-Switch Plan

The kill switch should be independent from strategy logic.

Triggers:

```text
Daily loss limit hit
Weekly loss limit hit
Equity drawdown breach
Spread extreme
Slippage extreme
Too many rejected orders
Too many trades in short period
Broker connection unstable
Bad tick detected
Manual emergency stop
News lockdown active
```

Actions:

```text
Block new trades
Optionally close open trades
Log reason
Display status on dashboard
Require manual reset if severe
```

Recommended reset behavior:

```text
Soft blocks can reset automatically.
Hard blocks require manual reset.
```

Example:

```text
Spread too high → auto reset when spread normalizes.
Daily loss limit hit → no auto reset until next trading day.
Bad feed detected → manual reset required.
```

---

# 20. Review Team Checklist

## Architecture Review

```text
Is one master EA with internal modules the correct approach?
Should modules be classes, include files, or separate EAs?
Is the router too restrictive or appropriately cautious?
Should multiple experts be allowed to vote?
```

## Strategy Review

```text
Are Trend Pullback, Range, and Fakeout the right first three experts?
Should Breakout-Retest replace one of them?
Are the regime definitions objective enough to code?
Are the invalidation rules clear?
```

## Risk Review

```text
Are the proposed risk limits acceptable?
Should risk be balance-based or equity-based?
Should daily loss include floating drawdown?
Should the bot close trades when daily loss is hit?
```

## Execution Review

```text
What spread threshold is realistic for the target broker?
What slippage threshold is realistic?
Should market orders be used?
Should some experts use limit orders only?
```

## News Review

```text
Which calendar source should be used?
Should the bot trade CPI / NFP / FOMC at all?
Should open trades be closed before major events?
Should news mode exist in v1 or only as a blocker?
```

## Testing Review

```text
What historical periods should be used?
What minimum trade count is required?
What profit factor threshold is acceptable?
What drawdown is acceptable?
What stress tests are mandatory?
```

## Deployment Review

```text
How long should demo testing run?
What risk should be used in live pilot?
What monitoring is required?
Who can reset the kill switch?
```

---

# 21. Recommended MVP

For the first build, the recommended exact scope is:

```text
Master EA
Market Data Engine
Feature Engine
Session Engine
News Guard
Regime Router
Risk Manager
Execution Guard
Position Manager
Logger
Dashboard

Trend Pullback Expert
Range Mean-Reversion Expert
Fakeout / Liquidity Sweep Expert
```

Do **not** include these in the first build:

```text
Martingale
Grid
Recovery mode
News trading
Spike fading
Aggressive breakout chasing
Multi-symbol trading
Machine learning
External macro feeds
```

The first version should be boring, controlled, and explainable.

---

# 22. Main Risks Before Coding

## Risk 1: Overengineering Too Early

Building all 10 trading experts immediately will make debugging difficult.

Mitigation:

```text
Build full infrastructure first.
Add only 3 experts initially.
```

## Risk 2: Experts Conflict With Each Other

Multiple experts may produce opposite signals.

Mitigation:

```text
Router has final authority.
Only one expert active in v1.
```

## Risk 3: Good Backtest, Poor Live Execution

XAUUSD can behave differently under live spread and slippage.

Mitigation:

```text
Stress test spread and slippage.
Demo forward test.
Start live with minimum size.
```

## Risk 4: News Volatility Destroys Normal Strategy Logic

Normal technical setups may fail during CPI, NFP, and FOMC.

Mitigation:

```text
News Guard blocks first version.
News trading is not enabled until later.
```

## Risk 5: Overfitting

Too many parameters can create a curve-fit system.

Mitigation:

```text
Use broad parameters.
Require out-of-sample validation.
Require walk-forward testing.
Require parameter stability.
```

---

# 23. Final Recommendation for Review

Recommended approval order:

```text
Step 1: Approve architecture.
Step 2: Approve risk model.
Step 3: Approve regime definitions.
Step 4: Approve first 3 experts.
Step 5: Approve testing standards.
Step 6: Start coding infrastructure.
Step 7: Add first expert only after infrastructure is stable.
Step 8: Add remaining experts one by one.
```

The final build should eventually support 10 trading experts, but the first release should only trade with:

```text
Trend Pullback Expert
Range Expert
Fakeout / Liquidity Sweep Expert
```

The most important system component is not the entry signal. It is the combination of:

```text
Regime Router
Risk Manager
Execution Guard
Logger
```

That is what will make the system reviewable, testable, and safe enough to improve over time.

---

# 24. Reviewer Feedback Template

The reviewing team can use the following structure to provide feedback.

## 24.1 Architecture Feedback

```text
Approved / Needs revision
Comments:
```

## 24.2 Risk Model Feedback

```text
Approved / Needs revision
Comments:
```

## 24.3 Strategy Expert Feedback

```text
Approved / Needs revision
Comments:
```

## 24.4 Execution and Broker Feedback

```text
Approved / Needs revision
Comments:
```

## 24.5 News and Session Feedback

```text
Approved / Needs revision
Comments:
```

## 24.6 Testing and Validation Feedback

```text
Approved / Needs revision
Comments:
```

## 24.7 Required Changes Before Coding

```text
1.
2.
3.
```

## 24.8 Optional Enhancements

```text
1.
2.
3.
```

---

# 25. Open Decisions Before Coding

The following decisions should be finalized before implementation starts:

```text
1. Confirm platform: MT5, MT4, Python, cTrader, or other.
2. Confirm broker and symbol specifications for XAUUSD.
3. Confirm main trading sessions.
4. Confirm whether Asia session is tradable or level-mapping only.
5. Confirm maximum spread threshold.
6. Confirm maximum slippage threshold.
7. Confirm risk per trade.
8. Confirm daily and weekly loss limits.
9. Confirm whether open trades are closed before major news.
10. Confirm whether the bot can hold trades overnight.
11. Confirm whether the bot can hold trades over the weekend.
12. Confirm whether only one expert can trade at a time in v1.
13. Confirm first three trading experts.
14. Confirm logging format.
15. Confirm backtest data source.
16. Confirm economic calendar source.
17. Confirm demo forward-test duration.
18. Confirm live pilot risk size.
```

---

# 26. Summary

The proposed system is a **modular, regime-controlled XAUUSD Expert Advisor**.

The design is intentionally cautious:

```text
Default state: No Trade
Control modules first
Strategy modules second
Risk centralized
Execution protected
All decisions logged
First release limited to 3 experts
Expansion only after validation
```

The recommended MVP is:

```text
Master EA
Market Data Engine
Feature Engine
Session Engine
News Guard
Regime Router
Risk Manager
Execution Guard
Position Manager
Logger
Dashboard
Trend Pullback Expert
Range Mean-Reversion Expert
Fakeout / Liquidity Sweep Expert
```

The long-term version can expand to:

```text
10 trading experts
9 control/infrastructure modules
1 master EA
```

The system should be built to survive bad market conditions first and find trades second.

