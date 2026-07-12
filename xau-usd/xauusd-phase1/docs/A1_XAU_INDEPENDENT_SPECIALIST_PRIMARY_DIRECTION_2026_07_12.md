# A1 XAUUSD Independent-Specialist Primary Direction

**Repository:** `maksoftwares/algo-trading-system`  
**Branch:** `codex/xau-router-entry-hold-audit`  
**Reviewed HEAD:** `c9873c2693872f41ce17c1ee31c35a8a4fc36fcb`  
**Reviewed tree:** `211bba5389e25ba5779dd39663366ac6a871f31f`  
**Direction date:** `2026-07-12`  
**Program mode:** repository-only, offline, exact-MT5 Strategy Tester, and shadow research  
**Deployment status:** `NO_GO_RESEARCH_ONLY`  
**Broker action:** prohibited  
**Historical boundary:** every observation through `2026-06-30` is `DEVELOPMENT_DATA`

---

# 1. Executive decision

```text
CURRENT R1/R2/R3/R4 SYSTEM:
  NOT DEPLOYABLE, INCLUDING DEMO BROKER ACTION

PRIMARY INDEPENDENT-SPECIALIST LANE:
  R6_H4_DISTRIBUTION_BREAK_FAILED_RECLAIM_SHORT_V1

R6 ECONOMIC MANDATE:
  PRE-DOWNTREND DISTRIBUTION / FAILED-RECLAIM TRANSITION SHORT

R6 NP1:
  CONTINUES AS A MANDATORY BOUNDED PREREQUISITE INSIDE THE PRIMARY LANE

SEPARATE PARALLEL SPECIALIST LANE:
  NOT AUTHORIZED

R1 + R2:
  FROZEN RESEARCH CONTROL / COMPARISON ONLY

R3:
  EXCLUDED FROM PORTFOLIO; NOT INDEPENDENT

R4:
  NO SURVIVOR; NO ACTIVITY FILLER

OLD ROUTER ENTRY/HOLD AUDIT:
  DEFERRED CONTROL DIAGNOSTIC
  REQUIRED BEFORE ANY FUTURE USE OF THE OLD R1+R2 CONTROL
  NOT ON THE CRITICAL PATH FOR R6 STANDALONE RESEARCH

SINGLE NEXT REPOSITORY ACTION:
  COMMIT THE OWNER-DIRECTION SUPERSESSION PACKET DEFINED IN SECTION 14
```

The project will not open a second independent-family search while R6 is unresolved. Doing so would create another researcher degree of freedom and invite selection of whichever family looks best on the same development history.

R6 is not a hedge overlay and is not allowed to rescue the unsafe H4 source. It must prove standalone alpha first, then prove independent time-path contribution under sealed comparison.

---

# 2. Why the current system remains NO-GO

The current historical control is useful evidence, but it is not a qualified portfolio:

```text
R1+R2 control:
  678 trades
  WR 51.03%
  PF 2.7182
  net +$9,640.05
  recent-three-month net +$764.92
  maximum closed DD $889.69
```

It remains inadmissible for deployment because:

1. It is component-exact/offline recomposition rather than one integrated MT5 portfolio with native floating equity.
2. The retained sources include forbidden historical P/L/session selection and source-local containment.
3. Legacy native-position attribution required repair.
4. The original H4 source produced roughly `39%–41%` native relative floating-equity drawdown.
5. R3 duplicates R1 and failed the portfolio DD gate.
6. R4 has no surviving chop source.
7. No existing source set establishes three standalone-good, independent specialists.
8. All inspected history is development evidence.
9. No forward-shadow exam or broker-action authorization exists.

The owner's higher-level decision supersedes the prior sequencing instruction that the router-path audit must finish before any new specialist begins. It does **not** weaken any safety, evidence, or historical-data boundary.

---

# 3. Mechanism comparison

## 3.1 H1/H4 objective range-box specialist

**Economic idea:** fade objectively verified H1/H4 range extremes or trade a structural false break back into the range.

**Advantages**

```text
owns a missing range/chop state;
directionally different from R1 and R3;
potentially active when trend sources are silent;
may have smaller stop geometry than H4.
```

**Disadvantages**

```text
four simpler R4 fade/reclaim families already failed;
gold ranges often terminate in violent expansion;
a genuine 2R target may not fit inside many boxes;
the result may become another threshold-heavy range classifier;
does not directly cover the pre-downtrend gap between R1 and R2;
would require a new hypothesis, lock, detector, and census from zero.
```

