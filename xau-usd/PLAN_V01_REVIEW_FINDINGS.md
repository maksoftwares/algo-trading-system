# XAUUSD Master EA Plan v0.1 — Review Findings

**Reviewed:** 2026-05-20
**Plan document:** `xauusd_algo_trading_system_plan_v0_1.md`
**Review prompt:** `xauusd_algo_review_prompt.md`
**Reviewer context:** Carries forward learnings from V61, V77, V80, V85, and GBPUSD Specific V1 reviews.

---

## 0. Executive Summary

**Overall verdict: Approved with changes — do not start Phase 1 coding yet.**

The architecture is the correct pivot away from the V61→V85 incremental tuning line. "Regime first, risk second, signal third, execution last" is the right ordering, and "default state = NO_TRADE" is the right discipline. Centralizing risk and lot sizing, mandating one active expert at a time, and forbidding martingale/grid/recovery logic are non-negotiables you already got right.

However, the plan as written reads like a textbook design that any retail algo team could have produced. It is missing **five things that your own prior reviews proved you need**:

1. An edge thesis tied to actual XAU behaviors that have shown holdout survival.
2. Hard blocking gates on sample size, cost-adjusted PF, holdout degradation, and concentration.
3. A magic-number plan that prevents collision with V85 and any other currently-deployed EA.
4. Recognition that the **Regime Router is the highest overfitting risk in the entire system**, with corresponding versioning and audit logging.
5. An automatic retirement mechanism for experts that fail post-deployment gates — V85 was named "NoOverfit" but still shipped EMR .mqh files. Don't repeat that pattern.

Fix items 1–5 below, answer the open decisions in §11, and this plan becomes coding-ready.

---

## 1. The Five Must-Change Items

### Must-change 1 — Plan has no edge thesis

**Issue:** Sections 9.1–9.3 describe Trend Pullback, Range Mean-Reversion, and Fakeout / Liquidity Sweep as generic categories. None of them references a specific XAU pattern that has demonstrated holdout survival in your prior validation work.

**Evidence from your prior work:**
- V61 large wins concentrated in **squeeze_long** and **post_spike_short** — these are XAU-specific squeeze/exhaustion behaviors, not generic "trend pullback" or "range" plays.
- V80/V85 retained an **EMR inactivity-long** specialist (extreme mean reversion after activity gate triggers) — that is a *specific* mechanic, not a generic regime.
- GBPUSD V1 attempted a "Delayed Long Compact" expert chosen on 7 train trades — it collapsed on holdout because the underlying pattern was statistical noise, not an identifiable market behavior.

**Required action:** Before any Phase 1 code is written, produce a one-page **Edge Thesis Document** with this structure for each of the three v1 experts:

```text
Expert: <name>
Underlying market behavior: <one paragraph — what is gold actually doing in the market when this expert is right?>
Evidence of persistence: <pointer to V61/V80/V85 validation results, or to new statistical work showing the behavior exists across multiple years>
Failure modes: <when does this behavior break down? what regimes invalidate it?>
Why it deserves a slot: <what is this expert capturing that the other two cannot?>
```

If you cannot fill this in for an expert, **do not build that expert**. Build infrastructure and one expert that you *can* defend.

---

### Must-change 2 — Sample-size, cost, and concentration gates must be hard blockers, not review targets

**Issue:** Section 13 lists profit factor, drawdown, parameter stability, etc. as "review targets". In practice, you have approved experts that should have been blocked by these criteria. The criteria need to be *executable* and *blocking*, not advisory.

**Evidence from your prior work:**
- GBPUSD "Delayed Long Compact": 7 train trades, PF 4.46, 0 losing months → holdout PF 1.49, 8 losing months, worst month −$72. Should have been blocked at "minimum trade count" gate.
- GBPUSD RSI component: train PF 1.13 (within noise of 1.0), cost-adjusted net ~$14 over 3 years — passed your previous bar.
- V85 EMR: 100% win rate on 11 trades after RSI-off variant tested — 11 trades is too few to draw any conclusion.
- V61 monthly data: ~22 dead months and extreme return lumpiness — would have been caught by a "max-zero-trade months" check that does not currently exist.

