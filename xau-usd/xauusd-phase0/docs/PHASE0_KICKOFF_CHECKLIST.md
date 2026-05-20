# Phase 0 Kickoff Checklist — Week 1 Action Plan

**Status:** Active execution plan for the first 7 days of Phase 0.
**Source plan:** `xauusd_master_ea_plan_v0_3_phase0_first_review_ready.md`
**Source spec:** `PHASE0_STATISTICAL_STUDY_SPEC.md`
**Date:** 2026-05-20
**Goal of Week 1:** Lock all three hypotheses with SHA256, acquire data, deploy passive spread logger, execute first 9 backtest cells.

---

## 0. Why This File Exists

You have iterated the plan from v0.1 → v0.3 over multiple review cycles. The plan is now 7.5–8/10 ex-ante. Further iteration on the document will not move the rating.

The only thing that moves the rating now is **executing Phase 0**.

This checklist converts the v0.3 plan into a concrete 7-day sequence. Every item has an exit criterion. If you finish Week 1 with all items checked, you are roughly 25% of the way through Phase 0 and on track to a verdict by end of Week 4.

If you cannot start this week, the smallest possible commitment is **Day 0 pre-flight (2 hours)**. Even doing only that breaks the planning-loop.

---

## 1. Day 0 — Pre-Flight (≈ 2 hours)

These are setup items. None require thinking, only doing.

### 1.1 Create the working directory

```text
C:\Users\DELL\Desktop\XAUUSD_MasterEA\
  ├── /phase0/
  │   ├── /hypotheses/
  │   ├── /data/
  │   ├── /backtests/
  │   ├── /reports/
  │   └── /cross_validation/
  ├── /spread_logger/
  ├── /tools/
  └── /reference/
```

Move the v0.3 plan, PATH_TO_10, PHASE0_STATISTICAL_STUDY_SPEC, PLAN_V01_REVIEW_FINDINGS into `/reference/`. Downloads folder is transient; this is the project home.

- [ ] Directory tree created
- [ ] All review documents moved to `/reference/`
- [ ] This checklist file copied to project root

### 1.2 Decide V85 coexistence

The new EA will not have OrderSend in Milestone 1, so technically V85 can keep running. But the passive spread logger and Phase 0 work should run on a **separate broker account** if possible.

- [ ] Decision recorded: V85 stays running on Capital.com-Demo #1025742 / V85 is paused / V85 is migrating
- [ ] If staying: confirm dedicated demo account for new EA — open a second Capital.com-Demo account if needed
- [ ] If migrating: pick the date

### 1.3 Verify toolchain

- [ ] MT5 portable instance is operational (`C:\MT5PortableGoldMission` or the `V61_Improvement_Lab/MT5_TestInstance` clone)
- [ ] Python 3.10+ installed (`python --version`)
- [ ] Required Python packages: `pandas`, `numpy`, `matplotlib`, `pytz`, `hashlib` (builtin). Install with `pip install pandas numpy matplotlib pytz`
- [ ] Optional but recommended: `backtrader` or `vectorbt` for cross-validation (D4 requirement)
- [ ] Git installed (`git --version`) — even local-only repo gives you a free audit trail

### 1.4 Initialize git repo (optional but high-value)

```powershell
cd C:\Users\DELL\Desktop\XAUUSD_MasterEA
git init
git add .
git commit -m "Phase 0 kickoff: directory structure and reference docs"
```

Every hypothesis registration, every backtest result file becomes a tracked commit. Tampering with locked hypotheses becomes git-visible.

- [ ] Git initialized
- [ ] Initial commit recorded

### 1.5 Sanity-check Capital.com data availability

- [ ] Open MT5 on Capital.com-Demo
- [ ] Open the symbol with which XAUUSD is exposed (record exact name: `XAUUSD`, `XAUUSD.`, `XAUUSDm`, `GOLD`, etc.)
- [ ] In History Center, attempt to download M5 data back to 2016-01-01
- [ ] Note the actual earliest available date — Capital.com tick data was previously confirmed only from 2026-01-01, so M5 bar data is what's available pre-2026
- [ ] Document findings in `phase0/data/capital_com_availability_note.md`

---

## 2. Day 1 — Hypothesis Registration

