# Final Repository Review After Updated Push — XAUUSD Algo Trading System

**Review date:** 2026-05-23  
**Repository:** `maksoftwares/algo-trading-system`  
**Branch reviewed:** `main`  
**Scope:** Updated public GitHub artifacts, Phase 0 / Phase 1 / Phase 2 readiness documents, current dashboard, and third-party Review #4 findings.  
**Review type:** Static artifact review. I did not clone the repo or independently run the test suite locally.

---

## 1. Executive Verdict

```text
Continue Phase 1 dry-run:                       GO
Continue Phase 2 documentation/prep:            GO
Authorize Phase 2 paper-mode implementation:    NO-GO
Authorize broker-side execution:                NO-GO
Authorize live trading:                         ABSOLUTE NO-GO
```

The repository is in a strong state. Phase 0 is closed for `breakout_retest`, the Phase 1 dry-run shell is implemented and operating with the correct passive boundary, and the project is being governed with unusually good evidence discipline.

However, the updated repo still has three load-bearing blockers before Phase 2 can be authorized:

```text
1. Phase 1 soak is still incomplete.
2. Measured cost model is still incomplete.
3. The Phase 2 cost-survival threshold is still too soft or not mathematically defended.
```

My current rating:

```text
Repository/process quality:          8.8 / 10
Phase 1 dry-run implementation:      Strong, still soaking
Phase 2 paper-mode readiness:        Not ready
Live-trading readiness:              No
Edge defensibility today:            Contingent on measured cost
```

The current best description is:

```text
Well-engineered Phase 1 dry-run system with one validated high-frequency breakout-retest edge family, but Phase 2 must wait for uninterrupted soak and measured-cost survival evidence.
```

---

## 2. Current Project State

The root repository now identifies the active project phase as:

```text
Phase 1 - Master EA dry-run shell
```

The current package structure is correct:

```text
xau-usd/xauusd-phase0  = statistical validation package
xau-usd/xauusd-phase1  = MT5 dry-run telemetry shell
```

The root README states that Phase 1 is dry-run only and that live expert behavior remains out of scope until stable demo telemetry and a separate go/no-go review approve the next milestone.

The generated status dashboard shows:

```text
Phase 0:            PASS
Phase 1:            PENDING
Measured cost:      PENDING
Phase 2:            PENDING
Dry run:            true
Trade permission:   false
Server time:        CLOCK_OK
Soak progress:      8.26%
Observed soak:      0.4132 of 5 trading days
Measured cost rows: 7994 rows / 2 days
```

This is the correct state. It is not a failure. It means the system is being held at the right gate.

---

## 3. Phase 0 Review

### 3.1 Phase 0 Is Closed for `breakout_retest`

The current consolidated Phase 0 verdict is:

```text
breakout_retest: PASS
trend_pullback:  FAIL
range_mr:        FAIL
```

The verdict also states:

```text
Experts approved for Phase 1: breakout_retest
Experts rejected: trend_pullback, range_mr
Experts pending manual review: none
Recommended action: proceed to Phase 1 with the 1-expert reduced package
```

This is accepted.

### 3.2 Breakout-Retest Passed the Ten-Gate Package

The `breakout_retest` result report shows:

```text
9-cell matrix:          PASS
Decile persistence:     PASS
Adversarial review:     PASS
Multi-symbol check:     PASS
Hypothesis SHA256 lock: PASS
Final verdict:          PASS
```

Important supporting details:

```text
9-cell PF pass count:       7/9 cells PF >= 1.30
Decile positive count:      10/10 deciles
Adversarial review:         120 reviewed losing trades, 0 logic gaps
EURUSD PF:                  1.451
USDJPY PF:                  1.540
SHA256 hash:                matched registered manifest
```

The result is valid enough to justify Phase 1 dry-run observation.

### 3.3 Keep the Reduced Scope

Do not re-enable rejected experts.

```text
trend_pullback = rejected
range_mr       = rejected
```

Any revisit must use:

```text
new versioned hypothesis
new SHA256 lock
new Phase 0 run
new verdict
```

No tuning rejected v0 strategies in place.

---

## 4. Independent Validation and Reality Check

### 4.1 D1–D4 Status

The repo continues to show the independent validation package is closed for the current evidence set:

```text
D1 CPCV:                    PASS
D2 Reality Check / SPA:      PASS
D3 true holdout audit:       PASS
D4 independent reproduction: PASS
```