**Required action:** Add to §13 (Expert Approval Criteria) as **blocking checks that must pass before an expert can be enabled in any environment beyond dry-run**:

| Check | Threshold | Rationale |
|---|---|---|
| Minimum train trades | ≥ 40 | Below this, PF is unstable noise |
| Cost-adjusted train PF | ≥ 1.50 | Net of modeled spread + commission |
| Holdout / train PF ratio | ≥ 0.70 | Catches curve-fits — GBPUSD Delayed Long Compact failed this at 1.49/4.46 = 0.33 |
| Holdout losing months / total months | ≤ 35% | Catches lumpy P&L distributions |
| Single trade contribution to net P&L | ≤ 10% | Catches V61-style "two trades own the year" |
| Single engine contribution to portfolio P&L | ≤ 40% | Catches V80-style 81% concentration |
| Single month contribution to net P&L | ≤ 30% | Catches a 2024-Mar-style anomaly month carrying the year |
| Max consecutive zero-trade months | ≤ 3 | Catches V61's 22 dead months pattern |

These thresholds are *defaults* — you can tune them later, but they must exist in code as `kMin*` constants the EA reads at startup, not in a Word document.

---

### Must-change 3 — Magic-number plan is missing

**Issue:** Section 7.8 (Position Manager) and §17 (Configuration) do not mention magic numbers at all. This is the single deployment failure mode you have personally hit.

**Evidence from your prior work:**
- V61 deployment observation: *"Magic Number Collisions Require Full Package Replacement."* You already paid this cost once.
- V77 introduced a new magic namespace vs V61 — proof you understand this matters but it is undocumented in the new plan.
- V85 is presumably still running on Capital.com-Demo #1025742 with its own magic ranges.

**Required action:** Reserve magic-number ranges *before* writing OrderSend code. Suggested layout:

```text
Master EA reserved range:  920000 – 929999
  Trend Pullback Expert:   920000 – 920099  (XAU only)
  Range MR Expert:         920100 – 920199  (XAU only)
  Breakout-Retest Expert:  920200 – 920299  (XAU only)  ← see Must-change item below
  Fakeout Expert:          920300 – 920399  (XAU only — deferred to v1.5)
  Reserved future experts: 920400 – 929999

Documented occupied (do NOT collide):
  V85 production:  <fill in actual range>
  V61 archive:     <fill in actual range>
  V77/V80:         <fill in actual range>
```

Bake this into a `magic_numbers.md` file in the project root and into a `MagicNumberAllocator` module in code. Every `OrderSend` must call this allocator. No expert may pick its own magic.

---

### Must-change 4 — Regime Router needs to be treated as the highest overfitting risk in the system

**Issue:** §7.5 describes the router as the most important module but treats it as plumbing. In practice, a regime classifier with thresholds on ADX, ATR percentile, EMA slope, range width, BoS/ChoCh, distance-from-moving-average, volatility percentile, spread percentile, etc. has **more tunable knobs than any single trading expert**. Every additional condition is a potential curve-fit.

**Evidence from your prior work:**
- Every prior strategy you have reviewed (V61, V77, V80, V85, GBPUSD) failed *first* at the filter / gate layer — too many filters that worked perfectly on train and broke on holdout.
- V85's "NoOverfit Core" tightened filters but did not prevent the EMR concentration problem from persisting.

**Required action:** Apply four mitigations:

1. **Version the Router independently from experts.** `router_v1.0`, `experts_v1.0`. Either can change without bumping the other. Every backtest log records both versions.
2. **Lock router thresholds early from objective stats, not optimization.** Set ADX trend cutoff from the long-run ADX distribution on XAUUSD (e.g., 70th percentile). Do not tune router thresholds per expert later — that re-enables curve-fitting through the back door.
3. **Log "would-have-allowed" for every blocked expert on every bar.** This is the single most important diagnostic you can build. Without it, you cannot tell whether the router is correctly filtering or silently strangling a profitable expert.
4. **No router changes after Phase 4.** Once experts are calibrated against `router_v1.0`, freeze the router. If the router needs to change, every expert calibrated against the prior version is re-validated.

---

### Must-change 5 — Automatic retirement mechanism is missing

