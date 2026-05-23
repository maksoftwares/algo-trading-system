# Final Repository Review After Review #6

**Project:** `maksoftwares/algo-trading-system`  
**Review date:** 2026-05-23  
**Prepared for:** XAUUSD Master EA governance / Phase 1–2 readiness  
**Scope:** Static review of latest public GitHub artifacts plus third-party `REPO_REVIEW_6_FINDINGS.md`.  
**Review mode:** Static artifact review only. I did not clone the repository or run the code locally.

---

## 1. Executive Verdict

```text
Continue Phase 1 dry-run:                    GO
Continue Phase 2 documentation/preparation:  GO
Authorize Phase 2 paper-mode implementation: NO-GO
Authorize broker-side execution:             NO-GO
Authorize live trading:                      ABSOLUTE NO-GO
```

The repository has improved again. The latest third-party Review #6 rates the project **9.0 / 10**, up from 8.75, and the review confirms the team addressed every actionable Review #5 item in one commit. The strongest improvements are:

```text
1. 72-hour uninterrupted soak gate implemented.
2. Cost-survival floor raised from +0.10R to +0.15R.
3. Hypothesis template now enforces timeframe/hold-time attribution.
4. H4/D1 non-level candidates were authored, hash-locked, tested, and rejected.
5. Paper-mode execution remains restricted to one execution-eligible stream: breakout_retest.
6. D2 Reality Check was rerun on fixed-notional monthly R-series and became materially stronger.
```

However, the repo is still **not ready for Phase 2 paper-mode implementation**. The remaining blockers are empirical and operational, not planning-related:

```text
1. Measured cost model is still PENDING: only 2 observed days, 5 required.
2. Breakout-retest measured-cost revalidation is still PENDING.
3. Phase 1 acceptance is still PENDING.
4. 72-hour uninterrupted active-market streak is still PENDING.
5. Five-trading-day cumulative soak is still PENDING.
6. VPS selection is still PENDING.
7. Owner approval is still PENDING.
8. Low-frequency concentration-gate calibration is now an open validation question.
9. Weekend handling for the 72-hour streak must be clarified.
10. R-series Reality Check should be declared canonical.
```

Final decision:

```text
The team may continue Phase 1 dry-run and Phase 2 preparation.
The team may not start Phase 2 paper-mode execution.
The team may not add broker-side trading behavior.
```

---

## 2. Current Rating

My rating after reviewing the latest repo and Review #6:

```text
Repo/process quality:          9.0 / 10
Phase 0 evidence discipline:   9.0 / 10
Phase 1 dry-run discipline:    9.0 / 10
Phase 1 final acceptance:      PENDING
Phase 2 paper-mode readiness:  NOT YET
Live-trading readiness:        NO
```

Review #6's 9.0 / 10 rating is fair. I would not raise it above 9.0 yet because the project has now hit the limit of what process and documentation can prove. The remaining proof must come from:

```text
1. measured cost data,
2. uninterrupted runtime evidence,
3. a resolved concentration-gate calibration question,
4. and eventually paper-mode / live evidence.
```

---

## 3. What Is Approved

### 3.1 Phase 0 closure for `breakout_retest`

The repo continues to show `breakout_retest` as the approved Phase 0 edge. The root README says Phase 0 has closed with `breakout_retest` passing matrix, decile, multisymbol, hash, and Gate 9 manual adversarial gates. It also says `trend_pullback` and `range_mr` remain rejected.

Approved future expert family:

```text
breakout_retest
```

Same-family future candidate, observer-only / not diversification:

```text
swing_breakout_retest_v0
```

Rejected v1 candidates:

```text
trend_pullback
range_mr
```

Do not re-enable rejected candidates under the same version. Any revisit must be a new hypothesis version with a new lock and fresh Phase 0 process.

---

### 3.2 Phase 1 dry-run shell remains correctly scoped

The current repo says the active phase is:

```text
Phase 1 — Master EA dry-run shell
```

The dry-run shell is still passive:

```text
dry_run = true
trade_permission = false
server_time_status = CLOCK_OK
```

The current Phase 1 status summary shows:

