# Phase 0 Statistical Study — Executable Specification

**Purpose:** Confirm or reject the edge thesis for each v1 expert candidate **before any expert code is written**.
**Status:** Mandatory pre-Phase-1 deliverable.
**Estimated duration:** 3–4 weeks focused work.
**Output:** `PHASE0_RESULTS.md` per expert + consolidated `PHASE0_VERDICT.md`.
**Related:** `xauusd_master_ea_plan_v0_2_review_ready.md`, `PATH_TO_10.md`.

---

## 0. Why Phase 0 Exists

The v0.2 plan requires an Edge Thesis Document for each expert (§5.1). But documentation is not evidence. Phase 0 produces the evidence.

The single largest reason retail algo strategies fail is that the underlying edge was never demonstrated to exist before tuning began. Once tuning starts, you can make almost any logic profitable on **any one time period at any one cost model** — and that fact has bitten every prior strategy in this line (V61 concentration, V77 thin samples, GBPUSD Delayed Long Compact, etc.).

Phase 0 forces the question: **does this behavior have positive expectancy on XAU when nothing is optimized?**

If yes → proceed to Phase 1.
If no → do not build that expert. Find a defensible candidate first.

---

## 1. Pre-Requisites

### 1.1 Data Requirements

| Item | Specification |
|---|---|
| Primary symbol | XAUUSD |
| Timeframes | M1, M5, M15, H1, H4, D1 |
| Date range | 2016-01-01 through 2025-12-31 (10 years) |
| Tick sources | Capital.com (primary), Pepperstone, Dukascopy (minimum 3) |
| Comparison symbols | EURUSD, USDJPY (same date range, primary broker only) |
| Cost data | Measured spread distribution from §B1 if available, else broker-published typical/max spread |

**Tick data acquisition:**
- Capital.com: MT5 history center on existing demo account
- Dukascopy: https://www.dukascopy.com/swiss/english/marketwatch/historical/ (free CSV download)
- Pepperstone: Request from broker or use third-party (Tickstory, ForexTester)

### 1.2 Tooling

| Tool | Use |
|---|---|
| MT5 Strategy Tester | Primary backtest runner per cell |
| Python (3.10+) with pandas, numpy | Decile analysis, statistical aggregation |
| Python with `mlfinlab` or equivalent | (Optional) Reality Check / SPA test for D2 |
| Excel / LibreOffice Calc | Result matrix consolidation |
| Git | Version control for analysis scripts |

### 1.3 Pre-Registered Hypotheses

For each candidate expert, write the hypothesis **before** running any test. Store as `hypothesis_<expert>.md` with date, version, and a SHA256 of the file content captured at write time to prevent retroactive editing.

Template:

```text
Expert: <name>
Hypothesis date: <date>
Hypothesis SHA256: <hash of this file content>

Mechanical definition:
  <unambiguous condition list>

Expected trade count per year:        <N> ± 20%
Expected cost-adjusted PF:            <X> ± 0.3
Expected losing-month percentage:     <Y%> ± 10%
Expected worst single month:          $<-N>
Expected max consecutive zero months: <Z>
Expected R-multiple distribution:     <description>

Why this hypothesis:
  <2–3 sentences on what XAU behavior creates this edge>

What would falsify it:
  <Specific outcomes that would reject the hypothesis>
```

---

## 2. Candidate Expert Definitions (starting drafts)

These are starting mechanical definitions. They will be refined during hypothesis registration but must be **complete and unambiguous** before any backtest runs. No parameter optimization is allowed in Phase 0.

### 2.1 Trend Pullback Expert

```text
Entry (long):
  - H1: EMA(50) > EMA(200), slope of EMA(50) over last 20 bars > 0
  - M15: price retraces to within 0.5 × ATR(14, H1) of EMA(21, M15)
  - M5: bullish engulfing OR pin bar with lower wick ≥ 2 × body close
  - Entry: market at close of confirmation candle
  - Stop: pullback low − 0.1 × ATR(14, M15)
  - Target: 1.5R (no scaling, no trailing)

Entry (short): mirror logic with bearish bias

Forbidden in Phase 0:
  - Parameter tuning
  - Filter additions (no news filter, no session filter, no spread filter)
  - Conditional logic beyond above
```

### 2.2 Breakout-Retest Expert

