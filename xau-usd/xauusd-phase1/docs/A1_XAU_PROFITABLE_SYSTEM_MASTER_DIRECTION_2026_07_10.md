# CODEX MASTER DIRECTION
## Build an Evidence-Valid XAUUSD Algorithmic Trading Business

**Repository:** `maksoftwares/algo-trading-system`
**Starting point:** latest `main` after commit `006824cde421ea61a0bcdb074804f9ccf95c17a9`
**Program scope:** A1 XAUUSD research and eventual controlled deployment
**Immediate mode:** Repository-only, exact-MT5, offline, and shadow-only
**Broker action:** Prohibited until a later, separately reviewed authorization packet
**Primary business goal:** Build an automated system capable of producing positive net returns over rolling multi-month periods with controlled equity drawdown, so that accumulated profits may eventually support disciplined withdrawals.

---

# 0. Codex operating instruction

Read this entire document before changing any file.

This document is the governing direction for the next stage of the XAUUSD project.

The objective is **not**:

```text
make every month profitable;
force one trade every day;
make the backtest reach a desired WR/PF/net number;
repair every losing historical month;
or keep adding filters until the scorecard passes.
```

The objective is:

> Build a small, regime-owned, cost-adjusted, exact-MT5-verified portfolio with positive long-run expectancy, controlled portfolio equity drawdown, and genuinely new forward evidence.

Codex must optimize for **truth and survivability**, not for attractive historical output.

Do not ask for permission between repository-only commits defined here. Stop only when:

```text
a safety boundary would be crossed;
a required source is missing;
a contract is contradictory;
a test cannot be deterministic;
an exact-MT5 run cannot be reproduced;
or a hard NO-GO condition is triggered.
```

When stopped, write a report explaining the exact blocker. Do not silently weaken a gate.

---

# 1. Business objective

## 1.1 Final desired outcome

The end system should behave like a small automated trading business:

```text
positive net expectancy after realistic cost;
positive rolling 6- and 12-month performance over time;
controlled balance and equity drawdown;
low concentration in one trade, day, month, source, or regime;
limited manual intervention;
clear suspension and retirement rules;
and a withdrawal policy funded from accumulated profits,
not from forced monthly trading.
```

The system is **not required to make money every calendar month**.

A valid system may have:

```text
profitable months;
flat months;
losing months;
and long no-trade periods.
```

The business test is whether it produces positive results over sufficiently long rolling windows without unacceptable risk.

## 1.2 North-star statement

Use this exact north star in project status documents:

> Build an automated XAUUSD system that produces positive net returns over rolling 6- and 12-month periods, survives realistic costs and regime changes, limits portfolio equity drawdown, and can eventually support controlled withdrawals from accumulated profits.

## 1.3 Priority order

All decisions must follow this priority:

```text
1. Safety and capital survival
2. Causal correctness
3. Positive stressed expectancy
4. Equity-drawdown control
5. Robustness and concentration control
6. Independent portfolio contribution
7. Forward confirmation
8. Activity
9. Withdrawal potential
```

Activity must never override items 1–7.

---

# 2. Current frozen evidence state

Treat the following as authoritative until a later reviewed packet changes it.

## 2.1 Current portfolio control

The only defensible current portfolio baseline is:

```text
current_r1_r2_baseline
```

Reference evidence:

```text
Trades:                678
WR:                    51.03%
Realized W/L:          2.6082
PF:                    2.7182
Net:                   +$9,640.05
Stress net -$0.30:     +$9,436.65
Recent3 net:           +$764.92
Max closed DD:         $889.69
Positive months:       26
Active weekdays:       approximately 21.28%
```

This is a research control, not a live-authorized portfolio.

## 2.2 R1

R1 is the primary bullish/uptrend profit engine.

Its job is:

```text
trade only when the broad gold uptrend is valid;
remain inactive outside its proven regime;
and provide most long-side portfolio expectancy.
```

Do not require R1 to create daily activity.

## 2.3 R2

R2 is a strict downtrend / downside-participation hedge and secondary profit source.

It is not required to mirror R1’s frequency.

