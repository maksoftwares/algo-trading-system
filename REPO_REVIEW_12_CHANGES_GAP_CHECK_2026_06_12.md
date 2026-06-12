# Repo Review 12 — Post-Change Gap Check (2026-06-12, midday)

Scope: verification of changes landed since Reviews 9–11, against source code and the
refreshed broker CSV (1,185 rows through 2026-06-12 11:25). As always: demo/observer
evidence only.

---

## 1. What landed — verified, with credit where due

| Item | Status | Verified how |
|---|---|---|
| Review 9 fixes in TrendGuarded **v2** (TimeGMT+240 buckets, cached EMA handles, `SLOPE_UNAVAILABLE`, plus atr14 / estimated_cost_r / EMA-distance columns) | **DONE** | agent.md + schema `trend_guarded_fix_policy_20260612_v2` |
| Trend observer attached on isolated terminal; expanded to **14 charts** incl. EURUSD/GBPUSD (owner request) | DONE | attachment reports, heartbeat |
| PositionPathObserver attached, running, login `1025742` verified, profile backed up | DONE | attachment report `POSITION_PATH_OBSERVER_TERMINAL_RUNNING` |
| Review 10 fix 1: slippage by `exit_reason` (`sl_last`/`tp_last`, `NA` for manual closes) | **DONE** | `SlippagePointsForExitText` L749–766 |
| Review 10 fix 2: magic bands (930000–930299 WR50 legacy, WST bands, 932100 W1D1) | **DONE** | L114–124 |
| Review 11 policy hole: `round_number_retest_v0` added to the shadow block list | **DONE in source** | `Phase2ShadowFixObserver.mq5` `ShadowActionForObservation` |
| Review 11 heartbeat visibility | DONE — `OBSERVER_HEARTBEAT_REPORT` PASS, all 3 lanes fresh (<1 min) | report + script + tests |
| Review 11 outcome-resolution script | **BUILT BUT NOT FUNCTIONING** | see §2 |

This is a good day's work. The observer stack is now attached, versioned, monitored, and
carries every evidence-quality fix the last three reviews asked for.

## 2. The keystone is broken: outcome resolution resolved 0 of 1,253 signals

`OBSERVER_OUTCOME_RESOLUTION_REPORT.md` says `Broker trade rows: 0` and 100%
`UNRESOLVED_NO_BROKER_MATCH_NO_REPLAY_BARS`. Two distinct causes, both verified in source:

1. **Direction vocabulary bug (definite, fatal).** Observer logs `direction` as `LONG`/`SHORT` (`observation.direction_text`); the broker CSV uses `BUY`/`SELL`. `_find_broker_match` builds keys with the raw strings — `("…","XAUUSD","SHORT",minute)` can never match `("…","XAUUSD","SELL",minute)`. The replay leg is killed by the same vocabulary: `direction not in {"BUY","SELL"}` skips every observer row. **Even with broker rows loaded, the join yields ~zero.** Fix: map LONG→BUY / SHORT→SELL at ingestion (one function), and rerun.
2. **Zero broker rows loaded at run time** despite the CSV containing 1,185 rows now. Most likely the script ran before/during the CSV refresh. Rerun after fix 1 and confirm `Broker trade rows ≈ 1,185`.
3. **No `bars_dir` supplied.** The broker join only resolves signals the live EAs also traded; guard-blocked and quarantined-lane signals need M5 replay. Phase 0 bars end 2025-07 — export June 2026 M5 bars (XAUUSD/EURUSD/GBPUSD/USDJPY) from any terminal once per week into a read-only folder and pass `--bars-dir`. This is the same export the dynamic-exit lane has been waiting on since 06-09 — one script unblocks both.

Until §2 is fixed, every observer table is still a flow report. This is the single highest
priority item — ideally before tonight's evening window so the trend-veto scoreboard can be
scored on day one.

## 3. Deployment-parity check to run today (small but important)