**Issue:** The plan has approval gates but no clearly-defined retirement gates. V85 was called "NoOverfit" but still shipped EMR .mqh files because retirement was a human decision, not a code-enforced one.

**Evidence from your prior work:**
- V85 package structure observation: *"EMR .mqh files still present despite 'NoOverfit' name."*
- V80 obs: *"Retires thin-sample engines in .set"* — but only in the .set file, not in code.

**Required action:** Add a Phase 2 module: `ExpertLifecycleManager`. Behaviors:

```text
On EA startup:
  For each expert:
    Read last-N-months performance from logs
    If holdout/train PF ratio < 0.70  → status = RETIRED
    If concentration > thresholds      → status = RETIRED
    If 3 consecutive losing months     → status = SUSPENDED (auto re-evaluate monthly)
    Otherwise                          → status = ACTIVE

If status = RETIRED:
  EnableExpert = false (forced, ignores .set file)
  Log retirement with reason
  Source file moved to _retired/  (or excluded from compile via #ifdef ENABLE_<EXPERT>)

If status = SUSPENDED:
  Expert runs in dry-run mode only
  After 1 month, re-evaluate
```

This converts retirement from a discipline problem into a code problem. Discipline problems repeat. Code problems do not.

---

## 2. Top 5 Nice-to-Have Improvements

1. **Dry-run mode as a first-class environment.** Phase 1 should boot the EA in a mode where the full decision pipeline runs (router, risk manager, execution guard, position manager) but `OrderSend` is a no-op that writes "would-have-traded" rows to the trade log. This lets you run alongside V85 for weeks at zero risk and validate the router *empirically* before committing capital.

2. **Time-based news blackout as fallback to calendar API.** MQL5 calendar APIs are fragile (failed feeds, time-zone drift, broker server clock skew). Hardcode a backup schedule:
   - NFP: first Friday of month, 12:25–13:30 UTC
   - FOMC rate decision: 17:55–19:30 UTC on scheduled dates
   - CPI: 12:25–13:30 UTC on release dates
   - Use the API when reachable, fall back to the schedule when it is not, and log which source blocked the trade.

3. **Explicit cost model in §11.** Add to the plan: *"Capital.com XAUUSD typical spread = X points, modeled commission = Y per lot, modeled slippage = Z points."* Every approval criterion is evaluated against *this* cost model, and the assumed values are written into the .set file header so every backtest is reproducible.

4. **Per-backtest concentration report.** Phase 6 (Backtesting and Debugging) should auto-generate a `concentration_report.csv` after every run with: per-expert P&L share, per-month P&L share, single-largest-trade share, top-5-trades P&L share. The report is the deliverable, not the equity curve.

5. **Snapshot bundle for every released version.** Zip = EA binary + .set file + tick data range (start/end dates) + broker ID + magic ranges + git commit hash + concentration report + holdout report. This is your audit trail. V61_Improvement_Lab already started this — formalize it as a `tools/snapshot.ps1` script.

---

## 3. Module-Level Review

### A. Architecture

**Verdict: Approved.**

- One master EA with internal modules is correct for MT5/MQL5. Separate EAs would require cross-EA risk coordination, which MT5 does not natively support.
- Modules should be **include files (`.mqh`)** organized as classes, not separate compilation units. Class-based modules + dependency injection at the master EA level gives you testability without runtime overhead.
- Separation between Router, Risk Manager, Execution Guard, Position Manager, Logger is correct as drawn.

**One revision:** Add **`ExpertLifecycleManager`** (per Must-change 5) and **`MagicNumberAllocator`** (per Must-change 3) to the §3 module list.

---

### B. Regime Classification

**Verdict: Needs revision — too many regimes, definitions too loose.**

- 21 regimes is too many. You cannot validate that many states with the data you have.
- Recommended v1 regime set (collapse from 21 to **7**):
  - `TREND_WITH_PULLBACK`  (handles TREND_UP, TREND_DOWN, PULLBACK_IN_UPTREND, PULLBACK_IN_DOWNTREND)
  - `RANGE`
  - `COMPRESSION`
  - `BREAKOUT_RETEST`  (handles BREAKOUT_UP/DOWN and BREAKOUT_RETEST_UP/DOWN)
  - `ABNORMAL_MARKET`  (handles GAP_UP/DOWN, NEWS_SPIKE_*, SPIKE_EXHAUSTION_*, FAKEOUT_*)
  - `NEWS_BLACKOUT`
  - `NO_TRADE`  (default)