The current `agent.md` says the latest Reality Check result remained a PASS after adding more candidate rows, with:

```text
White Reality Check p-value: 0.0200
Max pairwise SPA p-value:   0.0308
Candidate universe:         27 non-empty matrix-ledger candidates
```

The public `PHASE0_REALITY_CHECK.md` also shows `breakout_retest` remains the winner after the bootstrap adjustment, with White p-value `0.0200`.

### 4.2 Review Note: Re-run Reality Check on Fixed-Notional R Series

The current Reality Check still appears to be based on monthly PnL values. Since Review #2 correctly identified compounding dollar PnL as misleading for this strategy family, the cleanest next improvement is:

```text
Re-run Reality Check / SPA using fixed-notional monthly R returns,
not compounding or raw dollar PnL.
```

This is not a Phase 1 blocker, but it should be completed before Phase 2 authorization if the tooling can support it without disrupting the current evidence chain.

Rationale:

```text
- The fixed-notional report is now the canonical review surface.
- Reality Check should use the same no-compounding evidence layer.
- It avoids scale artifacts when comparing high-frequency and low-frequency candidates.
```

---

## 5. Candidate Universe and Rejection Audit

### 5.1 Rejection Audit Is Strong

The updated rejection audit now covers:

```text
Audited candidates:                      28
Rejected/research candidates audited:     26
Sample-size failures:                     4
Multi-cell expectancy failures:           23
Expectancy-only failures:                 19
Frequency-only failures:                  0
```

This is important. It means the Phase 0 gates are not merely killing low-frequency strategies. They are primarily rejecting weak expectancy and concentration risk.

### 5.2 Current Candidate Bench

The status dashboard currently shows:

```text
Accepted candidates:    2
Provisional candidates: 3
Rejected candidates:    23
```

Accepted:

```text
breakout_retest
swing_breakout_retest_v0
```

But this must be interpreted carefully:

```text
breakout_retest              = primary approved future expert
swing_breakout_retest_v0      = same-family future candidate, not independent diversification
round_number_retest_v0        = provisional, Gate 9 pending
session_extreme_retest_v0     = provisional, status pending/non-final
symbol_normalized_round_retest_v0 = provisional, Gate 9 pending
```

The candidate bench is improving, but it is still dominated by intraday and breakout/retest mechanics.

---

## 6. Same-Family Risk

The repo now correctly treats the system as a **single-edge-family project**.

The Phase 2 single-edge risk plan says:

```text
breakout_retest and swing_breakout_retest_v0 are one correlated breakout-retest family.
No portfolio-diversification uplift is allowed.
No compounding through paper or future micro pilot.
No live capital is authorized by the plan.
```

This is the correct risk treatment.

### Required Phase 2 Rule

For Phase 2 paper mode:

```text
breakout_retest = only execution-eligible paper expert
swing_breakout_retest_v0 = observer-only telemetry
```

Do not allow both variants to generate paper fills initially. Running both as execution-eligible paper strategies would confound attribution.

Correct Phase 2 setup:

```text
Primary paper-mode stream: breakout_retest
Observer telemetry only:   swing_breakout_retest_v0
All other candidates:      disabled or research-only
```

---

## 7. Cost Model Review

### 7.1 Current Cost Evidence

The fixed-notional report is now the right headline reporting surface.

Current fixed-notional metrics:

```text
Trades:                    66,759
Win rate:                  48.22%
Profit factor:             1.3625
Gross expectancy:          0.5115R
Modeled cost:              0.3228R
Net expectancy:            0.1888R
Cost edge consumption:     63.09%
Cost flag:                 ORANGE
```

This is a good but cost-sensitive edge.

### 7.2 Measured Cost Is Still Pending

The current measured cost report shows:

```text
Overall status:           PENDING
Observed rows:            7,994
Observed days:            2
Required days:            5
Median spread:            50 points
P95 spread:               75 points
Max spread:               75 points
```

This is the most important unresolved item.

### 7.3 Preliminary Warning: Measured Spreads Look Higher Than Configured Costs

The configured Phase 0 cost model uses:

```text
XAUUSD median spread: 20 points
XAUUSD P95 spread:    35 points
```

The preliminary measured model currently shows:

```text
Median spread: 50 points
P95 spread:    75 points
```

