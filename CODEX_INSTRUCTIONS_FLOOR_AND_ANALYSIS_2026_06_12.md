# Codex Instructions — Floor Decisions + Analysis Chores (2026-06-12)

Source: Reviews 7–12 standing recommendations, all re-confirmed by observer evidence.
Two work blocks. Block A changes demo runtime and **requires explicit owner authorization
recorded per the existing templates before execution**. Block B is analysis-only and can
run immediately.

Global boundaries (unchanged): demo only, no live trading, no canonical Phase 2 status
change, no edits to `breakout_retest` entry/stop/TP logic (it is the control), profile
backup before any terminal change, a report trail for every step, nothing deleted —
quarantined EAs keep logging.

---

## Block A — Trading-floor actions (owner-authorized runtime changes, standard demo terminal)

Execute as ONE maintenance window: graceful terminal close → profile backup → all preset
edits → recompile if needed → restart → verification report. Follow the procedure pattern
from the GBPUSD lot-update and WR50 attachment reports.

### A1. Quarantine the round family + session_extreme to observer-only
- Charts: all `symbol_normalized_round_retest_v0`, `round_number_retest_v0`, `session_extreme_retest_v0` instances (all symbols).
- Set `InpBrokerActionAllowed=false`, `InpDryRunOnly=true`. Signal/would-trade logging stays ON.
- Evidence basis: cumulative unique-view losses across three review windows; June 11 root cause; prospective validation continues via their logs.

### A2. Repair executors: broker action OFF
- Both `Phase2ExperimentalDemoRepairExecutor` charts (`*_repair_v1` lanes): `InpBrokerActionAllowed=false`.
- This restores the `NONE_SHADOW_ONLY` designation in `PHASE2_REPAIR_CANDIDATE_RULES.csv`. Delete the SHORT-only window logic from any future re-arm plan; do not re-tune it.

### A3. Family duplicate mutex in `Phase2ExperimentalDemoExecutor.mq5`
- In `TradingGuardsPass`: before sending, scan `PositionsTotal()`; if any open position exists with same symbol + same direction + magic in the same family band (920100–920299 = breakout family; 920300–920499 = round family; 920500–920599 = session family) opened within the current M5 bar, return guard reason `WOULD_DUPLICATE_FAMILY_EVENT`.
- Log suppressed signals with that reason. Add a pytest-style source test asserting the guard string exists and the band table matches `MAGIC_NUMBERS.md`.
- Priority is implicit: first instance to fire wins; `breakout_retest` charts load before `swing_*` in the profile order — verify and document the order.

### A4. Re-arm quantitative guards (values from the 06-09 plan, never applied)
- All remaining broker-action charts: `InpMaxEstimatedCostR=0.30`, `InpMaxMeasuredSpreadPoints=75`, `InpMaxOpenPositionsPerInstance=1`, `InpMinSecondsBetweenOrders=60`. Leave `InpMaxOrdersPerDay=0`.

### A5. Lot normalization
- EURUSD and GBPUSD back to `0.01` on every chart.
- Also change the committed source defaults `InpEURUSDFixedLot`/`InpGBPUSDFixedLot` from 0.05 to 0.01 so the sizing error cannot resurrect from a recompile.

### A6. USDJPY off
- All USDJPY charts: `InpBrokerActionAllowed=false` (observer-only). Basis: PF 0.45, avg win 5 AED, spread eats the moves; 260 unresolved replay rows make it the worst-instrumented symbol too.

### A7. Attach `AccountEquityGuardianShadow` (Stage A, observer-only)
- One chart, standard demo terminal (it must see the trading account). It contains no trade calls; run the forbidden-terms scan and record it in the attachment report.
- After 5 trading days of shadow agreement with manual checks, prepare (do not execute) the Stage B arming packet for owner sign-off: R1 −150 AED daily flatten/halt, R2 peak-giveback arm +150/40%, weekly −400 AED breaker.

### A-Verification (one consolidated report: `PHASE2_FLOOR_DECISIONS_APPLIED_2026_06_13.md`)
- Per chart: candidate, symbol, broker-action state, lot, guard values — before vs after.
- Startup-log rows proving each change; compile logs 0/0; profile backup path.
- Expected post-state: exactly 8–9 broker-action charts (breakout_retest on XAUUSD/EURUSD/GBPUSD + swing under mutex), everything else observer.
- Next trading day: confirm duplicate rate in the broker CSV drops from ~47% to ~0, and max same-direction stack ≤ 2.

---

## Block B — Analysis chores (read-only, run now)

### B1. Replay calibration (gates everything else)
- Take the 77 broker-joined signals; run the M5 replay on those same rows; report agreement: outcome match (WIN/LOSS), and PnL-sign match, per symbol and bucket.
- Output: `OBSERVER_REPLAY_CALIBRATION_REPORT.md`. Acceptance: ≥90% outcome agreement → replay rows usable; 75–90% → usable with a disclosed error bar; <75% → replay quarantined, broker-join only.

### B2. Cost-haircut column in the scoreboard
- For every replay-resolved row, compute `net_outcome` using the measured per-symbol-hour spread table (passive observer): subtract spread cost at entry from the R outcome; recompute cell win rates and add `net_breakeven_wr` (= (1+cost_R)/(1+RR)) per cell so each cell shows gross WR vs the bar it must clear.
- Re-emit the scoreboard with both gross and net columns. Expect night cells to compress most.

### B3. USDJPY M5 bar export (or formal exclusion)
- Export June 2026 USDJPY M5 bars into `m5_replay_bars/` with the same continuity report, rerun the resolver; OR write a one-paragraph exclusion note in the resolution report. No silent holes.

### B4. Family-level aggregation
- Scoreboard currently lists clone EAs as separate rows of the same signals. Add a `family` column (breakout / round / session) and a family-level rollup table that de-duplicates clone signals before summing. All portfolio-level totals must come from the family rollup.

### B5. Score the TrendGuarded lane
- Run the same resolver over `trend_guarded_fix_observer_v2_signal_log_*.csv` (it logs `trend_veto_action`), starting tonight after the evening window. Output `TREND_VETO_LANE_SCOREBOARD.md`: veto KEEP vs BLOCK outcomes, controls vs weak lanes separated, gross and net. Rename the existing shadow-policy scoreboard to `OBSERVER_SHADOW_POLICY_SCOREBOARD.*` to end the naming confusion.

### B6. Pre-register next week's hypotheses (one file, before Monday)
- `FORWARD_WEEK_HYPOTHESES_2026_06_15.md`, locked before the week starts: (1) round-family night/evening SHORT cells net-positive after cost — fresh week verdict; (2) M15/H1 veto improves weak-lane net expectancy with ≥60% kept on controls; (3) post-mutex duplicate rate ≈ 0 and portfolio unique-view PF ≥ 1.2; (4) breakout_retest control stays day-positive majority. Each with its pass/fail metric written down now.

---

## Order of execution
B1 → B2 → B3/B4 (parallel) → tonight: B5 → before Monday: B6. Block A as one owner-authorized window this weekend, before Monday's session. If the owner declines any A-item, record the decline in the report rather than skipping silently — the audit trail is the point.