**Decision**

```text
NOT SELECTED NOW
BACKLOG ONLY AS IS2 IF R6 CLOSES
```

No H1/H4 range-box rule may be authored in parallel with R6.

---

## 3.2 R6 market-only distribution-break / failed-reclaim short

**Economic idea:** after an objective completed-H4 upward impulse and six-H4 distribution box, the first immediate H4 breakdown and first failed H1 reclaim identify a supply-led transition before an established R2 downtrend exists.

**Advantages**

```text
already mechanically and causally locked;
market-only and outcome-blind;
uses completed H4/H1 structure;
owns the temporal gap after mature uptrend participation but before strict R2;
short direction is distinct from R1/R3;
structurally different from the failed R5 q55 impulse/retest family;
contract feasibility is tested before P/L;
incidence and concentration are tested before P/L;
can begin offline while markets are closed;
does not require a live wait to produce development evidence.
```

**Risks**

```text
may be too sparse;
may not fit the $1,000 / 0.01-lot risk budget;
may be a plausible pattern without positive expectancy;
native Router parity evidence is currently missing;
may fail to overlap enough existing long exposure to add time-path value.
```

**Decision**

```text
SELECTED PRIMARY LANE
```

---

## 3.3 Generic contemporaneous bearish alpha built to overlap H4 exposure

The failed R5 q55 probe already showed that availability, temporal coverage, and low correlation are not enough. It touched most H4 exposure episodes and was nearly uncorrelated, yet remained materially loss-making.

A new “bearish while H4 is exposed” mechanism without an independent market thesis would be another fitted hedge search.

**Decision**

```text
DO NOT AUTHOR A GENERIC H4-HEDGE SIGNAL
R6 MAY LATER BE TESTED FOR COMPLEMENTARITY
BUT H4 STATE/P&L MAY NEVER ENTER ITS SIGNAL
```

---

## 3.4 Compression expansion or another long specialist

The R3 router audit showed that most of the strong “compression” result was actually uptrend long expansion, and 110 of 139 strict-R1 R3 trades overlapped the existing R1 box source.

**Decision**

```text
NOT INDEPENDENT
NO NEW R1/R3 LONG-EXPANSION SIBLING
```

---

## 3.5 Intermarket/macro specialist

A DXY, real-yield, futures-basis, or cross-asset specialist could be economically independent. The present repository does not yet contain a locked, causally aligned, multi-source data contract suitable for promoting such a source.

**Decision**

```text
POTENTIALLY VALID FUTURE FAMILY
NOT THE NEXT LANE
```

Starting it now would add data-source, timestamp, contract, and survivorship risks before the existing market-only R6 path is resolved.

---

# 4. Selected specialist and regime mandate

## Specialist ID

```text
R6_H4_DISTRIBUTION_BREAK_FAILED_RECLAIM_SHORT_V1
```

## Economic regime

```text
R6_DISTRIBUTION_TRANSITION
```

This is a structural transition state, not merely a Router label.

Required context:

```text
EA Router V1 state at decision:
  UPTREND or CHOP

Structural state:
  completed-H4 upward impulse
  six completed-H4 distribution box
  immediate first bearish H4 breakdown
  first H1 reclaim attempt fails
```

Blocked contexts:

```text
SHOCK
COMPRESSION
DOWNTREND
UNKNOWN
```

R6 must not trade established downtrend continuation. That remains R2's mandate.

R6 must not trade a generic range fade. That remains an unproven future R4/IS2 concept.

---

# 5. Independence thesis

## Versus R1

R1 owns bullish continuation in an established broad uptrend.

R6 owns the first structurally confirmed bearish transition **while the slow broad state can still be UPTREND or CHOP**.

```text
R1:
  continuation after bullish participation

R6:
  distribution failure and bearish reclaim rejection
```

Their entry directions and market stages are different.

## Versus R2

R2 waits for established bearish/downtrend participation.

R6 acts before that state, during distribution-to-downtrend transition.

```text
R6:
  transition entry

R2:
  established downside continuation/pullback entry
```

R6 cannot be a renamed R2 continuation.

## Versus R3

R3 is another uptrend long-expansion expression and substantially overlaps R1.

R6 is short-only and structure-reversal oriented. It cannot inherit an R3 signal, box, priority, or source identity.

