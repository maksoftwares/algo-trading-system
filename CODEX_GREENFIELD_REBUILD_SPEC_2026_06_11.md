# Codex Greenfield Rebuild Spec — "If I Started This Project From Scratch" (2026-06-11)

Author role: senior quant researcher / MQL5 EA architect / risk reviewer.
Companion to: `REPO_REVIEW_7_DEMO_EVIDENCE_FINDINGS_2026_06_11.md` (all evidence citations live there).

This is a build spec, written for Codex to implement step by step. It reuses what the current
repo proved (the breakout-retest edge, the NY-window concentration, the cost measurements,
the Phase 0 gate discipline) and redesigns everything that caused the current pain
(EA-clone proliferation, duplicate stacking, missing path data, stale cost status,
doc sprawl, inverted sizing).

---

## 0. Honest Framing Before Any Code

**Win rate is a lever, not a goal.** The account makes money from
`expectancy_R = WR × avgWin_R − (1−WR) × avgLoss_R − cost_R`. Every win-rate lever in this
spec must pass one test: expectancy does not decrease. Raising WR by tightening TP is easy
and usually loses money; raising WR by *not taking bad trades* and by *matching exit
geometry to measured price paths* is what this spec does.

**Trade count is preserved by replacement, not by keeping junk.** The current ~318 unique
trades/week include ~215 from negative-expectancy streams. The rebuild replaces junk volume
with validated volume: one strategy kernel deployed across many validated
**cells** (symbol × session × timeframe), instead of five clone EAs spraying four symbols.
Every blocked signal is still journaled (shadow row), so *information count* never drops
even while execution count is being re-qualified.

**Ten things done differently from day one:**

1. Signals and execution are separated. Strategy code emits signals; one router places orders. Duplicate stacking becomes structurally impossible instead of being measured after the fact.
2. MFE/MAE and bid/ask path logging exist from the first trade. (Its absence is what blocked the entire dynamic-exit research lane in the current repo.)
3. The cost model is a per-symbol-per-hour spread table measured continuously, and every backtest uses it. No more "median stop 110 pts in research vs 600 pts deployed" mismatches — the config that is validated is byte-identical to the config that is deployed.
4. Validation is per **cell**, not per EA-name. A strategy is approved *for* XAUUSD-NY-M5, not approved in the abstract and then sprayed across symbols.
5. Sizing is volatility-normalized (fixed AED risk per trade), so a lot-size change is a config constant, never a per-chart hand edit.
6. Risk rules (daily stop, giveback trail, exposure caps) are armed account-level code from week one, not a Stage-A shadow spec written after a giveback.
7. Every rule ships with a built-in shadow mode (`enforce: false`) and a promotion record. Shadow→enforce is a one-line config change with an audit trail.
8. The registry of strategies, cells, parameters, and states is one machine-readable YAML. All docs and dashboards are *generated* from it. No 500-file doc tree, no 13 MB status page in git.
9. Decisions are scheduled: a weekly auto-generated review packet computes promotions/demotions against pre-registered thresholds. Evidence-to-action latency is one week by construction, not a month by negotiation.
10. Research stops when the ledger says stop. The candidate-mining conclusion from the current repo carries over: the OHLC information set holds one validated family. The rebuild spends effort exploiting it well, not re-mining.

**Target metrics (pre-registered, account currency AED):**

| Metric | Current (unique view) | Target after rebuild |
|---|---|---|
| Unique executed trades/week | ~280 (junk-inflated) | ≥ 100 by week 4, ≥ 150 by week 8 |
| Portfolio win rate | 36% | ≥ 48% |
| Portfolio expectancy | −0.04 R/trade | ≥ +0.10 R/trade after costs |
| Profit factor | 0.91 | ≥ 1.30 |
| Max daily loss | uncapped in practice | hard −150 AED flatten+halt |

---

## 1. Repo Layout (Step A0)