The shadow policy change (round_number block) exists in repo source. The 14 running
shadow observers in `C:\MT5PortableShadowFixObservers` are compiled from the *old* source
until someone recompiles/redeploys. Runtime≠repo drift is exactly the P2WEAKNESS failure
mode. Either redeploy the shadow lane with a bumped `shadow_policy_version`, or — simpler —
leave the running lane as-is and rely on the resolution script's `proposed_v2_shadow_action`
column (it already computes the v2 policy offline). **Pick one explicitly and record it**;
silent divergence between the running policy label and the analysis policy is how decision
views get corrupted. The offline-only route is cheaper and just as valid for shadow scoring.

## 4. Meanwhile, the trading floor: June 12 is a lesson, not a contradiction

To 11:25 today: 125 trades, −471.8 AED closed, **59/125 duplicates (47%)**. And the roles
flipped: breakout family −684 (18+14 trades), round family **+256**, BUYs −600 / SELLs +129
— gold turned down and today's counter-trend BUYs came from the breakout side. Three
readings, all consistent with prior reviews:

1. **Day-level attribution flip-flops; rolling windows decide.** Anyone reading June 11 alone kills the round family; anyone reading June 12 alone kills breakout. The 9-day cumulative view still has round family ≈ −370 raw and breakout family strongly positive. Keep decisions on the rolling 2-week unique view, exactly as Review 7 specified.
2. **Today is evidence FOR the fast two-TF veto, not against it.** A D1-bias gate would likely have *allowed* this morning's losing BUYs (D1 still bullish after the run-up); the M15/H1 slope veto is the layer that can catch an intraday turn. Tonight's evening scoreboard just got more interesting — make sure it can be scored (§2).
3. **The mutex remains unexecuted and duplication is still ~half the account's flow.** Third consecutive review window saying the same thing. The family mutex is hygiene with three layers of proof; it does not need more observation.

## 5. What more should be done — priority order

| # | Action | Type | When |
|---|---|---|---|
| 1 | Fix LONG/SHORT↔BUY/SELL mapping in `generate_observer_outcome_resolution.py` (join + replay legs), rerun, verify broker rows ≈ 1,185 and resolved% jumps | Code, ~30 min | **Today, before evening** |
| 2 | June-2026 M5 bar export script (4 symbols, weekly cadence, read-only output) → pass `--bars-dir`; this also unblocks the ATR-trail replay | Code | Today/tomorrow |
| 3 | Decide and record the §3 parity choice (redeploy shadow lane vs offline-v2-only) | Governance, 10 min | Today |
| 4 | Evening scoreboard tonight: trend-veto KEEP/BLOCK splits outcome-resolved per Review 11's pre-registered questions; treat as smoke test, not promotion evidence | Analysis | Tonight + weekend |
| 5 | Path-observer first checkpoint after ~3 trading days: coverage report (≥95% positions snapshotted, ≥90% closures with summaries, unknown-candidate count) | Analysis | Mon/Tue |
| 6 | **The standing floor decisions** — family mutex, round-family + session_extreme quarantine, USDJPY off, EUR/GBP lots → 0.01, guard re-arm, guardian attach. All measurement infrastructure is now in place to validate them prospectively; the only missing ingredient is the owner pressing the button. 47% duplicate flow today is the recurring cost of waiting | Runtime (owner) | This weekend / before Monday's session |
| 7 | After one outcome-resolved forward week: threshold sweep for the veto (50/150/300/ATR-norm from logged raw slopes), and the first exit-quality report from path data | Research | Next week |

## 6. What NOT to do

- Don't react to June 12 morning by filtering breakout_retest — same one-day-overfit trap as June 11, mirrored.
- Don't promote the trend veto tonight regardless of how good the evening looks — one evening is the pipeline test; the bar stays one full outcome-resolved forward week.
- Don't widen observers further (GBPUSD/EURUSD expansion is enough); the bottleneck is now resolution and decisions, not coverage.
- Don't start the greenfield build before items 1–3 are closed; measurement integrity first.

**Verdict: the observer layer is now built and healthy; the analysis layer has one fatal
but 30-minute bug; the trading floor still hasn't executed decisions that three review
windows and three evidence layers keep re-confirming. Fix the join, score the evening,
and spend the weekend pressing the buttons that are already justified.**