```text
Entry (long):
  - Level: previous day high, weekly high, or M5 swing high (4+ bars)
  - Break: M5 close > level by ≥ 0.3 × ATR(14, M5)
  - Retest: price returns to within 5 points of broken level within 20 bars after break
  - Hold: M5 low does not close below the broken level on the retest
  - Confirmation: bullish M5 candle after retest
  - Entry: buy stop above retest high
  - Stop: retest low − 0.1 × ATR(14, M5)
  - Target: 1.5R

Entry (short): mirror logic

Forbidden in Phase 0:
  - Round-number rules
  - Level "strength" filters
  - Time-of-day filters
```

### 2.3 Range Mean-Reversion Expert

```text
Entry (long):
  - H1: ADX(14) < 20 for last 20 bars
  - Range identification: 3+ touches of upper boundary, 3+ touches of lower boundary within last 50 M15 bars
  - Range width ≥ 2 × ATR(14, M15)
  - Price reaches lower boundary ± 0.2 × ATR
  - Confirmation: rejection candle (lower wick ≥ 2 × body close)
  - Entry: limit at boundary
  - Stop: range low − 0.3 × ATR(14, M15)
  - Target: opposite range boundary

Entry (short): mirror logic

Forbidden in Phase 0:
  - Subjective range "validity" filters
  - Asia-only filter
  - Width/spread filters
```

---

## 3. The 9-Cell Test Matrix

For each expert, run a backtest in each of the 9 cells below:

| Cell | Time window | Tick source | Cost model |
|---|---|---|---|
| 1 | 2016–2018 | Capital.com | Best-case spread |
| 2 | 2016–2018 | Capital.com | Median spread |
| 3 | 2016–2018 | Capital.com | P95 spread |
| 4 | 2019–2021 | Pepperstone | Best-case spread |
| 5 | 2019–2021 | Pepperstone | Median spread |
| 6 | 2019–2021 | Pepperstone | P95 spread |
| 7 | 2022–2024 | Dukascopy | Best-case spread |
| 8 | 2022–2024 | Dukascopy | Median spread |
| 9 | 2022–2024 | Dukascopy | P95 spread |

**Important rules:**
1. Same mechanical logic across all 9 cells. No parameter change between cells.
2. Same risk-per-trade across all 9 cells (use 0.50% fixed for Phase 0).
3. Account starts at $10,000 in every cell.
4. No filters added based on observed cell results.

### 3.1 Per-Cell Recorded Metrics

For each cell, record into `phase0_<expert>_results.csv`:

```text
cell_id, time_window, tick_source, cost_model,
trade_count, win_rate, profit_factor, total_return_pct,
total_pnl_usd, avg_trade_R, max_drawdown_pct, max_drawdown_usd,
worst_month_usd, best_month_usd, losing_month_pct,
max_consecutive_zero_trade_months, max_consecutive_losing_months,
largest_single_trade_pct_of_pnl, top5_trades_pct_of_pnl
```

---

## 4. Acceptance Criteria — Hard Gates

The expert passes Phase 0 only if **all of the following are true**:

### Gate 1 — Multi-Cell Survival
```text
Cost-adjusted PF ≥ 1.30 in at least 7 of 9 cells
```

### Gate 2 — Sample Size
```text
Trade count ≥ 40 in every cell
```

### Gate 3 — No Catastrophic Failure
```text
No cell shows max_drawdown_pct > 30%
No cell shows total_return_pct < -25%
```

### Gate 4 — Concentration
```text
largest_single_trade_pct_of_pnl ≤ 10% in every cell
top5_trades_pct_of_pnl ≤ 40% in every cell
```

### Gate 5 — Activity
```text
max_consecutive_zero_trade_months ≤ 3 in every cell
```

### Gate 6 — Cost Sensitivity
```text
For each time window, (P95-cost PF) / (best-case PF) ≥ 0.50
(I.e., the edge does not collapse entirely under worst-case costs)
```

If any gate fails, the expert is **rejected from v1**. Do not "fix" the logic by adding filters — that becomes curve-fitting. Instead, either accept the rejection or restart with a different candidate behavior.

---

## 5. The Decile Test (A3 Detail)

After the 9-cell matrix passes, run an additional persistence check on the full 2016–2025 dataset (Capital.com data) split into 10 equal-time deciles.

### 5.1 Procedure

1. Identify decile boundaries (10% of date range each, ~12 months per decile).
2. Run the expert with locked parameters on each decile independently.
3. Record PF and trade count per decile.

### 5.2 Acceptance

```text
PF > 1.0 in at least 8 of 10 deciles
No decile PF > 2.0 × median PF (catches one-decile-carries-the-result)
No decile trade count < 10 (catches dead deciles)
```

If a decile fails, document it in `phase0_<expert>_decile_failures.md` with the underlying market context (what happened in that 12-month period). This becomes input to the router's regime classification.

---

