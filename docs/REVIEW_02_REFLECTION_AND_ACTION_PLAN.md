# Review #2 Reflection and Action Plan

**Project:** `algo-trading-system` / XAUUSD Master EA
**Source review:** Third-party Review Findings #2
**Review date:** 2026-05-22
**Reflection date:** 2026-05-22
**Prepared for:** repository inclusion and next-phase planning
**Recommended repo path:** `docs/REVIEW_02_REFLECTION_AND_ACTION_PLAN.md`

---

## 0. Executive Verdict

Review #2 is materially positive and should be accepted.

The important conclusion is not simply that the repo rating improved to **9.0 / 10 ex-ante**. The more important conclusion is that the project has moved from planning discipline into operational discipline: prior recommendations were acted on quickly, independent validation was added, reporting was consolidated, the second candidate was started, and Phase 1 CI exists.

However, Review #2 also changes the risk framing.

The surviving expert, `breakout_retest`, is not a low-frequency discretionary-style breakout/retest strategy. Based on the D4 reproduction numbers, it behaves like a **high-frequency intraday level-retest strategy** with roughly **10 trades per day** in at least one major cell. Its edge appears real but modest. The dominant remaining risk is no longer whether the backtest implementation was wrong. The dominant remaining risk is whether the gross per-trade edge survives real execution costs.

Therefore, the next phase should be managed with this revised mental model:

```text
Phase 1 remains a dry-run soak and telemetry validation phase.
Phase 2 must be treated primarily as a real-cost measurement phase.
Phase 2 should not be treated as a profit-confirmation phase.
```

The immediate decision is:

```text
Continue Phase 1 soak: YES
Start Phase 2 implementation immediately: NO
Prepare Phase 2 infrastructure/specification: YES
Allow live execution / OrderSend / CTrade: NO
```

Phase 2 should only be authorized after:

```text
1. Five-day Phase 1 soak = PASS
2. Phase 1 acceptance = PASS
3. Review index = PASS
4. Fixed-notional/no-compounding reporting mode is added
5. Per-trade all-in cost in R is added as a first-class metric
6. Passive spread logger data is analyzed
7. breakout_retest is revalidated against measured P95 costs
8. C3 external live drift monitor is built and tested
9. C4 disaster-recovery runbook is written
10. Owner explicitly approves Phase 2
```

---

## 1. What We Accept from Review #2

### 1.1 Accept: The project has improved materially

Review #2 says the team addressed all major Review #1 recommendations, including:

```text
D1 / D2 independent validation
D3 holdout audit
D4 independent reproduction
second-candidate research
Phase 1 CI workflow
reporting-policy consolidation
workspace ownership clarification
```

This should be recorded as a project strength. The most valuable signal is not only that the code changed, but that the team responded to review findings instead of defending prior work.

### 1.2 Accept: D1-D4 validation is closed but does not remove risk

The D1-D4 validation package should be treated as legitimate evidence.

Summary:

| Validation item | Review #2 verdict | Our reflection |
|---|---|---|
| D1 CPCV | PASS, strong | Strong robustness evidence, but the minimum OOS PF is close enough to 1.0 that costs remain decisive. |
| D2 White Reality Check / SPA | PASS, modest | p-values around 0.02 are meaningful but not overwhelming. Treat the edge as real but modest. |
| D3 true holdout audit | PASS, excellent | Strong governance. Keep this process unchanged. |
| D4 independent reproduction | PASS, valid | Confirms the implementation is not the artifact. It also reveals the cost-dominated nature of the strategy. |

The conclusion is:

```text
Implementation validity improved.
Statistical defensibility improved.
Live execution risk became more visible, not smaller.
```

### 1.3 Accept: `breakout_retest` is high-frequency and cost-dominated

This is the single most important new finding.

The D4 reproduction surfaced:

```text
Cell 2 trade count: 7,287 trades over 2016â€“2018
Approximate annual frequency: ~2,400 trades/year
Approximate daily frequency: ~10 trades/day
Win rate: ~48.4%
Gross expectancy: ~+0.21R/trade
Reported compounding PnL: ~$18.6M from $10k starting capital
```

The frequency changes the interpretation of the strategy. At 10 trades/day, small differences in spread, commission, slippage, order timing, stop-entry behavior, and quote freshness can materially change the outcome.

Reframed risk:

```text
Old question:
Does breakout_retest have a backtested edge?

New question:
Does the +0.21R/trade gross edge survive real all-in execution cost at ~10 trades/day?
```

This is now the main project question.

### 1.4 Accept: The $18.6M headline PnL must be retired

Absolute dollar PnL under compounding should no longer appear as a headline metric in any verdict, reproduction report, dashboard, or review bundle.

Reason:

```text
The compounding PnL is mathematically consistent but operationally fictional.
It assumes no broker lot-size ceiling, no liquidity constraint, no market impact, no compounding-path risk, and perfect scaling.
```

Going forward, all headline reporting should prioritize:

```text
profit factor
win rate
average trade in R
gross expectancy in R
all-in cost per trade in R
net expectancy after cost in R
max drawdown percentage
fixed-notional no-compounding PnL
trade count
cost sensitivity
fill quality / slippage metrics
```

Dollar PnL may remain as a secondary diagnostic, but only if clearly labelled as:

```text
compounding simulation output, not operational target
```

### 1.5 Accept: Phase 2 must become a cost-measurement exercise

Phase 2 should not be designed to answer:

```text
Does the EA make money immediately?
```

It should answer:

```text
What is the real per-trade cost?
What is the realised spread at signal time?
What is the realised slippage at entry and exit?
How often do stop entries fail, slip, or become stale?
Does measured P95 cost preserve a positive edge?
Does paper-mode execution materially diverge from Phase 0 assumptions?
```

The backtest edge has been demonstrated enough to justify moving forward after Phase 1 acceptance. The remaining uncertainty is live cost realism.

### 1.6 Accept: `squeeze_breakout_long_v0` is useful but not validated yet

The second candidate is a good start because it reduces dependency on a single approved expert.

But the current state is only:

```text
hypothesis registered
smoke test passed
plumbing verified
```

That is not evidence of edge.

The correct next step is the full Phase 0 battery:

```text
9-cell matrix
decile persistence
multisymbol check
adversarial review
hypothesis-vs-reality comparison
final Phase 0 verdict
```

Because it is long-only, the adversarial review must explicitly test whether it is just capturing long gold drift from 2016â€“2025.

---

## 2. Updated Project Status After Review #2

As of the reviewerâ€™s snapshot:

| Area | Status | Reflection |
|---|---|---|
| Review #1 recommendations | 8 of 8 addressed | Strong execution discipline. |
| Phase 1 soak | In progress, 13.06% complete | Continue; do not shortcut. |
| Phase 1 acceptance | Pending | Only final acceptance after soak and reports pass. |
| Phase 2 readiness | Pending | Requires soak, acceptance, C3, C4, measured cost revalidation, owner approval. |
| `breakout_retest` | Defensible but modest edge | Approved candidate, but cost-dominated. |
| $ PnL reporting | Needs change | Retire compounding headline PnL. |
| Second candidate | Started, not validated | Run full battery in parallel with soak. |
| Live execution | Not authorized | Still forbidden. |

Current go/no-go:

```text
Continue Phase 1 dry-run soak: GO
Prepare Phase 2 documentation/tools: GO
Run second-candidate validation: GO
Implement fixed-notional reporting: GO
Implement C3/C4: GO
Start Phase 2 paper execution before soak: NO-GO
Start live trading: NO-GO
```

---

## 3. Key Strategic Reframe

### 3.1 The strategy is no longer a â€œbreakout retestâ€ in the intuitive low-frequency sense

The label `breakout_retest` remains acceptable, but internally we should understand the expert as:

```text
M5 high-frequency level-retest continuation engine
```