This is the most important day in Phase 0. Once SHA256-locked, the hypotheses cannot be edited without explicit re-versioning.

### 2.1 Write `hypothesis_trend_pullback.md`

Use the template from PHASE0_STATISTICAL_STUDY_SPEC.md §1.3. Required fields:

- Expert name
- Hypothesis date (today)
- Hypothesis version (`v1.0`)
- Mechanical definition (copy from v0.3 §9.1, refine if needed)
- Expected trade count per year: write your honest expectation, e.g. `~80 ± 20%`
- Expected cost-adjusted PF: e.g. `1.6 ± 0.3`
- Expected losing-month percentage: e.g. `40% ± 10%`
- Expected worst single month: e.g. `−$150 at 0.50% risk on $10k`
- Expected max consecutive zero-trade months: e.g. `≤ 2`
- Why this behavior should exist (2–3 paragraphs grounded in XAU microstructure / session liquidity / trend persistence literature — NOT just "pullbacks work")
- What would falsify it (concrete: which gate failures count)

**Critical:** Write what you genuinely expect, not what you hope. Wildly-better-than-expected results are a curve-fit warning per Gate 10.

- [ ] `phase0/hypotheses/hypothesis_trend_pullback.md` written
- [ ] SHA256 computed: `Get-FileHash phase0/hypotheses/hypothesis_trend_pullback.md -Algorithm SHA256`
- [ ] Hash recorded in `phase0/hypotheses/manifest.md`

### 2.2 Write `hypothesis_breakout_retest.md`

Same template. Use v0.3 §9.2 as the starting mechanical definition.

- [ ] File written
- [ ] SHA256 computed and recorded in manifest

### 2.3 Write `hypothesis_range_mr.md`

Same template. Use v0.3 §9.3 as the starting mechanical definition.

- [ ] File written
- [ ] SHA256 computed and recorded in manifest

### 2.4 Commit and seal

```powershell
git add phase0/hypotheses/
git commit -m "Phase 0: hypothesis registration — three v1 expert candidates, SHA256 locked"
```

- [ ] All three hypotheses committed
- [ ] `phase0/hypotheses/manifest.md` contains all three SHA256 hashes, dates, and versions
- [ ] You have read each hypothesis aloud once to verify nothing ambiguous remains

### Exit criterion for Day 1

You can hand any of these three hypothesis files to an unaffiliated MQL5 coder and they could implement the logic with zero ambiguity. If there's any line you'd need to verbally explain, it's not done.

---

## 3. Day 2 — Data Acquisition

Phase 0 requires data from three sources. Get them all today.

### 3.1 Capital.com data

- [ ] Use MT5 History Center to export XAUUSD M1, M5, M15, H1, H4, D1 bars
- [ ] Date range: 2016-01-01 through 2025-12-31 (or earliest available)
- [ ] Save as CSV in `phase0/data/capital_com/`
- [ ] File naming: `XAUUSD_M5_2016_2025_capital.csv` etc.

### 3.2 Dukascopy data

- [ ] Visit https://www.dukascopy.com/swiss/english/marketwatch/historical/
- [ ] Download XAUUSD M1 bars 2016–2025 (free)
- [ ] Save as CSV in `phase0/data/dukascopy/`
- [ ] Note: Dukascopy uses GMT — document timezone for later alignment

### 3.3 Pepperstone data

Pepperstone tick history is not freely downloadable. Options in order of preference:
- [ ] Request from Pepperstone support if you have an account
- [ ] Alternative: use Tickstory (free tier exists) or ForexTester data
- [ ] Alternative: substitute another raw-spread broker (IC Markets, OANDA) and document the substitution
- [ ] If Pepperstone genuinely cannot be obtained, you may proceed with 2 sources and document this as a known limitation in `PHASE0_DATA_MANIFEST.md` — but flag it explicitly

### 3.4 Comparison symbols (for A5 multi-symbol check)

- [ ] EURUSD M5 2016–2025 from Capital.com
- [ ] USDJPY M5 2016–2025 from Capital.com
- [ ] Save in `phase0/data/capital_com/`

### 3.5 Build the data manifest

Create `phase0/data/PHASE0_DATA_MANIFEST.md` documenting:

- Each broker/source
- Each symbol with exact suffix
- Each timeframe
- Date range actually obtained
- Timezone (UTC, GMT, broker server time, etc.)
- Digit precision
- Point size
- Missing data periods (gaps, weekends excluded by default)
- File path
- File SHA256

- [ ] Manifest written
- [ ] All data files have recorded SHA256 (catches accidental overwrite later)
- [ ] Commit:

```powershell
git add phase0/data/PHASE0_DATA_MANIFEST.md
git commit -m "Phase 0: data acquisition complete, manifest sealed"
```

### Exit criterion for Day 2

`PHASE0_DATA_MANIFEST.md` lists every data file you need for the 27-cell matrix plus EURUSD/USDJPY. Any missing pieces are flagged with a documented workaround.

---

## 4. Day 3 — Passive Spread Logger Deployment

This must run for 4 weeks. Every day you delay deployment costs you a day of measured cost data. Deploy today, even if backtests slip.

### 4.1 Write the spread logger EA

It is intentionally minimal. Pseudocode for `SpreadLogger.mq5`:

```mql5
// On every tick:
//   1. Read Bid, Ask, spread
//   2. Determine session bucket (Asia / London / NY / Rollover / ...)
//   3. Determine if within ±10 min of known red-folder USD news (from MT5 calendar)
//   4. Determine if within rollover window (broker daily close ± 30 min)
//   5. Append CSV row: timestamp_broker, timestamp_utc, timestamp_local,
//      symbol, bid, ask, spread_points, session, hour_of_day, day_of_week,
//      is_news_window, is_rollover_window
//   6. No OrderSend. No state. Pure passive logging.
```

**Implementation tip:** instead of writing per-tick (which is 100k+ rows/day), write once per 5 seconds OR on spread change. Both produce useful distributions without disk thrashing.

- [ ] EA source written, compiled in MetaEditor
- [ ] Compiled with no warnings
- [ ] Attached to XAUUSD chart on dedicated demo account
- [ ] Verified writing to `phase0/spread_logger/spread_log_raw.csv` (or MQL5/Files/ directory)
- [ ] Logged at least 100 rows in first 30 minutes — confirms it's alive
- [ ] Start date recorded: today
- [ ] Target end date recorded: today + 28 days

### 4.2 Schedule the analysis

- [ ] Calendar reminder set for end of Week 4 to run aggregation script
- [ ] `tools/aggregate_spread.py` skeleton written (can be filled in later — just needs to read the CSV, compute medians and P95 per bucket, output `cost_model_measured.csv`)

### Exit criterion for Day 3

Spread logger is running on a dedicated account, writing CSV rows, with a recorded start date. The 4-week clock has begun.

---

## 5. Day 4 — First 9 Backtest Cells (Trend Pullback)

Implement the locked Trend Pullback logic in MT5 Strategy Tester. Run all 9 cells before doing anything else.

### 5.1 Implement Trend Pullback as a backtest-only EA

This EA exists solely to test the hypothesis. It is NOT the production EA. Keep it minimal:
- No router, no risk manager, no execution guard — those are Phase 1+
- Fixed 0.50% risk per trade
- Fixed 1.5R target, no break-even, no trailing, no partial close
- Output: trade list CSV + summary metrics

- [ ] `tools/phase0_trend_pullback_backtest.mq5` written
- [ ] Compiled clean
- [ ] Logic matches `hypothesis_trend_pullback.md` SHA256-locked definition (re-read both side-by-side)

### 5.2 Run cells 1, 2, 3 (2016–2018 Capital.com × 3 cost models)

- [ ] Cell 1: best-case spread (1 point typical) — record metrics row in `phase0/backtests/trend_pullback_matrix.csv`
- [ ] Cell 2: median spread — record
- [ ] Cell 3: P95 spread (until measured data exists, use 2× median as proxy) — record

Cost models implemented by adjusting the slippage parameter in Strategy Tester OR by post-processing the trade list. Either works.

### 5.3 Cross-validation seed

Pick ONE of cells 1–3 to reproduce in Python this week (D4 requirement). Don't do the implementation today — just decide which cell.

- [ ] Cell selected for cross-validation: ___
- [ ] Added to backlog: "Reproduce cell X in Python, compare to MT5 within 5%"

### Exit criterion for Day 4