## Versus R4

R4 attempted simple chop and reclaim families. R6 is not a generic chop fade. It requires an upward impulse, a multi-H4 distribution structure, an immediate breakdown, and a failed H1 reclaim.

## Outcome-leakage protection

The R6 rule may not access:

```text
H4 strategy positions
H4 entries/exits
H4 holding intervals
H4 P/L
H4 equity or drawdown
H4 losing dates
R1/R2/R3/R4 result ledgers
portfolio P/L
MFE/MAE
future post-entry prices
```

Complementarity evidence is opened only after standalone PASS.

---

# 6. Primary phase: outcome-blind incidence and contract feasibility

Historical P/L is not the next experiment.

The next specialist phase remains:

```text
market-only native Router/contract parity
then outcome-blind R6 opportunity census
```

The current R6 preregistration, rule lock, row schema, and status precedence remain authoritative.

## Required census questions

```text
Does the market structure occur often enough?
Does it occur in both five-year halves?
Is it temporally concentrated?
Can the first causal entry tick be reconstructed?
Can Capital.com 0.01 lot fit the USD 2.50 risk budget?
Can all rows be produced without outcome fields?
Does Python match the exact native Router and contract semantics?
```

## Locked census gates

```text
Raw causal opportunities:
  >= 120 decade total
  >= 40 early half
  >= 40 late half
  >= 8 of 10 July-June buckets with >=5 opportunities
  no bucket >25% of raw opportunities
  best contiguous 24 months <=40% of raw opportunities

USD 10,000 reference at $25 risk:
  >=100 feasible
  >=35 early
  >=35 late
  >=8 July-June buckets

USD 1,000 deployment at $2.50 risk:
  >=100 feasible
  >=80% of raw opportunities
  >=35 early
  >=35 late
  >=8 July-June buckets
```

Exactly one census status:

```text
R6_CENSUS_EVIDENCE_INVALID
R6_CENSUS_INSUFFICIENT_INCIDENCE
R6_CENSUS_REFERENCE_RISK_UNDERPOWERED
R6_SMALL_ACCOUNT_CONTRACT_INFEASIBLE
R6_CENSUS_PASS
```

Any failed gate closes R6 V1. No neighboring threshold may be tested.

---

# 7. Future execution envelope if and only if the census passes

This section precommits the only allowed standalone execution shape. It does not authorize a P/L run now.

```text
Direction:
  SHORT only

Entry:
  first eligible broker-session-open tick after the first completed H1
  failed-reclaim bar, exactly as defined by the census lock

Initial stop:
  max(reclaim_bar_high, frozen_box_low) + 0.25 * H1 ATR14
  normalized upward to symbol tick
  one additional conservative tick for risk calculation

Target:
  fixed 2.00R

Position count:
  one R6 position at a time
  one signal per box
  one signal per episode

Risk:
  0.25% of fixed initial reference equity
  no compounding
  block if minimum lot exceeds risk cap

Management:
  no break-even
  no partial close
  no trailing stop
  no source-local daily loss stop
  no session mask
  no month/day/hour exclusion
  no H4-aware hedge logic

Exit:
  original SL or fixed 2R TP only
```

If an overnight-financing model is required, it is applied as cost evidence; it does not alter the exit.

Any different exit or management rule is a different hypothesis and is not authorized as an R6 sibling.

---

# 8. Historical, exam, and forward boundaries

## Development period

```text
Warm-up:
  starts no later than 2015-06-01 broker time

Development evidence:
  2016-07-01T00:00:00
  through
  2026-07-01T00:00:00 exclusive
```

Every result in that interval is development evidence.

## Untouched historical exam

```text
NONE
```

No historical subset through `2026-06-30` may be relabeled as untouched.

A second broker/feed replay may be used as robustness evidence, but not called an untouched market exam.

## Forward period

Forward shadow begins only on the first market tick after all are frozen and hashed:

```text
standalone rule
source code
EX5
Router identity
contract identity
risk rule
cost rule
report schema
forward start timestamp
pass/fail gates
```

Minimum forward evidence:

```text
the longer of:
  12 calendar months
  or 30 mature R6 trades

plus:
  >=3 independent R6 distribution-transition episodes
  zero wrong-router executions
  zero unresolved order/timestamp discrepancies
  measured spread/slippage/funding evidence
```