The expert fires frequently because its level universe includes:

```text
previous day high / low
previous weekly high / low
confirmed M5 swing highs / lows
```

The M5 swing-level component is likely responsible for a large share of the frequency.

This is not automatically bad. Many valid systems are high-frequency and modest-edge. But it means:

```text
Costs matter more than narrative elegance.
Slippage matters more than the pattern name.
Fill quality matters more than backtest dollar PnL.
```

### 3.2 The main edge metric becomes net expectancy per trade in R

The reviewâ€™s calculation:

```text
Win rate â‰ˆ 48.4%
Target = 1.5R
Loss = -1R
Gross expectancy â‰ˆ (0.484 Ã— 1.5) âˆ’ (0.516 Ã— 1.0) = +0.21R/trade
```

This must now become the central monitoring structure.

Required new reporting fields:

```text
gross_expectancy_R
entry_cost_R
exit_cost_R
commission_R
slippage_R
all_in_cost_R
net_expectancy_R
cost_to_gross_edge_ratio
cost_adjusted_profit_factor
```

Example interpretation:

```text
Gross expectancy: +0.21R/trade
All-in cost: 0.10R/trade
Net expectancy: +0.11R/trade
Cost consumes: 47.6% of gross edge

Gross expectancy: +0.21R/trade
All-in cost: 0.15R/trade
Net expectancy: +0.06R/trade
Cost consumes: 71.4% of gross edge
```

This should be more prominent than dollar PnL.

### 3.3 Phase 2 should measure costs before proving profitability

Phase 2 should be evaluated by these questions first:

```text
Is measured spread close to assumed spread?
Is P95 spread worse than assumed P95?
What is median and P95 slippage?
What is all-in cost in R?
How often does cost exceed 0.10R?
How often does cost exceed 0.15R?
How often do stop entries slip or trigger late?
How many signals are skipped by execution guard?
Does measured-cost replay still pass Phase 0 gates?
```

Only after those are answered should we discuss capital scaling.

---

## 4. Reporting Policy Changes Required

### 4.1 New rule: no compounding PnL as headline

Any file that currently headlines compounding dollar PnL should be revised.

Files likely affected:

```text
PHASE0_VERDICT.md
phase0_breakout_retest_results.md
PHASE0_INDEPENDENT_VALIDATION.md
D4 reproduction report
review bundle summary
status dashboards
any README summary quoting total PnL
```

New headline section should use:

```text
PF
win rate
average R/trade
gross expectancy R
cost per trade R
net expectancy R
max DD %
trade count
fixed-notional PnL
```

### 4.2 Add fixed-notional, no-compounding reporting mode

Add a reporting mode that keeps trade notional constant across the simulation.

Purpose:

```text
Remove compounding artifact.
Make performance comparable across cells.
Show the underlying per-trade edge without exponential equity growth.
```

Suggested mode names:

```text
fixed_notional
no_compounding
constant_risk_dollars
```

Recommended default for review reports:

```text
primary_report_mode = fixed_notional_no_compounding
secondary_report_mode = compounding_backtest_diagnostic
```

### 4.3 Add cost-in-R as a first-class metric

Every report should include:

```text
median_cost_R
p95_cost_R
mean_cost_R
entry_spread_R
entry_slippage_R
exit_spread_R
exit_slippage_R
commission_R
net_expectancy_R
cost_edge_consumption_pct
```

Definitions:

```text
risk_R = absolute(entry_price - stop_loss_price)
spread_R = spread_price / risk_R
slippage_R = abs(actual_fill_price - expected_fill_price) / risk_R
commission_R = commission_money / risk_money
all_in_cost_R = spread_R + slippage_R + commission_R
net_expectancy_R = gross_expectancy_R - all_in_cost_R
cost_edge_consumption_pct = all_in_cost_R / gross_expectancy_R
```

If cost consumes more than a defined threshold of gross edge, the system should be flagged.

Suggested flags:

```text
cost_edge_consumption_pct <= 40%: GREEN
40% < cost_edge_consumption_pct <= 60%: YELLOW
60% < cost_edge_consumption_pct <= 80%: ORANGE
> 80%: RED
```

### 4.4 Regenerate reports after reporting change

After implementing the new reporting mode, regenerate:

```text
PHASE0_VERDICT.md
phase0_breakout_retest_results.md
PHASE0_INDEPENDENT_VALIDATION.md
D4 reproduction report
review bundle
README summary if needed
```

The new reports should no longer make the $18.6M figure prominent.

---

## 5. Phase 1 Completion Requirements

Phase 1 remains valid and should continue. Do not shortcut the soak.

### 5.1 Required before Phase 1 acceptance

```text
five-day dry-run soak = PASS
PHASE1_STATUS_SUMMARY.json = PASS
PHASE1_ACCEPTANCE_REPORT.md = PASS
review bundle generated
safety audit = PASS
dry-run lock = PASS
permission lock = PASS
no exact duplicate runtime rows
no unexplained runtime gaps
would-signal clusters reviewed
```

### 5.2 Would-signal cluster review

Any would-signal clusters observed during Phase 1 should be manually reviewed.

Purpose:

```text
Confirm MQL5 observer matches Python Phase 0 logic.
Confirm levels are reasonable.
Confirm entry/stop/target projections are mechanically valid.
Confirm no hidden runtime mismatch exists.
```

This review must not lead to tuning the strategy logic. It is only an implementation-consistency audit.

### 5.3 Phase 1 acceptance language

Use strict status wording:

```text
AUTHORIZED_AND_RUNNING
PENDING_SOAK
ACCEPTED
FAILED
```

Do not use vague terms like:

```text
basically done
ready enough
nearly approved
```

---

## 6. Phase 2 Readiness Requirements

Phase 2 is not authorized merely because Phase 0 passed. It is authorized only after Phase 1 acceptance and added operational controls.

### 6.1 Required before Phase 2 authorization

| Gate | Required status |
|---|---|
| Phase 1 soak | PASS |
| Phase 1 acceptance report | PASS |
| Phase 1 review bundle | PASS |
| Fixed-notional reporting mode | Implemented |
| Compounding PnL retired from headline reporting | Complete |
| Cost-in-R metrics | Implemented |
| Passive spread logger data | Analyzed |
| Measured P95 cost model | Produced |
| `breakout_retest` measured-cost revalidation | PASS or explicit owner-reviewed conditional PASS |
| C3 live drift monitor | Built and tested |
| C4 disaster-recovery runbook | Written |
| Phase 2 capital/risk plan | Approved |
| Owner approval | Explicit YES |

### 6.2 Phase 2 should be paper mode, not live trading

Phase 2 should measure execution without placing real risk.

Possible Phase 2 modes:

```text
paper_mode_internal_simulation
broker_quote_attached_paper_fill
demo_micro_lot_execution
```

Recommended order:

```text
1. paper_mode_internal_simulation
2. broker_quote_attached_paper_fill
3. demo micro-lot only after paper-mode evidence is acceptable
```

If demo micro-lot execution is used, it should be treated as an execution-cost experiment, not capital deployment.

### 6.3 Phase 2 primary metrics

The Phase 2 dashboard/report should lead with:

```text
signals generated
signals skipped by execution guard
paper entries filled
paper entries missed
median spread at signal
P95 spread at signal
median slippage estimate
P95 slippage estimate
all-in cost in R
net expectancy in R
fill latency
stale quote count
requote/rejection count if demo execution is used
cost-adjusted PF
cost-edge-consumption percentage
```

### 6.4 Phase 2 pass/fail interpretation

Phase 2 passes only if measured costs do not destroy the edge.

Suggested interpretation:

```text
GREEN:
measured P95-cost replay PF >= 1.30
net expectancy_R remains materially positive
cost_edge_consumption_pct <= 60%

YELLOW:
measured P95-cost replay PF between 1.10 and 1.30
net expectancy_R positive but thin
cost_edge_consumption_pct between 60% and 80%
Requires owner review and reduced-risk continuation.

RED:
measured P95-cost replay PF < 1.10
or net expectancy_R near zero / negative
or cost_edge_consumption_pct > 80%
Do not proceed to live pilot.
```

---

## 7. Required New Documents / Repo Artifacts

Create or update these artifacts before Phase 2 authorization.

### 7.1 `docs/COST_REPORTING_POLICY.md`

Purpose:

```text
Define fixed-notional reporting.
Define no-compounding reporting.
Define allowed and forbidden headline metrics.
Define cost-in-R metrics.
Define how compounding PnL may be referenced, if at all.
```

Required sections:

```text
1. Reporting principle
2. Forbidden headline metrics
3. Primary metrics
4. Secondary diagnostic metrics
5. Fixed-notional calculation
6. Cost-in-R calculation
7. Report regeneration requirements
8. Acceptance gates using measured costs
```

### 7.2 `outputs/reports/FIXED_NOTIONAL_REPORT.md`

Purpose:

```text
Show breakout_retest performance without compounding.
```

Required fields:

```text
trade_count
win_rate
PF
average_R
median_R
gross_expectancy_R
all_in_cost_R
net_expectancy_R
fixed_notional_total_pnl
fixed_notional_max_dd
max_losing_streak
largest_trade_contribution
```

### 7.3 `outputs/reports/MEASURED_COST_MODEL.md`

Purpose:

```text
Replace assumed spread/cost model with measured spread logger data.
```

Required fields:

```text
spread_logger_start
spread_logger_end
rows_collected
median_spread_by_session
P95_spread_by_session
median_spread_by_hour
P95_spread_by_hour
rollover spread distribution
news-window spread distribution
max observed spread
recommended measured_median_cost
recommended measured_P95_cost
```

### 7.4 `outputs/reports/BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md`

Purpose:

```text
Rerun breakout_retest cost sensitivity against measured P95 cost.
```

Required sections:

```text
1. Source cost model
2. Replay assumptions
3. Fixed-notional results
4. Compounding diagnostic results, de-emphasized
5. Cost-in-R results
6. Pass/fail gates
7. Final recommendation
```

### 7.5 `docs/BREAKOUT_RETEST_EDGE_THESIS_DEEP_DIVE.md`

Purpose:

```text
Explain why M5 retests of broken levels on XAU should have edge beyond merely passing tests.
```

Required questions:

```text
What market behavior creates this edge?
Which participants or flows make retests meaningful?
Why does XAU show this behavior?
Why does the M5 timeframe work?
Which level types produce most signals?
Is the edge concentrated in M5 swing levels vs daily/weekly levels?
Does the strategy exploit continuation, liquidity recycling, or microstructure noise?
When should the edge decay?
What would falsify the mechanism in live data?
```

### 7.6 `docs/LIVE_DRIFT_MONITOR_SPEC.md`

Purpose:

```text
Specify the external health and performance drift monitor required before Phase 2.
```

Must include:

```text
heartbeat source
heartbeat interval
missing-heartbeat alert threshold
log-ingestion method
PF drift metric
cost drift metric
spread drift metric
signal-frequency drift metric
alert channels
manual escalation process
```

### 7.7 `docs/DR_RUNBOOK.md`

Purpose:

```text
Define emergency procedures before any broker-affecting mode exists.
```

Required procedures:

```text
VPS dies mid-session
MT5 crashes
broker disconnects
EA stops writing heartbeat
dry-run unexpectedly disabled
Phase 2 paper bridge stalls
demo micro-lot order gets stuck, if applicable
all EA positions need emergency closure, for later phases
broker symbol changes / suffix changes
magic number collision discovered
```

### 7.8 `docs/PHASE2_CAPITAL_AND_COST_MEASUREMENT_PLAN.md`

Purpose:

```text
Define exactly what Phase 2 is allowed to do and how risk remains contained.
```

