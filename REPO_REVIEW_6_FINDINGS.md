# REPO_REVIEW_6_FINDINGS

**Reviewer:** Claude (independent technical reviewer)
**Date:** 2026-05-23 (late)
**Repo:** `maksoftwares/algo-trading-system` @ `main`
**Commits since Review #5:** 1 (`51315a2 respond to review 5 and test h4 d1 candidates`)
**Diff size:** 62 files, +3137 / -426
**Scope:** Verify the team's direct response to every Review #5 actionable finding. Assess whether the response holds up under read.

---

## Headline

**Rating: 9.0 / 10** (Review #5 was 8.75).

The team addressed **every actionable finding from Review #5** in a single commit:

| R#5 Finding | R#6 Status | Notes |
|---|---|---|
| N1 — continuous-streak soak gate | **IMPLEMENTED** | New `phase1_soak_streak.py`; 72 h required; resets on restart or 15-min gap |
| N2 — defend or raise +0.10R floor | **RAISED to +0.15R** | Exactly the recommendation. Codified in protocol, checklist, and owner-approval template |
| N4 — mandatory hold-time hypothesis fields | **IMPLEMENTED** | HYPOTHESIS_TEMPLATE.md adds 6 new fields including explicit "M5 entry on D1 level does not qualify" rule |
| N5 — forcing rule + non-level next candidate | **IMPLEMENTED** | Two H4/D1 candidates authored, hash-locked, run, both rejected. Next candidate `d1_compression_h4_expansion_v0` specced |
| S2 — single execution-eligible paper expert | **ADOPTED** | `breakout_retest` is only first-slice paper stream; same-family variants observer-only |
| (Unsolicited bonus) D2 on R-series | **DONE** | White p 0.0200 → **0.0002**; max SPA 0.0308 → **0.0188** |

This is the cleanest response-to-review cycle in the project's history. Both N6 and N7 below are *new* consequences of the team's correct work, not regressions.

The rating moves +0.25 because the *process* sub-scores can finally move. Edge defensibility moves only +0.5 (5.5 → 6.0) because two H4/D1 attempts both rejected — the team is now testing in the right space but has not found a non-level edge. Composite at 9.0.

---

## What the team shipped

### 1. N1 — Continuous-streak soak gate (`phase1_soak_streak.py`, 115 lines)

The implementation is correct. Reading the code:

- Segment resets on `run_id` change (restart) — correct.
- Segment resets on bar gap > 15 min — correct for active-market continuity.
- `_is_good_soak_row` requires `lifecycle_state == "DRY_RUN"`, `dry_run == "true"`, `trade_permission == "false"`, `server_time_status == "CLOCK_OK"`. Any deviation breaks the streak — correct.
- Both `current_streak_hours` and `longest_streak_hours` exposed in `PHASE1_STATUS_SUMMARY.json`.
- Acceptance gate adds `required_uninterrupted_streak_hours: 72.0`.

Current status as of 2026-05-23T18:04Z:

```json
"current_streak_hours": 0.0,
"longest_streak_hours": 2.25,
"required_uninterrupted_streak_hours": 72.0,
"uninterrupted_soak_pass": false,
"unique_run_ids": 5
```

**The gate is correctly implemented, correctly wired into PASS/PENDING/FAIL evaluation, and is currently the dominant blocker.** See N7 below.

### 2. N2 — +0.15R floor codified

`PHASE2_COST_MEASUREMENT_PROTOCOL.md`:

```
MIN_NET_EXPECTANCY_R_AFTER_MEASURED_COST = +0.15R

IF measured paper/live execution cost pushes breakout_retest family net expectancy below +0.15R
THEN suspend the breakout-retest family and return to research.
```

Owner-approval template now requires the signer to commit `minimum_net_expectancy_r >= 0.15`. Three interpretation buckets:

| Outcome | Decision |
|---|---|
| Net ≥ +0.15R, drift OK | Continue paper-mode |
| +0.00R to +0.15R | Suspend; no live pilot |
| ≤ +0.00R | Retire or redesign as new locked hypothesis |

This is exactly the right shape. The level is the conservative end of my Review #4 N2 recommendation. N2 is fully closed.

### 3. N4 — Hypothesis template enforces timeframe attribution

`HYPOTHESIS_TEMPLATE.md` now mandates:

```
Mechanic family: <level-and-pullback / mean-reversion / macro-regime / intermarket / volatility / other>
Entry / decision timeframe: <M5 / M15 / H1 / H4 / D1 / W1>
Expected median hold bars M5-equivalent:
Expected median hold hours:
Expected decisions per week:
Timeframe diversification qualifies: <yes/no>
```

Plus the killer line:

> A D1, W1, or prior-session reference level with M5 entries does not qualify as timeframe diversification.

This is precisely the rule I asked for in R#5 N4. The team didn't water it down; they sharpened it. N4 fully closed.

### 4. N5 — Two H4/D1 candidates authored, tested, rejected

| Candidate | PF range | Trades/cell | Decision |
|---|---|---:|---|
| `d1_momentum_h4_pullback_v0` | 1.146–1.395 | 69–80 | REJECTED (3/9 cells ≥ 1.30; concentration FAIL) |
| `d1_volatility_expansion_reversal_v0` | 0.862–1.268 | 30–53 | REJECTED (0/9 cells ≥ 1.30; sample_size FAIL on most cells) |

The team has now done what I asked: registered, hash-locked, smoke-tested, and result-producing run of two genuinely H4/D1-decision-timing candidates. The forcing rule is documented:

> No new same-family candidate is authored until at least one genuinely-non-level candidate has been registered, hash-locked, and result-producing run completed.

Next candidate per the action plan: `d1_compression_h4_expansion_v0` (D1 directional + H4 entry + median hold > 24 h + < 100 trades/year + no M5 entry trigger). The forcing rule is alive.

**N5 process closed.** N5 *outcome* (find a non-level edge) is unresolved and may not be resolvable. See N6 for a structural reason why.

### 5. D2 re-run on monthly R series — substantially stronger

| Methodology | n | White p | Max SPA p |
|---|---:|---:|---:|
| R#3, % returns, 3 candidates | 3 | 0.0200 | 0.0234 |
| R#3 rerun, % returns, 18 candidates | 18 | 0.0200 | 0.0336 |
| R#5, % returns, 27 candidates | 27 | 0.0200 | 0.0308 |
| **R#6, fixed-notional R series, 27 candidates** | **27** | **0.0002** | **0.0188** |

The R-series methodology removes leverage-scaling distortion in the bootstrap. White p moves from "passes α=0.05 comfortably" to "passes α=0.001 comfortably." This is meaningfully stronger evidence. Recommend this become canonical going forward — see S3.

### 6. Other unsolicited improvements

- `HYPOTHESIS_LOCKING.md` adds the 30-candidate alpha-tightening rule (S1 in R#4, even though I closed it in R#5 — the team adopted it anyway as a fail-safe).
- `CANDIDATE_RESEARCH_BACKLOG.md` updated with the next candidate spec.
- `PHASE1_ACCEPTANCE_REPORT`, `PHASE2_READINESS_REPORT`, `PHASE1_SOAK_HISTORY_REPORT`, `PHASE1_REVIEW_INDEX`, `status.html` all wired to the new streak metric.
- Review files (REPO_REVIEW_4_FINDINGS.md, REPO_REVIEW_5_FINDINGS.md) committed alongside the team's own response — external reviews are now version-controlled inside the repo. This is unusually good transparency practice.

---

## New Findings (consequences of the team's correct work)

### N6 — The concentration gate may be miscalibrated for low-frequency strategies. **(Validation rigor)**

Both H4/D1 candidates failed on **concentration**.

`d1_momentum_h4_pullback_v0` failed concentration *despite* posting:
- PF 1.146–1.395 across 9 cells (3 above 1.30)
- Max DD 4.74% (very clean)
- Every cell positive return
- All 9 cells above the 40-trade minimum

This is a clean-looking H4/D1 edge that failed on a single gate. And concentration was *also* the most common rejection reason in the R#5 24-candidate audit (22/24 = 92%).

Math sketch: if `breakout_retest` has ~7400 trades per cell and a top-trade-share cap of, say, 5%, then any single trade may contribute up to ~370 trades' worth of expectancy ≈ 0.05% of cell PnL. If `d1_momentum_h4_pullback_v0` has 80 trades per cell and the *same absolute-dollar* cap is applied, a single trade can be 1.25% of cell PnL — **25x more concentrated by construction**, before any edge difference.

The R#5 §4-audit answer ruled out frequency-*only* rejection. It did **not** rule out concentration-via-low-frequency rejection, which is a different failure mode. The audit shows 22/24 candidates failed concentration, but does not slice "concentration failures whose trade count was below 200/cell."

**Recommend** one of:

(a) **Frequency-normalize the concentration gate.** Express the cap as `(top_trade_R) / (mean_abs_R * sqrt(n_trades))` or similar — a measure that is invariant to trade count under iid trades. The current cap on absolute-share is inherently biased toward HF strategies.

(b) **Audit the concentration failures** specifically: for each of the 22/24 concentration-failed candidates, recompute their gate result under a frequency-normalized rule. If any flip to PASS, the gate is the issue. If none flip, the strategies were genuinely concentrated.

(c) **Accept the bias and document it.** State explicitly: "The Phase 0 gates as configured are calibrated for ≥1000-trades-per-cell strategies. Lower-frequency strategies are structurally disadvantaged. The current candidate universe should be read as a search across HF strategies." This is honest if the team chooses it, but it has implications for the diversification search.

This is the open question I had hoped the R#5 N3 audit would close, and which on reflection it did not.

### N7 — The streak gate is correct but currently dominant; weekend handling is not yet clarified. **(Operational)**

`longest_streak_hours: 2.25` against `required_uninterrupted_streak_hours: 72.0`. **The team's all-time longest uninterrupted soak run is 3.1% of the gate target.**

This is not a criticism — the gate just exists. But two implementation questions need answers before the gate can be passed:

1. **Weekend gap policy.** `_is_good_soak_row` (line 86 of `phase1_soak_streak.py`) only checks lifecycle/trade-permission/server-time fields; it does **not** specifically tolerate weekend-pause rows. Combined with `max_bar_gap_minutes = 15.0`, any market-closure gap > 15 min resets the streak. Gold market closes ~21:00 Fri UTC → ~22:00 Sun UTC (≈49 hours). **Under the current implementation, the streak cannot survive any weekend** — so 72 hours of uninterrupted streak requires the system to bridge from Monday open to Wednesday end-of-day without restart.

   But agent.md L32 says weekend gaps *are* tolerated by the verifier/soak/runtime-health/external-health checks. There is a documentation-vs-implementation asymmetry here. Either:
   - (a) Weekend gaps should be excluded from the streak metric (define active-market bridge) — in which case 72 h becomes ~9.5 active-market days achievable on either side of a weekend, or
   - (b) Weekend gaps should break the streak (current code) — in which case 72 h is a hard Mon-Wed window with no human touches.

2. **What counts as a "touch"?** The streak resets on `run_id` change. Phase 1 has had 5 unique run_ids — meaning 5 restarts. Every code change → recompile → redeploy increments run_id. The team needs an operational rule: **the next 72-hour run must include a code-freeze window**.

**Recommend:**

- Clarify the weekend policy in `phase1_soak_streak.py` itself (a comment block plus, if (a), an `_is_market_paused_gap()` helper).
- Add a `code_freeze_started_at` field to `PHASE1_STATUS_SUMMARY.json`; pre-commit a freeze window of at least 96 hours before the streak can be expected to pass.

---

## Soft concerns

### S3 — D2 methodology going forward should be R-series only

The two D2 results (% returns and fixed-notional R) currently coexist in the repo. The R-series version gives substantially stronger p-values because it removes leverage distortion from the bootstrap. **Recommend** the team mark the % returns version as superseded and use the R-series as the canonical methodology in `PHASE0_INDEPENDENT_VALIDATION.md` and the Reality Check manifest. Otherwise downstream readers will see two p-values and pick whichever flatters their argument.

### S4 — Two H4/D1 rejections is a useful sample of 2, not a definitive answer

The team has met the forcing-function requirement. But two rejections is not strong evidence about whether (a) non-level edges don't exist in XAUUSD, (b) the gates select against them, or (c) the team's authoring instincts are converging. Both rejected H4/D1 candidates also failed on concentration (N6), which clouds the read.

**Recommend** the team plan to ship **at least three** non-level H4/D1 candidates before Phase 2 paper-mode is authorized — the `d1_compression_h4_expansion_v0` plus two more from different mechanic families (e.g., one volatility-regime, one intermarket). If all three fail with PF in the 1.1-1.4 band on concentration, that's an N6 issue. If they fail with PF < 1.0, that's an edge issue.

---

## Sub-Score Breakdown

| Dimension | R#4 | R#5 | R#6 | Δ | Note |
|---|---:|---:|---:|---:|---|
| Plan quality | 9.0 | 9.0 | 9.5 | +0.5 | Forcing rules + mandatory fields + signed approval thresholds |
| Edge defensibility | 5.5 | 5.5 | 6.0 | +0.5 | D2 much stronger; +0.15R floor codified; family still single |
| Execution discipline | 9.5 | 9.5 | 9.5 | flat | At ceiling |
| Operational maturity | 9.0 | 9.0 | 9.5 | +0.5 | Streak metric, owner-approval template, status integration |
| Code quality (inferred) | 8.0 | 8.0 | 8.5 | +0.5 | New soak-streak module is clean; new D1/H4 strategies + tests added |
| Long-term survival design | 6.5 | 6.5 | 7.0 | +0.5 | Two H4/D1 attempts, forcing rule active, next candidate specced |
| Validation rigor | 8.5 | 8.75 | 9.0 | +0.25 | D2 on R-series, stronger evidence; concentration audit not yet done |
| **Composite** | **8.75** | **8.75** | **9.0** | +0.25 | |

The team has now lifted everything that can be lifted by process. The remaining 1.0 to a 10/10 ex-ante ceiling lives entirely in:

- Measured cost data passing the +0.15R floor (or failing it honestly).
- A non-level edge family passing Phase 0 — or N6 being resolved by frequency-normalized gates allowing a clean-looking H4/D1 candidate through.
- 72-hour uninterrupted streak achieved.
- 5-day soak completed.
- Owner approval signed.

---

## Pre-Phase-2 Gating — Updated Punch List

| # | Item | Type | Status | Note |
|---:|---|---|---|---|
| 1 | Measured cost ≥ 5 days + revalidation ≥ +0.15R | Wall-clock + outcome | 2/5 days | Outcome unknown until day 5 |
| 2 | 72-hour uninterrupted streak | Wall-clock + operational | 2.25 h / 72 h (3.1%) | Needs code-freeze + weekend policy clarified (N7) |
| 3 | 5-day cumulative soak | Wall-clock | 8.26% | Will compound with #2 if streak resets |
| 4 | Phase 1 review index PASS | Process | PENDING | Auto-pass once #1–#3 land |
| 5 | VPS selection | Owner decision | PENDING | Not technical |
| 6 | Owner approval signed with `≥ 0.15` | Owner decision | PENDING | Template ready |
| 7 | Concentration gate audit (N6) | New | Open | One-day analysis task |
| 8 | Weekend-handling clarification in streak code (N7) | New | Open | Half-day task |
| 9 | Mark R-series as canonical D2 (S3) | New | Open | Half-day task |
| 10 | Plan 2+ more non-level H4/D1 candidates (S4) | New | Open | Research-time task |

Items 7–10 are within the team's direct control and could land within 48 hours.

---

## Closing Note

This is the kind of review cycle that justifies the project's high process scores. Five concrete recommendations were made in R#5; five were implemented in 24 hours; the level-and-pullback diagnosis was tested empirically (and not yet broken); the suspension threshold was raised to the conservative end of the recommended range; and external reviews were committed into the repo for transparency.

The remaining risk is not process. It is:

1. **Measured cost.** Will the +0.15R floor be cleared when broker reality lands?
2. **Concentration math.** Will N6 reveal that the gate has been quietly biased against the only candidates that could diversify the system?
3. **72-hour streak.** Can the team go 72 active market hours without touching the system?

If the answer to (1) is yes, to (2) is "no bias, the strategies were genuinely concentrated," and to (3) is yes, the system clears Phase 2 paper-mode authorization. None of those answers are knowable today, and the team has correctly built the gates that will produce them.

The 9.0 rating is the highest this project will see until measured cost data arrives. If the +0.15R floor holds and a non-level candidate passes, 9.5 is in range. The last 0.5 (to 10/10) is reserved for live evidence and cannot be earned by any plan or backtest.

— End of Review #6
