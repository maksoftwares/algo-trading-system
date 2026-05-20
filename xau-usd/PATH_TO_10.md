# XAUUSD Master EA Plan — Path From 6.5 / 10 to 10 / 10

**Reviewed plan:** `xauusd_master_ea_plan_v0_2_review_ready.md`
**Current rating:** 6.5 / 10 ex-ante
**Realistic ceiling:** 9.5 / 10 ex-ante; 10 / 10 only achievable post-hoc after 6+ months live data confirms edge survival
**Date:** 2026-05-20

---

## 0. Honest Framing

A 10/10 plan does not exist *ex-ante* in retail algorithmic trading.

Even institutional quant teams with research budgets and PhD staff rate their own plans at 7–8 *before* live data validates them. The "last 1–2 points" of any algo plan are answered by markets, not by documents.

What 10/10 means in practice: every known failure mode is addressed at the planning and validation stage so that any subsequent failure is attributable to **market regime change or counterparty risk** — not to anything controllable.

This document maps the gap from the current v0.2 plan (6.5/10) to a realistic ex-ante ceiling of 9.5/10, with the final 0.5 earned only by live performance.

---

## 1. Composite Rating Path

| Stage | Action category | Rating after |
|---|---|---:|
| Current state | v0.2 plan as written | 6.5 |
| + Phase 0 edge validation | Category A (A1–A5) | 8.0 |
| + Calibrated cost model | Category B (B1–B4) | 8.6 |
| + Operational maturity | Category C (C1–C5) | 9.0 |
| + Validation rigor | Category D (D1–D4) | 9.25 |
| + Long-term survival design | Category E (E1–E4) | 9.4 |
| + Plan-quality tightening | Category F (F1–F10) | **9.5** |
| + Live data proves edge for 6+ months | Post-hoc only | **10.0** |

---

## 2. Category A — Edge Validation (+2.0 points, biggest gap)

The three v1 experts — Trend Pullback, Breakout-Retest, Range MR — are currently described as **categories**, not **validated behaviors**. The v0.2 plan requires an Edge Thesis Document but does not require evidence the edge exists. This is the single largest threat.

### A1. Phase 0 Statistical Study

Before any expert is coded, each candidate behavior must pass a 9-cell test matrix:

| Dimension | Cells |
|---|---|
| Time windows | 2016–2018, 2019–2021, 2022–2024 |
| Tick sources | Capital.com, Pepperstone, Dukascopy |
| Cost assumptions | Best-case spread, median spread, P95 spread |

For each of the 9 combinations, record: trade count, cost-adjusted PF, total return, worst month, max DD, losing-month percentage, max consecutive zero-trade months.

**Acceptance:** Behavior passes only if **7 of 9 cells** show positive cost-adjusted expectancy with PF ≥ 1.30 at minimum. If 3+ cells fail, the behavior is regime-dependent or non-existent — reject and try the next candidate.

This is the single most valuable thing missing from the plan. See `PHASE0_STATISTICAL_STUDY_SPEC.md` for the full executable specification.

### A2. Pre-Registered Hypothesis

Before each backtest, write down on paper (and commit to file):
- Expected trade count: X ± 20%
- Expected PF: Y ± 0.3
- Expected losing-month %: Z ± 10%
- Expected worst single month: −$N
- Expected max consecutive zero-trade months

If actual results are **wildly better than predicted**, that's a curve-fit warning — you tuned. If wildly worse, the edge doesn't exist. Only matches within band count as evidence.

This converts "the backtest looks great" into a falsifiable claim. Without pre-registration, every backtest can be retroactively rationalized.

### A3. Edge Persistence (Decile) Test

Sort backtest period into 10 equal-time deciles. Run the expert on each decile independently with locked parameters. If PF varies more than 2× across deciles, the edge is regime-dependent (acceptable but flagged in router design); if half the deciles show PF < 1.0, the edge is fragile and should be rejected.

**Acceptance:** PF > 1.0 in at least **8 of 10 deciles**, no single decile > 2× the median PF.

### A4. Adversarial Counter-Example Search

Spend one full working day actively trying to break each expert.