Required sections:

```text
Phase 2 objective
Allowed modes
Forbidden behavior
Starting size
Lot-size cap
daily paper-risk cap
weekly paper-risk cap
cost measurement fields
success criteria
failure criteria
owner approval line
```

---

## 8. Codex / Developer Task List

### 8.1 Reporting mode implementation

Ask Codex/developer to implement:

```text
Add fixed-notional / no-compounding report mode.
Add CLI option: --report-mode fixed_notional.
Add config key: reporting.primary_mode = fixed_notional_no_compounding.
Add config key: reporting.allow_compounding_diagnostic = true/false.
Remove compounding total_pnl from headline tables.
Add warning label wherever compounding PnL is shown.
```

Acceptance:

```text
Generated reports show fixed-notional metrics first.
No headline table displays $18.6M-style compounding PnL.
Unit tests verify compounding and fixed-notional modes differ.
```

### 8.2 Cost-in-R implementation

Ask Codex/developer to implement:

```text
Calculate spread_R per trade.
Calculate slippage_R per trade.
Calculate commission_R per trade.
Calculate all_in_cost_R per trade.
Calculate median_cost_R and p95_cost_R.
Calculate cost_edge_consumption_pct.
Add these to Phase 0 reports and Phase 1/Phase 2 telemetry.
```

Acceptance:

```text
Every trade row has cost_R fields.
Every report has aggregate cost_R summary.
Cost_R calculations are unit-tested with known entry/SL/spread values.
```

### 8.3 Measured cost model integration

Ask Codex/developer to implement:

```text
Read cost_model_measured.csv if present.
Fallback to configured costs only if measured file is absent.
Label reports as MEASURED or ASSUMED cost model.
Block Phase 2 readiness if measured cost model is missing.
```

Acceptance:

```text
MEASURED_COST_MODEL.md generated.
Phase 2 readiness fails if measured P95 cost has not been applied.
```

### 8.4 Revalidation against measured P95 cost

Ask Codex/developer to implement:

```text
Command: phase0 revalidate-measured-cost --expert breakout_retest
Output: BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md
```

Acceptance:

```text
Report includes PF, net expectancy_R, fixed-notional PnL, cost_edge_consumption_pct.
Report states PASS / YELLOW / FAIL.
```

### 8.5 Second-candidate validation

Ask Codex/developer/researcher to run:

```text
phase0 run-matrix --expert squeeze_breakout_long_v0
phase0 run-deciles --expert squeeze_breakout_long_v0
phase0 run-multisymbol --expert squeeze_breakout_long_v0
phase0 create-adversarial-packets --expert squeeze_breakout_long_v0
phase0 score-adversarial-review --expert squeeze_breakout_long_v0
phase0 aggregate-results --expert squeeze_breakout_long_v0
```

Additional adversarial requirement:

```text
Flag whether the long-only edge is merely gold upward drift.
Compare long-only performance against neutral baselines.
Document whether performance is concentrated in bullish gold regimes.
```

Acceptance:

```text
SQUEEZE_BREAKOUT_LONG_V0_PHASE0_RESULTS.md exists.
PHASE0_VERDICT.md updated if it passes.
If it fails, it remains research-only.
```

### 8.6 C3 live drift monitor

Ask Codex/developer to implement or specify:

```text
External heartbeat monitor, separate from MT5.
Reads latest heartbeat/log timestamp.
Alerts if no heartbeat > 10 minutes.
Tracks spread drift, signal-frequency drift, and cost drift.
Produces daily drift summary.
```

Acceptance:

```text
LIVE_DRIFT_MONITOR_SPEC.md complete.
Health monitor smoke test passes.
Simulated missing heartbeat triggers alert.
```

### 8.7 C4 disaster recovery runbook

Ask team to write:

```text
DR_RUNBOOK.md
```

Acceptance:

```text
Runbook has step-by-step procedures.
Owner can follow it without developer assistance.
Emergency close procedure documented.
Broker/VPS/MT5 failure paths documented.
```