```
trading-system/
  config/
    registry.yaml          # strategies, cells, params, states — single source of truth
    risk.yaml              # account risk constants
    costs/                 # measured spread tables, auto-updated
  core/
    data/                  # ingestion, bar building, validation
    backtest/              # path-aware event engine
    signals/               # strategy kernels (pure functions)
    gates/                 # context gates (bias, session, spread, vol)
    exits/                 # exit policies (fixed RR, cell-tuned RR, time-stop)
    router/                # signal bus, dedup, order intent
    risk/                  # sizing, account guards
    journal/               # trade + path + shadow journal, one schema
    reports/               # generated, never hand-written
  mt5/
    Experts/MasterExecutor.mq5     # ONE executor EA
    Include/{SignalKernel,Gates,Router,Risk,Journal}.mqh
    Files/                 # runtime configs pushed from registry.yaml
  tests/
  scripts/
```

One Python package, one MQL5 executor. No per-phase sub-repos, no lane folders. Lanes are
**states in the registry** (`research / shadow / demo / scaled / retired`), not directory trees.

---

## 2. Phase A — Data and Cost Foundation

### Step A1 — Canonical bar store
- Ingest M5 for XAUUSD, EURUSD, GBPUSD from ≥2 venues (reuse existing Capital.com + Dukascopy assets; they are already clean through 2025-07).
- Derive M15/H1/H4/D1 from M5 only (the current repo learned downloaded higher-TF exports are holey — keep that lesson).
- Acceptance: continuity report ≥ 99.5% expected bars per session calendar; SHA-stamped datasets.

### Step A2 — Measured cost table (replaces the stale cost-suspension mechanism)
- Continuous passive spread logger (port of the existing observer) → `config/costs/{symbol}_hourly.csv` with median/P75/P95 spread per (symbol, hour-of-week).
- Function: `cost_R(symbol, hour, stop_points) = (spread_p95(symbol,hour) + slippage_const) / stop_points`.
- Every backtest and every live entry gate calls this same function. **One cost model, two callers.**
- Acceptance: table covers 120 hour-of-week buckets/symbol; unit test pins XAUUSD P95 ≈ 75 pts vs the existing measurement.

### Step A3 — Path-aware backtest engine
- Event-driven on M5 with intrabar high/low resolution rules (reuse Phase 0 intrabar ambiguity logic).
- Mandatory outputs per simulated trade: entry/exit, **MFE_R, MAE_R, bars_to_MFE, bars_in_trade**, spread-at-entry from A2 table.
- Acceptance: replaying the June demo week's breakout signals reproduces broker PnL within ±10% (the existing exact-logged-path replay shows this is achievable).

---

## 3. Phase B — The Strategy Kernel and the Win-Rate Levers

### Step B1 — One kernel: `breakout_retest_core`
The only validated mechanic. Implement once as a pure function:

```
signal = kernel(bars_M5, bars_HTF, params) -> {direction, level, stop_points, quality_tags}
```

State machine: (1) level break on closed M5 bar → (2) retest touch within `retest_window`
bars → (3) **confirmation close** back in breakout direction → signal. Stop = `max(ATR_mult
× ATR14_M5, stop_floor_points)` (deployed demo geometry: floors 250–400 pts; median realized
stop ~630 pts on XAUUSD — keep that, it is what makes cost_R ≈ 0.12–0.15 instead of 1.1).

`swing_breakout_retest`, `p2weakness_br` etc. do **not** exist as separate EAs. Their
parameter differences become entries in the cell grid of the SAME kernel. This alone removes
the 44% duplicate-order problem and the five-clone maintenance burden.

### Step B2 — Win-rate lever 1: D1 trend-alignment gate (`gate_bias`)
- Rule: only emit signals whose direction matches D1 bias = sign(EMA20(D1) − EMA50(D1)), with neutral zone when |diff| < 0.15 × ATR(D1).
- Evidence: June demo — XAUUSD BUYs −687 AED over 91 trades (counter-trend dip-buys in a falling market), SELLs +548 over 117. Expected WR lift: +5–8 pp.
- Trade-count protection: gate blocks ~40% of round-family junk but only ~15–20% of breakout signals (breakouts are mostly with-trend by construction). Blocked signals are journaled as shadow rows.
- Ship as `enforce: false` for week 1 (shadow), promote by the Phase D rule.