If incidence is too low:

```text
CONTINUE_EVIDENCE
```

No rule may change during the forward exam. A change starts a new version and a new future exam.

Forward evidence remains shadow-only until a separate integrated portfolio and explicit owner authorization exist.

---

# 9. Maximum variants and anti-overfit rules

## Variant budget

```text
Census variants:
  1

Standalone exact-MT5 variants:
  1

Management variants:
  0

Session/hour/day/month masks:
  0

Threshold neighbors:
  0
```

No:

```text
q50/q60/q65 sibling
five-bar/seven-bar box sibling
second-reclaim sibling
alternate body/close threshold
different Router state pair
loss-window exclusion
H4 drawdown governor
portfolio rescue
lower RR
```

If the census or standalone test fails, R6 V1 closes.

A later independent family requires:

```text
new economic mechanism
new owner direction
new preregistration
new future exam
```

---

# 10. Standalone exact-MT5 admission gates

These gates apply only after `R6_CENSUS_PASS` and a separately reviewed standalone preregistration.

## Sample and frequency

```text
Ten-year exact trades:           >=100
Early-half exact trades:         >=35
Late-half exact trades:          >=35
July-June buckets with trades:   >=8 of 10
```

## Win/payoff quality

```text
Point win rate:                  >=42.00%
Wilson 95% lower win-rate bound: >33.33%
Realized average win/loss:       >=1.80
```

`42%` is a hard floor, not the design target. The preferred shape is `45%–50%+` with near-2R realized payoff.

## Cost-adjusted profitability

Report:

```text
NATIVE:
  real-tick spread + native commission/swap/fee

EXPECTED:
  NATIVE - 0.05R per trade
  plus measured expected financing

HARD STRESS:
  NATIVE - 0.10R per trade
  plus measured P95 financing
```

Pass gates:

```text
Native PF:                       >=1.50
Expected-cost PF:                >=1.35
Hard-stress PF:                  >=1.20
Bootstrap 5th-percentile
hard-stress PF:                  >1.00

Hard-stress net:                 >0
Hard-stress expectancy:          >=+0.10R per trade
Bootstrap 5th-percentile
hard-stress expectancy:          >0R
```

Unknown overnight financing is a NO-GO, not zero cost.

## Drawdown and risk

```text
Native maximum relative
floating-equity DD:              <=8.00%

Maximum source open initial risk:
                                  <=0.25% of fixed initial equity

Compounding:                      OFF
Minimum-lot excess risk:          BLOCK
```

## Concentration

All must pass:

```text
largest winning trade share:      <=12.50% of net
top-five winner share:            <=45.00% of net
top-10 winners removed net:       >0
top-three winning days removed:   >0
best July-June bucket share:      <=35.00%
best contiguous 24-month share:   <=50.00%
```

## Time stability

```text
Hard-stress early-half net:       >0
Hard-stress late-half net:        >0
Positive July-June buckets:       >=6 of 10
Three consecutive negative
July-June buckets:                forbidden
```

## Evidence quality

```text
native position/deal reconciliation exact
0 unresolved order failures
0 management failures
compile 0 errors / 0 warnings
all manifests exact
all effective inputs exact
Python/native signal parity 100%
Python/native trade parity >=99.9%
```

Any failed standalone gate means:

```text
R6_STANDALONE_NO_GO
```

No portfolio test may hide or rescue it.

---

# 11. Independence and portfolio-contribution gates

These gates are evaluated only after standalone PASS. Existing specialist ledgers remain sealed until then.

## 11.1 Same-opportunity overlap

Against existing short sources:

```text
same symbol
same SHORT direction
same completed H1 decision bar
entry level within 0.25 H1 ATR
```

Maximum overlap with R2:

```text
<=20% of R6 trades
```

R1/R3 are opposite-direction sources, so temporal coincidence is measured separately rather than called duplicate execution.

## 11.2 Return correlation

Using zero-filled fixed-risk daily and weekly R series:

```text
absolute daily Pearson correlation:
  R6 vs R1 <=0.30
  R6 vs R3 <=0.30
  R6 vs R2 <=0.50

absolute weekly Pearson correlation:
  R6 vs every existing source <=0.50
```

Report Spearman correlation as a diagnostic, not a substitute.

## 11.3 Regime ownership