Its job is:

```text
protect and add return in genuine downside regimes;
avoid shorting chop or exhausted breakdowns;
and remain small when no strict R2 state exists.
```

## 2.4 R3

R3 is frozen as:

```text
STANDALONE_SHADOW_ONLY
```

Portfolio use is killed.

The overlap audit proved:

```text
139 total R3 trades
110 same-opportunity overlaps with the existing R1 box
29 non-overlap trades
```

R3 priority improved profit but exceeded the hard DD cap.

Therefore:

```text
Do not include R3 in the current portfolio.
Do not run another source-priority test.
Do not add a DD governor to rescue R3.
Do not tune R3.
```

## 2.5 R4

No R4/chop specialist is approved.

The following forms are frozen as unsuccessful:

```text
M5 sweep/reclaim;
daily-extreme reclaim;
prior-day reclaim;
opening-range reversal.
```

Default in chop remains:

```text
NO_TRADE
```

## 2.6 Historical-window status

All data through:

```text
2026-06-30
```

that has been inspected during this project is now:

```text
DEVELOPMENT DATA
```

It is not an untouched holdout.

No new result on this window alone may authorize demo or live broker action.

---

# 3. Core research correction

The project must stop repeating this loop:

```text
observe a weak month;
design a repair;
test the repair on the same history;
keep the best result;
then call the same history validation.
```

Exact MT5 verifies execution and code correctness.

It does not remove:

```text
selection bias;
multiple testing;
adaptive hypothesis choice;
or historical overfitting.
```

From now on:

```text
historical exact-MT5 work may diagnose and qualify a frozen idea;
only new locked forward evidence may confirm it.
```

---

# 4. Immediate program: prove regime ownership before changing strategy

The immediate next task is:

```text
A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_V1
```

Do not change any trading rule before this audit is complete.

## 4.1 Audit purpose

Determine whether current R1 and R2 trades are:

```text
A. entering under the wrong EA-router state;
B. entering under the correct slow D1/H4 label after the tactical market has already reversed;
C. entering correctly and later experiencing a regime change while open;
D. affected by data/timestamp/attribution defects;
E. valid losses inside the intended regime.
```

## 4.2 Authoritative classifier

Use:

```text
EA-side Router V1
```

as the authoritative regime state for this audit.

Do not substitute:

```text
the separate 10-year D1 diagnostic map.
```

The 10-year map may remain a contextual diagnostic only.

## 4.3 Trade universe

Audit every trade in the frozen R1+R2 control.

R3 may be reported separately as shadow diagnostic evidence, but must not alter the control portfolio.

## 4.4 Required trade-level fields

For every trade, output:

```text
source_id
component
trade_id
direction
signal_time
entry_time
exit_time

expected_regime
router_state_at_signal
router_state_at_entry
router_state_on_each_completed_H1_bar_while_open
router_state_at_exit

D1 close
D1 EMA20
D1 EMA50
D1 EMA20 slope
D1 EMA50 slope

H4 close
H4 EMA20
H4 EMA50
H4 EMA20 slope
H4 EMA50 slope

H1 close
H1 EMA20
H1 EMA50
H1 EMA20 slope
H1 EMA50 slope

M15 tactical structure
M15 last confirmed swing high
M15 last confirmed swing low
M15 structure-break direction

M5 signal state
spread
cost_R
initial risk
entry price
SL
TP

first_regime_change_time
router_state_before_change
router_state_after_change
unrealized_R_at_change
MFE_R_before_change
MAE_R_before_change
final_R
final_PnL
holding_seconds
holding_H1_bars
percentage_of_holding_time_in_expected_regime
```

Use completed bars only.

## 4.5 Required classifications

Assign exactly one primary class:

```text
CORRECT_ENTRY_STABLE_REGIME
CORRECT_ENTRY_LATER_REGIME_CHANGE
STALE_TREND_ENTRY
WRONG_ROUTER_ENTRY
TRANSITION_ENTRY
DATA_OR_TIMESTAMP_ERROR
VALID_LOSS_IN_EXPECTED_REGIME
```