- For Range MR: hand-collect every historical instance where a "valid range" was followed by an immediate breakout within K bars after entry. Count them. If they're > 25% of trades, the range gate is broken.
- For Breakout-Retest: hand-collect every historical instance where a retest "held" then failed within 24 hours. Count them.
- For Trend Pullback: hand-collect every "pullback in trend" that was actually the start of a trend reversal.

The expert must either filter these out mechanically or explicitly accept the failure rate.

### A5. Multi-Symbol Consistency Check

If "trend pullbacks have positive expectancy" is a real behavior, it should be at least **directionally positive** on EURUSD and USDJPY too. If the edge ONLY works on XAU, that is a red flag for over-fit unless you can identify a XAU-specific reason (e.g., London Fix window).

**Acceptance:** PF ≥ 0.9 on EURUSD and USDJPY with same logic, OR explicit XAU-specific mechanism documented and defended.

---

## 3. Category B — Cost Model Realism (+1.0 point)

The cost model is documented but not yet calibrated against measured data.

### B1. Passive 4-Week Spread Logger

Before any backtest gate is run, deploy a passive spread logger on Capital.com-Demo for 4 weeks and produce:
- Median spread by hour-of-day (24 buckets)
- Median spread by day-of-week (5 buckets)
- Spread distribution during rollover (22:00 server time ± 30 min)
- Spread distribution within ±10 min of red-folder USD news
- Maximum observed spread per session

Every approval gate then runs against **measured P95 spread**, not a planning estimate. The output is `cost_model_measured.csv`, signed and dated, that replaces the cost assumptions in §5.4 of the plan.

### B2. Worst-Case Cost Gating

Approval gates must pass at **P95 cost**, not median. An expert profitable at median spread but unprofitable at P95 will die during any bad week. The hard gate in §23 must use P95 as the cost reference.

### B3. Multi-Broker Cost Scenarios

Even though Capital.com is the planned demo broker, model the plan against:
- +$3/lot commission (typical raw-spread account)
- +$7/lot commission (institutional cost)
- Capital.com's documented spread + zero commission

If the expert only passes at zero commission, it cannot survive a broker move. Document the cost-floor at which the expert fails.

### B4. Slippage Model From Live Execution

After Phase 8 (demo forward test), measure actual slippage on real fills and **re-run all backtest gates against measured slippage**. If the expert's PF drops below the §23 threshold under real slippage, the expert is rejected — backtest passes do not grandfather an expert past live evidence.

---

## 4. Category C — Operational Maturity (+0.75 points)

The plan covers the EA itself but not the operating environment.

### C1. CI/CD Discipline

- Git repository with branches: `develop` / `release-candidate` / `production`
- `release_check.ps1` script that refuses to enable live trading unless ALL of:
  - Unit tests pass
  - Snapshot bundle exists for current commit hash
  - `magic_numbers.md` validated against deployed accounts
  - Edge Thesis Document signed off (date, version)
  - Walk-forward report exists with all-folds-pass status
- No human can flip `EnableLiveTrading = true` without the script's approval

### C2. VPS Hardening Specification

Documented in `vps_plan.md`:
- Provider chosen (Beeks, ForexVPS, AWS — with reasoning)
- OS, MT5 install method, terminal version pinned
- Auto-restart policy on EA crash
- 2-factor auth on broker login
- Network monitoring with alert if connection drops > 5 min
- State snapshot of EA-managed positions hourly so a VPS death does not require manual reconstruction

### C3. External Health Monitor

A **separate process on a different host** (not the EA itself — it cannot monitor its own death) that pings the EA every 5 min and alerts via SMS/email if:
- No heartbeat for > 10 min
- Abnormal log activity spike
- Margin warning
- Broker connection lost
- EA in unexpected state (e.g., DRY_RUN unexpectedly disabled)

### C4. Disaster Recovery Runbook

Documented procedures in `dr_runbook.md`:
- VPS dies mid-trade → how to close positions manually from a phone
- Capital.com demo/live account closed → backup broker plan
- MT5 itself crashes → reinstall + state recovery procedure
- All EA-managed positions need emergency exit → manual close procedure with magic-number list

### C5. Account Isolation