```text
100% of R6 entries:
  Router UPTREND or CHOP
  plus the full R6 distribution-transition structure

0 entries:
  SHOCK
  COMPRESSION
  DOWNTREND
  UNKNOWN

Independent transition episodes:
  >=3 early half
  >=3 late half
```

## 11.4 Temporal coverage

Without using H4 loss outcomes to define the rule, after standalone PASS measure against **all** frozen R1/H4 exposure episodes:

```text
R6 position interval intersects:
  >=25% of all R1/H4 exposure episodes
```

This is a complementarity test, not a signal input.

Failure means R6 may remain a standalone research clue but does not satisfy the owner's missing-time-path mandate.

## 11.5 Drawdown-window independence

Define the five largest fixed-risk drawdown windows independently for each source.

Require:

```text
Jaccard overlap of R6 drawdown days
with R1 drawdown days:             <=0.50

Jaccard overlap of R6 drawdown days
with R3 drawdown days:             <=0.50
```

Also report R6 stress P/L across the five already-frozen R1/H4 drawdown windows, but do not use those values to modify R6.

## 11.6 Integrated gate

Only after standalone and independence PASS may one integrated exact-MT5 portfolio test be proposed.

The later integrated portfolio must:

```text
use one Router and one family mutex;
use common fixed risk;
measure native tick-level floating equity;
keep maximum relative equity DD <=10%;
show positive marginal stressed expectancy from R6;
and not rely on offline ledger addition for promotion.
```

The current historical `+$8,000` aspiration is a portfolio objective, not an R6 standalone gate.

---

# 12. Isolated Strategy Tester authorization

## Authorized while markets are closed

```text
market-only Router/contract oracle runs;
historical outcome-blind census preparation;
isolated exact-MT5 standalone testing after separate authorization;
compile and deterministic replay tests.
```

Historical Strategy Tester work does not require the live market to be open.

## Required isolation

```text
dedicated tester terminal
fixed account/server metadata
Strategy Tester only
no chart/profile attach
no production or demo runtime profile
no preset arming outside tester
no open/pending broker positions
zero trade/deal oracle contract where specified
```

`InpAllowDemoTrading=true` inside a tester configuration is not runtime authorization.

## Not authorized

```text
demo chart attachment
live chart attachment
broker order
position modification
account-risk change
runtime profile mutation
EA arming
```

---

# 13. Reconciliation with R6 NP1 and the old program

## R6 NP1

The previously authorized sequence remains valid:

```text
NP1-A:
  acquisition locks only

NP1-B:
  market-only oracle/probe implementation and tests

NP1-C:
  exact zero-action native evidence only
```

NP1 is now formally the first prerequisite inside the primary independent-specialist lane.

It is not a competing project.

## C2R5 and C3

After valid NP1 evidence:

```text
C2R5:
  replace prohibited fixture dependencies;
  close exact Router/contract parity and input attestation.

C3A:
  freeze exact historical bars/ticks/session/ownership inputs,
  command, hashes, schemas, and prefix cutoffs.

C3:
  produce the real outcome-blind census with no code change.
```

## Old router entry/hold audit

The old audit remains useful for diagnosing the frozen R1+R2 control.

It is no longer the next primary task.

Status:

```text
DEFERRED_CONTROL_DIAGNOSTIC
```

It must finish before the old R1+R2 control can ever enter an integrated portfolio, but it does not block R6 standalone discovery.

## No contradictory second lane

The following remain unauthorized while R6 is active:

```text
new H1/H4 range-box family
new R4 family
new R1/R3 long source
new R2 sibling
intermarket specialist
ML signal selector
```

If R6 closes, an owner/reviewer packet may select exactly one IS2 mechanism. No automatic fallback is permitted.

---

# 14. Exact first commit

## Commit ID

```text
IS1-A_OWNER_DIRECTION_SUPERSESSION_AND_R6_PRIMARY_LANE_LOCK
```

## Exact files allowed

Add:

```text
xau-usd/xauusd-phase1/docs/
  A1_XAU_INDEPENDENT_SPECIALIST_PRIMARY_DIRECTION_2026_07_12.md

xau-usd/xauusd-phase1/outputs/manifests/
  A1_XAU_INDEPENDENT_SPECIALIST_PRIMARY_DIRECTION_LOCK_V1.json

xau-usd/xauusd-phase1/tests/
  test_a1_xau_independent_specialist_primary_direction.py
```

Modify:

```text
status_summary.md
status_summary.json
status.html
agent.md

xau-usd/xauusd-phase1/tests/
  test_a1_xau_governance_status.py
```

No other file may change.

## Lock manifest contents

Hash and byte-size lock:

```text
new primary-direction document
existing R6 census preregistration
existing R6 rule lock
existing R6 row schema
existing R6 C1 lock manifest
current R6 builder
current R6 validator
controlling C2R4 review SHA:
  d7824eca268f3fb2443406d929e7565723e79ec4bafef6b501c3eab49bb4fb7b
native-parity acquisition direction SHA:
  a2d10661e58e95c516291b7e1d9b07b8b59904b94cff8474e28b16d569f0c1ca
```

The manifest must state:

```text
primary_lane = R6
next_action = NP1-A
demo_authorized = false
live_authorized = false
broker_action_authorized = false
separate_parallel_specialist_authorized = false
historical_data_status = DEVELOPMENT_DATA
```

## Required tests

The new/updated tests must assert:

```text
authoritative status = NO_GO_RESEARCH_ONLY
R6 = PRIMARY_INDEPENDENT_SPECIALIST_LANE
NP1-A = NEXT_ACTION
R1+R2 = RESEARCH_CONTROL_ONLY
R3 = EXCLUDED
R4 = NO_SURVIVOR
router entry/hold audit = DEFERRED_CONTROL_DIAGNOSTIC
parallel specialist lane = false
all history through 2026-06-30 = DEVELOPMENT_DATA
demo/live/broker authorization = false
direction and dependency hashes verify
status_summary.md/json/status.html/agent.md agree
no runtime or EA source changed
```

## Commit boundary

This is governance and lock alignment only.

It contains:

```text
no detector change
no Router change
no MT5 source
no test result
no census
no P/L
no broker action
```

Stop after committing and running the governance tests. Return the exact commit and tree for review.

---

# 15. Subsequent phase order

After `IS1-A` passes review:

```text
1. NP1-A market-only native-parity acquisition locks
2. NP1-B oracle/probe code and tests
3. NP1-C exact zero-action native evidence
4. C2R5 parity/input-attestation closure
5. C3A exact historical input lock
6. C3 outcome-blind incidence/contract census
7. If C3 PASS: standalone preregistration
8. one exact-MT5 standalone result
9. if standalone PASS: sealed independence audit
10. if independence PASS: forward-shadow lock
```

One falsifiable step per commit.

---

# 16. Hard NO-GO conditions

Any one stops R6 V1:

```text
market-only native parity unavailable or invalid;
prohibited H4/portfolio dependency;
Router source-lineage mismatch;
future data or bar-0 leakage;
prefix-invariance failure;
census incidence failure;
USD 1,000 / 0.01 contract-feasibility failure;
standalone trade count <100;
standalone profitability/stress gate failure;
native relative equity DD >8%;
concentration failure;
early/late stability failure;
same-opportunity overlap >20% with R2;
correlation gate failure;
insufficient temporal exposure coverage;
drawdown-window overlap failure;
unknown financing cost;
order/position reconciliation defect;
any historical threshold repair;
any parallel variant;
any attempt to use portfolio results to rescue standalone failure.
```

Valid terminal outcomes include:

```text
R6_CENSUS_NO_GO
R6_STANDALONE_NO_GO
R6_INDEPENDENCE_NO_GO
R6_SMALL_ACCOUNT_CONTRACT_INFEASIBLE
CONTINUE_EVIDENCE
```

---

# 17. Deployment statement

No historical result generated under this direction is deployment authorization.

Even a full historical PASS would authorize only:

```text
a locked forward-shadow exam
```

Demo broker action would require a later, separate packet proving:

```text
standalone forward survival;
integrated exact-MT5 portfolio behavior;
native floating-equity DD <=10%;
tested mutex and containment;
zero-exposure baseline;
exact hash approval;
independent review;
explicit owner authorization.
```

Until then:

```text
NO DEMO ATTACH
NO LIVE ATTACH
NO BROKER ACTION
```

---

# 18. Single next action

```text
Create IS1-A_OWNER_DIRECTION_SUPERSESSION_AND_R6_PRIMARY_LANE_LOCK
using only the files in Section 14.

Do not create NP1-A in the same commit.
Do not modify R6 code.
Do not generate a census.
Do not run strategy P/L.
Do not start a second specialist family.
```