This may be a broker-point-format issue, a short-sample issue, a weekend/rollover artifact, or a real cost mismatch. It cannot be ignored.

Before Phase 2 authorization, the team must answer:

```text
Are measured spread points using the exact same point scale as the configured cost model?
If yes, does breakout_retest still preserve enough net expectancy under measured median/P95 costs?
If no, document the conversion and regenerate the measured-cost model cleanly.
```

### 7.4 Cost Threshold Problem

The current Phase 2 cost protocol still uses:

```text
MIN_NET_EXPECTANCY_R_AFTER_MEASURED_COST = +0.10R
```

This is too soft unless mathematically defended.

Recommended change:

```text
Hard continuation floor:     +0.15R
Preferred target:            +0.20R
Below +0.15R:                suspend family and return to research
```

Alternative acceptable path:

```text
Keep +0.10R only if the team produces a minimum-detectable-effect / forward-sample variance calculation proving +0.10R is statistically distinguishable from zero under expected Phase 2 sample size.
```

Until that is resolved:

```text
Phase 2 paper-mode implementation remains blocked.
```

---

## 8. Phase 1 Dry-Run Review

### 8.1 Phase 1 Shell Is Working

The Phase 1 shell has advanced to:

```text
phase1-dry-run-v0.6
```

The repo shows the dry-run shell now includes:

```text
market snapshot
session detection
execution guard
news guard
router regime classification
decision logger
dashboard
feature telemetry
server-time validation
magic-number allocator
expert lifecycle manager
risk lock simulations
breakout-retest dry-run observer
swing-breakout-retest dry-run observer
```

Current safety posture:

```text
dry_run = true
trade_permission = false
server_time_status = CLOCK_OK
```

This is correct.

### 8.2 Runtime Reports Are Healthy

Current reports show:

```text
Runtime health:       PASS
Log verification:     PASS
Soak/drift analysis:  PASS
Would-signal report:  PASS
Permission lock:      PASS
Dry-run lock:         PASS
```

The would-signal report shows:

```text
Would-signal rows:    10
Setup clusters:       10
Directions observed:  LONG and SHORT
Observers observed:   breakout_retest and swing_breakout_retest_v0
All permission false: true
All dry-run:          true
```

This is a healthy Phase 1 observation state.

### 8.3 Phase 1 Acceptance Is Not Complete

The current Phase 1 acceptance report remains:

```text
Overall status: PENDING
```

Current soak evidence:

```text
Decision rows:              56
Observed unique-bar span:   0.41 calendar days
Soak progress:              8.26%
Unique run IDs:             5
```

This is not enough.

---

## 9. Soak Gate Review

Third-party Review #4 correctly identifies a weakness: cumulative row count is not the right primary soak metric.

A soak is supposed to prove:

```text
continuous runtime stability
no memory/resource drift
no crash/restart loops
no silent telemetry death
no schema/log corruption over uninterrupted wall-clock time
```

Repeated short bursts cannot prove this.

### Required Change

Add these fields to `PHASE1_STATUS_SUMMARY.json`:

```json
{
  "soak": {
    "observed_days": 0.4132,
    "progress_pct": 8.26,
    "required_days": 5,
    "current_streak_hours": 0,
    "longest_streak_hours": 0,
    "required_uninterrupted_streak_hours": 72,
    "restart_count_during_current_streak": 0,
    "last_restart_utc": "...",
    "uninterrupted_soak_pass": false
  }
}
```

Phase 1 acceptance should require:

```text
cumulative five-trading-day soak target met
AND
soak_longest_streak_hours >= 72
AND
no dry-run / permission / schema / server-time violations during the streak
```

The 72-hour sub-gate should reset on:

```text
EA restart
MT5 restart
terminal process restart
machine reboot
schema reset
manual log reset
```

Weekend market breaks can pause market-bar growth, but they should not falsely count as active market soak.

---

## 10. Phase 2 Readiness Review

The current Phase 2 readiness report says:

```text
Overall status: PENDING
Phase 2 preparation may continue, but implementation is not authorized yet.
```

Pending gates include:

```text
VPS selection
measured cost model
measured-cost revalidation
Phase 1 acceptance
Phase 1 review index
five-trading-day soak
project owner approval
```

This is correct.

### Phase 2 Preparation Allowed

The team may continue preparing:

```text
paper ledger schema
cost measurement protocol
operations prep
external health monitor design
DR runbook
VPS selection matrix
owner approval template
status dashboard
```