## 6. The Adversarial Counter-Example Search (A4 Detail)

### 6.1 Procedure

For each expert, spend one full working day (8 hours) manually reviewing chart situations from the 9-cell backtest output:

1. Filter trades to **losing trades only**.
2. For each losing trade, classify the failure mode:
   - "Setup was valid, market simply moved against us" (acceptable)
   - "Setup was technically valid but appeared in a regime where it shouldn't have" (router opportunity)
   - "Setup looked valid but was actually an inverse pattern" (logic gap)
3. Aggregate failure-mode counts.

### 6.2 Acceptance

```text
"Logic gap" failures ≤ 25% of total losing trades
Identified router-opportunity failures: documented for Phase 3 router design
```

If logic gap > 25%, the mechanical definition is too loose. Tighten the definition (without parameter optimization — by removing ambiguous wording, not adding filters), re-run the matrix, repeat.

---

## 7. Multi-Symbol Consistency Check (A5 Detail)

### 7.1 Procedure

Run the **identical mechanical logic** (no parameter changes, no XAU-specific constants) on EURUSD and USDJPY for the same 2016–2025 period using Capital.com data. ATR-based stops/targets adjust naturally to the new instrument's volatility.

### 7.2 Acceptance

```text
EURUSD: cost-adjusted PF ≥ 0.90 (directionally positive)
USDJPY: cost-adjusted PF ≥ 0.90 (directionally positive)
```

If either fails badly (PF < 0.7), the edge is XAU-specific. This is acceptable ONLY IF a XAU-specific mechanism is identified and documented:

```text
Why is this edge XAU-specific?
  Example acceptable answers:
  - "Edge concentrates in 14:00–15:30 UTC LBMA Fix window which only affects gold"
  - "Edge depends on COMEX futures gap behavior — XAU-specific"
  - "Edge depends on gold's correlation breakdown during USD strength regimes"

  Example unacceptable answers:
  - "Gold is more volatile" (so is XAGUSD — should also work)
  - "We tuned it for gold" (you weren't supposed to tune in Phase 0)
```

---

## 8. Output Format

### 8.1 Per-Expert Deliverable: `phase0_<expert>_results.md`

```text
# Phase 0 Results: <Expert Name>

## Hypothesis
- File: hypothesis_<expert>.md
- SHA256 at registration: <hash>
- SHA256 at result writing (must match): <hash>

## 9-Cell Matrix Results
<paste 9-row CSV inline as markdown table>

## Gate Pass/Fail Summary
- Gate 1 (Multi-cell survival): PASS / FAIL — <evidence>
- Gate 2 (Sample size):         PASS / FAIL — <evidence>
- Gate 3 (No catastrophic):     PASS / FAIL — <evidence>
- Gate 4 (Concentration):       PASS / FAIL — <evidence>
- Gate 5 (Activity):            PASS / FAIL — <evidence>
- Gate 6 (Cost sensitivity):    PASS / FAIL — <evidence>

## Decile Test
<decile PF table>
Verdict: PASS / FAIL

## Adversarial Search
- Trades reviewed: <N>
- Logic-gap failures: <N> (<%>)
- Verdict: PASS / FAIL

## Multi-Symbol Check
- EURUSD PF: <X>
- USDJPY PF: <Y>
- Verdict: PASS / FAIL / PASS WITH XAU-SPECIFIC JUSTIFICATION

## Hypothesis vs Reality
- Predicted trade count: <X> ± 20%
- Actual: <Y>
- Match: YES / NO

- Predicted PF: <X> ± 0.3
- Actual: <Y>
- Match: YES / NO

[continue for all hypothesis fields]

## Final Verdict
PASS — proceed to Phase 1 expert coding
FAIL — do not build this expert

## If Failed: Why
<documented reason — what specifically failed and why the behavior does not have edge>
```

### 8.2 Consolidated Deliverable: `PHASE0_VERDICT.md`

```text
# Phase 0 Consolidated Verdict

| Expert | 9-cell | Decile | Adversarial | Multi-symbol | Hypothesis-match | FINAL |
|---|---|---|---|---|---|---|
| Trend Pullback   | PASS/FAIL | PASS/FAIL | PASS/FAIL | PASS/FAIL | PASS/FAIL | PASS/FAIL |
| Breakout-Retest  | PASS/FAIL | PASS/FAIL | PASS/FAIL | PASS/FAIL | PASS/FAIL | PASS/FAIL |
| Range MR         | PASS/FAIL | PASS/FAIL | PASS/FAIL | PASS/FAIL | PASS/FAIL | PASS/FAIL |

## Experts approved for Phase 1: <list>
## Experts rejected: <list with brief reason each>

## Recommended action:
- If 2+ approved: proceed to Phase 1 as planned (v0.2 plan §27)
- If 1 approved: proceed to Phase 1 with single-expert v1; defer the other two slots
- If 0 approved: do not begin Phase 1. Research replacement candidates.
```