---

## 9. Risk Register Update

| Risk | Severity | Current status | Mitigation |
|---|---:|---|---|
| Execution cost destroys edge | Critical | Newly elevated | Cost-in-R metrics, measured P95 revalidation, Phase 2 as cost-measurement phase. |
| Compounding PnL creates overconfidence | High | Newly visible | Retire headline dollar PnL; use fixed-notional reports. |
| Single-expert concentration | High | Partially mitigated | Validate `squeeze_breakout_long_v0`; do not scale until second expert evidence exists or risk is adjusted. |
| Phase 1 soak shortcut | Medium | Pending | Do not shorten wall-clock soak. |
| Weak mechanism explanation | Medium | Partial | Write deeper breakout_retest Edge Thesis. |
| Long-only second candidate is just gold drift | Medium | Pending | Explicit adversarial bias check. |
| No live drift monitor | High before Phase 2 | Missing | Build C3. |
| No disaster recovery runbook | High before Phase 2 | Missing | Write C4. |
| Router overfit | Medium | Controlled but ongoing | Continue router versioning and would-have-allowed logs. |
| Live broker differences | High | Unknown | Measured costs, paper fills, demo micro-lot later only if approved. |

---

## 10. Revised Phase Roadmap

### Current phase

```text
Phase 1 â€” Master EA Dry-Run Shell / Soak
```

Allowed:

```text
soak continuation
telemetry collection
would-signal review
fixed-notional reporting implementation
measured cost model analysis
second-candidate research
C3/C4 preparation
Phase 2 specification
```

Forbidden:

```text
OrderSend
CTrade
trade.Buy
trade.Sell
PositionOpen
live position modification
capital deployment
paper-mode broker bridge before readiness gates
```

### Next phase after acceptance

```text
Phase 2 â€” Paper-Mode Cost Measurement
```

Primary objective:

```text
Measure real per-trade all-in cost and determine whether breakout_retest survives measured costs.
```

Secondary objective:

```text
Validate MQL5 signal generation and paper-fill assumptions under live quote conditions.
```

Not the objective:

```text
Maximize profit.
Scale capital.
Prove the strategy is ready for live trading.
```

---

## 11. Phase 2 Authorization Checklist

Phase 2 may begin only when every item below is complete.

```text
[ ] Five-day Phase 1 soak complete
[ ] PHASE1_STATUS_SUMMARY.json = PASS
[ ] PHASE1_ACCEPTANCE_REPORT.md = PASS
[ ] Phase 1 review bundle generated
[ ] Safety audit = PASS
[ ] Dry-run lock = PASS
[ ] Permission lock = PASS
[ ] Would-signal clusters manually reviewed
[ ] Fixed-notional reporting mode implemented
[ ] Compounding PnL retired from headline reports
[ ] Per-trade all-in cost in R implemented
[ ] Measured cost model produced from spread logger data
[ ] breakout_retest revalidated against measured P95 costs
[ ] C3 external live drift monitor built and tested
[ ] C4 DR_RUNBOOK.md written
[ ] Phase 2 capital/cost-measurement plan approved
[ ] Owner approval recorded
```

If any item is incomplete:

```text
Phase 2 implementation remains blocked.
```

---

## 12. Decisions We Should Record Now

### Decision 1 â€” Accept Review #2

```text
Decision: ACCEPTED
Reason: Review #2 is specific, evidence-based, and identifies a genuine new risk: cost dominance.
```

### Decision 2 â€” Retire compounding PnL as headline metric

```text
Decision: ACCEPTED
Reason: Compounding PnL is not operationally meaningful for a high-frequency strategy that would eventually face lot-size, liquidity, and execution constraints.
```

### Decision 3 â€” Treat Phase 2 as cost measurement

```text
Decision: ACCEPTED
Reason: At ~10 trades/day and modest per-trade edge, real spread/slippage/commission determine viability.
```

### Decision 4 â€” Continue Phase 1 soak without shortcut