### Phase 2 Implementation Not Allowed

Do not implement:

```text
paper fill bridge
broker-side execution hooks
OrderSend
OrderSendAsync
CTrade
trade.Buy
trade.Sell
PositionOpen
PositionModify
PositionClose
live order handling
```

Phase 2 paper mode should not start until all objective gates pass.

---

## 11. Hypothesis-Authoring Space Review

Review #4 correctly noted that the candidate-authoring space is still biased toward intraday mechanics.

The current backlog has added slow-reference candidates such as:

```text
daily_pivot_reclaim_v0
weekly_level_reclaim_v0
```

But both still use M5 entries. They test higher-level references, not truly higher-timeframe operating logic.

So the H4/D1 gap is only partially addressed.

### Required Next Research Addition

Add at least one candidate that truly operates on H4/D1 timing, for example:

```text
H4 breakout retest after D1 close confirmation
D1 multi-day momentum continuation with H4 pullback entry
D1 weekly pivot reclaim with H4 confirmation
10-day breakout with H4 retest filter
D1 failed range expansion reversal
```

Add a visible metric to `agent.md`:

```yaml
hypothesis_timeframe_coverage:
  M5_M15: <count>
  M30_H1: <count>
  H4_D1: <count>
  W1_plus: <count>
```

Important: classify by **entry/decision timeframe**, not merely by the level source. A weekly level with M5 entries still belongs mostly to the intraday execution family.

---

## 12. Sequential Testing / Candidate-Count Risk

The candidate universe is expanding. The Reality Check still passes, but p-values get more fragile as the universe grows.

Add this rule to `HYPOTHESIS_LOCKING.md` or `NO_TUNING_RULES.md`:

```text
If the non-empty matrix-ledger candidate universe reaches 30 candidates,
then Reality Check / SPA must clear alpha = 0.01 for Phase 2 authorization to remain valid.
```

Also add:

```text
Every new candidate that enters the matrix ledger must be counted in future D2 Reality Check runs.
Rejected candidates remain in the Reality Check universe unless there is a documented data-quality reason to exclude them.
```

This avoids an implicit sequential-test problem.

---

## 13. Documentation Consistency Issues

The repo is largely consistent, but a few documents need synchronization.

### 13.1 Phase 2 Authorization Checklist Has Stale Counts

The current checklist mentions older counts such as:

```text
19 non-empty matrix-ledger candidates
18 rejected/research candidates
```

Current repo artifacts show:

```text
Reality Check universe:       27 non-empty matrix-ledger candidates, per agent.md
Rejection audit:              28 audited candidates, 26 rejected/research candidates
Status dashboard:             2 accepted, 3 provisional, 23 rejected
```

Update the checklist so it reflects current reports.

### 13.2 Cost Threshold Documents Must Match

If the team raises the threshold to +0.15R, update all of:

```text
PHASE2_COST_MEASUREMENT_PROTOCOL.md
PHASE2_SINGLE_EDGE_RISK_PLAN.md
PHASE2_AUTHORIZATION_CHECKLIST.md
status.html generator text
agent.md
```

If the team keeps +0.10R, add a formal MDE justification file and cross-link it.

Suggested file:

```text
xau-usd/xauusd-phase1/docs/PHASE2_COST_THRESHOLD_JUSTIFICATION.md
```

---

## 14. Required Actions Before Review #5

### Must complete before Phase 1 acceptance

```text
1. Implement uninterrupted soak tracking.
2. Add soak_longest_streak_hours and current_streak_hours to PHASE1_STATUS_SUMMARY.json.
3. Require >=72h uninterrupted runtime plus cumulative five-trading-day soak.
4. Continue dry-run with trade_permission=false.
5. Regenerate PHASE1_ACCEPTANCE_REPORT.md.
6. Regenerate PHASE1_REVIEW_INDEX.md.
7. Keep status.html updated.
```

### Must complete before Phase 2 paper-mode authorization

```text
1. Complete 5 observed days of passive spread logging.
2. Regenerate MEASURED_COST_MODEL.md as PASS.
3. Regenerate BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md as PASS.
4. Resolve measured spread scale vs configured spread scale.
5. Raise net expectancy floor to +0.15R or defend +0.10R numerically.
6. Make breakout_retest the only execution-eligible Phase 2 paper expert.
7. Keep swing_breakout_retest_v0 observer-only.
8. Add candidate-count Reality Check ceiling rule.
9. Add true H4/D1 hypothesis to backlog.
10. Complete VPS selection matrix.
11. Produce owner approval only after all objective gates pass.
```

