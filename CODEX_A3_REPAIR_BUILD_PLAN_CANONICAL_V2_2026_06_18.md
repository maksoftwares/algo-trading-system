# Codex A3 Repair — Canonical Build Plan v2 (single source of truth) — 2026-06-18

**Supersedes:** `CODEX_A3_REPAIR_BUILD_PLAN_CANONICAL_2026_06_18.md`,
`A3_SIGNAL_QUALITY_REPAIR_PLAN_ab95b3de_2026_06_18.md`, and the uploaded
`FINAL_REVIEW_AB95B3DE_…` (all merged here, reconciled). **Work from this file only.**

## Status & hard boundary
- HEAD `ab95b3d` ("Harden A3 repair safety gates") = P1/P2 done: hardened pause, two-tier kill,
  arming audit, status semantics, locked hypothesis + implementation contract + provenance.
- **Signal quality is NOT yet addressed.** A3 `1033669` stays **PAUSED** (933200/933300/933400 PAUSED,
  profit-lock DRY_RUN_DISARMED, 0 exposure). **Repo-only / shadow-only. No reactivation.**
- Frozen: do not touch A1/A2, MT5 runtime, presets, orders, the locked hypothesis file, or thresholds.

## Guiding principles
1. **Cheapest decisive test first.** Screen the edge **offline** before building the heavy forward
   apparatus — don't spend ~10 commits of MQL5/parity machinery on an edge that may not exist.
2. **Discovery ≠ validation (hard train/test split).** Diagnostic sweeps generate hypotheses; they are
   never promotion evidence. A winning diagnostic must be **re-locked as V2** and validated on a **fresh**
   window — discovery-window results may not be reused.
3. **Preserve frequency.** A filter that "wins" by blocking nearly everything fails the project objective.
4. **Honest prior:** the breakout edge is small (~48% WR, regime-fragile). The **most likely honest
   outcome is "no candidate clears the bar → A3 stays paused,"** and that is the process working. Build accordingly.
5. Repair **breakout-retest** only. Do **not** promote round-retest (no edge). Do **not** combine lanes.

## Root-cause ranking (calibrated)
1. **Direction/regime mismatch — leading repair *hypothesis*, not a proven rule.** With-trend beats
   against-trend broadly, but for the *breakout family specifically* the effect is positive-but-modest
   (the Day-3 flip was account-wide). So test **moderate H1 trend control**, don't assume it.
2. **Permissive retest quality** (deep penetration / weak body / poor close-loc / late confirm) — secondary.
3. **Duplicate family exposure** — an amplifier, not a signal cause → handle via the mutex, separately.
4. **Session/timing** — a stratification dimension, **not** the first fix (evening-only cuts ~75% frequency).
5. **Stop/cost geometry** — keep the stop floor + `cost_R ≤ 0.15R` as baseline invariants; a wider stop is not an entry fix.
6. **Exit give-back** — a *separate* Stage-2 study (do not mix into the entry experiment).

---

## PHASE A — Fix-before-P3 cleanup (verified gaps in `ab95b3de`)
All three were verified against the repo.

**SQ-00 — Status + arming-audit cleanup (no strategy code).**
- Regenerate `status_summary.json/.md`, `status.html`, `agent.md`: they still say commit **`e3e3e7a` / 415
  passed** while HEAD is **`ab95b3d` / 425 passed**. Set `next_allowed_transition` = P3 offline discovery.
  Prune already-closed next-evidence items.
- Extend `audit_phase1_arming.py`: `SCAN_SUFFIXES` is `{.set .ini .chr .args .env .json}` — it scans
  `scripts/`/`deployment/` but **not `.py/.ps1/.bat/.cmd/.yaml/.yml/.toml/.cfg`**, so a committed Python
  attach utility with `InpBrokerActionAllowed=true` slips through. Add a **per-script policy** (no blanket
  ban — owner-authorized attach utilities exist): default mode verify/dry-run; `--apply` explicit; owner
  packet path+hash required; review hash; zero-exposure check; profile backup; current-A3-pause ack.