```text
Decision: ACCEPTED
Reason: Wall-clock runtime is an operational gate, not a code gate.
```

### Decision 5 â€” Validate second candidate in parallel

```text
Decision: ACCEPTED
Reason: Single-expert concentration remains a major risk.
```

### Decision 6 â€” No Phase 2 authorization before C3/C4

```text
Decision: ACCEPTED
Reason: Paper/trading-adjacent modes require external monitoring and disaster recovery procedures.
```

---

## 13. My Final Reflection

Review #2 is a strong review and should not be treated as a setback. It is a refinement of the risk model.

The project has reached a better state than most retail algo projects because it has evidence, gates, independent validation, CI, reporting policy, and a controlled dry-run shell. That is valuable.

But the review correctly identifies the uncomfortable truth: `breakout_retest` passed as a **real but modest** high-frequency edge. That means the next failure mode will not be a missing document or a flawed backtest implementation. The next failure mode will likely be execution cost.

Therefore, the project should now become stricter, not looser.

The correct attitude is:

```text
We have enough evidence to continue.
We do not yet have enough evidence to scale.
We have not earned live trading.
We must measure cost before interpreting profit.
```

If measured cost remains controlled, `breakout_retest` may deserve progression into later demo and pilot phases. If measured cost consumes most of the edge, the correct decision is to stop or reduce scope, even if all historical validations looked good.

The best next move is not another plan rewrite. The best next move is precise implementation of the reviewâ€™s requested controls:

```text
fixed-notional reporting
cost-in-R metrics
measured P95 cost model
measured-cost revalidation
five-day soak completion
second-candidate validation
C3 live drift monitor
C4 disaster recovery runbook
```

Once those are complete, Phase 2 can be considered with a clean decision.

---

## 14. Immediate Next Commands / Tasks

### Reporting and cost work

```bash
# Suggested conceptual commands; actual CLI names may differ.
phase0 generate-fixed-notional-report --expert breakout_retest
phase0 compute-cost-r-metrics --expert breakout_retest
phase0 analyze-spread-logger --symbol XAUUSD
phase0 revalidate-measured-cost --expert breakout_retest
```

### Second candidate work

```bash
phase0 run-matrix --expert squeeze_breakout_long_v0
phase0 run-deciles --expert squeeze_breakout_long_v0
phase0 run-multisymbol --expert squeeze_breakout_long_v0
phase0 create-adversarial-packets --expert squeeze_breakout_long_v0
phase0 score-adversarial-review --expert squeeze_breakout_long_v0
phase0 aggregate-results --expert squeeze_breakout_long_v0
```

### Phase 1 acceptance work

```bash
phase1 generate-status-summary
phase1 generate-acceptance-report
phase1 generate-review-bundle
phase1 audit-safety
```

### Phase 2 readiness work

```bash
phase1 generate-phase2-readiness-report
```

Do not create a command that enables broker execution until Phase 2 readiness is explicitly PASS and owner approval is recorded.

---

## 15. Final Go / No-Go

| Decision | Status |
|---|---|
| Accept Review #2 | GO |
| Continue Phase 1 soak | GO |
| Implement fixed-notional reporting | GO |
| Add cost-in-R metrics | GO |
| Analyze measured spread logger data | GO |
| Revalidate breakout_retest against measured P95 cost | GO |
| Run full battery for `squeeze_breakout_long_v0` | GO |
| Build C3 live drift monitor | GO |
| Write C4 disaster recovery runbook | GO |
| Authorize Phase 2 before soak completes | NO-GO |
| Authorize live trading | NO-GO |
| Quote $18.6M PnL as headline | NO-GO |
| Treat Phase 2 as profit confirmation | NO-GO |

Final recommendation:

```text
Proceed with Phase 1 completion and Phase 2 preparation.
Do not authorize Phase 2 implementation until the new cost/reporting/monitoring requirements are satisfied.
Treat measured real execution cost as the decisive next evidence.
```