### Must never happen in this phase

```text
No live orders.
No broker execution.
No OrderSend.
No CTrade.
No position modification.
No live expert activation.
No compounding.
No treating same-family variants as diversification.
No tuning rejected candidates in place.
```

---

## 15. Final Go / No-Go Table

| Area | Verdict |
|---|---|
| Phase 0 closure for `breakout_retest` | GO / PASS |
| `trend_pullback` | REJECTED |
| `range_mr` | REJECTED |
| `swing_breakout_retest_v0` | Same-family candidate only |
| Round-number retest variants | Provisional; Gate 9 pending |
| Phase 1 dry-run continuation | GO |
| Phase 1 final acceptance | NO-GO until soak complete |
| Phase 2 documentation/prep | GO |
| Phase 2 paper-mode implementation | NO-GO |
| Broker-side execution | NO-GO |
| Live trading | ABSOLUTE NO-GO |

---

## 16. Final Review Statement

The repo is now mature enough that the main risk is not architecture or discipline. The main risk is empirical:

```text
Can a high-frequency breakout-retest edge survive actual measured XAUUSD spread/slippage costs?
```

The answer is not known yet.

The project should continue exactly as follows:

```text
1. Keep Phase 1 running in dry-run mode.
2. Add uninterrupted 72h soak tracking.
3. Complete the five-trading-day soak.
4. Finish 5-day measured cost collection.
5. Revalidate breakout_retest under measured median/P95 costs.
6. Tighten or mathematically defend the Phase 2 cost survival threshold.
7. Only then consider Phase 2 paper-mode implementation.
```

My final verdict:

```text
Approved to continue Phase 1 dry-run.
Approved to continue Phase 2 preparation.
Not approved to start Phase 2 paper-mode implementation.
Not approved for any broker-side trading behavior.
```

The team is doing the right thing. The next evidence must come from uninterrupted runtime and measured cost, not from more planning or more backtest variants.

---

## 17. Source References

Reviewed repository artifacts and third-party review notes included:

- Root README: `https://raw.githubusercontent.com/maksoftwares/algo-trading-system/main/README.md`
- Agent handoff: `https://raw.githubusercontent.com/maksoftwares/algo-trading-system/main/agent.md`
- Status dashboard: `https://raw.githubusercontent.com/maksoftwares/algo-trading-system/main/status.html`
- Phase 0 verdict: `xau-usd/xauusd-phase0/outputs/reports/PHASE0_VERDICT.md`
- Breakout Retest Phase 0 results: `xau-usd/xauusd-phase0/outputs/reports/phase0_breakout_retest_results.md`
- Fixed-notional report: `xau-usd/xauusd-phase0/outputs/reports/FIXED_NOTIONAL_REPORT.md`
- Measured cost model: `xau-usd/xauusd-phase0/outputs/reports/MEASURED_COST_MODEL.md`
- Reality Check report: `xau-usd/xauusd-phase0/outputs/reports/PHASE0_REALITY_CHECK.md`
- Rejected candidate audit: `xau-usd/xauusd-phase0/outputs/reports/PHASE0_REJECTED_CANDIDATE_GATE_AUDIT.md`
- Phase 1 status summary: `xau-usd/xauusd-phase1/outputs/reports/PHASE1_STATUS_SUMMARY.json`
- Phase 1 acceptance report: `xau-usd/xauusd-phase1/outputs/reports/PHASE1_ACCEPTANCE_REPORT.md`
- Phase 2 readiness report: `xau-usd/xauusd-phase1/outputs/reports/PHASE2_READINESS_REPORT.md`
- Phase 2 cost protocol: `xau-usd/xauusd-phase1/docs/PHASE2_COST_MEASUREMENT_PROTOCOL.md`
- Phase 2 authorization checklist: `xau-usd/xauusd-phase1/docs/PHASE2_AUTHORIZATION_CHECKLIST.md`
- Candidate research backlog: `xau-usd/xauusd-phase0/docs/CANDIDATE_RESEARCH_BACKLOG.md`
- Third-party Review #4: uploaded `REPO_REVIEW_4_FINDINGS.md`
