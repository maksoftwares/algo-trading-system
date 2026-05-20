# Review Prompt: XAUUSD Algo Trading System Plan v0.1

Please review the attached **XAUUSD Algo Trading System Plan v0.1** as a technical, strategy, risk, and implementation design document.

The goal of this review is **not** to optimize parameters or create a final profitable strategy yet. The goal is to identify whether the proposed architecture is logical, safe, testable, modular, and realistic before coding begins.

Please review the plan critically. Assume the system will be built as an MT5/MQL5 Expert Advisor unless you believe another implementation route is better.

---

## 1. Main review objective

Please assess whether this plan is suitable as the foundation for building a modular XAUUSD algo trading system with:

- One master EA
- A regime router
- Centralized risk management
- Execution protection
- Logging and diagnostics
- Multiple independent trading experts
- Conservative default behavior where “no trade” is the default state

We are looking for specific, actionable feedback, not general comments.

---

## 2. Areas to focus on

### A. Architecture review

Please evaluate:

- Is the proposed **one master EA with internal modules** the right structure?
- Should the system be built as classes, include files, separate EAs, or another structure?
- Is the separation between Router, Risk Manager, Execution Guard, Position Manager, Logger, and Experts clear?
- Are there any missing infrastructure modules?
- Is the architecture too complex for v1?
- Is anything overengineered?
- Is anything under-specified?
- Should the system allow only one active expert at a time in v1, or should multiple experts be allowed to vote?

Feedback requested:

```text
Architecture verdict:
- Approved / Needs changes / Not recommended

Key concerns:
1.
2.
3.

Recommended changes:
1.
2.
3.
```

---

### B. Regime classification review

Please evaluate whether the proposed market regimes are complete and codable.

Key regimes include:

- Trend up/down
- Pullback in trend
- Range
- Compression
- Breakout
- Breakout retest
- Fakeout/liquidity sweep
- Reversal
- News spike
- Spike exhaustion
- Gap/abnormal market
- No-trade state

Please assess:

- Are these regimes enough for XAUUSD?
- Are any regimes missing?
- Are any regimes unnecessary?
- Are the definitions objective enough to code?
- Which regimes are most important for v1?
- Which regimes should be delayed until later?

Feedback requested:

```text
Regime review:
- Complete / Needs additions / Too complex

Missing regimes:
1.
2.
3.

Regimes to remove or delay:
1.
2.
3.

Regimes that need clearer definitions:
1.
2.
3.
```

---

### C. First expert selection review

The proposed first three trading experts are:

1. Trend Pullback Expert
2. Range Mean-Reversion Expert
3. Fakeout / Liquidity Sweep Expert

Please evaluate:

- Are these the right first three experts to build?
- Should Breakout-Retest replace one of them?
- Should Trend Continuation be included earlier?
- Should Range trading be delayed because of breakout risk?
- Is Fakeout/Liquidity Sweep too subjective for v1?
- Which expert should be coded first?

Feedback requested:

```text
First 3 experts verdict:
- Approved / Modify / Replace

Recommended first 3 experts:
1.
2.
3.

Recommended build order:
1.
2.
3.

Reasoning:
```

---

### D. Risk management review

Please review the proposed risk model.

Current suggested assumptions:

- Risk per trade: 0.25% to 0.50%
- Max daily loss: 1% to 2%
- Max weekly loss: 3% to 5%
- Max open XAUUSD trades: 1 to 2
- Max trades per session: 2 to 4
- Risk reduction after losing streak
- Kill switch for daily/weekly loss, spread, slippage, news, bad ticks, abnormal execution

Please assess:

- Are these limits too conservative, too aggressive, or appropriate?
- Should daily loss be based on balance, equity, or realized P/L?
- Should floating drawdown count toward daily loss?
- Should the bot close open trades after daily loss is hit?
- Should risk reduce after each loss or only after a losing streak?
- Should the strategy have different risk settings per expert?

Feedback requested:

```text
Risk model verdict:
- Approved / Needs changes / Too risky

Recommended risk per trade:
Recommended max daily loss:
Recommended max weekly loss:
Recommended max open trades:
Recommended max trades per day:

Must-change risk rules:
1.
2.
3.

Optional risk improvements:
1.
2.
3.
```