```text
decision_rows: 56
unique_run_ids: 5
observed_days: 0.4132
soak_progress: 8.26%
current_streak_hours: 0.0
longest_streak_hours: 2.25
required_uninterrupted_streak_hours: 72.0
acceptance: PENDING
log_verification: PASS
runtime_health: PASS
soak_analysis: PASS
would_signal: PASS
```

This is healthy for continuing dry-run. It is not enough for Phase 1 final acceptance.

---

### 3.3 The +0.15R cost-survival floor is now implemented

The Phase 2 cost protocol now states:

```text
MIN_NET_EXPECTANCY_R_AFTER_MEASURED_COST = +0.15R
```

and the decision rule is:

```text
IF measured paper/live execution cost pushes breakout_retest family net expectancy below +0.15R
THEN suspend the breakout-retest family and return to research.
```

This fully closes the earlier concern that +0.10R was too soft. The +0.15R threshold is the right hard floor for Phase 2 continuation. I would also keep +0.20R as the preferred target, but +0.15R is a reasonable minimum.

---

### 3.4 Fixed-notional R-series Reality Check is stronger and should become canonical

The latest Reality Check report uses monthly fixed-notional R returns, not compounding-dollar returns. This removes leverage-scaling distortion from the bootstrap. It reports:

```text
Status: PASS
Winner: breakout_retest
White Reality Check p: 0.0002
Max SPA-style p: 0.0188
Bootstrap iterations: 5000
Candidate universe: 29 non-empty matrix-ledger candidates
```

This is a materially stronger result than earlier percent-return versions. Going forward, the **R-series Reality Check should be the canonical D2 methodology**. Percent-return D2 outputs should be marked as superseded or secondary to avoid cherry-picking whichever p-value looks better.

---

### 3.5 Timeframe attribution discipline has improved

The hypothesis template now requires:

```text
Mechanic family
Entry / decision timeframe
Expected median hold bars M5-equivalent
Expected median hold hours
Expected decisions per week
Timeframe diversification qualifies: yes/no
```

It also states that a D1/W1/prior-session reference level with M5 entries does **not** qualify as timeframe diversification.

This is important because it prevents the team from claiming diversification merely because a fast M5 strategy references a slow level.

---

### 3.6 H4/D1 diversification attempts were made honestly

Two genuine H4/D1-decision-timeframe candidates were authored, hash-locked, implemented, and tested:

```text
d1_momentum_h4_pullback_v0
d1_volatility_expansion_reversal_v0
```

Both were rejected. This is not a failure of discipline; it is exactly what the process should do. The candidate backlog now lists the next planned non-level H4/D1 candidate:

```text
d1_compression_h4_expansion_v0
```

Current timeframe coverage from the backlog:

```yaml
M5_M15: 28
M30_H1: 0
H4_D1: 2
W1_plus: 0
planned_next_H4_D1: d1_compression_h4_expansion_v0
```

This confirms that the project is now testing in the right direction, but it still has not found a true independent non-level edge.

---

## 4. What Is Not Approved

### 4.1 Phase 1 final acceptance is not approved

The Phase 1 acceptance report remains:

```text
Overall status: PENDING
```

The current blockers are:

```text
1. Uninterrupted 72-hour soak: PENDING
   - longest active streak: 2.25h
   - current active streak: 0.0h
   - required: 72h

2. Five trading day soak: PENDING
   - observed unique-bar span: 0.41 calendar day
   - required: 5 trading days

3. Runtime freshness: WARN
   - latest row age is high because the market is paused/weekend-state.

4. Soak history ledger: WARN
   - historical progress decreased between rows.
```

The dry-run shell is behaving safely, but the soak evidence is still incomplete.

---

### 4.2 Phase 2 paper-mode implementation is not approved

The Phase 2 readiness report remains:

```text
Overall status: PENDING
```

Pending gates include:

```text
VPS selection
measured cost model
measured-cost revalidation
Phase 1 acceptance
Phase 1 review index
five trading day soak
72-hour uninterrupted soak
project owner approval
```

The report explicitly states that it does not authorize Phase 2 implementation and that paper-mode implementation still requires all gates to pass.