- Require a **green CI run** tied to this commit (415/425 is local-only today). Add policy tests.

**SQ-01 — Implementation addendum (hash-locked; do NOT edit the locked contract).**
- Add `docs/A3_SIGNAL_QUALITY_V1_IMPLEMENTATION_ADDENDUM_01.md` + `.sha256.json`. Resolve the seams the
  contract leaves open: first-retest definition, signal timestamp, entry-tick eligibility + expiry,
  EMA/Wilder-ATR seeding, warm-up, timezone/DST mapping, weekend/gap behavior, restart recovery, tick
  freshness, rounding, holding duration, gap-exit pricing.
- Reconcile the window contradiction: contract says **one-week** minimum; locked hypothesis needs **4
  weeks / 100 trades / 25+25 / 3 weeks×15**. State: *one week = implementation-validation only; the locked
  minimum = promotion evidence.* No threshold may change.

**SQ-02 — Pre-register + hash-lock the diagnostic sweep** (`docs/A3_SIGNAL_QUALITY_DIAGNOSTIC_SWEEP_V1…md`
+ `.sha256.json`): the B0/B1/F_* definitions below and the discovery-window rules. Diagnostics are
hypothesis-generation only — **not** promotion evidence, **not** broker-action authorization.

---

## PHASE B — OFFLINE discovery screen (cheap go/no-go, do this BEFORE the MQL5 build)

**SQ-03 — Offline Python discovery sweep.** Run every candidate over **existing historical bars + the
10-second position-path data** (no MQL5, no attach). Produce the frequency↔quality table + loss
attribution. This is discovery only (bar/coarse-tick replay is **not** promotion evidence — the locked
hypothesis still requires forward tick-level for promotion).
- **Decision gate:** if **no** candidate shows a frequency-preserving quality lift offline (per the V2
  eligibility bar below), **STOP — A3 stays paused, do not build the forward apparatus.** Only if a
  candidate (or locked V1) looks promising do we proceed to Phase C.

### Sweep candidates (every one starts from the same raw `breakout_retest` would-signal; log all rejected)
| id | rule | role | est. freq vs B0 |
|---|---|---|---|
| `B0_RAW_ALL_SESSION` | raw breakout-retest, no new filter, all sessions | reference | 100% |
| `B1_EVENING_BASELINE` | B0 + Dubai 16:00–19:59 (apples-to-apples for V1) | reference | — |
| `F_LOOSE_CT_VETO` | block only strong counter-trend: LONG blocked if `(H1 EMA20[1]−EMA20[4])/pt ≤ −50`; SHORT if ≥ +50; neutral kept; unavailable H1 = DATA_UNAVAILABLE | diagnostic | 70–90% |
| `F_H1_ALIGN` | LONG `H1 close[1]>EMA20[1] AND EMA20[1]>EMA20[4]`; SHORT symmetric (sign only) | diagnostic | 50–70% |
| `F_H1_M15_ALIGN` | `F_H1_ALIGN` + same on M15 | diagnostic | 35–55% |
| `F_RETEST_LIGHT` | break ≥0.30 ATR; retest within 1–10 M5 bars; no invalid-side close pre-confirm; body/range ≥0.40; close-loc ≥0.65 long / ≤0.35 short; confirm on breakout side (no strict penetration/wick limits) | diagnostic | 45–70% |
| `F_LOOSE_CT_PLUS_RETEST_LIGHT` | `F_LOOSE_CT_VETO` + `F_RETEST_LIGHT` | diagnostic | 35–55% |
| `A3_SQ_MTF_ONLY_V1` | locked triple-MTF | diagnostic (locked) | 15–30% |
| `A3_SQ_RETEST_ONLY_V1` | locked strict retest | diagnostic (locked) | 40–60% |
| `A3_SQ_COMBINED_V1` | **locked primary** (MTF+retest) — **only promotion-eligible V1** | promotion-eligible | 5–15% |
Frequencies are hypotheses, not gates. **Do not relax V1 to gain trades.**

---

## PHASE C — Forward validation apparatus (ONLY if SQ-03 is promising)