- **Regimes to delay until v2:** Reversal, News Spike Continuation, Spike Fade. These need execution data you do not yet have.
- **Regime definitions must be objective and codable.** Example: "TREND" is not "HTF bias is bullish" — it is "ADX(14) on H1 ≥ 25 AND EMA(50)/EMA(200) slope same sign AND price > EMA(50)". Define every regime to this level of specificity before Phase 3.

---

### C. First Expert Selection

**Verdict: Modify — swap Fakeout for Breakout-Retest.**

**Approved:**
- Trend Pullback Expert — most defensible, easiest to backtest cleanly.
- Range Mean-Reversion Expert — needs strict range-validity gate (width ≥ N × spread, ≥ M touches of each boundary) but workable.

**Replace:**
- ❌ Fakeout / Liquidity Sweep Expert → ✅ **Breakout-Retest Expert**

**Why swap:**
- Fakeout / liquidity sweep detection on M5 has very high false-positive rate. "Price swept below prior low and reclaimed" is a fuzzy definition that will require subjective tuning, which is exactly what blew up the GBPUSD Delayed Long Compact expert.
- Breakout-Retest is mechanically defined: a level was broken, price returned to within N points of the level within K bars, the retest held (lower wick / no close below level), and a continuation candle formed. Every condition is countable.
- Breakout-Retest also gives you an entry mode you currently lack — it can use **stop entries** (limit orders to enter on confirmation), reducing market-order slippage exposure.

**Recommended v1.5 addition:** Once Phase 8 demo data proves spread/slippage behavior, add the Fakeout expert.

**Recommended build order:**
1. Trend Pullback (highest mechanical clarity, builds first)
2. Breakout-Retest (next clearest, validates limit-order infrastructure)
3. Range MR (depends on robust range-validity gate)

---

### D. Risk Management

**Verdict: Approved with two changes.**

**Approved as written:**
- Risk per trade 0.25–0.50%
- Max daily loss 1–2%
- Max weekly loss 3–5%
- Forbidden behaviors list

**Required changes:**
1. **Add monthly hard stop.** Plan jumps from weekly (3–5%) to total drawdown with nothing in between. V61 had a `-$35 monthly hard stop` for a reason. Recommended: `MaxMonthlyLoss = 6–8%` of starting-of-month equity. When breached, EA switches to dry-run mode for the rest of the month.
2. **Specify daily-loss accounting:** **equity-based, including floating drawdown.** Realized-only daily loss allows a losing trade to stay open across the cap; equity-based forces the cap to be enforced in real time.

**Open decision (answered):**
- Should daily loss force-close open trades? **Yes** — if equity-based daily cap is hit, force-close all open trades and lock the EA until the next trading day. This is more conservative than the plan suggests but matches your existing portfolio-governor pattern.

---

### E. Execution and Broker Realism

**Verdict: Needs revision — spread/slippage rules too vague.**

- `MaxSpreadPoints = configurable` is not a rule — it is a placeholder. Write the actual rule.
- **Recommended spread rule:** Block if `current_spread > max(30 points absolute, 1.5 × 20-bar_median_spread)`. Both clauses must be checked — absolute floor protects against rollover spikes, dynamic clause protects against quiet-session spread compression that would otherwise let bad fills through.
- **Recommended slippage rule:** Block market orders if `Ask - lastQuote.Ask > 5 points` (broker requote behavior). Use limit orders with `MaxDeviation = 3 points` for Breakout-Retest expert.
- **Market orders allowed?** Only for Trend Pullback (which needs immediacy of entry). Range MR and Breakout-Retest should use limit/stop orders.