**Dedicated trading account** for the new EA. Not shared with V85, not shared with manual trading, not shared with any other automation — even in dry-run. This eliminates an entire class of position-confusion bugs.

---

## 5. Category D — Validation Rigor (+0.5 points)

Walk-forward is good but not best-in-class.

### D1. Combinatorial Purged Cross-Validation (CPCV)

Beyond anchored walk-forward, run CPCV (López de Prado, 2018, *Advances in Financial Machine Learning*). Tests multiple non-overlapping permutations of train/test splits with a purge buffer to prevent leakage. Implementation: Python `mlfinlab` or equivalent.

Acceptance: median holdout PF / median train PF ≥ 0.70 across all CPCV splits.

### D2. Formal Data-Mining Bias Test

Apply **White's Reality Check** or **Hansen's Superior Predictive Ability (SPA) test** — formal statistical tests for whether observed performance is distinguishable from data mining noise. Standard tools in quant lit, rarely applied in retail.

Acceptance: p-value < 0.05 against the null hypothesis that the strategy is data-mining noise.

### D3. Held-Out True Holdout

Beyond train/walk-forward holdout, **set aside 6 months of recent data the team commits to never touch during development.** Only opened at the final pre-live approval review. If results materially degrade on this set, the expert fails.

Suggested set: most recent 6 months prior to final review date.

### D4. Independent Reproduction

A person NOT on the build team replicates the backtest from the spec alone. If they cannot reproduce within 5% of stated metrics, the spec is incomplete (or the original result was over-fit through undocumented implementation details).

This is the single hardest item to arrange but the most valuable check against self-deception.

---

## 6. Category E — Long-Term Survival (+0.5 points)

The plan covers v1 launch but not multi-year operation.

### E1. Pre-Committed Quarterly Review

Calendar dates committed in `review_calendar.md` for: P&L vs expectation, drift metrics, parameter stability check, regime-classification accuracy.

Decisions are **pre-committed**, not negotiated ad-hoc:
- "If 90-day rolling PF drops below 1.1, expert is suspended"
- "If 90-day losing-month % exceeds 50%, expert is suspended"
- "If holdout PF / train PF degrades below 0.5, expert is retired"

Pre-commitment prevents post-hoc rationalization during live drawdowns.

### E2. Strategy Decay Acknowledgement

Retail edges decay over 6–24 months typically. Plan must acknowledge this with:
- A "next expert" research pipeline running **concurrently** with live v1
- Trigger conditions for when to retire v1 experts even if still marginally profitable
- Allocated time budget for v2 development before v1 starts decaying

### E3. Capital Allocation Ladder

Defined graduation rules for live pilot in `capital_ladder.md`:

| Phase | Months | Risk per trade | Lot size cap |
|---|---|---:|---|
| Pilot | 1–3 | 0.25% | Minimum |
| Probation | 4–6 | 0.50% | 2× minimum |
| Production | 7–12 | Target risk | 5× minimum |
| Scale | 13+ | Target risk | Target |

With explicit scale-down triggers at each step.

### E4. Accounting and Tax Infrastructure

At small scale this seems irrelevant; at meaningful scale it isn't. Documented approach to: P&L tracking outside MT5, broker statement reconciliation, jurisdiction-specific tax treatment of FX/CFD gains.

---

## 7. Category F — Plan-Quality Tightening (+0.5 points)

Smaller items that push plan-quality from 8.5 to 9:

| # | Change | Rationale |
|---|---|---|
| F1 | Pick single risk-per-trade value (0.25% OR 0.50%), not range | Range is a tuning knob |
| F2 | Walk-forward initial train **24–36 months**, not 18 | XAU multi-year regime shifts |
| F3 | Tighten holdout/train PF gate to **≥ 0.80** (currently 0.70) | More margin against drift |
| F4 | Single-engine concentration **≤ 35%** (currently 40%) | True 3-way diversification |
| F5 | Single-month contribution **≤ 25%** (currently 30%) | Reduce lumpy-month risk |
| F6 | Define "stable" for live pilot: ≥30 trades over ≥3 months, PF within ±20% of band | Removes ambiguity |
| F7 | All timestamps logged in **broker time + UTC + local** | Eliminates timezone debugging hell |
| F8 | Resolve Asia trading explicitly (§9.4) — yes/no, not router-discretion | Closes a curve-fit pathway |
| F9 | Define "portfolio backtest" (§7) — router-switching aggregate | Removes ambiguity in test interpretation |
| F10 | Symbol-rename / contract-change recovery procedure | Currently aborts, should also notify and document recovery |