---

## 9. Decision Tree After Phase 0

```text
                  ┌─────────────────────────┐
                  │  Phase 0 Verdict        │
                  └────────────┬────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
        3 experts        1–2 experts       0 experts
        approved         approved          approved
              │                │                │
              ▼                ▼                ▼
       Proceed to        Proceed to        STOP. Do not
       Phase 1 with      Phase 1 with      begin Phase 1.
       3-expert v1       reduced v1.
       as planned.       Defer empty       Options:
                         slots until        - Research new
       (Best case)       new candidates       candidate
                         pass Phase 0.        behaviors
                                            - Consider
                         (Most likely         entirely
                          case)               different
                                              symbol or
                                              approach
                                            - Defer
                                              project
                                              entirely

                                            (Most honest
                                             outcome if
                                             no edge
                                             exists)
```

---

## 10. Common Mistakes to Avoid

These are the failure modes that have killed every prior strategy in this line. They are explicitly forbidden in Phase 0:

1. **Adding filters when a cell fails.** If Trend Pullback fails Cell 5 (2019–2021 Pepperstone median), do NOT add an ADX filter to make Cell 5 pass. That is curve-fitting. Either the edge survives without the filter, or it doesn't.

2. **Tweaking the mechanical definition.** Phase 0 logic is locked at hypothesis registration. If results disappoint, the answer is "the edge isn't there," not "let me try EMA(35) instead of EMA(50)."

3. **Excluding outlier trades.** If one huge trade carries the result, the concentration gate (Gate 4) will catch it. Do not retroactively exclude trades from the analysis.

4. **Re-running with different starting capital.** $10,000 fixed. Different capital changes lot sizing which changes everything downstream.

5. **Cherry-picking the "best" cell as evidence of edge.** Gate 1 requires 7 of 9 cells. One good cell is meaningless.

6. **Skipping the adversarial search because the backtest "looks good".** The adversarial search is where logic gaps are found. Skipping it is the same as not running it.

7. **Rationalizing failed gates as "close enough".** Gates are pass/fail. PF 1.29 is not 1.30.

8. **Running Phase 0 in MT5 Strategy Tester ONLY.** MT5 has well-known modeling-accuracy quirks. Cross-validate at least one cell in Python with a separate backtester (e.g., `backtrader`, `vectorbt`) to confirm MT5 results are not artifacts.

---

## 11. Timeline Estimate

| Week | Activity |
|---|---|
| 1 | Data acquisition (tick data from 3 brokers, format conversion), hypothesis registration for all 3 experts |
| 2 | 9-cell matrix backtests (3 experts × 9 cells = 27 backtests), result aggregation |
| 3 | Decile tests, multi-symbol checks, adversarial counter-example search |
| 4 | Result write-up, gate evaluation, consolidated verdict |

Realistic with focus: 3 weeks. Realistic part-time: 6 weeks.

---

## 12. Cost Estimate

| Item | Cost (USD) |
|---|---|
| Capital.com Demo tick data | $0 (already have) |
| Dukascopy tick data | $0 (free download) |
| Pepperstone tick data | $0–$100 (depending on source) |
| Python tooling | $0 (open source) |
| Time | 80–120 hours focused work |

**Total cash cost: under $100. Total time: 3–4 focused weeks or 6–8 part-time weeks.**

This is by far the highest-leverage spend in the entire project. A failed Phase 0 saves 12+ months of doomed Phase 1–9 work.

---

## 13. Definition of Done

Phase 0 is complete when:

- [ ] `hypothesis_trend_pullback.md` written and SHA256-locked
- [ ] `hypothesis_breakout_retest.md` written and SHA256-locked
- [ ] `hypothesis_range_mr.md` written and SHA256-locked
- [ ] 27 backtest cells executed and CSVs saved
- [ ] `phase0_trend_pullback_results.md` written
- [ ] `phase0_breakout_retest_results.md` written
- [ ] `phase0_range_mr_results.md` written
- [ ] Decile tests run for all approved experts
- [ ] Adversarial searches documented for all approved experts
- [ ] Multi-symbol checks run for all approved experts
- [ ] `PHASE0_VERDICT.md` consolidated and signed (dated)
- [ ] Decision communicated to project: proceed with N experts, or stop

Only after this is Phase 1 authorized.