**SQ-04 — `mt5/Include/A3VirtualExecution.mqh`** (tick state machine): `IDLE→SIGNAL_PENDING→VIRTUAL_OPEN→
VIRTUAL_CLOSED` (+ `CANCELLED_NO_FRESH_TICK`, `INVALID_DATA`, `RECOVERY_REQUIRED`). Decision on completed
bars; long fills at first fresh **ask**, short at first fresh **bid**; no same-bar fill; entry expires at
next M5 close. Risk `= max(raw, stops+5, 3×spread, 300 XAU)`; TP 1.50R. Long SL/TP on bid, short on ask;
gap exit on the actual quote; **don't double-count spread**. Append-only `a3_sq_decisions/events/trades.csv`
+ `state.json`; restart rebuilds from events, else `RECOVERY_REQUIRED` + block. Deterministic tests.

**SQ-05 — `mt5/Include/A3SignalQualityFilters.mqh`**: locked V1 byte-for-byte + the pre-registered F_*
diagnostics; pure completed-bar functions; fixture tests for each (accept/block + frequency direction).

**SQ-06 — `mt5/Experts/Account3SignalQualityShadowObserver.mq5`** + `…safe_xauusd.set`: hard dry-run; **no**
OrderSend/OrderSendAsync/CTrade/TRADE_ACTION_*; no position/order modification; login 1033669 + demo +
XAUUSD only; isolated observer terminal; runs all candidates in parallel, one virtual position each, shared
`signal_id` for paired comparison. Passive-source safety tests. **No MT5 attachment in this commit.**

**SQ-07 — Independent Python parity** (`reproduce_a3_signal_quality.py`, `replay_a3_virtual_execution.py`,
`generate_a3_parity_report.py`): separate codepath (do not import MQL-facing code). Feature parity (EMA/ATR
seeding, warm-up, timezone/DST, session, geometry, cost_R, all documented); **decision parity ≥99% / 100%
on accepted promotion-eligible**; execution parity (signal_id, fill tick, entry/SL/TP within 1 pt, exit,
net R, MFE/MAE). Mismatch taxonomy; any `UNKNOWN` on an accepted signal = NO-GO.

**SQ-08 — Reporting + loss attribution** (`generate_a3_signal_quality_sweep_report.py`,
`generate_a3_loss_attribution_report.py`). Loss taxonomy per losing virtual trade (path-order):
`BAD_SIGNAL` (−0.5R before +0.5R, or +0.5R never reached) · `MIXED` (+0.5R first, MFE<+0.75R, loses) ·
`BAD_EXIT_GIVEBACK` (+0.75R before −0.5R, closes ≤0R) · `NEAR_TP_GIVEBACK` (+1.25R, no TP, closes ≤0R).
Keep the fixed 1.50R exit for all entry candidates — entries and exits are not tested together. Expect
most losses = bad-signal, ~¼–⅓ give-back; exit handling is a **separate Stage-2** study.

**SQ-09 — Deterministic offline integration**: MQL5/Python fixtures + captured-tick replay; build/parity
reports; fix defects **without** changing thresholds.

**SQ-10 — Isolated shadow attachment packet** (only after SQ-00…09 pass): owner-approved, observer-only,
isolated terminal, no broker-action surface, 0/0 compile, startup hash verified, `forward_start_utc` recorded.

**SQ-11 — Discovery conclusion** (after the discovery minimum): **select no candidate** OR select one
diagnostic for a **new locked `A3_SIGNAL_QUALITY_V2_<id>.md`** — then start a **fresh** validation window.
**Never promote from the discovery window.**

---

## Metrics & gates

**Per-candidate metrics:** raw/accepted signals, signal & trade retention %, win rate, PF (after bid/ask
cost), expectancy R, net R, max DD R, max consecutive losses, P50/P95 cost_R, concentration
(largest/top-5/best-day), weekly PF, regime coverage, bad-signal vs give-back loss share.

**Frequency floor (any V2 candidate):** signal retention ≥40% of B0 · trade retention ≥35% · ≥100 closed
trades · median weekly trades ≥40% of B0. *A candidate that improves PF by blocking nearly everything fails.*

