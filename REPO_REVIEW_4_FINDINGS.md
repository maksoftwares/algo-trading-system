# REPO_REVIEW_4_FINDINGS

**Reviewer:** Claude (independent technical reviewer)
**Date:** 2026-05-23
**Repo:** `maksoftwares/algo-trading-system` @ `main`
**Commits since Review #3:** 13 (53 → 66)
**Scope:** Verify resolution of Review #3 findings (V1/V2/F1/F2/F3 and §4 frequency-bias hypothesis); audit work shipped over the 24 h since Review #3.

---

## Headline

**Rating: 8.75 / 10** (Review #3 was 8.5).

The team closed **4 of the 6** open verification items from Review #3 in a single day — including building from scratch a new audit module (`phase0/rejection_audit.py`) specifically to falsify my own §4 frequency-bias hypothesis. They falsified it cleanly. That is mature, evidence-first engineering.

The composite moves up only +0.25 because the two load-bearing sub-scores — **Edge Defensibility (5.5)** and **Long-Term Survival Design (6.5)** — cannot move further without (a) measured cost data (wall-clock dependent) and (b) a genuinely non-breakout-family expert passing Phase 0 (research-time dependent). The team has done everything they can do in their direct control. The remaining gates are physics, not process.

Three **new** findings are introduced below (N1–N3), none of which are blockers, but all of which should be answered before Phase 2 paper-mode is authorized.

---

## What Closed Since Review #3

### V1 D2 against the full 18-candidate universe — **CLOSED**

The team re-ran the Reality Check across all 18 non-empty matrix-ledger candidates with 5000 bootstrap iterations and 3-month blocks. Each expert is collapsed to one monthly series so cost/broker cells do not become separately-optimized candidates (correct call).

| Metric | Review #3 (3 cand) | Review #4 (18 cand) | Δ |
|---|---:|---:|---:|
| White p | 0.0200 | 0.0200 | 0.000 |
| Max pairwise SPA p | 0.0234 | 0.0336 | +0.0102 |
| Iterations | 5000 | 5000 | — |

`breakout_retest` remained the family winner. **My stale-N concern is closed for the current universe.**

### §4 / V3 Rejected-candidate gate audit — **CLOSED, hypothesis falsified**

The team built `phase0/rejection_audit.py` + tests + a generated `PHASE0_REJECTED_CANDIDATE_GATE_AUDIT.{csv,md}` report. This was constructed specifically to test whether the Phase 0 gates structurally penalize low-frequency strategies.

Aggregated rejection reasons across the 17 rejected/research candidates:

| Gate | Failures | % of n=17 |
|---|---:|---:|
| concentration | 15 | 88% |
| multi_cell_survival | 13 | 76% |
| sample_size | 4 | 24% |
| activity (zero-trade months) | 4 | 24% |
| cost_sensitivity | 4 | 24% |

**Zero candidates were rejected on frequency-only grounds.** Multi-cell expectancy and concentration are doing the rejection work; sample size is co-incident, not causal. The §4 concern from Review #3 is properly retired.

I will note in N3 below that this audit tests the **gate behaviour**, not the **hypothesis-authoring space** — distinct concerns.

### F2 / V5 Same-family acknowledgement — **CLOSED as acknowledgement; not solved as risk**

`swing_breakout_retest_v0` is now formally classified as `APPROVED_FUTURE_EXPERT_CANDIDATE` **same-family**. The new `PHASE2_SINGLE_EDGE_RISK_PLAN.md`:

- Consolidates both variants as one correlated edge unit.
- Disables compounding through paper and any future micro pilot.
- Pre-commits: no portfolio-diversification uplift until a genuinely independent (non-breakout-family) expert passes Phase 0.
- Adds 7 review triggers (cost drift, frequency drift, rolling PF, drawdown bands, PnL concentration, execution degradation, out-of-hypothesis behaviour).

The `PHASE2_AUTHORIZATION_CHECKLIST.md` adds `Independent second candidate implementation — PENDING` as an explicit gate.

This is the correct response. The underlying risk (one edge family carrying all P&L) is unchanged, but the team has stopped pretending it is diversified. The mitigation set is among the more disciplined single-edge plans I've seen.

### Partial: V4 P95 cost sensitivity exposure — **STAGED**

Best/median/P95 cost cells are now exposed separately in the fixed-notional report. Final closure waits on measured P95 replacement — see V1 below.

---

## What Did NOT Close

### F3 / V1 The 0.3228R mean cost is still **assumed**, not measured

The MEASURED_COST_MODEL.md report has progressed from 4002 → 4326 observed rows, but agent.md confirms only **2 of the required 5 days** of passive spread-logger data exist. COST_REPORTING_POLICY.md correctly labels every current cost figure as **"assumed-cost baseline"**. The honest labelling is integrity — but the underlying answer (is the net edge real?) is still unresolved.

**This is the single most important unresolved question in the project.** The 0.1888R headline net expectancy is gross-minus-assumed-cost. Until 5 days of spread data + paper-mode realized cost are integrated, the entire net-edge claim is contingent.

Positive: the new `PHASE2_COST_MEASUREMENT_PROTOCOL.md` pre-commits a kill rule — if measured cost pushes net expectancy below **+0.10R**, the breakout-retest family is suspended and returned to research. See N2 for why I think that threshold is too soft.

### V6 Five-trading-day soak — **REGRESSED**

| Date | Decision rows | % of target | Note |
|---|---:|---:|---|
| 2026-05-22 (R#3) | 182 | 13.06% | — |
| 2026-05-23 mid | 43 | 2.5% | post-shutdown |
| 2026-05-23 late | 56 | 8.26% | post-resume |

The team shipped a "shutdown resume checkpoint" feature (commit `1059c58` / `8d30298`), which is good engineering, but it does not put hours on the clock. The cumulative-row metric is **not the right gate**. See N1 below.

---

## New Findings (N1–N3)

### N1 — Soak metric is the wrong gate. **(Operational)**

`% of decision rows collected` can be filled by repeated short bursts that do not prove what a 5-day soak is meant to prove: that the system survives **continuous, uninterrupted** wall-clock operation without leak, drift, or crash. A soak that resets every 12–24 hours never tests the failure modes the gate exists to catch.

**Recommend:** add a sub-gate before five-day cumulative is allowed to count:

> **Continuous uninterrupted soak ≥ 72 hours** (no process restart, no MT5 restart, no machine reboot).

Tracked as `soak_longest_streak_hours` in `PHASE1_STATUS_SUMMARY.json`. Resets to zero on any restart. The cumulative-row count is a *secondary* metric, not the gate.

Pre-commit a target like: `longest_streak_hours >= 72 AND cumulative_decision_rows >= target`.

### N2 — The +0.10R suspension threshold is too soft. **(Edge Defensibility)**

`PHASE2_COST_MEASUREMENT_PROTOCOL.md` pre-commits suspension if measured cost pushes net expectancy below **+0.10R**. The form of the rule is correct. The level is not defended numerically.

Context:
- Gross expectancy ≈ 0.5116R.
- Assumed cost ≈ 0.3228R → assumed net ≈ 0.1888R.
- A strategy that bleeds 0.08R of net edge under measurement (cost goes from 0.3228R → 0.4316R, a 34% miss) would still pass the +0.10R floor.

At net +0.10R with ~10 trades/day and ~3-year sample, the realized edge is plausibly within 1σ of zero (rough calc: even at PF ≈ 1.1, with intraday noise, the t-stat against zero across a real 6-month forward period is below 2). The +0.10R floor authorises Phase 2 *capital* on a strategy that is borderline statistically distinguishable from breakeven.

**Recommend one of:**

(a) **Raise the floor** to +0.15R (cost bleed budget 0.04R, ~12% miss) or +0.20R (cost bleed budget zero — no miss permitted).

(b) **Defend +0.10R numerically**: compute the minimum-detectable-effect at +0.10R given trade count, variance, and expected forward sample. If MDE > 0.10R, +0.10R cannot be reliably distinguished from zero and is therefore not a defensible kill threshold.

Either path is fine. The current document picks a round number with no justification, which is the only place in the recent work where the team has not shown their math.

### N3 — Hypothesis-authoring space is family-biased. **(Long-Term Survival)**

The V3 audit cleared the **gates** of frequency bias. It did not address whether the **set of hypotheses being authored** is biased toward high-frequency intraday mechanics.

Of the 20 registered hypotheses:

| Family (loose grouping) | Count |
|---|---:|
| Breakout / retest / continuation | 8 |
| Compression / squeeze / range break | 4 |
| Session-window mechanics (London/NY/Asia) | 6 |
| Mean reversion / rejection / sweep | 3 |
| **Pure swing / D1+ momentum / carry** | **0** |

`liquidity_sweep_reversal_v0` (registered today) is genuinely a different *family* (reversal off failed sweeps) — credit there. But it is still **M5 entry with M15 ATR**, i.e., intraday. There is **no hypothesis in the registry that operates above the H1 timeframe.**

This is a strategic prior baked into the research team's authoring choices, not a gate bias. It means:

1. The next "independent" expert (PHASE2_AUTHORIZATION_CHECKLIST item) is highly likely to be another intraday family.
2. If gold's intraday microstructure changes (broker cost regime, session liquidity, MT5 server time policy), the team's entire portfolio of authored ideas is correlated.
3. The Phase 2 measured-cost gate punishes high-frequency strategies disproportionately, which compounds with (2).

**Recommend:** the team add to the candidate research backlog (`CANDIDATE_RESEARCH_BACKLOG.md`) at least **one H4-or-higher swing hypothesis** before authorising Phase 2 paper-mode capital. Suggestions:

- Weekly pivot reclaim continuation on D1.
- Multi-day momentum (e.g., 10-day breakout with H4 retest filter).
- COT / sentiment-divergence mean reversion on D1.

Track as a new operational metric in agent.md:

```
hypothesis_timeframe_coverage:
  M5_M15: 17
  M30_H1: 3
  H4_D1: 0     ← gap
  W1+:   0     ← gap
```

---

## Soft Concerns (not blockers)

### S1 — D2 SPA p drifted closer to α=0.05

Max pairwise SPA p moved 0.0234 → 0.0336 when the universe expanded from 3 → 18 candidates. Still passes at α=0.05, but the margin halved. The hypothesis universe is still growing (20 hypotheses today, more in the backlog). Without a pre-committed candidate-count ceiling, the team is implicitly running a sequential test without sequential correction.

**Recommend:** pre-commit a rule like "if non-empty candidate universe reaches 30, the Reality Check must clear at α=0.01 for Phase 2 to remain authorised." Pin this in `HYPOTHESIS_LOCKING.md` or `NO_TUNING_RULES.md`.

### S2 — Same-family acknowledgment is good, but the operational plan still runs both variants

The single-edge risk plan correctly removes the *capital* uplift from running both. It does not remove the **telemetry confound** of running both. If `breakout_retest` and `swing_breakout_retest_v0` are both live in Phase 2 paper, attribution of a P&L change becomes harder, not easier.

**Recommend:** in Phase 2 paper, run `breakout_retest` as the only execution-eligible expert. Keep `swing_breakout_retest_v0` as **observer-only telemetry** (already a Phase 1 capability — `Phase 1 swing dry-run observer` shipped in commit `19eba44`). Promote `swing_breakout_retest_v0` to execution-eligible only after a clean attribution baseline exists for the primary expert.

---

## Updated Sub-Score Breakdown

| Dimension | R#2 | R#3 | R#4 | Trend | Note |
|---|---:|---:|---:|---:|---|
| Plan quality | 9.5 | 9.0 | 9.0 | flat | Comprehensive; nothing missing in plan |
| Edge defensibility | 7.0 | 5.5 | 5.5 | flat | Cost still assumed; same-family; thin margin. Cannot move until measured cost arrives. |
| Execution discipline | 9.5 | 9.5 | 9.5 | flat | Continues to over-deliver |
| Operational maturity | 8.5 | 8.5 | 9.0 | up | Dashboard, ledger schema, suspension protocol, review triggers |
| Code quality (inferred) | 8.0 | 8.0 | 8.0 | flat | New rejection_audit module + tests is clean |
| Long-term survival design | 7.5 | 6.0 | 6.5 | up | Single-edge plan + step-ladder + active non-family research |
| Validation rigor | 8.5 | 8.0 | 8.5 | up | D2 re-run properly; frequency-bias audit built and run |
| **Composite** | **9.0** | **8.5** | **8.75** | up | |

**Do not let the composite obscure the load-bearing weakness.** Edge defensibility is still 5.5. The strategy keeps 37% of its gross edge under *assumed* cost. Until measured cost arrives, the entire net-edge claim is contingent.

---

## What I'd Want To See Before Review #5

In order of importance:

1. **Measured cost integrated** (5 of 5 days of passive spread data + paper-mode realized cost). Closes V1, V4. If measured cost pushes net under +0.10R, the team executes its own kill rule. If measured net stays ≥ +0.15R, edge defensibility moves to 7.0+.
2. **Continuous uninterrupted soak ≥ 72 h** as a sub-gate (N1).
3. **+0.10R floor either raised or defended numerically** (N2).
4. **At least one H4-or-higher hypothesis** registered in the backlog (N3).
5. **D2 candidate-count ceiling rule** committed in HYPOTHESIS_LOCKING.md (S1).
6. **Phase 2 paper plan downgraded to single execution-eligible expert** with swing variant as observer-only (S2).

Items 1, 2 are wall-clock blockers (cannot accelerate). Items 3–6 are paperwork — should land before Review #5 if the team has 24 h.

---

## Closing Note

The team's response to Review #3 was the cleanest evidence-first reply I have seen in this project. They built a new module specifically to falsify a reviewer hypothesis, ran it, and the data went against the reviewer (me) — and they reported the result without softening it. That is the discipline that justifies the 8.75 rating despite the still-unresolved cost question.

The remaining two real risks are:

1. **Measured cost vs. assumed cost** — a wall-clock physical gate. The team has pre-committed a kill rule. The kill rule's *level* is the one place in this review where I am not satisfied.
2. **One edge family carrying everything** — a research-time gate. The team has acknowledged it, removed the diversification claim, and is actively authoring non-breakout hypotheses. But there is no H4+ hypothesis in the registry yet.

Neither blocks the current Phase 1 dry-run. Both block Phase 2 capital authorisation in any honest reading.

— End of Review #4