Classification must not use final profit/loss as an input.

## 4.6 Definitions

### `WRONG_ROUTER_ENTRY`

```text
R1 long entered when EA router state != R1
OR
R2 short entered when EA router state != R2
```

Allowed count:

```text
0
```

### `STALE_TREND_ENTRY`

The slow D1/H4 router still shows the expected trend, but a locked tactical-opposition condition was already present at signal/entry.

Diagnostic opposition flags:

For R1 long:

```text
H1 close < H1 EMA50
OR
H1 EMA20 slope is strongly negative
OR
M15 completed-bar structure broke bearish
```

For R2 short:

```text
H1 close > H1 EMA50
OR
H1 EMA20 slope is strongly positive
OR
M15 completed-bar structure broke bullish
```

Do not search a threshold grid.

If a new slope threshold is required, define one market-distribution-based threshold before outcome analysis.

### `TRANSITION_ENTRY`

Use an objective, preregistered condition such as:

```text
D1 and H4 structural trend disagree;
or
D1 trend remains valid but H4 has lost its stack;
or
D1/H4 remain aligned while H1 is strongly opposed for a fixed completed-bar persistence.
```

Do not define transition from trade outcome.

### `CORRECT_ENTRY_LATER_REGIME_CHANGE`

Entry was valid, but the router changed away from the expected state while the position remained open.

Do not automatically classify this as a strategy error.

---

# 5. Router-path audit validity gates

The audit is valid only if all are true:

```text
100% of frozen R1+R2 trades traced
0 missing signal timestamps
0 missing entry timestamps
0 missing router snapshots
0 future-bar reads
0 bar-0 regime decisions
all snapshot joins are at or before the source timestamp
all source trade counts reconcile exactly
all source P/L totals reconcile exactly
all classifications deterministic
all ambiguous cases fail closed
```

## 5.1 Wrong-router defect gate

```text
WRONG_ROUTER_ENTRY count must equal 0
```

If nonzero:

```text
stop;
fix only the routing/configuration defect;
rerun the frozen exact-MT5 baseline;
do not add a filter;
do not change a threshold.
```

## 5.2 Stale-entry evidence gate

Router V2 is justified only if all are true:

```text
stale entries represent >= 15% of specialist losses;
stale-entry aggregate net R < 0;
stale-entry PF < 1.0;
same adverse sign exists in >= 3 calendar-year buckets;
not driven by one month;
not driven by one drawdown window;
and at least 30 stale-entry trades exist.
```

## 5.3 Holding-regime-change gate

A separate exit/de-risk study is justified only if:

```text
>= 30 correctly entered trades later change regime;
aggregate post-change R < 0;
loss after change is negative in >= 3 yearly buckets;
and result is not concentration-driven.
```

Do not change entry and exit in the same test.

---

# 6. Allowed post-audit paths

Assign one status:

```text
ROUTER_PATH_VALID_NO_CHANGE
ROUTER_PATH_WRONG_ENTRY_DEFECT
ROUTER_PATH_STALE_ENTRY_V2_JUSTIFIED
ROUTER_PATH_HOLDING_CHANGE_STUDY_JUSTIFIED
ROUTER_PATH_INVALID_EVIDENCE
```

## 6.1 `ROUTER_PATH_VALID_NO_CHANGE`

Actions:

```text
Freeze Router V1.
Stop blaming the router.
Keep current R1+R2 control.
Move to integrated portfolio proof.
```

## 6.2 `ROUTER_PATH_WRONG_ENTRY_DEFECT`

Actions:

```text
Fix the defect only.
No threshold changes.
Rerun exact-MT5 baseline.
Require zero violations.
```

## 6.3 `ROUTER_PATH_STALE_ENTRY_V2_JUSTIFIED`

Create:

```text
ROUTER_V2
```

Allowed change:

```text
one symmetric strong-opposition entry veto
OR
one explicit TRANSITION_NO_TRADE state
```

Run one fixed candidate only.

No grid.

No session/hour/month filter.

## 6.4 `ROUTER_PATH_HOLDING_CHANGE_STUDY_JUSTIFIED`

