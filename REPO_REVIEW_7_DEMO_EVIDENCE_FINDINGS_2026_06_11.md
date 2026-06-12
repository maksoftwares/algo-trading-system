# Repo Review 7 — Demo-Evidence Review and Improvement Plan (2026-06-11)

Reviewer role: senior quant researcher / MQL5 EA architect / trading-systems risk reviewer.
Primary evidence: `PHASE2_DEMO_WEEKLY_TRADES_REVIEW_2026_06_11` (565 raw / 318 unique actual broker trades, account `1025742 Capital.ComMena-Demo`, AED, 2026-06-01 → 2026-06-11), cross-checked against the 2026-06-04 loss case study, `PHASE2_EA_WEAKNESS_SHADOW_REPORT`, the dynamic-exit replay verdict, the measured-cost forensics, the passive cost observer, and the Phase 0 / Phase 0R candidate ledger.

All numbers below are from the duplicate-hidden ("unique") decision view unless marked RAW. No history was filtered after the fact; losing EAs and losing buckets are reported in full.

---

## 1. Executive Verdict

**The biggest weakness is not research quality. It is the gap between what your own evidence says and what the demo account is actually running.**

Three concrete contradictions:

1. **The portfolio still runs the configuration your own shadow reports proved is losing.** The 06-04 case study flagged `symbol_normalized_round_retest_v0` and XAUUSD morning/afternoon as the loss drivers and pre-registered the shadow rules. The following week (06-05 → 06-11) confirmed every one of those findings forward — `symbol_normalized_round_retest_v0` went on to lose another ~−290 AED — and the EAs are still attached with broker action enabled. Your own promotion rule ("survive one fresh forward week") has been satisfied; the decision just hasn't been taken.
2. **Sizing is inverted.** On 06-08/06-09 EURUSD and GBPUSD lots were raised to 0.05 (5×) across *all five* executors — including the two confirmed losing EAs — while XAUUSD, the only symbol with a demonstrated edge (`breakout_retest` XAUUSD +524 AED, PF 1.82), stays at 0.01. EURUSD and GBPUSD are both net-negative symbols in the unique view. The account is now sized largest exactly where the evidence is worst.
3. **The formal project status contradicts the live evidence.** `breakout_retest` is `COST_SUSPENDED_CANONICAL` based on a Phase 0 ledger whose median stop was ~110 points, where P95 spread (75 pts) produces cost_R ≈ 1.13 — fatal. But the *as-deployed* demo EA trades with ~300–630-point stops; the passive observer measures median cost_R 0.13–0.15 and net edge_R ≈ 0.37 (mostly `COST_OK_STRONG`), and the actual demo result is PF 1.70 over 103 closed unique trades. The cost suspension is testing a configuration you no longer run. Until that is reconciled, the project's gating system is blocking its best asset on stale evidence while the demo floor freely runs five same-family clones whose live evidence is mostly negative.

Secondary weakness: **process weight is outrunning decision value.** 508 docs in phase0/docs, 100+ committed reports, a 13 MB `status.html` and 8.6 MB dashboard in git, a 120 KB `agent.md`. The owner needs roughly five numbers a day; the repo produces hundreds of pages a week.

What is genuinely strong and should be said plainly: the Phase 0 discipline (SHA-locked hypotheses, 9-cell matrices, no-tune-v0, multiplicity ledger, VOIDing the era-rotated run) is better than most professional shops. The dynamic-exit replay that *rejected* partial-profit and breakeven instead of deploying them is exactly right. And `breakout_retest` on XAUUSD is a real, repeated, two-window result — positive all 7 trading days, both review windows, concentrated where backtest research independently said the edge lives (NY-morning/evening window). That convergence is the most valuable thing in the repo.

---

## 2. Top 10 Highest-Impact Changes (ranked)