---

### E. Execution and broker realism review

Please evaluate whether the execution protection is realistic for XAUUSD.

Focus on:

- Spread filters
- Slippage filters
- Minimum stop distance
- Freeze level
- Margin checks
- Order rejection handling
- Broker feed anomalies
- Rollover spread expansion
- News execution risk
- Friday close / Monday open behavior

Please answer:

- What spread threshold is realistic for XAUUSD?
- Should spread limits be fixed or dynamic?
- Should market orders be allowed?
- Should limit orders be preferred for certain experts?
- What slippage limit should be used?
- What execution conditions should immediately block trading?

Feedback requested:

```text
Execution model verdict:
- Approved / Needs changes / Unrealistic

Recommended max spread rule:
Recommended max slippage rule:
Market orders allowed?
Limit orders required for any expert?

Execution risks not covered:
1.
2.
3.
```

---

### F. News and calendar review

The plan suggests blocking or reducing risk around high-impact USD news, especially:

- CPI
- PPI
- NFP
- FOMC
- Fed speeches
- PCE
- GDP
- ISM
- Retail sales
- Unemployment data

Please evaluate:

- Should v1 block news completely?
- Should v1 allow news trading?
- How long should the pre-news blackout be?
- How long should the post-news cooldown be?
- Should open trades be closed before CPI/NFP/FOMC?
- Which economic calendar source should be used?
- Should news filtering be automatic or manual in v1?

Feedback requested:

```text
News handling verdict:
- Block all high-impact news / Allow reduced-risk trading / Allow news expert

Recommended pre-news blackout:
Recommended post-news cooldown:
Should open trades be closed before major news?
Recommended calendar source:

News risks not covered:
1.
2.
3.
```

---

### G. Position management review

Please review the proposed trade management logic.

The plan includes:

- Hard stop loss on every trade
- Fixed or ATR-based stop
- Structure-based stop
- Take profit
- Break-even
- Partial close
- Trailing stop
- Time stop
- Session exit
- Emergency exit

Please evaluate:

- Should exits be centralized or expert-specific?
- Should each expert have unique exit rules?
- Should break-even be used?
- Should partial close be used?
- Should trailing stop be ATR-based, structure-based, or disabled in v1?
- Should trades be held overnight?
- Should trades be held over weekends?

Feedback requested:

```text
Position management verdict:
- Approved / Needs changes / Too complex

Recommended v1 exit model:
Should use break-even?
Should use partial close?
Should use trailing stop?
Should hold overnight?
Should hold weekends?

Exit risks not covered:
1.
2.
3.
```

---

### H. Testing and validation review

Please evaluate the proposed testing process:

- Unit testing
- Visual backtesting
- Single-expert backtesting
- Router backtesting
- Full-system backtesting
- Out-of-sample testing
- Walk-forward testing
- Spread/slippage stress testing
- Demo forward testing
- Small live pilot

Please assess:

- Is this testing process sufficient?
- What periods of XAUUSD history should be included?
- What minimum trade count is needed before judging an expert?
- What profit factor is acceptable after costs?
- What drawdown limit is acceptable?
- How should overfitting be detected?
- How long should demo forward testing run?

Feedback requested:

```text
Testing plan verdict:
- Approved / Needs additions / Insufficient

Required historical test periods:
1.
2.
3.

Minimum acceptable metrics:
Profit factor:
Max drawdown:
Minimum trade count:
Minimum forward-test duration:

Stress tests to add:
1.
2.
3.
```

---

### I. Logging and diagnostics review

Please evaluate whether the logging plan is sufficient.

The system should log:

- Time
- Symbol
- Session
- Spread
- ATR
- ADX
- Regime
- Allowed expert
- Blocked experts
- Entry reason
- No-trade reason
- Risk mode
- Lot size
- SL/TP
- Reward-to-risk
- Order result
- Slippage
- Exit reason
- P/L
- Drawdown

Please assess:

- Are these logs enough for debugging?
- Should every decision be logged or only trade-related events?
- Should logs be CSV, database, or both?
- Should the bot mark decisions on the chart?
- What diagnostics are missing?