Run one shadow-only management study.

Allowed comparison:

```text
original SL/TP control
versus
one fixed regime-change de-risk rule
```

Do not force-close on the first state change unless preregistered and mechanically defined.

---

# 7. Integrated exact-MT5 portfolio requirement

After router-path work is closed, build and test one integrated portfolio.

Component-exact plus Python/offline recomposition remains diagnostic only.

## 7.1 Integrated system requirements

One exact-MT5 run must include:

```text
one authoritative router;
all approved specialists;
one account-wide family mutex;
one source-ownership policy;
one position manager;
shared exposure accounting;
shared margin;
shared balance/equity tracking;
portfolio daily/weekly/monthly containment;
one symbol-level position cap;
broker order contention;
actual MT5 balance DD;
actual MT5 equity DD;
order failures and retries;
all broker stop/freeze constraints.
```

## 7.2 Initial integrated source set

Start only with:

```text
current frozen R1 sources
current frozen R2 sources
```

Exclude:

```text
R3
R4
frequency filler
experimental observers
```

## 7.3 Opportunity ownership

Use one claim key:

```text
account
symbol
direction
family
decision M5 bar
```

Only one specialist may own one market opportunity.

Do not allow two correlated long engines to trade the same event.

## 7.4 Risk during integrated research

Research tester defaults:

```text
fixed 0.01 lot
no compounding headline
fixed-notional/R reporting
one XAUUSD direction at a time
max total open account risk equivalent <= 0.50%
```

Do not scale from historical profits.

---

# 8. Specialist standalone admission gate

No specialist enters an integrated portfolio unless it independently passes.

## 8.1 Universal gate

```text
Trades >= 100
Net > 0
Stress net > 0
PF >= 1.30
Stress PF >= 1.15
Realized W/L >= 1.80
Top10-winners-removed net > 0
Top3-best-days-removed net > 0
Best-month share <= 35%
Positive result in >= 3 calendar-year buckets
No unresolved order/fill/data defect
```

## 8.2 Core profit specialist

For a source intended to carry portfolio profit:

```text
WR >= 45%, preferably >= 50%
Realized W/L >= 2.00
PF >= 1.50, preferably >= 2.00
Stress PF >= 1.30
Max MT5 balance DD <= 8R
Max MT5 equity DD <= 12R
```

## 8.3 Hedge specialist

A hedge may have lower WR only if:

```text
Realized W/L >= 2.30
PF >= 1.25
Stress PF >= 1.10
Stress net > 0
weak-regime contribution > 0
combined DD does not exceed cap
```

## 8.4 Standalone-first rule

If standalone fails:

```text
do not use portfolio metrics to rescue it.
```

A combined diagnostic may be generated but must be labeled:

```text
NOT_PROMOTION_EVIDENCE
```

---

# 9. Independence gate before combination

A new specialist must pass independence before additive portfolio treatment.

Suggested locked defaults:

```text
same-opportunity overlap <= 40%
monthly return correlation absolute value <= 0.65
not more than 50% of its net from the same regime already owned by another source
maximum-DD windows must not materially coincide
```

If opportunity overlap exceeds 40%:

```text
classify as an alternative source owner;
do not classify as diversification;
run one ownership comparison only if preregistered.
```

R3 is the reference example of why this gate exists.

---

# 10. Integrated portfolio acceptance gates

Use acceptance gates as pass/fail checks, not optimization objectives.

## 10.1 Historical integrated exact-MT5 gates

```text
WR >= 49.5%
Realized W/L >= 2.00
PF >= 1.80
Stress PF >= 1.50
Stress net > 0
Top10-removed net > 0
Top3-days-removed net > 0
Best-month share <= 30%
Positive months >= 55%
Positive rolling 6-month windows >= 70%
All rolling 12-month windows non-negative after stress
Max MT5 balance DD <= locked account cap
Max MT5 equity DD <= locked account cap
No source is admitted only to increase activity
```

The rolling-window rules must be reported honestly.

Do not tune a specialist to make a specific rolling window pass.