**Execution risks not currently covered:**
1. **Capital.com tick data quality during news.** Your prior work confirmed Capital.com-Demo only provides tick data from 2026.01.01 — historical backtests use bar data, not tick data, for pre-2026 periods. This needs to be flagged in §14 (Data Plan).
2. **Symbol suffix variants.** Some brokers expose `XAUUSD`, `XAUUSD.`, `XAUUSDm`, etc. Master EA must read `_Symbol` at runtime, not hardcode.
3. **Server time vs broker time vs UTC drift.** Add a server-time validation check at startup that compares `TimeCurrent()` against an NTP-derived reference, and aborts startup if drift > 60s.

---

### F. News and Calendar

**Verdict: Approved with one addition.**

- v1 should **block all high-impact USD news.** No news trading expert in v1.
- Pre-news blackout: **30 minutes**.
- Post-news cooldown: **30 minutes** (covers the initial spike, the retracement, and the second-leg fakeout).
- Open trades **must be closed** before CPI / NFP / FOMC. Holding through these events is incompatible with the 0.25–0.50% risk-per-trade model — a single 200-point news spike at 1.0 lot is 4× your daily risk budget.
- Calendar source: MT5 built-in economic calendar as primary, **hardcoded time schedule as fallback** (per Nice-to-Have item 2).

---

### G. Position Management

**Verdict: Approved with simplifications for v1.**

**v1 exit model:**
- ✅ Hard stop loss on every trade (mandatory, no exceptions)
- ✅ ATR-based take profit (1.5–2.0R targets)
- ✅ Break-even at +1R (price moves favorably by stop distance, SL moves to entry)
- ❌ Partial close — **disable in v1**. Adds complexity and obscures expert P&L attribution.
- ❌ Trailing stop — **disable in v1**. Adds parameters that are extremely prone to curve-fit. Consider in v1.5 only if break-even isn't capturing enough.
- ✅ Time stop: close trade if not at +0.5R within 4 hours
- ✅ Session exit: close all positions 30 minutes before broker daily rollover
- ❌ Hold overnight: **no** in v1. Friday-close enforces this.
- ❌ Hold weekend: **no** in v1. Mandatory.

**Centralized vs expert-specific exits:** Centralize the *mechanism* (one Position Manager handles all SL/TP/BE/Time logic) but allow per-expert *parameters* (Trend Pullback can use different ATR multipliers than Range MR). This gives you per-expert tunability without code duplication.

---

### H. Testing and Validation

**Verdict: Needs additions — walk-forward and stress-test sections are too brief.**

**Required historical test periods (XAU-specific):**
1. **2020-03 to 2020-04** — COVID volatility crash + rally. Stress test for ATR extremes.
2. **2022-09 to 2022-11** — Strong USD trend (DXY peak). Stress test for sustained-trend behavior of Range MR (it should *not* trade).
3. **2023-03** — SVB / banking crisis week. Stress test for gap and abnormal-market handling.
4. **2024-04** — Iran/Israel geopolitical spike. Stress test for news-blackout effectiveness.
5. **2025 full year** — Most recent regime, closest to expected forward behavior.
6. **Continuous 5-year M5 backtest** — overall expectancy validation.

**Walk-forward specification:**
- Method: **anchored walk-forward** (train window grows, validation window slides).
- Initial train window: 18 months.
- Validation window: 3 months.
- Step: 3 months.
- Acceptance: holdout PF ≥ 0.70 × train PF on **every fold**, not just average. One bad fold is grounds for rejection — your priors show median PF hides catastrophic months.

**Stress tests to add to §12.4:**
1. **Spread × 2 sustained for a full session** (rollover scenario).
2. **VPS restart at random tick** (recovery / open-position state).
3. **Symbol disabled mid-session** (broker maintenance / leverage change).
4. **Negative balance / margin call simulation** — does the EA stop trying to send orders?

**Minimum forward-test duration:** 6 weeks demo, of which 2 weeks must include at least one high-impact USD news event.

---

### I. Logging and Diagnostics

**Verdict: Approved with one critical addition.**

**Missing log field — add to §7.9:**
- **`would_have_allowed_experts`** — list of experts that *would have* been activated if the router had not blocked them. Per Must-change item 4, this is the single most important diagnostic. Without it, you cannot audit the router's decisions.

**Recommended format:** CSV is sufficient for v1. SQLite if you want queryable history later, but CSV first.

**Recommended dashboard fields are correct.** Add one row: `would_have_allowed: <list>` so you can see in real time what the router is blocking.