Feedback requested:

```text
Logging verdict:
- Approved / Needs changes / Insufficient

Missing log fields:
1.
2.
3.

Recommended log format:
Recommended dashboard fields:
```

---

### J. Missing risks and failure modes

Please identify anything the plan does not handle well.

Focus especially on:

- Broker manipulation or abnormal spreads
- Bad tick data
- VPS disconnection
- Broker server time mismatch
- Economic calendar failure
- Parameter overfitting
- Too many filters causing no trades
- Experts conflicting with each other
- Strong trend days where range/fakeout logic fails
- Low-liquidity holiday behavior
- Weekend gaps
- News slippage
- Strategy degradation over time

Feedback requested:

```text
Missing failure modes:
1.
2.
3.
4.
5.

Highest-risk part of the plan:
Recommended mitigation:
```

---

## 3. Specific questions we want answered

Please answer these directly:

1. Should we proceed with the proposed master EA architecture?
2. Should v1 include only 3 trading experts?
3. Are Trend Pullback, Range, and Fakeout the correct first experts?
4. Should Breakout-Retest be included earlier?
5. Should news trading be completely disabled in v1?
6. Are the proposed risk limits acceptable?
7. Is the “only one active expert at a time” rule correct for v1?
8. Is the regime router too restrictive?
9. Are the testing standards strong enough?
10. What should be changed before coding starts?

---

## 4. Feedback format requested

Please return feedback in this format:

```text
Overall verdict:
- Approved to proceed
- Approved with changes
- Needs major revision
- Not recommended

Top 5 must-change items:
1.
2.
3.
4.
5.

Top 5 nice-to-have improvements:
1.
2.
3.
4.
5.

Modules approved as-is:
1.
2.
3.

Modules needing revision:
1.
2.
3.

Modules to delay:
1.
2.
3.

Missing modules:
1.
2.
3.

Recommended MVP scope:
1.
2.
3.
4.
5.

Recommended first coding milestone:
1.
2.
3.

Main risks:
1.
2.
3.

Final recommendation:
```

---

## 5. Review standard

Please avoid vague feedback like:

- “Looks good”
- “Needs better risk management”
- “Add AI”
- “Improve entries”
- “Use better indicators”

Instead, please provide specific feedback such as:

- “The Range Expert should be delayed because range classification is not objective enough yet.”
- “Daily loss should be equity-based, not balance-based.”
- “The router should allow expert scoring but only execute the highest-confidence expert.”
- “News trading should be disabled until execution slippage is measured on demo.”
- “Breakout-Retest should replace Range Expert in v1 because it is easier to define objectively.”
- “The plan needs a broker-time synchronization module.”
- “The logger should include reason codes for every blocked trade.”

The purpose of this review is to help us finalize a coding-ready specification.

---

# Short Review Prompt Version

Please review the attached XAUUSD Algo Trading System Plan v0.1.

Focus on whether the proposed architecture is safe, modular, testable, and realistic before coding begins. We are especially looking for feedback on:

1. Whether one master EA with internal modules is the right architecture
2. Whether the Regime Router, Risk Manager, Execution Guard, Position Manager, and Logger are properly separated
3. Whether v1 should include only three trading experts
4. Whether Trend Pullback, Range, and Fakeout/Liquidity Sweep are the right first experts
5. Whether Breakout-Retest should be included earlier
6. Whether news trading should be blocked completely in v1
7. Whether the proposed risk limits are appropriate
8. Whether the execution/spread/slippage protections are realistic for XAUUSD
9. Whether the testing and validation plan is strong enough
10. What must be changed before coding starts

Please provide feedback in this format:

- Overall verdict: Approved / Approved with changes / Needs major revision / Not recommended
- Top 5 must-change items
- Top 5 nice-to-have improvements
- Modules approved as-is
- Modules needing revision
- Modules to delay
- Missing modules
- Recommended MVP scope
- Recommended first coding milestone
- Main risks
- Final recommendation

Please avoid generic comments. We need specific, actionable feedback that can be converted into a final coding specification.