## 10.2 Risk-adjusted comparison

Report:

```text
net R
net R / max equity DD R
Calmar-style annual return / max DD
monthly return volatility
worst month
worst rolling 3 months
worst rolling 6 months
```

A higher net result is not better if drawdown grows disproportionately.

## 10.3 Activity

Activity is informational.

Do not impose a minimum activity gate until the quality gates pass.

---

# 11. Forward-shadow exam

After the final integrated rules are frozen, create:

```text
A1_XAU_FORWARD_SHADOW_EXAM_V1
```

## 11.1 Freeze before start

Freeze and hash:

```text
EA source
router version
specialist versions
input presets
family mutex
source-priority policy
risk policy
report schema
start date
minimum sample
pass/fail gates
```

## 11.2 No-change rule

During the forward exam:

```text
no parameter change
no router change
no source change
no excluded days
no reset after losses
no removal of failed signals
no retrospective label change
```

A change invalidates the exam and starts a new version.

## 11.3 Minimum forward evidence

Require the longer of:

```text
6 calendar months
OR
200 mature portfolio trades
```

Also require:

```text
at least one meaningful regime transition;
at least 30 R1 trades if R1 was active;
at least 30 R2 trades if R2 was active;
all would-signals logged;
all blocked signals logged;
cost and slippage measured;
all order failures reconciled.
```

If a regime did not occur, mark:

```text
CONTINUE_EVIDENCE
```

Do not fabricate coverage.

## 11.4 Forward gates

```text
Net > 0 after measured cost
PF >= 1.20
Stress PF >= 1.05
Max equity DD within locked cap
No wrong-router entries
No concentration breach
No safety defect
No unclassified execution discrepancy
```

Forward evidence confirms implementation and survival.

It does not guarantee future return.

---

# 12. Demo micro-pilot

Demo broker action requires a separate reviewed authorization packet.

This document does not authorize it.

Minimum prerequisites:

```text
integrated exact-MT5 PASS
forward shadow PASS or CONTINUE_EVIDENCE with reviewer-approved scope
zero wrong-router entries
family mutex tested
containment tested
kill switch tested
compile 0 warnings / 0 errors
CI green
zero exposure baseline
owner approval of exact hashes
independent reviewer signoff
```

Micro-pilot constraints:

```text
one account
XAUUSD only
fixed 0.01 lot
no compounding
single integrated EA
daily equity-loss cap
weekly equity-loss cap
monthly equity-loss cap
automatic pause on order anomaly
fixed pilot end date
no withdrawals
```

Suggested initial containment:

```text
risk per trade target equivalent <= 0.25%
max total open risk <= 0.50%
daily equity-loss cap = 0.75%
weekly equity-loss cap = 2.00%
monthly equity-loss cap = 4.00%
```

These values must be reviewed before activation.

---

# 13. Live pilot and income model

Live capital is a later program, not an immediate Codex task.

## 13.1 Live ladder

Suggested future ladder:

```text
Stage 1 — minimum-size live pilot:
  3–6 months
  minimum lot
  no regular withdrawals

Stage 2 — probation:
  another 3–6 months
  scale only if risk and drift gates pass

Stage 3 — production:
  scale gradually
  preserve fixed risk caps

Stage 4 — withdrawal phase:
  withdraw only from profits above a high-water mark
```

## 13.2 Withdrawal policy

Do not model income as:

```text
fixed amount every month regardless of performance.
```

Suggested future policy:

```text
At quarter end:
  if equity is above the prior high-water mark
  and rolling 6-month PF/DD remain inside limits,
  withdraw 25–40% of profits above the high-water mark.

Otherwise:
  withdraw zero.
```

Living-expense reserve should remain outside the trading account.

---

# 14. New specialist research after the baseline

Do not begin a new strategy branch until:

```text
router-path audit is closed;
integrated R1+R2 exact-MT5 result exists;
and current baseline is frozen.
```

If a new source is later authorized, it must be genuinely independent.

## 14.1 Preferred missing-regime direction

The only currently defensible new XAU research direction is:

```text
H1/H4 range-box specialist
```

