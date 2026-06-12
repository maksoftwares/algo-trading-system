# Repo Review 8 — XAUUSD Shorting Defect: Independent Code + Evidence Verdict (2026-06-11)

Reviewer role: senior quant + MQL5 code reviewer.
Scope: independent verification of `PHASE2_XAUUSD_TODAY_ROOT_CAUSE_ANALYSIS.md` and
`PHASE2_XAUUSD_SHORTING_LOGIC_DEFECT_2026_06_11.md` against the actual source
(`Phase2ExperimentalDemoExecutor.mq5`, `Phase2ExperimentalDemoRepairExecutor.mq5`), the
Python research mirrors, and a from-scratch re-analysis of
`PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv` (I did not rely on the report's aggregates).

---

## 1. Executive Verdict

**Is this a real logic defect?** Yes — but it is a *design flaw faithfully executed*, not an
execution bug, and Codex's report understates one thing: the deployed composite
(SHORT-only windows + stripped guards + five stacked clones) **was never validated by any
research artifact in this repo**. Three distinct failures combined:

1. **Design flaw (signal layer):** direction is chosen by the color of one closed M5 candle, then a level is searched in that direction. This logic exists *identically* in the locked Python research code (`breakout_retest.py:55–62`), so the MQL5 port is faithful — it is the design that is fragile. It is survivable for `breakout_retest` (the level must be a confirmed *swing structure* break) and structurally broken for the round-number variants (a round level always exists just above price, so in any uptrend the short-candidate machine never runs dry).
2. **Overfit configuration (repair layer):** the repair executor hard-codes 5-trade cluster rules as SHORT-only permission filters (`Phase2ExperimentalDemoRepairExecutor.mq5:956–993`). The source CSV for those rules (`PHASE2_REPAIR_CANDIDATE_RULES.csv`) marks every row `runtime_action = NONE_SHADOW_ONLY` — yet a broker-action executor was built and attached anyway, with `InpDryRunOnly = false` as the committed default (line 13). This is a governance breach, not just a modeling error.
3. **Risk-control removal (account layer):** the 2026-06-09 "execution unblock" disabled cost, spread, exposure, and throttle guards. The committed executor defaults are all zeros: `InpMaxOrdersPerDay=0`, `InpMaxAccountOrdersPerDay=0`, `InpMinSecondsBetweenOrders=0`, `InpMaxOpenPositionsPerInstance=0`, `InpMaxEstimatedCostR=0.00`, `InpMaxMeasuredSpreadPoints=0.0` (lines 34–40). The re-arm plan (`EXPERIMENT_GUARD_REARM_AND_DEDILUTION_PLAN_2026_06_09.md`) has sat `RUNTIME_ACTION_PENDING_OWNER_CONFIRMATION` since 06-09. XAUUSD trade count exploded from ~30–60/day to 206 (06-10) and 221 (06-11), with **19 concurrent open positions** and **96 same-minute same-direction entry clusters** (max 6 EAs in one minute) on June 11. The guard stripping is as causal for the *size* of the loss as the direction logic is for its *sign*.

**Is demo execution behaving according to code?** Yes. Every behavior in the broker history
is reproducible from the source. No MT5/broker anomaly, no slippage story. One forensic
hazard: order-log reason codes are labeled `*_DRY_RUN` (`RepairExecutor.mq5:544`) on rows
where real orders were sent (`ORDER_SEND_OK`) — the logs lie about the mode.

**Immediate suspensions?** Yes:

| Action | Target | Basis |
|---|---|---|
| Quarantine to observer-only NOW | `symbol_normalized_round_retest_v0_repair_v1`, `session_extreme_retest_v0_repair_v1` (the whole repair executor's broker action) | Deployed against their own `NONE_SHADOW_ONLY` designation; 13/13 SELL trades on an up day, 2 wins, −401.6 AED |
| Quarantine to observer-only NOW | `round_number_retest_v0`, `symbol_normalized_round_retest_v0`, `session_extreme_retest_v0` | Third consecutive review window of net losses; structural short-in-uptrend defect; June 11: −534 AED per round clone |
| Re-arm guards NOW (values already written in the 06-09 plan) | all remaining executors | cost_R ≤ 0.30, spread ≤ 75 pts, 1 open/instance, ≥60 s between orders |
| Keep active (control) | `breakout_retest` (+ `swing_breakout_retest_v0` only if mutexed; it duplicates breakout 1:1) | +323 AED combined on the same defective day, 50% WR, PF ≈ 2.3 |

---

## 2. Evidence Review (independently recomputed from the broker CSV)

Market: gold rose ~79 pts on 2026-06-11 (4082.57 → 4161.25), strong night/morning grind,
small afternoon dip, evening recovery.

June 11 XAUUSD, 221 entries, 215 closed, **closed PnL −1,298.4 AED** (report's −912.66
reconciles after +386 floating on still-open positions):

| EA | Dir split (B/S) | Closed PnL AED | Note |
|---|---|---:|---|
| breakout_retest | 6/6 | +160.5 | 50% WR, TP/SL symmetric — fine |
| swing_breakout_retest_v0 | 6/6 | +162.4 | identical trades to breakout_retest — clone, not confirmation |
| round_number_retest_v0 | 43/44 | −534.3 | BUYs +268.5, SELLs −802.8 |
| symbol_normalized_round_retest_v0 | 43/44 | −521.6 | BUYs +285.7, SELLs −807.3 — same trades as round_number to the minute |
| symbol_normalized_round_retest_v0_repair_v1 | 0/11 | −319.0 | SHORT-only by code; 2/9 W/L |
| session_extreme_retest_v0 | 0/4 | −163.9 | 0/4, all SL |
| session_extreme_retest_v0_repair_v1 | 0/2 | −82.6 | SHORT-only by code |
| p2weakness_br_v1 | 2/0 | +128.7 | n=2 |

Direction asymmetry across the day: **SELL −1,733.1 AED over 117 trades; BUY +434.6 over 98.**

So yes — the Codex headline holds: **the core breakout lane was genuinely okay** on the
same day, same symbol, same market, and the loss came from the round/session/repair lane
shorting a rising market repeatedly, in stacks. The worst single minutes (18:15, 18:35,
19:00) each put 3–5 EAs into the same SELL with stops at nearly the same price; one upward
impulse swept entire clusters simultaneously (−277.5, −228.3, −165.5 AED per minute-cluster).

One correction to the narrative: the round-family EAs traded both directions
(43 BUY / 44 SELL each — the candle-color trigger flip-flops every bar run). Their BUYs were
net positive. The day's damage is specifically *short-side, evening-clustered, stop-exit*
(141 SL exits totaling −5,298 AED across the day vs 72 TP exits +4,000).

---

## 3. Code Findings (file / line verified)

### Direction selection — `Phase2ExperimentalDemoExecutor.mq5`
- `EvaluateExperimentalRetestObserver` (L429): direction set at **L458–466** — `is_long = close[1] > open[1]` on M5, nothing else. No M15/H1/D1 input exists anywhere in the file.
- Level generation `DemoCandidateLevels` (L413/424): for round-number candidates, the level is `ceil(price/increment)·increment` — **in an uptrend there is always a fresh round level just overhead**, so short candidates are generated continuously. This is the precise mechanism that kept producing shorts while gold rose.
- `DemoBreakValid` (L219–224): a "break" is any single bar in shifts 3–22 closing 0.3×ATR beyond the level — in a rising market, bars from below the level on the way up satisfy the short-side "break" trivially. No structural break requirement.
- `DemoRetestValid` (L226–238): touch within 5 points + close on the level's far side. Satisfied by ordinary consolidation under a round number during an uptrend.
- Verdict: matches the Python research design (`phase0/strategies/breakout_retest.py:55–62`, inherited by `round_number_retest_v0.py` whose `_candidate_levels_from_arrays` L50–58 does the same ceil/floor). **Design flaw, not a port bug.** Note the Python classes are literally labeled `version = "0.1-research-disabled"`.

### Trading guard — same file
- `TradingGuardsPass` (L1027–1128): checks authorization tokens, demo-server, spread/cost/day caps, instance exposure — **every quantitative cap is input-disabled by default (L34–40)**, and there is no trend/regime check, no family mutex, no same-symbol-direction cap, no daily-loss halt.
- Lot defaults **L32–33**: `InpEURUSDFixedLot = 0.05`, `InpGBPUSDFixedLot = 0.05` — the 5× sizing on the weakest symbols is now baked into committed source, not just chart state.
- Session gate (L41–43, L585–608): exists, **disabled by default**, and defined in *server* hours — a different time base from every report.

### Repair filter — `Phase2ExperimentalDemoRepairExecutor.mq5`
- `RepairFilterPass` (L956–993): `symbol_normalized..._repair_v1` → XAUUSD + **SHORT only** + Dubai-evening only; `session_extreme..._repair_v1` → **SHORT only**, XAUUSD afternoon/evening or EURUSD night. These are the `PREFERRED_CLUSTER` rows from `PHASE2_REPAIR_CANDIDATE_RULES.csv` — samples of **n = 5, 5, 4, and 3 trades** — compiled into permission logic. The repair never validates that *now* is a shorting regime; it only checks the calendar bucket.
- The "repair" is therefore strictly worse than its parent in an up-regime: it deletes the BUY side (which was net **positive** on June 11) and keeps only the counter-trend SELLs.
- Timezone: `DubaiTimeNow() = TimeGMT() + 240 min` (L938–941) with bucket boundaries matching the reports (L943–954). **Correct and consistent** for the repair lane; Dubai has no DST so the fixed offset is safe. The broker-UTC→Dubai mapping in the defect report (13:20Z → 17:20 local) checks out. No timezone bug caused June 11. The residual inconsistency: the main executor's (disabled) session gate uses server hours, and `AddSessionExtremeLevels` (L377–395) computes "Asia 00–06h / London 07–11h" extremes in **server** time while all reporting buckets are Dubai time — the session-extreme levels do not mean what the labels imply. Latent design inconsistency, worth fixing, not the June 11 cause.
- `InpDryRunOnly = false` default (L13) and `*_DRY_RUN` reason strings on real sends (L544): misleading committed defaults and forensic mislabeling.

### Hidden risks Codex missed (or under-weighted)
1. **The guard stripping is half the story.** With caps at 1-open-per-instance (the 06-09 state), June 11's same-thesis exposure would have been capped at ~5 positions instead of 19, and cluster wipeouts would have been roughly third-sized. The pending re-arm plan already contains the right values; it was never applied.
2. **Clone double-counting in both directions:** `round_number` vs `symbol_normalized` produced byte-identical trade streams (88 trades each, same minutes, same outcomes) — running both is pure 2× leverage; and the *good* lane is also doubled (`swing` ≡ `breakout`, 13 identical trades), so the breakout family's +323 is really one stream sized 2×.
3. **Correlated stop placement:** all cluster members compute stops from the same retest bar with a 300-point XAUUSD floor (L1167–1173), so stops land within points of each other — a single impulse takes out the whole cluster in one sweep. This is engineered tail risk independent of direction logic.
4. **No daily-loss halt anywhere in the execution path** — the equity guardian is still an unattached Stage-A spec while executors run guard-free.
5. **Misleading lifecycle labels:** runtime startup advertises `InpCandidateStatus = "EXPERIMENTAL_QUARANTINE_REVIEW_ONLY"` (L16) on EAs that send real orders, and research classes say `research-disabled`. After three weeks of live evidence, "accepted/provisional/repaired" labels in the reports no longer describe behavior; they describe history. The labels should be regenerated from the live scoreboard (see §5.6).

---

## 4. Root Cause, Separated

| Layer | Finding | Share of June 11 damage |
|---|---|---|
| Market regime | Strong up-day in gold. A trigger, not a cause — the same regime was profitable for the breakout lane. | — |
| Code bug | None found. Execution matches source; source matches locked research logic. The `_DRY_RUN` labels are a logging bug only. | 0 |
| Design flaw | Candle-color direction + ubiquitous round levels ⇒ continuous counter-trend shorts in trends; no HTF veto anywhere. | ~40% (the SELL-side bleed) |
| Overfitting | SHORT-only repair lanes built from 3–5-trade clusters and deployed against their own SHADOW_ONLY designation. | ~15% (−402 direct, plus cluster amplification) |
| Portfolio weighting / risk config | Guards stripped on 06-09 (orders/day, open positions, cost, spread, spacing all → 0/unlimited); 5 correlated clones stacked; 19 concurrent positions; no daily-loss halt; re-arm plan left pending. | ~45% (turned a bad day into a −1,300 AED day) |

---

## 5. Repair Recommendations (shadow first; no blind tuning; nothing hidden)

**Demo-act now (config/runtime hygiene — these need no new research):**
1. Repair executor: `InpBrokerActionAllowed = false` everywhere (restores the CSV's own `NONE_SHADOW_ONLY`). Keep logging.
2. Round/session family: observer-only. Their would-trade logs continue, so the quarantine is validated prospectively — losses stay in history, nothing is deleted.
3. Apply the 06-09 guard re-arm values exactly as written: `InpMaxEstimatedCostR = 0.30`, `InpMaxMeasuredSpreadPoints = 75`, `InpMaxOpenPositionsPerInstance = 1`, `InpMinSecondsBetweenOrders = 60`.
4. Family mutex in `TradingGuardsPass`: refuse to send if any open position exists with same symbol + direction + family magic-range within the current M5 bar. (Scan `PositionsTotal()` by magic range; ~30 lines.)
5. Fix the `_DRY_RUN` reason labels and make startup status text reflect actual broker-action mode.

**Shadow-test first (pick ONE veto family after a scoreboard week — do not stack all of them):**
6. **M15+H1 trend veto (primary candidate):** block counter-trend entries when EMA20(M15) slope and EMA20(H1) slope agree against the signal direction. Symmetric (blocks bad longs in downtrends too) — less June-11-shaped than a shorts-only rule.
7. **Broken-structure requirement for round-retest shorts (secondary):** require a confirmed M15 lower-low within the last 12 M15 bars before any short level candidate is valid. This repairs the actual defect (no structural break behind the "break") rather than masking it.
8. Log `d1_bias`, `m15_ema20_slope`, `h1_ema20_slope` columns on every signal row now, regardless — that data costs nothing and powers both vetoes' scoreboards.

**Do not do:**
- Do not re-enable SHORT-only windows with new thresholds (same overfit, new clothes).
- Do not add per-symbol-session-direction block lists from June 11 (n-of-one-day curve fit).
- Do not tune stops/TP of the round family before the direction logic is fixed — stop size was not the failure mode (141 SL exits were *correct* exits from wrong-direction trades).
- Do not delete or restate historical trades; quarantine forward only.

---

## 6. Backtest / Shadow-Test Plan

**Data already in hand:** `PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv` (entries, exits, SL/TP),
M5/M15/H1 bars from the demo terminal, and the signal logs. The veto rules in §5.6–5.7 are
computable per historical trade *without* re-simulation: for each actual trade, compute the
veto inputs at its entry timestamp and split the ledger into KEPT vs BLOCKED.

Procedure (same harness as the existing weakness shadow report):
1. Apply each veto to all June 1–11 trades → `D1_BIAS_SHADOW_SCOREBOARD.md` style output, per EA, per symbol, per bucket, duplicate-hidden as the decision view.
2. Acceptance to *promote a veto to demo* (all required, measured on duplicate-hidden view):
   - net PnL improvement and PF ≥ baseline + 0.15;
   - win rate not lower than baseline;
   - **kept trade count ≥ 60% of baseline** (the trade-count preservation constraint);
   - max drawdown reduced;
   - evening XAUUSD subset specifically not degraded (the proven edge must survive the rule);
   - **one fresh forward week** of shadow agreement after the rule is coded — the historical split alone is insufficient, that's how the repair lanes were born.
3. The quarantined EAs' observer logs over the same forward week serve as the control arm: if their would-trades turn sustainably positive, the quarantine is reviewed openly rather than silently kept.

---

## 7. Final Go / No-Go

No live or real-money trading. Demo continues, reshaped:

| Status | EAs |
|---|---|
| **ACTIVE (demo, control)** | `breakout_retest` — unchanged rules, re-armed guards, XAUUSD/EURUSD/GBPUSD at 0.01 |
| **ACTIVE only if mutexed, else observer** | `swing_breakout_retest_v0` (1:1 duplicate of breakout) |
| **OBSERVER-ONLY (quarantine, logging on)** | `round_number_retest_v0`, `symbol_normalized_round_retest_v0`, `session_extreme_retest_v0` |
| **REMOVED from demo execution** | `symbol_normalized_round_retest_v0_repair_v1`, `session_extreme_retest_v0_repair_v1` (repair executor broker-action off; SHORT-only windows deleted, not re-tuned), WR50 lane |
| **NEEDS MORE DATA** | `p2weakness_br_v1` (n=2 on the day; also still pending its clean-deployment governance fix) |

**Codex's exact next implementation task (one ticket, in order):**
1. Push presets re-arming the four guard values on all attached executor charts (values from the 06-09 plan; report trail like the existing lot-update reports).
2. Set `InpBrokerActionAllowed = false` on both repair-executor charts; verify via startup log rows.
3. Add the family-mutex check to `TradingGuardsPass` (symbol + direction + family magic range + current M5 bar), with `WOULD_DUPLICATE_FAMILY_EVENT` logging for suppressed signals.
4. Add `d1_bias`, `m15_ema20_slope`, `h1_ema20_slope` columns to the signal log (no behavioral change).
5. Fix `*_DRY_RUN` reason-code strings to reflect actual mode.
6. Generate the veto shadow scoreboard from June 1–11 trades and start the fresh forward week.

The honest one-line summary: the EAs did exactly what they were told; the instructions
were structurally wrong on direction, overfit on the repairs, and unguarded on risk — and
all three were knowable from artifacts the repo had already produced before June 11.