3 of 27 cells complete. `trend_pullback_matrix.csv` has 3 valid rows. You know the implementation works end-to-end.

---

## 6. Day 5 — Cells 4–9 (Trend Pullback Pepperstone + Dukascopy)

- [ ] Cells 4, 5, 6: 2019–2021 Pepperstone × 3 cost models
- [ ] Cells 7, 8, 9: 2022–2024 Dukascopy × 3 cost models
- [ ] All 9 rows in `trend_pullback_matrix.csv`
- [ ] Quick eyeball: does ANY cell show PF ≥ 1.30? If zero do, the hypothesis is already in trouble. Do NOT add filters to rescue it.

### Critical reminder

If results look bad, your only allowed responses are:
1. Verify the implementation matches the hypothesis (bug check, not logic change)
2. Document the result
3. Move on to Breakout-Retest

Forbidden responses:
- Adding an ADX filter
- Switching to a different EMA period
- Excluding bad months
- Calling it "close enough"

### Exit criterion for Day 5

All 9 Trend Pullback cells completed. Results saved. No emotional reaction to the numbers — they are evidence, not failure.

---

## 7. Day 6 — Breakout-Retest 9 Cells

Repeat the Day 4–5 pattern for Breakout-Retest:

- [ ] `tools/phase0_breakout_retest_backtest.mq5` written matching `hypothesis_breakout_retest.md`
- [ ] All 9 cells run
- [ ] `phase0/backtests/breakout_retest_matrix.csv` populated

### Pacing note

Day 6 is tight. If you slip, push Range MR to Day 7 and let Day 7 absorb both. Don't compromise the rigor for the timeline.

### Exit criterion for Day 6

Breakout-Retest 9-cell matrix complete OR at least 6 of 9 cells done with the remaining 3 scheduled.

---

## 8. Day 7 — Range MR 9 Cells + Week 1 Wrap

- [ ] `tools/phase0_range_mr_backtest.mq5` written matching `hypothesis_range_mr.md`
- [ ] All 9 Range MR cells run
- [ ] `phase0/backtests/range_mr_matrix.csv` populated

### Week 1 wrap-up

- [ ] Re-verify all three hypothesis SHA256 hashes match manifest (no accidental edits)
- [ ] Commit all results to git
- [ ] Spread logger is still running and has produced ~5–7 days of data
- [ ] Note Week 1 lessons in `phase0/week1_retrospective.md`:
  - What surprised you?
  - What's running smoothly?
  - What's behind schedule?
  - Any hypothesis you already suspect will fail Gate 1?

### Exit criterion for Day 7

All 27 backtest cells complete and results saved. Three matrix CSVs exist. Spread logger still running. Hypotheses still SHA256-valid.

---

## 9. Week 2 Preview (for context only — do not start yet)

| Day | Activity |
|---|---|
| 8 | Decile persistence test — Trend Pullback (10-decile split, 2016–2025 Capital.com) |
| 9 | Decile persistence — Breakout-Retest + Range MR |
| 10 | Adversarial counter-example search — Trend Pullback (1 day, manual review of losers) |
| 11 | Adversarial — Breakout-Retest |
| 12 | Adversarial — Range MR |
| 13 | Multi-symbol consistency check — all three on EURUSD + USDJPY |
| 14 | Python cross-validation of one cell per expert (D4 requirement) |

Week 3: Verdict preparation, results.md per expert, PHASE0_VERDICT.md draft.

Week 4: Final review, spread logger results, signed verdict.

---

## 10. Files Produced By End of Week 1

```text
/phase0/
  /hypotheses/
    hypothesis_trend_pullback.md          ← SHA256 locked
    hypothesis_breakout_retest.md         ← SHA256 locked
    hypothesis_range_mr.md                ← SHA256 locked
    manifest.md                           ← 3 hashes, dates, versions
  /data/
    PHASE0_DATA_MANIFEST.md
    /capital_com/                         ← XAU + EURUSD + USDJPY
    /dukascopy/                           ← XAU
    /pepperstone/ (or substitute)         ← XAU
  /backtests/
    trend_pullback_matrix.csv             ← 9 rows
    breakout_retest_matrix.csv            ← 9 rows
    range_mr_matrix.csv                   ← 9 rows
  /reports/                               ← empty (Week 3)
  /cross_validation/                      ← empty (Week 2)
  week1_retrospective.md
/spread_logger/
  SpreadLogger.mq5
  spread_log_raw.csv                      ← growing daily
/tools/
  phase0_trend_pullback_backtest.mq5
  phase0_breakout_retest_backtest.mq5
  phase0_range_mr_backtest.mq5
  aggregate_spread.py (skeleton)
```