---

### 4.3 Live trading remains completely blocked

No broker-side order behavior should be added yet.

Forbidden scope remains:

```text
OrderSend
OrderSendAsync
CTrade
trade.Buy
trade.Sell
PositionOpen
PositionModify
PositionClose
any broker-side execution bridge
any live position management
```

The project is not at execution stage. It is still in dry-run and evidence-collection stage.

---

## 5. Main Current Blockers

### Blocker 1 — Measured cost model is still pending

The measured cost report currently shows:

```text
Overall status: PENDING
observed rows: 9844
observed days: 2
required days: 5
median spread: 50 points
P95 spread: 75 points
max spread: 75 points
```

This is the single most important empirical blocker because `breakout_retest` is a high-frequency, cost-dominated strategy. The modeled baseline is:

```text
net expectancy: 0.1888R
mean all-in modeled cost: 0.3228R
gross expectancy estimate: 0.5115R
cost consumption: 63.09%
```

A strategy where costs consume ~63% of gross edge cannot be authorized for paper-mode until measured spread/slippage evidence is complete.

Required closure:

```text
MEASURED_COST_MODEL.md = PASS
observed_days >= 5
measured median/P95 cost applied
measured-cost revalidation generated
net expectancy after measured cost >= +0.15R
```

---

### Blocker 2 — Breakout-retest measured-cost revalidation is still pending

The measured-cost revalidation report currently says:

```text
Overall status: PENDING
Reason: measured cost model status is PENDING
```

This cannot pass until the measured cost model passes and `cost_model_measured.csv` is available.

Do not authorize Phase 2 until:

```text
BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md = PASS
net expectancy after measured cost >= +0.15R
```

---

### Blocker 3 — 72-hour uninterrupted soak is still far from passing

The current longest active streak is:

```text
2.25h / 72h
```

Review #6 correctly says the gate is implemented and wired correctly, but it is now the dominant blocker.

The current implementation resets the streak on:

```text
run_id change
bar gap > 15 minutes
dry-run violation
trade-permission violation
server-time violation
```

This is strict, which is good. But it creates a weekend-policy ambiguity.

---

### Blocker 4 — Weekend handling for the 72-hour streak is ambiguous

There is a documentation-versus-implementation mismatch:

```text
agent.md says weekend/offline resume gaps are tolerated by verifier/soak/runtime-health/external-health checks.
phase1_soak_streak.py currently resets on bar gaps > 15 minutes.
```

Because XAUUSD market closure over the weekend is normally far longer than 15 minutes, the current streak cannot survive a weekend. This is not necessarily wrong, but it must be made explicit.

Recommended resolution:

```text
Adopt a two-gate soak model:

Gate A — active-market decision streak:
    active_market_streak_hours >= 72
    Market-closed gaps may be excluded only if:
        no run_id change occurred,
        heartbeat/runtime monitor confirms the process remained alive,
        dry_run stayed true,
        trade_permission stayed false,
        server_time stayed CLOCK_OK or expected market-paused.

Gate B — calendar/process uptime streak:
    process_uptime_streak_hours >= 96
    This includes weekend and proves the EA/VPS can remain running without human touch.
```

At minimum, the repo must choose one policy:

```text
Option A: weekend gaps are excluded from active-market streak but require heartbeat continuity.
Option B: weekend gaps break the streak, requiring a clean Monday-Wednesday window.
```

My recommendation is Option A plus a separate calendar/process uptime gate. This avoids unfairly punishing expected market closure while still testing operational uptime.

---

### Blocker 5 — Concentration gate may be biased against low-frequency candidates

Review #6 raises a legitimate new concern: the current concentration gate may structurally disadvantage low-frequency strategies.

The rejected-candidate audit shows:

```text
audited candidates: 30
rejected/research candidates: 28
sample-size failures: 5
multi-cell expectancy failures: 25
frequency-only failures: 0
```

That proves candidates are not being rejected on frequency alone. But it does not prove low-frequency candidates are not being rejected through a concentration mechanism.

The clearest example is `d1_momentum_h4_pullback_v0`:

```text
PF range: 1.146–1.395
PF cells >= 1.30: 3/9
trades per cell: 69–80
max DD: clean
all cells positive return
failed concentration
```

This does not mean the candidate should pass. It means the gate needs a calibration audit.

Required action:

```text
Create a frequency-normalized concentration audit.
```

Suggested implementation:

```text
scripts/audit_concentration_frequency_normalized.py
outputs/reports/PHASE0_CONCENTRATION_FREQUENCY_NORMALIZED_AUDIT.md
```

For every concentration-failed candidate, compute both:

```text
absolute concentration:
    largest_trade_pct_of_pnl
    top5_trades_pct_of_pnl

frequency-normalized concentration:
    top_trade_R / (mean_abs_R * sqrt(n_trades))
    top5_trade_R_sum / (mean_abs_R * sqrt(n_trades))
```

Decision rule:

```text
If no rejected candidate flips under normalized concentration:
    keep existing gate and document that concentration failures were genuine.

If one or more H4/D1 candidates flip:
    do not auto-approve them;
    mark them for deeper review and consider separate LF-gate calibration.
```

Do not weaken the concentration gate for high-frequency strategies. This audit is about whether the same absolute-share gate is fair for low-frequency candidates.

---

## 6. Updated Go / No-Go Table

| Area | Verdict |
|---|---|
| Phase 0 closure for `breakout_retest` | PASS |
| `swing_breakout_retest_v0` | Same-family future candidate; observer-only |
| `round_number_retest_v0` | Provisional same-family; Gate 9 pending |
| `symbol_normalized_round_retest_v0` | Provisional same-family; Gate 9 pending |
| `session_extreme_retest_v0` | Provisional same-family; Gate 9 pending |
| Independent non-level H4/D1 expert | Not found yet |
| Phase 1 dry-run continuation | GO |
| Phase 1 final acceptance | PENDING |
| Phase 2 documentation/preparation | GO |
| Phase 2 paper-mode implementation | NO-GO |
| Paper broker bridge | NO-GO |
| Live trading | ABSOLUTE NO-GO |

---

## 7. Required Actions Before Next Review

### 7.1 Resolve weekend and code-freeze handling for the 72-hour streak

Add explicit fields to `PHASE1_STATUS_SUMMARY.json`:

```json
{
  "code_freeze_started_at": "",
  "code_freeze_hours": 0.0,
  "required_code_freeze_hours": 96.0,
  "weekend_policy": "active_market_excluded_with_heartbeat" or "weekend_breaks_streak",
  "active_market_streak_hours": 0.0,
  "process_uptime_streak_hours": 0.0
}
```

Also add a clear comment block in `phase1_soak_streak.py` explaining whether weekend gaps are included or excluded.

Acceptance:

```text
PHASE1_ACCEPTANCE_REPORT.md must show:
- active-market 72h streak PASS/PENDING
- process uptime/code-freeze PASS/PENDING
- restart count
- last restart UTC
- weekend policy
```

---

### 7.2 Run a code-freeze soak window

Because every code change/recompile/redeploy creates a new run and resets the streak, the team needs a freeze period.

Recommended rule:

```text
Start a 96-hour code-freeze window.
No recompiles.
No EA redeployments.
No schema changes.
No manual terminal restarts unless required for safety.
```

If a restart occurs:

```text
reset the 72-hour streak
record reason
restart the freeze window
```

---

### 7.3 Complete measured-cost evidence

Continue the isolated passive spread logger until at least 5 observed days are available.

Then regenerate:

```text
MEASURED_COST_MODEL.md
cost_model_measured.csv
BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md
PHASE2_READINESS_REPORT.md
status.html
```

Acceptance:

```text
Measured cost model = PASS
Measured-cost revalidation = PASS
Net expectancy after measured cost >= +0.15R
```

If measured net expectancy falls below +0.15R:

```text
suspend breakout-retest family
return to research
no Phase 2 paper-mode
```

---

### 7.4 Make R-series D2 canonical

Update:

```text
PHASE0_INDEPENDENT_VALIDATION.md
PHASE0_REALITY_CHECK.md
Reality Check manifest / summary
```

Required wording:

```text
The canonical D2 Reality Check / SPA methodology is fixed-notional monthly R-series.
Percent-return / compounding-return D2 outputs are superseded and retained only for historical reference.
```

This avoids p-value cherry-picking.

---

### 7.5 Add frequency-normalized concentration audit

Create a new report:

```text
PHASE0_CONCENTRATION_FREQUENCY_NORMALIZED_AUDIT.md
```

Minimum contents:

```text
1. All candidates that failed concentration.
2. Their min/median trades per cell.
3. Existing concentration failure values.
4. Frequency-normalized concentration scores.
5. Which candidates would remain rejected.
6. Which candidates would flip to review.
7. Final recommendation: keep gate / split HF-LF gates / document HF bias.
```

This report should not auto-rescue any candidate. It is a validation-rigor audit.

---

### 7.6 Plan at least three more non-level H4/D1 candidates

Review #6 correctly says two H4/D1 rejections are not enough to conclude that non-level edges do not exist.

Update `CANDIDATE_RESEARCH_BACKLOG.md` with at least three non-level H4/D1 candidates from different families.

Recommended candidates:

```text
1. d1_compression_h4_expansion_v0
   Family: volatility expansion
   Decision timeframe: D1/H4
   Expected hold: >24h
   Expected trades: <100/year

2. h4_real_yield_proxy_momentum_v0
   Family: intermarket / macro proxy
   Decision timeframe: H4/D1
   Expected hold: >24h
   Requires external/proxy data only if data contract is feasible.

3. d1_multi_day_exhaustion_reversion_v0
   Family: volatility / exhaustion
   Decision timeframe: D1/H4
   Expected hold: >24h
   No M5 entry trigger.
```

Only pre-register and run one at a time. Do not tune rejected versions.

---

### 7.7 Keep provisional same-family candidates out of execution

The backlog contains provisional same-family candidates with strong automated results but pending Gate 9:

```text
round_number_retest_v0
symbol_normalized_round_retest_v0
session_extreme_retest_v0
```

These must remain:

```text
research/provisional only
not execution eligible
not diversification
not part of Phase 2 first paper slice
```

Phase 2 first paper slice remains:

```text
breakout_retest only
```

---

## 8. Phase 1 Final Acceptance Gates

Phase 1 should be accepted only if all of the following pass:

```text
1. MT5 compile = PASS
2. source safety audit = PASS
3. no OrderSend / CTrade / trade.Buy / trade.Sell / PositionOpen exists
4. dry_run = true on every decision row
5. trade_permission = false on every decision row
6. server_time_status remains acceptable
7. decision log schema = PASS
8. startup/shutdown schema = PASS
9. runtime health = PASS
10. would-signal telemetry = PASS
11. risk-lock simulation coverage = PASS
12. active-market 72h streak = PASS
13. process/code-freeze uptime gate = PASS
14. cumulative five-trading-day soak = PASS
15. Phase 1 review index = PASS
16. Phase 1 acceptance report = PASS
17. owner approval = PASS
```

Current status:

```text
Phase 1 final acceptance = PENDING
```

---

## 9. Phase 2 Authorization Gates

Phase 2 paper-mode implementation is authorized only if all of the following are true:

```text
1. Phase 1 final acceptance = PASS
2. Phase 1 review index = PASS
3. Phase 2 readiness report = PASS
4. measured cost model = PASS
5. breakout-retest measured-cost revalidation = PASS
6. net expectancy after measured cost >= +0.15R
7. 72h active-market streak = PASS
8. code-freeze/process uptime gate = PASS
9. VPS selection = PASS
10. owner approval file exists
11. owner approval confirms minimum_net_expectancy_r >= 0.15
12. single-edge risk remains acknowledged
13. no compounding remains enforced
14. only breakout_retest is execution-eligible in first paper slice
15. same-family variants remain observer-only
16. provisional same-family candidates remain disabled
17. frequency-normalized concentration audit completed or explicitly deferred with owner sign-off
18. weekend policy documented
19. R-series D2 canonicalized
20. magic-number / identifier collision check complete
```

Current status:

```text
Phase 2 paper-mode implementation = NO-GO
```