**V2 registration eligibility (discovery window, NOT broker-action):** signal retention ≥40% · ≥100 closed
trades · PF ≥1.20 · expectancy ≥+0.10R · (PF vs B0 ≥ +0.15 **or** expectancy vs B0 ≥ +0.05R) · blocked
bucket expectancy worse than kept · bad-signal loss share improves ≥20% relative · no concentration breach ·
both rising and falling regimes. → then re-lock as V2 and run a fresh window.

**Final reactivation gates:** locked V1 uses all existing gates incl. WR ≥50%. For a **V2**, set the WR
objective *before* locking — recommended **hard WR ≥45% / target 50%**, PF ≥1.30, expectancy ≥+0.15R
(rationale: the breakout core ran ~48%; a mandatory 50% may reject a valid 1.5R-payoff edge — owner decides
and writes it into V2 before the fresh test). Plus: ≥100 trades / ≥20 days / ≥4 weeks / ≥25 long + 25 short /
≥3 weeks×15 · frequency floor · P95 cost_R ≤0.15 · no trade >0.15 · max consec losses ≤8 · max DD ≤8R ·
concentration · session compliance · zero duplicate-family events · decision parity ≥99% · accepted parity 100%.

---

## NO-GO — A3 stays paused if ANY is true
933200/933300/933400 proposed for reactivation · round promoted/combined · status stale or contradictory ·
arming audit doesn't cover executable scripts · CI not green · addendum missing/hash-invalid · sweep not
pre-registered · threshold changed after forward start · observer has any broker-action code · virtual state
can't deterministically recover · parity <99% · accepted parity <100% · any `UNKNOWN` on an accepted signal ·
signal retention <40% · trade retention <35% · sample minimum unmet · one regime only · PF/expectancy/cost/
concentration gate fails · bad-signal share not materially improved · any duplicate-family event · A3 has any
open position/order at preflight · profit-lock armed · >1 A3 lane proposed · missing reviewer signoff or owner
exact-hash approval.

## Minimum evidence before reactivation can be discussed
Pause verification PASS · source safety audit PASS · expanded arming/script audit PASS · full suite + CI PASS ·
locked hypothesis + implementation addendum + locked diagnostic sweep · observer source + 0/0 compile + safe
preset + isolated attachment report · raw bars/ticks manifest with hashes · tick-execution test report ·
independent Python parity report · full minimum sample across up + down regimes · frequency floor PASS · all
PF/expectancy/cost/concentration gates PASS · bad-signal loss share materially reduced · zero duplicate-family
events · new locked V2 (if a diagnostic was selected) + fresh V2 validation window · family mutex + containment
built/tested · zero-exposure preflight · profit-lock dry-run/disarmed · reviewer signoff · owner approval of
exact source/binary/hypothesis/contract hashes · one-lane 0.01-lot micro-pilot plan with hard end date.

## Explicitly out of scope
No reactivation of 933200/933300/933400 · no round promotion · no combined executor · no A1/A2 change · no
broker action · no live/real capital · no preset arming · no profit-lock deployment change · no lot increase ·
no grid/martingale/averaging/recovery · no threshold tuning after forward start · no discovery data as V2
validation · **no daily loss breaker presented as an entry-quality fix**.

## Codex order of work
1. **Do not touch MT5 runtime.**
2. SQ-00 (status + arming-script audit) → SQ-01 (addendum) → SQ-02 (pre-register sweep).
3. **SQ-03 offline Python discovery screen → DECISION GATE.** If nothing clears the V2-eligibility bar, **stop; A3 stays paused.**
4. Only if promising: SQ-04…SQ-09 (tick engine → filters → observer → parity → reporting → integration), then SQ-10 (isolated shadow attach), then SQ-11 (conclude: no candidate, or lock V2 + fresh window).
5. One task per commit; preserve the report-trail pattern; change no threshold mid-stream.

**Boundary:** repo-only / shadow-only. Demo only. A3 stays paused; no reactivation; canonical Phase 2/3 unchanged.