not another M5 reclaim variant.

Required structural premise:

```text
objective H4 range boundaries;
multiple completed-bar touches;
minimum range width relative to spread and ATR;
one trade per box;
clear breakout invalidation;
fixed 2R if mechanically feasible;
NO_TRADE when the box is not valid.
```

## 14.2 Design/exam split

A new family must use:

```text
design period
one locked exam period
future forward period
```

Do not reuse 2022–2026 as a clean exam.

## 14.3 Variant limit

```text
maximum 2 fixed variants
```

No broad grid.

No post-result repair on the exam window.

---

# 15. Python/ML direction

Do not use ML to create direction or trades now.

ML remains a later meta-label layer only.

Allowed future role:

```text
deterministic EA creates valid signal;
Python estimates setup quality;
Python outputs TAKE / SKIP / ABSTAIN in shadow;
Python never controls direction, stop, target, lot, or broker action.
```

ML starts only after:

```text
clean multi-account data;
would-signal universe;
causal labels;
purged walk-forward;
fair deterministic benchmark;
and enough sample.
```

A simple deterministic opposition veto wins if it performs as well as ML.

---

# 16. Immediate file plan

## Commit 1 — governance reset

Create:

```text
docs/A1_XAU_PROFITABLE_SYSTEM_MASTER_DIRECTION_2026_07_10.md
docs/A1_XAU_CURRENT_RESEARCH_FREEZE_2026_07_10.md
docs/A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_PREREG_2026_07_10.md
```

Update:

```text
status_summary.md
status_summary.json
status.html
agent.md
```

Current status must explicitly say:

```text
R1+R2 = current research control
R3 = standalone shadow only
R3 portfolio use = killed by DD gate
R4 = no survivor
no demo/live authorization
next task = router entry/hold path audit
```

## Commit 2 — audit schemas and tests

Add:

```text
scripts/analyze_a1_xau_router_entry_hold_path.py
scripts/verify_a1_xau_router_entry_hold_path.py

tests/test_a1_xau_router_entry_hold_path.py
tests/test_a1_xau_router_path_causality.py
tests/test_a1_xau_router_path_reconciliation.py
tests/test_a1_xau_router_path_safety.py
```

No audit result yet.

## Commit 3 — exact snapshot and path evidence

If necessary, add read-only snapshot mode or reuse the existing one.

Generate immutable snapshot/log artifacts.

No strategy change.

## Commit 4 — audit result

Generate:

```text
outputs/reports/A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_20260710.md
outputs/reports/A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_20260710.json
outputs/reports/A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_20260710_TRADES.csv
outputs/reports/A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_20260710_REGIME_PATHS.csv
outputs/reports/A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_20260710_CLASS_SUMMARY.csv
outputs/reports/A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_20260710_SOURCE_SUMMARY.csv
outputs/reports/A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_20260710_YEARLY.csv
outputs/reports/A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_20260710_MONTHLY.csv
```

Assign one status and stop for review.

## Commit 5 — conditional router action

Only if justified by Commit 4:

```text
fix defect
OR
one Router V2 veto
OR
one holding-change shadow study
```

Otherwise skip.

## Commit 6 — integrated portfolio harness

Build one integrated exact-MT5 R1+R2 portfolio.

No R3.

No R4.

No broker action outside Strategy Tester.

## Commit 7 — integrated exact-MT5 report

Generate balance/equity DD, source attribution, order reconciliation, and all gates.

Stop for review.

## Commit 8 — forward-shadow exam lock

Create and hash the forward exam packet.

No broker action.

---

# 17. Required reports

```text
A1_XAU_CURRENT_RESEARCH_FREEZE
A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT
A1_XAU_ROUTER_PATH_CAUSALITY_REPORT
A1_XAU_ROUTER_PATH_RECONCILIATION_REPORT
A1_XAU_INTEGRATED_PORTFOLIO_EXACT_MT5
A1_XAU_INTEGRATED_PORTFOLIO_DRAWDOWN_REPORT
A1_XAU_INTEGRATED_PORTFOLIO_COST_REPORT
A1_XAU_INTEGRATED_PORTFOLIO_CONCENTRATION_REPORT
A1_XAU_FORWARD_SHADOW_EXAM_LOCK
A1_XAU_FORWARD_SHADOW_MONTHLY_REPORT
A1_XAU_FORWARD_SHADOW_FINAL_VERDICT
```