---

## 10. Updated Risk Register

| Risk | Severity | Current control | Remaining action |
|---|---:|---|---|
| Real measured costs erase edge | Critical | passive spread logger, measured-cost gate, +0.15R floor | complete 5-day measured cost + revalidation |
| 72h soak not achieved | High | new streak tracker | define weekend policy, freeze code, complete streak |
| Weekend handling ambiguity | High | partial tolerance in runtime tools | document and implement consistent policy |
| Low-frequency candidates unfairly rejected by concentration | Medium/High | rejected-candidate audit | add frequency-normalized concentration audit |
| Single edge family carries system | High | single-edge risk plan | keep only breakout_retest paper-eligible; continue independent research |
| Data-mining risk from expanding candidates | Medium | R-series Reality Check, alpha-tightening rule | make R-series canonical |
| Provisional same-family candidates create false diversification | Medium | backlog labels | keep observer/research only |
| Operational restart risk | Medium | soak history, run_id tracking | enforce code-freeze window |
| Live execution creep | Critical | safety audits, dry-run shell | continue blocking broker-side action |

---

## 11. Final Recommendation

The latest push is a strong response to Review #5 and deserves the improved 9.0 / 10 process rating.

The team has now closed most controllable paperwork and implementation items:

```text
+0.15R floor implemented
72h streak gate implemented
H4/D1 hypothesis rules implemented
H4/D1 candidates tested honestly
D2 R-series Reality Check strengthened
single execution-eligible paper stream adopted
external reviews version-controlled
```

But the project is still not ready for Phase 2 because the remaining blockers are real:

```text
1. Measured cost still pending.
2. Measured-cost revalidation still pending.
3. 72h uninterrupted streak still pending.
4. Five-day soak still pending.
5. Weekend/code-freeze policy unresolved.
6. Low-frequency concentration calibration unresolved.
7. Owner approval pending.
```

Final verdict:

```text
Continue Phase 1 dry-run.
Continue Phase 2 preparation.
Do not start Phase 2 paper-mode implementation.
Do not add broker-side execution.
Do not trade live.
```

The next milestone is not more backtest work and not execution. The next milestone is:

```text
72h active-market dry-run streak
+
5-day measured cost model
+
measured-cost revalidation >= +0.15R
+
weekend/code-freeze policy clarified
+
concentration-frequency audit completed
+
Phase 2 readiness PASS
```

Only after those pass should the team request a Phase 2 paper-mode authorization review.

---

## 12. Source References Reviewed

Primary repo artifacts reviewed:

```text
README.md
agent.md
status.html
xau-usd/xauusd-phase1/outputs/reports/PHASE1_STATUS_SUMMARY.json
xau-usd/xauusd-phase1/outputs/reports/PHASE1_ACCEPTANCE_REPORT.md
xau-usd/xauusd-phase1/outputs/reports/PHASE2_READINESS_REPORT.md
xau-usd/xauusd-phase1/outputs/reports/PHASE1_SOAK_HISTORY_REPORT.md
xau-usd/xauusd-phase1/outputs/reports/PHASE1_REVIEW_INDEX.md
xau-usd/xauusd-phase1/docs/PHASE2_AUTHORIZATION_CHECKLIST.md
xau-usd/xauusd-phase1/docs/PHASE2_COST_MEASUREMENT_PROTOCOL.md
xau-usd/xauusd-phase1/scripts/phase1_soak_streak.py
xau-usd/xauusd-phase0/outputs/reports/MEASURED_COST_MODEL.md
xau-usd/xauusd-phase0/outputs/reports/BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md
xau-usd/xauusd-phase0/outputs/reports/PHASE0_REALITY_CHECK.md
xau-usd/xauusd-phase0/outputs/reports/PHASE0_REJECTED_CANDIDATE_GATE_AUDIT.md
xau-usd/xauusd-phase0/docs/HYPOTHESIS_TEMPLATE.md
xau-usd/xauusd-phase0/docs/CANDIDATE_RESEARCH_BACKLOG.md
```

Third-party review artifact reviewed:

```text
REPO_REVIEW_6_FINDINGS.md
```