### Step B3 — Win-rate lever 2: session cells, not session bans
- Define cells per strategy: `XAU-NY` (12:00–17:00 UTC), `XAU-LDN` (07:00–11:00 UTC), `XAU-ASIA` (00:00–05:00 UTC), same for EURUSD/GBPUSD.
- Each cell is independently validated (Phase D) and independently sized. Evidence so far: NY window WR 46% / PF 1.47 vs 32–34% elsewhere — but the answer is not "ban everything else", it is "let every cell earn its size." Weak cells run at minimum size or shadow, so trade count survives while capital concentrates where WR is high.

### Step B4 — Win-rate lever 3: entry-quality gates (cheap, mechanical)
- `gate_spread`: skip entry if current spread > P75(symbol, hour). Blocks the worst-cost entries (night/rollover). +1–2 pp WR, near-zero count cost in liquid hours.
- `gate_chase`: skip if price is already > 0.5 × stop_distance beyond the retest level (don't chase; late entries have structurally worse WR).
- `gate_news` (optional, phase 2): block entries ±5 min around scheduled high-impact events from a static weekly calendar file. Keep it boring and auditable.

### Step B5 — Win-rate lever 4: cell-tuned exit geometry (the honest one)
This is where most of the WR gain lives, and it must be data-driven, which is why A3 logs MFE/MAE.

- Breakeven WR at fixed RR with measured cost_R ≈ 0.13:

| TP | Breakeven WR | June evidence |
|---|---|---|
| 1.5R (current) | ~42% | breakout 44.7% → thin +0.10 R/trade |
| 1.2R | ~47% | unknown — needs MFE data |
| 1.0R | ~53% | unknown — needs MFE data |

- Procedure (`core/exits/rr_optimizer.py`): from backtest + live path logs, build the MFE distribution of all signals per cell. For each candidate TP in {1.0, 1.2, 1.5, 2.0}R compute realized WR and expectancy *from the recorded paths* (no re-simulation guesswork). Select per-cell TP = argmax expectancy, **tie-broken toward higher WR**, locked per cell, re-fit only monthly (walk-forward, never on the evaluation week).
- Example of the intended effect: if 30% of current 1.5R losers reached +1.0R first (the path data will say), a 1.2R TP in that cell converts them to winners — WR up, expectancy roughly flat or better. If the paths say otherwise, the lever is rejected exactly like partial-BE was. No deployment without the path evidence.
- Time-stop scratch exit (test, don't assume): exit at market if trade is < +0.2R after `8 × median(bars_to_MFE)` bars. Converts slow full losses into scratches. Counted honestly: scratches are not wins; the KPI is expectancy.

### Step B6 — What is deliberately absent
- No partial-close-at-1R, no breakeven-move, no trailing in v1 — the current repo's exact-path replay already falsified the first two on this strategy (−134 AED, dragged 21 winners, saved 0 losers). ATR-trail may be re-tested in month 2 from accumulated path data — as research, with the same expectancy KPI.
- No per-direction-per-session micro block rules (n=3–7 cluster rules are memorized noise).
- No new signal mechanics from the same OHLC data. The 119-candidate ledger conclusion stands.

---

## 4. Phase C — Signal Bus, Router, Risk Engine

### Step C1 — Signal bus and structural dedup
- All kernel instances (all cells, all timeframes) publish to one in-process bus:
  `SignalEvent{ts, cell_id, strategy, symbol, direction, level, stop_points, quality_tags}`.
- Router collapses events by key `(symbol, direction, M5_bar_index)` — first valid cell by priority wins; the rest are journaled `WOULD_DUPLICATE`. The 111 and 61 same-minute clone pairs from June become impossible.

### Step C2 — Order intent and execution
- Router → `OrderIntent{symbol, direction, entry, sl, tp, risk_aed, cell_id, magic}`.
- One magic-number block per cell from one generated registry. Comment = `cell_id`.
- Execution caps: 1 open position per (symbol, direction); ≤ 4 open total; per-cell daily order cap (default 6).

### Step C3 — Risk engine (armed from week one, on demo)
| Rule | Trigger | Action | Default |
|---|---|---|---|
| Per-trade risk | sizing | lot = risk_aed / (stop_points × point_value) | 25 AED (~0.25% of 10k) |
| Daily loss stop | realized+floating ≤ −150 AED | flatten all, halt until next day | armed |
| Weekly breaker | week ≤ −400 AED | all cells → shadow, owner review | armed |
| Giveback trail | peak ≥ +150 AED, give back 40% | flatten all | armed |
| Daily profit lock | day ≥ +300 AED | flatten, halt (optional, owner flag) | shadow |
| Exposure cap | >2 same-direction positions | block new entries | armed |
| Kill switch | file `KILL.txt` present | halt + flatten | armed |

- Volatility-normalized sizing replaces fixed lots entirely: XAUUSD/EURUSD/GBPUSD all risk the same AED per trade. The June failure mode (5× lots hand-set on the losing symbols) becomes impossible.

### Step C4 — Cell throttling (the allocation layer)
- Each cell carries a rolling 4-week score: `score = expectancy_R × √n`.
- Size multiplier ladder: shadow (0×) → probe (0.5×) → standard (1×) → proven (1.5×) → max (2×). Movement up requires: ≥ 30 unique closed trades in state, PF ≥ 1.25, WR ≥ 42%. One step per week max. Any week with PF < 0.8 → drop one step. Two consecutive → shadow.
- This is how "more in our favour" actually happens: winners compound size, losers de-fund themselves automatically, count is preserved because demotion is to shadow (still journaling), not deletion.

### Step C5 — MQL5 implementation notes
- One `MasterExecutor.mq5` attached to one chart per symbol (3 charts total). It loads `Files/cells_{symbol}.json` (pushed from `registry.yaml` by a deploy script with hash check), runs all kernels for that symbol on each closed M5 bar, applies gates, sends the router-approved order.
- Mutex across symbols via MQL5 GlobalVariables (`GV_open_total`, `GV_daily_pnl`); journal via CSV append in `MQL5/Files/journal/` with the Phase E schema.
- Runtime parity check at init: EA computes hash of its loaded config and writes it to the journal header; the weekly report fails loudly if runtime hash ≠ repo hash (the P2WEAKNESS stale-source incident becomes detectable in one line).

---

## 5. Phase D — Validation Ladder (per cell, frequency-aware)

Keep the current Phase 0 spine — it worked — with three fixes: validate the **as-deployed
geometry**, use **frequency-aware trade floors**, and make demo promotion **mechanical**.

| Gate | Requirement |
|---|---|
| D-1 Pre-registration | cell params SHA-locked before any scoring run |
| D-2 Cost precheck | structural P95 `cost_R ≤ 0.20` using the A2 table and the cell's real stop distribution |
| D-3 Matrix | 9-cell (3 eras × brokers) PF ≥ 1.25 in ≥ 6 cells; trade floor scaled by signal frequency: `max(20, 0.5 × expected_trades_per_era)` |
| D-4 Walk-forward | last 12 months held out from any parameter fitting; positive expectancy on holdout |
| D-5 Shadow week(s) | ≥ 2 calendar weeks live shadow journaling; realized WR/expectancy within the backtest's 90% interval |
| D-6 Probe | 0.5× size, ≥ 30 closed trades; PF ≥ 1.25 → standard size |

- Demotion is the same ladder downward, automatic, no meetings.
- Multiplicity ledger carries over as-is: every cell variant tested is logged; the family-wise error budget caps how many cells may be probed per month (default 4).

---

## 6. Phase E — Journal, Reports, Status (the anti-sprawl layer)

### Step E1 — One journal schema (every row, executed or shadow)
```
ts_utc, cell_id, strategy, symbol, tf, direction, decision(EXECUTED|SHADOW_GATE_X|WOULD_DUPLICATE|THROTTLED),
entry, sl, tp, lot, risk_aed, spread_points_at_entry, cost_R_at_entry,
exit_ts, exit_price, pnl_aed, pnl_R, outcome(WIN|LOSS|SCRATCH|OPEN),
mfe_R, mae_R, bars_to_mfe, bars_held, d1_bias, session, config_hash
```

### Step E2 — Generated artifacts (the complete list — nothing else is committed)
1. `STATUS.json` — owner numbers: day/week PnL, per-cell table, risk state, next decision.
2. `weekly_review.md` — auto-generated Monday: per-cell scorecard, promotion/demotion verdicts against D-gates, shadow-rule scoreboards, anomaly list. THE decision document.
3. `status.html` — small, generated on demand, gitignored.

### Step E3 — Tests Codex must ship with each phase
- A: bar continuity, cost-table pinning, replay-vs-broker tolerance.
- B: kernel golden-file tests (known bars → known signals); gate unit tests; rr_optimizer walk-forward leak test (fitting window may not touch eval window).
- C: router dedup property test (no two EXECUTED rows share symbol+direction+bar); risk-engine simulated breach drills (daily stop, giveback, kill file).
- D: gate evaluator regression tests with locked fixtures.
- E: journal schema round-trip; STATUS.json correctness against a synthetic journal.

---

## 7. Build Order for Codex (dependency-sorted)

| Week | Deliverables |
|---|---|
| 1 | A1 bar store, A2 cost table + logger, E1 journal schema, C3 risk engine core (pure Python, tested) |
| 2 | A3 backtest engine with MFE/MAE; B1 kernel; golden tests; replay-vs-June-demo validation |
| 3 | B2–B4 gates (shadow mode); C1–C2 router/bus; registry.yaml + config push; MQL5 MasterExecutor skeleton compiling, dry-run |
| 4 | D-gate evaluator + first cell validations (XAU-NY-M5, XAU-LDN-M5, EUR-NY-M5, GBP-NY-M5, XAU-NY-M15); E2 reports; demo go-live of approved cells at probe size, risk engine armed |
| 5–6 | Path data accumulates; B5 rr_optimizer first fit; promote/demote per weekly review; bias gate shadow→enforce if scoreboard passes |
| 7–8 | Cell expansion to hit ≥150 trades/week from approved cells only; time-stop test; ATR-trail research from real path data |

Trade-count budget (estimates from June frequencies; the weekly review trues them up):

| Cell | Est. unique trades/week |
|---|---|
| XAU-NY-M5 | 25–30 |
| XAU-LDN-M5 | 15–20 |
| XAU-ASIA-M5 (probe) | 10–15 |
| EUR-NY-M5 | 15–20 |
| GBP-NY-M5 | 10–15 |
| XAU-NY-M15 | 8–12 |
| EUR-LDN-M5 (probe) | 10–15 |
| **Total** | **~95–125 executed** + all shadow rows |

---

## 8. What This Spec Does Not Promise

- It will not turn 36% WR into 60%. Realistic stack: selection gates (+6–10 pp) + cell concentration (+3–5 pp) + path-fitted exit geometry (+3–8 pp, only if the MFE data supports it) on top of the breakout kernel's 44–45% ⇒ a defensible 50–55% in good cells, with expectancy verified at every step.
- It will not produce a second independent edge from the same OHLC data. New edge requires new information (order flow, options surface, positioning) — an owner purchasing decision, out of scope here.
- It does not authorize live capital. The real-money bar from Review 7 §10 applies unchanged to the rebuilt system.