Machine-readable JSON must accompany all primary Markdown reports.

---

# 18. Required tests

At minimum:

```text
router uses completed bars only
no bar-0 regime decision
no future snapshot join
100% trade reconciliation
100% P/L reconciliation
wrong-router classification deterministic
stale-entry classification deterministic
later-regime-change classification deterministic
unknown state fails closed
family mutex exactly one owner
no duplicate same-opportunity execution
source priority deterministic
portfolio position cap
shared exposure cap
daily/weekly/monthly equity containment
order failure lock
MT5 balance/equity DD export
fixed-notional reporting
stress-cost reporting
no broker-action surface in audit/shadow scripts
status artifacts fresh
artifact hashes verify
```

---

# 19. Hard NO-GO conditions

Stop and keep all runtime paused if any applies:

```text
wrong-router entry count > 0 before defect closure
future-bar or bar-0 leakage
trade/P&L reconciliation mismatch
missing exact-MT5 evidence
new parameter selected after results
2022–2026 called an untouched holdout
standalone specialist fails
independence gate fails but source called diversification
integrated equity DD exceeds cap
cost stress fails
concentration gate fails
order failures unresolved
status artifacts misleading
tests red
CI absent without local capture
runtime/demo state changed
reviewer signoff missing
owner hash approval missing
```

Valid terminal outcomes include:

```text
NO_GO
CONTINUE_EVIDENCE
NO_TRADE
FREEZE_CURRENT_BASELINE
```

Do not weaken gates to avoid these outcomes.

---

# 20. Explicitly forbidden

```text
No new R1 parameter variation.
No new R2 parameter variation.
No new R3 parameter variation.
No R3 portfolio repair.
No R4 micro-reclaim variation.
No month filters.
No loss-window filters.
No discovered hour/session filters.
No RR reduction.
No BE/partial/trailing repair.
No activity filler.
No portfolio grid.
No compounding headline.
No promotion from offline recomposition.
No demo/live attach.
No broker action.
No promise of monthly profit.
```

---

# 21. Definition of success

The program succeeds when it can truthfully show:

```text
1. Specialists enter only in correct and economically timely regimes.
2. Every included specialist is independently profitable after cost stress.
3. Included specialists add independent value rather than duplicate exposure.
4. One integrated exact-MT5 portfolio passes balance and equity-DD limits.
5. The final frozen system survives genuinely new forward shadow evidence.
6. A minimum-size demo/live ladder can be authorized without changing the rules.
7. Returns are sufficient over rolling periods to support future withdrawals from accumulated profits.
```

The program also succeeds if it honestly concludes:

```text
the current system is too selective to support the desired income level;
additional independent edge is required;
or the project should remain research-only.
```

Preventing capital deployment on a false edge is a successful outcome.

---

# 22. Codex immediate action

Start with Commit 1 only:

```text
1. Create the master-direction and research-freeze documents.
2. Create the router entry/hold-path audit preregistration.
3. Update stale status artifacts to the current R1/R2/R3/R4 decisions.
4. Record that all history through 2026-06-30 is development data.
5. Record that no demo/live authorization exists.
6. Do not modify the EA’s trading logic.
7. Do not run a new optimization.
8. Do not create another specialist.
9. Run documentation/schema tests.
10. Stop only if a governance contradiction is found.
```

Then proceed to the audit implementation commits.

---

# 23. Final instruction

The goal from this point is not:

```text
find a backtest that looks profitable.
```

The goal is:

> Produce the smallest integrated system whose positive expectancy, regime ownership, equity risk, independence, and forward survival can all be demonstrated without changing the rules after the evidence appears.

Do not trade more merely to look active.

Do not repair history.

Do not mistake exact simulation for unseen evidence.

Build the system that deserves capital.