---

### J. Missing Risks and Failure Modes

The plan's §22 Risk list is too generic. Specific failure modes to add, derived from your prior incidents:

1. **Magic number collision with existing live EAs** (V61 lesson). Mitigation: Must-change 3.
2. **"Approved" expert that fails on the first holdout fold but passes on average** (GBPUSD Delayed Long Compact lesson). Mitigation: Must-change 2, every-fold acceptance rule in §H above.
3. **Filter that ships as a configurable input but defaults to "on" in the .set file** (GBPUSD "NoCalendarGuard" lesson — EA name implied no calendar filter, source had a live 12-month input filter that was just defaulted to all-true). Mitigation: every configurable filter must be documented in a `filter_inventory.md` listing every filter, its default, and whether disabling it has been tested.
4. **Reported P&L that varies by aggregation method** (GBPUSD: combined Full was reported as $616 / $781 / $571 across three methods). Mitigation: one authoritative tester run per release, P&L reported from that run only.
5. **EA continues to send orders after broker rejects a series of orders** (potential live failure mode). Mitigation: after 3 consecutive `OrderSend` failures, EA enters LOCKED_MODE.
6. **Strategy degradation detected too late** (no live drift detection currently planned). Mitigation: daily P&L vs backtest expectation, alert if 7-day rolling PF drops below 0.8 × backtest PF.

---

## 4. Answers to the 10 Specific Questions (from review prompt §3)

| # | Question | Answer |
|---|---|---|
| 1 | Proceed with master EA architecture? | **Yes**, with Must-change items applied. |
| 2 | v1 includes only 3 trading experts? | **Yes** — but swap Fakeout for Breakout-Retest. |
| 3 | Are Trend Pullback, Range, Fakeout the correct first experts? | **No** — replace Fakeout with Breakout-Retest in v1. |
| 4 | Should Breakout-Retest be included earlier? | **Yes**, in v1 (replacing Fakeout). |
| 5 | Should news trading be disabled in v1? | **Yes**, completely disabled. |
| 6 | Are proposed risk limits acceptable? | **Yes**, with addition of monthly hard stop. |
| 7 | Is "only one active expert at a time" correct for v1? | **Yes** — non-negotiable for v1 debuggability. |
| 8 | Is the regime router too restrictive? | **No** — being restrictive is the point. Restrictive routers produce explainable behavior. |
| 9 | Are testing standards strong enough? | **No** — walk-forward and stress tests need the additions in §H above. |
| 10 | What should be changed before coding starts? | The five Must-change items in §1 of this document. |

---

## 5. Missing Modules

The following modules are not in the plan but are required:

1. **`MagicNumberAllocator`** — single source of truth for magic-number assignment. (Must-change 3)
2. **`ExpertLifecycleManager`** — automatic retirement / suspension of failing experts. (Must-change 5)
3. **`DryRunMode`** — full pipeline runs but `OrderSend` is a no-op. (Nice-to-have 1)
4. **`ServerTimeValidator`** — startup check that broker time matches NTP reference within 60s. (§E above)
5. **`LiveDriftMonitor`** — daily comparison of live P&L vs backtest expectation, alerts on degradation. (§J above)
6. **`ConcentrationReporter`** — auto-generates per-engine / per-month / per-trade contribution after each backtest. (Nice-to-have 4)

---

## 6. Recommended MVP Scope (Adjusted)

Replace §21 of the plan with this scope:

**Build for v1:**
- Master EA shell
- Market Data Engine
- Feature Engine
- Session Engine
- News Guard (with time-based fallback)
- Regime Router (versioned, 7 regimes, frozen after Phase 3)
- Risk Manager (with monthly hard stop, equity-based daily cap)
- Execution Guard (with explicit spread/slippage rules)
- Position Manager (no partial close, no trailing in v1)
- Logger (with would-have-allowed field)
- Dashboard
- **MagicNumberAllocator** ← new
- **ExpertLifecycleManager** ← new
- **DryRunMode** ← new
- **ServerTimeValidator** ← new
- Trend Pullback Expert
- Breakout-Retest Expert ← replaces Fakeout
- Range Mean-Reversion Expert