| # | Change | Mode | Why |
|---|--------|------|-----|
| 1 | **Quarantine `symbol_normalized_round_retest_v0` + `round_number_retest_v0` to observer-only (broker action off).** | **Demo-act now** | −623 AED unique / −922 RAW combined, negative in all four time buckets, confirmed across two independent windows. Your own one-fresh-week rule is already satisfied. Keep them logging would-trades so the block is validated prospectively, not by erasing history. |
| 2 | **Enforce a duplicate-family mutex at the executor level: one order per signal event per family.** | Demo-act now | 247 of 565 rows (44%) are same-minute same-symbol same-direction same-lot duplicates. `round_number`+`symbol_normalized` co-fired 111 times; `breakout`+`swing` 61 times. This is unintended 2× leverage on single signals, not diversification. It is execution hygiene, not a strategy change. |
| 3 | **Revert EURUSD/GBPUSD lots 0.05 → 0.01 on every EA.** | Demo-act now | The 5× increase went live ~06-08/06-09 on net-losing symbol-EA combos with no evidence basis. Restore uniform ~20–25 AED risk/trade before any other tuning. |
| 4 | **Re-run measured-cost revalidation using the as-deployed stop distribution (ATR/floor, ~300–630 pts), pre-registered as a new locked version.** | Research, this week | Resolves contradiction #3. If it passes, the canonical path unblocks honestly. If it fails, you must explain a demo PF of 1.70 before trusting it. Either outcome unblocks the project's decision logic. |
| 5 | **Turn off USDJPY for all EAs.** | Demo-act now | 21 unique trades, PF 0.45, win rate 19%, avg win 5 AED — moves too small for the spread. It adds noise, not diversification. Cheap decision, small loss saved, big cleanup of the decision view. |
| 6 | **Promote the XAUUSD morning/afternoon session block for the retest-family EAs only (not for `breakout_retest`).** | Demo-act now (it was shadow-tested 06-04 and confirmed forward) | Shadow delta +389.79 AED. But keep `breakout_retest` unfiltered: its non-evening buckets are roughly flat (−16 aft, −19 morn, +84 night) and filtering your only profitable EA on one week of bucket data is overfitting. |
| 7 | **Attach `AccountEquityGuardianShadow` (Stage A) now; pre-commit Stage B thresholds.** | Demo-act now (it's observer-only by construction) | The "+300 → −100 giveback" pain is an account-level problem; R1 (150 AED daily stop) / R2 (peak-giveback) are the right layer for it — not per-trade partial exits, which your replay already rejected. One week of shadow agreement, then arm Stage B. |
| 8 | **Instrument MFE/MAE + bid/ask path logging on every open demo position.** | Code, this week | The ATR-trail test is `BLOCKED_NO_PRICE_PATH`. This single logging gap blocks all future exit research. Highest data-value-per-line-of-code change in the repo. |
| 9 | **Shadow-test one rule, not seven: a D1 trend-alignment gate (trade only with D1 bias direction).** | **Shadow first** | XAUUSD BUYs lost −687 AED over 91 trades; SELLs made +548 over 117. The loss engine is counter-trend dip-buying at round numbers in a falling market. One regime gate addresses what a pile of per-cluster blocks would only memorize. Do **not** deploy the per-symbol-session-direction `BLOCK_CLUSTER` rules from the repair research (n=3–7 cells — that is curve-fitting noise). |
| 10 | **Stop the new-candidate mining treadmill; redirect to exploitation.** | Process | 119+ hash-registered candidates, 14 final rejections in 48 hours, and your own locked conclusion: "no second independent edge in this information set." Further hypothesis volume from the same OHLC data is multiplicity risk with ~zero expected value. The marginal research hour now belongs to: cost-revalidation of the as-deployed config (#4), exit-path data (#8), and the trend gate (#9). |

---

## 3. EA-by-EA Decision Table

| EA / lane | Unique closed | PnL AED | PF | Verdict | Reasoning |
|---|---:|---:|---:|---|---|
| `breakout_retest` | 103 | +567.81 | 1.70 | **KEEP (demo)** | Positive 7/7 trading days, both review windows, both raw and dedup views. WR 44.7% vs ~40% breakeven at 1.5R. The only EA with a defensible edge claim. Do not touch its rules this week — it is the control. |
| `swing_breakout_retest_v0` | 12 (+75 dup) | +52 unique / +627 RAW | 3.16 | **PAUSE executor / keep as logger** | 75 of its 86 raw trades duplicate `breakout_retest` to the minute. It is the same stream twice, not a second EA. Its raw profit is the mutex question (see §5), not an independence claim. |
| `symbol_normalized_round_retest_v0` | 131 | −630.46 | 0.72 | **QUARANTINE → observer-only** | Largest loss driver. Negative in all 4 buckets, both windows (−337 by 06-04, −630 by 06-11). Forward week confirmed. |
| `round_number_retest_v0` | (hidden as dup) | −445 RAW | — | **QUARANTINE → observer-only** | 111/126 of its trades are clones of the above. Same family, same verdict. |
| `session_extreme_retest_v0` | 55 | −208.52 | 0.64 | **PAUSE; run repair_v1 as observer** | WR 27%. Loses everywhere except afternoon (+48, n=17 — noise). Repair_v1 shadow (+139 delta, kept PF 1.04) is marginal, not yet deployable. |
| `session_extreme_retest_v0_repair_v1` | 3 RAW | +99.5 RAW | — | **NEEDS MORE DATA (observer-forward only)** | n=3. Nothing is known yet. |
| `symbol_normalized_round_retest_v0_repair_v1` | 1 (+7 dup) | +265 RAW / 8 | — | **NEEDS MORE DATA (observer-forward only)** | Promising direction, tiny n. Do not let it place broker orders while its parent is being quarantined. |
| `p2weakness_br_v1` | 1 | −14 unique / +200 RAW (6) | — | **NEEDS MORE DATA + governance cleanup first** | The runtime attachment audit found the portable terminal still holds old `930101` source with broker-action default true. Clean-deploy `931000` per the Phase 2X procedure or kill the lane. A lane whose runtime ≠ repo source is a liability regardless of PnL. |
| `WR50_BreakoutEvening_v0` | 2 | −74.00 | 0.00 | **KILL (or fix + observer)** | Both losses fired at *night* (05:43 entry) from an EA named "Evening" — its session window is not enforced in code. The WR50 premise (optimize win rate) also contradicts your own KPI (`net_expectancy_R_after_measured_cost`; win rate diagnostic only). |
| `WR50_BreakoutQuality_v0`, `WR50_BreakoutExit1R_v0` | 1–3 RAW | −21 / −18 | — | **KILL lane or observer-only** | No signal at this n; the lane multiplies complexity for no decision value. |
| `quarter_round_retest_v0` | 0 | — | — | **DO NOT DEPLOY** | Same family as two quarantined EAs; zero demo evidence; nothing to add. |
| `W1D1MomentumM5Continuation` (active profile) | 0 (not attached) | — | backtest PF 1.04 capital / 0.86 dukascopy | **DO NOT ATTACH active profile** | Fails cross-broker by your own G7 logic. The "activity scan" chose more trades over edge (slow profile PF 1.15 → active 1.04) — that is optimizing for action, not expectancy. The slow profile may run as observer only. |
| `trend_pullback`, `range_mr`, 119 rejected candidates | — | — | — | **KEEP DEAD** | The no-tune-v0 discipline is correct. Do not resurrect. |

---

## 4. Symbol × Session Routing Table

Time buckets are local (Asia/Dubai); "Evening 16:00–19:59" ≈ NY morning / London-NY overlap — the same funded window your Phase 0 research independently identified. That convergence is why the evening edge is more believable than one week of data alone would justify.

| EA | XAUUSD | EURUSD | GBPUSD | USDJPY |
|---|---|---|---|---|
| `breakout_retest` | **ALL sessions** (evening is the core: +518/22 trades; keep night/morning for now — roughly flat, and one week is too little to filter the winner) | Evening only (+49.6 ev vs −41.6 night; PF 1.25 overall) | Insufficient evidence (n=8, ~flat) — keep 0.01, evening only, re-decide at n≥30 | **OFF** |
| `swing_breakout_retest_v0` | logger only | logger only | logger only | OFF |
| round-family (`symbol_normalized`, `round_number`, `quarter`) | observer only | observer only | observer only | OFF |
| `session_extreme_retest_v0` (+repair) | observer only | observer only | observer only | OFF |
| Everything else | not attached | not attached | not attached | not attached |

Answer to the policy question: **no, EAs should not trade all qualified symbols.** Each EA gets its own symbol/session whitelist in its preset, derived from unique-view evidence with a minimum-n rule (no whitelist decision on n<30 unique closed trades). Ranking metric for EAs: unique-view net AED and PF over a rolling 2-week window, with day-positive consistency as the tiebreaker — exactly the view your weekly export already produces.

---

## 5. Duplicate / Family-Stacking Recommendation

**Treat `breakout_retest` + `swing_breakout_retest_v0` (+ `p2weakness_br_v1`) as ONE execution stream, and the three round-retest variants as ONE stream.** The README already states this ("same-family variants… not independent diversification"); the runtime just doesn't enforce it.

Be honest about the trade-off: this week, stacking *helped* the raw account (+720 RAW vs −330 unique) because the winning family was the one doubling up. That is not an argument for stacking — it is 2× leverage applied blindly to whichever family fires, and it amplified round-family losses just as mechanically (−922 RAW). If you want 2× exposure on breakout-evening signals, take it deliberately through lot size on the kept stream, where the guardian and daily caps can see it — not through accidental clone co-firing.

Implementation: shared family registry (you already have `MAGIC_NUMBERS.md`); first-priority EA in the family places the order; others log `WOULD_DUPLICATE`. Priority: `breakout_retest` for the breakout family. Mutex scope: same symbol + direction + family within the same M5 bar.

---

## 6. Dynamic-Exit Recommendation

**Leave exits fixed at 1.5R. Do not deploy partials, breakeven, or trailing now.**

- Partial @+1R + BE: your own exact-logged-path replay showed −134 AED vs control, dragging 21 winners to save 0 losers. REJECTED — correct call, keep it rejected.
- BE-only: zero improvement, zero losers saved. REJECTED.
- ATR trail: untested, `BLOCKED_NO_PRICE_PATH`. The correct response is change #8 (log MFE/MAE + M5 path per trade), collect 4+ weeks, then replay trail variants offline on `breakout_retest` evening XAUUSD only. Promotion KPI stays `net_expectancy_R_after_measured_cost`.
- The giveback pain (+300 → −100 days) is an **account-level** problem. Solve it with the Equity Guardian R1/R2/R3 (daily stop, peak-giveback trail, daily profit lock), not by degrading per-trade exits that are currently positive-expectancy as designed.

---

## 7. Risk and Lot-Size Recommendation

Current per-trade risk (0.01 XAUUSD, ~6 USD stop) ≈ 20–25 AED — sensible for a demo research account. Fix the deviations:

1. EURUSD/GBPUSD back to 0.01 everywhere (undo the 5× increase on losing combos).
2. Per-family max 1 open position (already partially enforced via `family_open_exposure_cap`); total account max 3 open positions.
3. Daily loss limit: −150 AED → flatten + halt all executors until next session (Guardian R1; shadow now, armed after one clean week of shadow agreement).
4. Weekly circuit breaker: −400 AED unique-view → all EAs to observer-only pending owner review.
5. Peak-giveback: arm at +150 AED floating, flatten at 40% giveback (Guardian R2 v0 as specced).
6. Do **not** size `breakout_retest` up yet. Earn it: after the cost revalidation (#4) passes and the Guardian is armed, one step to 0.02 on XAUUSD evening only, then re-evaluate after 2 weeks.
7. Cost answer: **broker cost is not the live blocker for the as-deployed configuration** — passive observer median cost_R ≈ 0.14 vs net edge_R ≈ 0.37, and demo losses are stop-outs from selection/timing, not spread bleed (the 06-04 case study says exactly this). The cost blocker is real only for the *old tight-stop backtest config*. Resolve the paperwork (change #4) instead of treating cost as a permanent wall.

---

## 8. What to Change in Code First (ordered)

1. **Executor family mutex** (one order per family signal event) — `Phase2ExperimentalDemoExecutor.mq5` + family registry include.
2. **MFE/MAE + M5 bid/ask/ATR path logging** for every open position — unblocks all exit research.
3. **Per-EA symbol/session whitelist as preset inputs** (so routing changes are preset edits with an audit trail, not source edits).
4. **Attach Guardian Stage A**; wire its CSV into the daily risk report.
5. **Lot revert + USDJPY off** (preset changes, with the same report trail as the 06-08 lot report).
6. **Status page diet**: generate `status.html` on demand; commit only a small `STATUS.json` + one-page MD summary. Remove the 13 MB HTML and 8.6 MB dashboard from git history going forward (gitignore them).
7. Split `agent.md` (120 KB): a 1-page CURRENT_STATE.md the owner can actually read, plus an append-only history file.

Canonical report set (everything else becomes on-demand): weekly unique-trades packet, weakness shadow report, daily risk report, Guardian log summary, STATUS.json. The dozens of one-off `DEMO_14_EA_*` / countdown / packet variants should be archived to an `archive/` folder — they are write-once artifacts that now obscure the canon.

---

## 9. What to Test in the Next 7 Days

Pre-register all of this before Monday (your own hypothesis-lock discipline, applied to the portfolio layer):

| Track | Mode | Success criterion (pre-registered) |
|---|---|---|
| `breakout_retest` XAUUSD+EURUSD, unchanged rules, 0.01 | Demo (control — touch nothing) | Stays day-positive majority of days; unique PF ≥ 1.3 |
| Family mutex + quarantines + USDJPY off + lot revert | Demo | Portfolio unique view turns net-positive; duplicates → ~0 |
| Round-family + session_extreme as observers | Observer | Their would-trade logs stay net-negative (prospective validation of the block — if they go positive, the quarantine gets reviewed, honestly) |
| D1 trend-alignment gate | Shadow | On logged signals: kept subset PF > blocked subset PF with ≥60% of trades kept |
| Guardian Stage A | Shadow | R1/R2 would-fire log matches manual account math; zero false fires |
| MFE/MAE path logger | Logging | 100% of closed trades have path rows; data-quality report PASS |
| Cost revalidation v2 (as-deployed stops) | Research | Locked, pre-registered; either verdict accepted |

Explicitly **not** this week: new candidates, W1D1 attachment, exit-rule changes, sizing up, any per-cluster block rules.

---

## 10. Evidence Bar for Small Real-Money Testing

Do not go live now. Authorize a small real account only when ALL of:

1. **Cost status resolved**: measured-cost revalidation v2 (as-deployed stop model, pre-registered) is PASS, or a documented, locked explanation reconciles demo PF 1.70 with the cost model.
2. **Forward demo proof on the final routing**: ≥4 consecutive weeks and ≥80 unique closed trades on the post-mutex, post-quarantine configuration, with unique-view PF ≥ 1.3, positive net AED after all costs, max drawdown ≤ 2× the worst weekly drawdown seen in demo, and no week worse than −300 AED.
3. **Risk armed and tested**: Guardian Stage B live with a passed kill-switch fire drill (the Phase 2X procedure already exists — execute it).
4. **Runtime = repo**: clean-clone reconciliation PASS on the day of go-live; no stale-source lanes (the current P2WEAKNESS `930101` situation would be disqualifying).
5. **Scope locked**: one family (`breakout_retest`), one symbol (XAUUSD), 0.01 lots, evening-anchored window, daily loss cap ≤1% of account, and a pre-registered demotion rule (e.g., rolling 3-week PF < 1.0 → back to demo). Owner authorization recorded per your existing templates.

Nothing about 7 trading days of demo data — however good `breakout_retest` looks — meets that bar yet. The week is evidence of promise, not of robustness.

---

## Appendix: Answers to Specific Process Questions

**Are Phase 0 gates too strict / too loose / frequency-biased?** Strictness is right — 119 rejections with one surviving family is what honest gates look like. There IS a structural bias: the ≥40-trades-per-cell rule penalizes H4/D1 candidates (G2 failures on Pepperstone windows show it). The `PHASE0_LOWFREQ_GATE_SET_V1` work addresses this correctly; keep frequency-aware trade-count floors rather than loosening PF floors. The bigger issue is asymmetry: Phase 0 is fortress-grade while the demo floor ran five same-family clones across four symbols (three of which were never the family's validation target) with ad-hoc lot increases. Apply one-tenth of the Phase 0 discipline to deployment decisions and the system is coherent.

**Are we overfitting by testing many candidates?** The pipeline's multiplicity controls (D2 ledger, SHA locks, no-tune-v0) are genuinely good. The live overfitting risk is elsewhere: (a) per-cluster repair rules built on 3–7 trades, (b) session/symbol whitelists derived from one week, (c) variant proliferation (WR50, P2WEAKNESS, repairs, W1D1 × 2) — each new lane is another implicit hypothesis test against the same week of data. Fewer, bigger rules; minimum-n thresholds; one fresh forward week before promotion — rules you already wrote. Follow them.

**Candidate discovery pipeline?** Your own Wave 4–6 conclusion is correct and final for this information set: the signal layer is exhausted on retail OHLC. Stop paying the mining tax. New candidates only when there is genuinely new information (order flow/depth, options surface, positioning granularity) or a new validated instrument. Validation before any new EA touches demo: locked hypothesis → 9-cell matrix at as-deployed cost model → cost_R structural precheck → observer-only forward ≥2 weeks → owner sign-off. That last observer step is the one your current lanes keep skipping.

**Is the status page useful for owner decisions?** Not in its current form. 13 MB of generated HTML answers "is the bureaucracy consistent," not "what should I do today." The owner page should be one screen: unique-view net AED (day/week), per-EA PF table with verdict colors, open risk, guardian state, the single next decision with its evidence link. Everything else on demand.