---

## 8. Category G — Outside the Plan's Control (the residual 0.5)

These are why even a perfect plan stops at ~9.5/10 ex-ante:

| Risk | Mitigation possible? | Notes |
|---|---|---|
| Future XAU regime shift (2027+ unlike 2020–2025) | Partial | Drift monitor catches it, doesn't prevent it |
| Broker counterparty risk (account freeze, term changes) | Partial | Multi-broker readiness reduces blast radius |
| Black swan event (central bank intervention, futures halt) | Partial | Risk caps contain damage, can't prevent event |
| Fixed-cost burden at small scale | Mitigated by scale | VPS + subscription costs need ~$5k/mo P&L to be net-positive |
| Personal bandwidth (5+ year commitment) | Real risk | Algo work decays without active maintenance |
| Tax / regulatory changes | Real risk | Outside operator control |

---

## 9. Priority Matrix: Highest Asymmetric Value

If you cannot do everything above, these five items provide the largest rating gain per unit of cost/time:

| Priority | Item | Cost | Estimated rating gain |
|---|---|---|---:|
| **#1** | A1 — Phase 0 statistical study | 2–4 weeks of analysis | +1.5 |
| **#2** | B1 — 4-week passive spread logger | Trivial code, 4 weeks wall-clock | +0.5 |
| **#3** | D3 — True holdout never touched | Free, requires discipline | +0.3 |
| **#4** | C3 — External health monitor | Few hundred USD, 1 day to build | +0.2 |
| **#5** | F1–F10 — Plan tightening | Free, requires decisions | +0.5 |

**Total from top 5: +3.0 points → 9.5 / 10** (which is the realistic ex-ante ceiling).

The remaining items add operational and validation depth but with diminishing marginal returns. Do them if resources permit, but the top 5 are the difference between "good" and "very good."

---

## 10. The Brutal Summary

**The plan as written (v0.2) is 6.5 / 10.** Top-decile for retail algo planning.

**With items A1, B1, D3, C3, and F1–F10:** 9.5 / 10 ex-ante. This is the realistic ceiling without institutional resources.

**With all 33 items in this document:** still 9.5 / 10 ex-ante. The last 0.5 cannot be planned.

**The last 0.5 is earned by:** the system running live for 6+ months with PF and drawdown metrics inside the pre-registered band, with at least one full regime change observed. That's the only path to 10/10, and it cannot be accelerated.

**The brutal truth:** the v0.2 plan is now good enough to start building. Every additional planning iteration past this point has diminishing returns. The highest-leverage next step is **doing the Phase 0 statistical study** (Category A) — because if the edge doesn't survive Phase 0, no amount of planning rigor will save the build. Better to discover that in 4 weeks of statistical work than 12 months of coding.

---

## 11. Recommended Next Action

In order of priority:

1. **Execute `PHASE0_STATISTICAL_STUDY_SPEC.md`** — 4 weeks of focused analysis to confirm or reject the edge thesis for each of the three v1 expert candidates.
2. **Run the 4-week passive spread logger in parallel** — costs nothing, calibrates the cost model.
3. **Make the F1–F10 plan-tightening decisions** — free, immediate.
4. **Begin Phase 1 (Master EA dry-run shell) only if** Phase 0 confirms at least one expert's edge survives.
5. **Defer Categories C, D, E** until Phase 0 + Milestone 1 are complete. Operational maturity, advanced validation, and long-term survival design are worth doing — but only for a system that has cleared the edge-validation bar.

If Phase 0 fails for all three candidates, the most valuable thing the plan can do is **not be built** until a defensible edge candidate is found. That is the most disciplined possible outcome and is far better than building a beautiful system around a non-existent edge.