**Defer to v1.5:**
- Fakeout / Liquidity Sweep Expert (after demo data validates execution model)
- LiveDriftMonitor
- ConcentrationReporter

**Defer to v2+:**
- Trend Continuation, Compression Breakout, Reversal, News Spike, Spike Fade, Gap / Abnormal experts
- Multi-symbol support
- External macro feeds
- Machine learning

---

## 7. Recommended First Coding Milestone

**Milestone 1 (Phase 1 + Phase 2):**

> Master EA boots on the Capital.com-Demo account, runs in dry-run mode, classifies regime on every bar, logs to `decision_log.csv` with one row per bar, displays dashboard, and respects daily/weekly/monthly risk caps. **No expert is enabled yet.** No `OrderSend` calls in the codebase.

**Acceptance criteria for Milestone 1:**
- EA runs for 5 trading days continuously without runtime errors.
- `decision_log.csv` has one row per M5 bar with valid regime classification.
- Dashboard updates correctly.
- Server time validator catches a deliberately-injected time skew.
- Risk caps trigger correctly under simulated equity-curve injection.

This is roughly **3–4 weeks of focused work**. Do not start Milestone 2 (first expert) until Milestone 1 has run 5 clean days.

---

## 8. Pre-Coding Decisions Still Open

These need answers before Phase 1 starts:

1. **V85 coexistence vs replacement.** Is V85 staying on Capital.com-Demo #1025742 while the new EA builds, or is it being retired? Affects magic-number plan, risk budget, and whether dry-run mode can run on the same account.
2. **Platform commitment.** §4 still hedges between MT5, MT4, Python, cTrader. Commit to MT5/MQL5 — your toolchain, tick data, and existing EAs are all MT5. Pick MT5 and remove the hedging language.
3. **Build cadence.** Phases 1–9 sequentially is realistic at ~3–4 weeks per phase = **9–12 months to live pilot**. Confirm this is acceptable, or scope-cut now.
4. **VPS / hosting plan.** §16.1 lists environments but does not say where the demo forward-test will run. If on the same desktop as MT5_TestInstance, you have a power-loss single-point-of-failure.
5. **Walk-forward acceptance threshold.** Must-change 2 proposes holdout/train PF ≥ 0.70. Is that the right number for your risk tolerance, or should it be 0.80?

---

## 9. Final Recommendation

The plan is the correct architectural pivot. After five prior strategy reviews ending in concentration risk, marginal cost-adjusted edges, and undocumented filter foot-guns, building a regime-routed master EA with centralized risk and execution protection is the right next step.

But the plan as written would, if implemented verbatim, repeat the V77/V80/V85/GBPUSD failure pattern at higher complexity. The architecture is necessary but not sufficient. What makes it work is the **discipline encoded in code**, not in documents:

- Hard sample-size and concentration gates (not "review targets").
- A magic-number allocator (not a convention).
- A regime router that is versioned and frozen (not continuously tuned).
- An automatic retirement mechanism (not a quarterly cleanup task).
- A dry-run mode that proves the system works before any capital is at risk.

If those five things are baked into Phase 1 and Phase 2, this build has a real chance of producing the first strategy in your line that survives holdout *and* survives 6 months of live demo without quiet degradation.

If they are not, you will be back here in 6 months reading the V90 review document and recognizing the same patterns.

**Recommended next step:** Author the **Edge Thesis Document** (Must-change 1) for Trend Pullback, Range MR, and Breakout-Retest. If you can defend all three, start Milestone 1. If you cannot defend one of them, drop it and start with two experts.

---

## Summary Scorecard

| Question | Answer |
|---|---|
| Can this plan be coded as-is? | **No.** Apply five must-change items first. |
| Is the architecture sound? | **Yes.** |
| Are the right experts chosen for v1? | **Mostly** — swap Fakeout for Breakout-Retest. |
| Are the risk limits adequate? | **Almost** — add monthly hard stop, equity-based daily cap. |
| Is the testing protocol sufficient? | **No** — every-fold walk-forward and additional stress tests required. |
| Are the failure modes well covered? | **No** — magic-number, retirement, drift detection missing. |
| Is this a good foundation? | **Yes — after the five fixes.** |