---

## 11. Common Mistakes to Avoid (from PHASE0_STATISTICAL_STUDY_SPEC §10)

These are the behaviors that have killed every prior strategy in your line. Re-read this list before each work session:

1. **Adding filters when a cell fails.** Curve-fit. Reject the candidate instead.
2. **Tweaking the mechanical definition.** Locked at SHA256. Edits require new hypothesis version.
3. **Excluding outlier trades.** Concentration gate catches them; don't retroactively remove.
4. **Re-running with different starting capital.** $10,000 fixed.
5. **Cherry-picking the "best" cell as evidence.** Gate 1 needs 7 of 9.
6. **Skipping adversarial search because backtest looks good.** Adversarial is where logic gaps live.
7. **Rationalizing failed gates as "close enough".** PF 1.29 is not 1.30.
8. **Running only in MT5.** Cross-validate one cell in Python — Strategy Tester has known modeling quirks.

---

## 12. Done Definition for Week 1

You can sign off Week 1 when:

- [ ] All three hypotheses are SHA256-locked and committed to git
- [ ] All 27 backtest cells have results recorded in matrix CSVs
- [ ] Spread logger has been running ≥ 5 days with growing CSV
- [ ] Data manifest documents every source and timezone
- [ ] Cross-validation cell is chosen and scheduled
- [ ] Week 1 retrospective is written
- [ ] You have NOT edited any hypothesis file since SHA256 lock
- [ ] You have NOT added filters to rescue failing cells
- [ ] You can describe your three pre-registered hypotheses from memory

---

## 13. If Week 1 Slips

The plan assumes 40 focused hours over 7 days. Reality usually shaves that to ~25 hours.

Acceptable slip path:
- Day 1 (hypotheses) and Day 3 (spread logger) are **non-negotiable**. The spread logger 4-week clock cannot start retroactively.
- Day 2 (data) can shift to a weekend.
- Days 4–7 (backtests) can spread into Week 2. The 27 cells must be done by end of Week 2, not necessarily Week 1.

Unacceptable slip:
- Editing a hypothesis after SHA256 lock to "improve" results
- Skipping cross-validation
- Skipping the spread logger to "save time"
- Letting Phase 0 drift into Week 8 because "the planning needs more work"

---

## 14. After Week 4 — Verdict Day

When all of Phase 0 is complete, you write `PHASE0_VERDICT.md` with the master table:

```text
| Expert         | Gate 1 | Gate 2 | Gate 3 | ... | Gate 10 | FINAL  |
|----------------|--------|--------|--------|-----|---------|--------|
| Trend Pullback | PASS   | PASS   | FAIL   | ... | PASS    | FAIL   |
| Breakout-Retest| PASS   | PASS   | PASS   | ... | PASS    | PASS   |
| Range MR       | FAIL   | PASS   | PASS   | ... | FAIL    | FAIL   |
```

Then make the call per the decision tree in v0.3 §12:

- **3 pass** → Phase 1 begins with 3-expert v1.
- **1–2 pass** → Phase 1 begins with reduced v1.
- **0 pass** → Project stops. Research new candidates. This is a successful outcome.

---

## 15. The Discipline Bet

Every previous strategy in your line (V61, V77, V80, V85, GBPUSD V1) failed in one of two ways:

1. **Built first, validated later.** Optimization had already shaped the EA before honest evaluation. Sunk-cost pressure made retirement harder.
2. **Validated loosely.** Generous criteria let weak edges through. The market eventually delivered the rigor that the development process didn't.

Phase 0 is the bet that doing it differently this time produces a different outcome. The discipline is not in the plan document — it is in **executing this checklist without shortcuts**.

The plan is good enough. The hypotheses are clear enough. The data is available enough.

The remaining variable is whether you actually run the experiment.

Start with Day 0 today. Two hours. That's all it takes to break the planning loop.
