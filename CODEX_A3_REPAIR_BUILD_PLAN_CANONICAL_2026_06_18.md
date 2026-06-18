# Codex A3 Repair — Canonical Build Plan (single source of truth) — 2026-06-18

This file reconciles three reviews (Claude guidance `A3_REPAIR_IMPLEMENTATION_GUIDANCE_e3e3e7a`, the
third-party `FINAL_REVIEW_…` line, and the GPT review) into **one ordered plan**. Where they conflicted,
the resolution is stated inline. **Work from this file; ignore the overlapping three for sequencing.**

## Status & hard boundary
- Commit `e3e3e7a`: GO (governance/test closure verified — hash-lock recomputed and matches; profit-lock
  SLTP-only; safety audit fail-closed for source scope; A3 fully paused, 0 exposure).
- **A3 stays PAUSED. All work below is repo-only / shadow-only. No reactivation is authorized.**
- Frozen, must not change while this plan runs:
  `933200=PAUSED · 933300=PAUSED · 933400=PAUSED · profit-lock=DRY_RUN_DISARMED · open=0 · pending=0`.

## Guiding principle (the one reorder that matters)
**Prove the edge in shadow BEFORE building the reactivation machinery.** The mutex and containment are
only needed *for reactivation*, which is far off and conditional on evidence we do not yet have. So the
cheap safety fixes come first, then the shadow **edge test** (observer + tick engine + parity), and the
mutex/containment **last and only if the shadow shows an edge worth reactivating**. Do not spend weeks on
mutex race-tests and containment for a lane the shadow may prove has no edge.

**Honest prior:** the breakout core historically ran ~47.75% win; the locked spec requires WR ≥ 50%. The
*most likely* honest outcome of this whole effort is "shadow did not clear the gates → A3 stays paused,"
and that is the process **working**. Build accordingly; do not assume a green light.

---

## P0 — Preserve the freeze (always)
No chart, terminal, profile, order, lot, SL/TP, preset, or account change is authorized in any stage
below. Do not touch A1 or A2. Do not touch MT5 runtime.

## P1 — Cheap safety + governance fixes (DO FIRST)

### P1.1 Harden `apply_a3_emergency_pause.py` (fail-closed, idempotent)
Modes: `--verify-only`, `--dry-run`, `--apply`. The script must:
1. **Dynamically enumerate** every A3 profile chart with an execution/management surface — do **not** rely
   on hardcoded EA names/magics; a future lane must not escape the pause.
2. **Abort before any edit** if A3 has any open position or pending order.
3. **Verify the terminal process is fully stopped** before writing profile files.
4. **Hash every chart before/after** and prove non-target charts are byte-unchanged.
5. **Idempotent:** a repeat run returns `ALREADY_PAUSED` with zero changes.
6. **Auto-rollback** the profile if post-restart verification fails.
7. **Fail-closed:** if it cannot *confirm* a lane disarmed, report FAIL — never assume success.
8. Write a hashable report: before/after exposure, profile hashes, changed inputs, startup rows, rollback path.

### P1.2 Kill-switch two-tier semantics (correction — do NOT write the current full-stop file)
The current A3 base checks the kill switch inside startup scope locks, so the existing `A3_KILL.txt` blocks
EA init **including dry-run**, which would destroy shadow telemetry. Implement:
- `A3_EXECUTION_KILL.txt` → blocks broker action, **permits** passive init + logging.
- `A3_FULL_STOP.txt` → refuses init entirely.
Until these semantics exist, rely on verified dry-run/broker-action inputs + zero-exposure checks; do **not**
write the current full-stop file during shadow work.

### P1.3 Arming-layer audit — `scripts/audit_phase1_arming.py` (the largest remaining audit gap)
The source audit does not inspect the layer that actually arms trading. Fail the build on any committed
`.set` / `.ini` / `.chr` / deployment-arg / auth-token artifact containing:
`InpDryRunOnly=false`, `InpBrokerActionAllowed=true`, `InpManageActionAllowed=true`,
`InpAllowDemoTrading=true`, `InpAllowNonDemoAccounts=true`, a nonblank execution-authorization token, or a
nonblank cost-suspension token. Policy: **no armed preset/profile may be committed**; owner-armed presets
stay local/private; the repo stores only a signed hash + authorization record. `*.template.set` allowed only
with execution disabled and tokens blank. Confirm `_scan_paths` covers every executable source tree.

### P1.4 Status semantic corrections (`generate_project_status_*`)
- Rename `source_runtime_parity_status` → `pause_artifact_runtime_consistency_status` (it only proves the
  review+pause artifacts agree). Real source↔runtime parity requires source SHA + compiled EX5 SHA +
  deployed EX5 SHA + profile-input hash + compile log + runtime startup hash (terminal-side capture).
- `shadow_hypothesis_status`: the generator must **recompute the SHA256 and verify manifest status**, not
  rely on file existence / the unit test alone.
- Replace generic `a3_tier1.status = PASS` with **named** statuses (historical attach PASS vs runtime
  performance FAIL vs authorization PAUSED).
- Keep `runtime_performance_status = FAIL` **immutable as audit history.** Do not overwrite it to obtain
  reactivation. Add a separate future field `shadow_candidate_performance_status` that must pass instead.

**P1 exit gate:** full pytest green **and a green CI run** (the 415-pass is currently local-only evidence) ·
source safety audit PASS · arming audit PASS · pause `--verify-only` PASS.

## P2 — Freeze the implementation contract (before any observer code)
- **Do not edit the locked hypothesis file.** Its header still says `PRE_REGISTERED_LOCK_PENDING_MANIFEST`
  while the manifest says `LOCKED`; editing breaks the valid hash. Record the discrepancy in a separate lock
  note, or cut V1.1 later. No thresholds may change.
- Create + separately hash-lock:
  - `docs/A3_SIGNAL_QUALITY_V1_IMPLEMENTATION_CONTRACT.md` — resolves the seams the hypothesis leaves open:
    exact first-retest definition, signal timestamp, entry-tick eligibility + expiry, indicator warm-up,
    EMA/Wilder-ATR seeding, timezone mapping, weekend/open-gap treatment, holding duration, restart recovery,
    tick-freshness, rounding, gap-exit pricing, candidate priority, `forward_window_start_utc`.
  - `docs/A3_SIGNAL_QUALITY_V1_THRESHOLD_PROVENANCE.md` — label the `±50`-pt slopes and ATR ratios honestly
    as expert-prior / prior-review-derived / recent-sample-derived. **Do not invent a post-hoc derivation.**
    If informed by the recent A3 loss cluster, V1 is a repair hypothesis and needs strictly post-lock forward proof.
  - `outputs/manifests/A3_SIGNAL_QUALITY_V1_IMPLEMENTATION_CONTRACT.sha256.json`.
- Lock a forward protocol: observer source commit, observer binary hash, hypothesis hash, `forward_start_utc`,
  minimum end condition, market-regime coverage definition, data-embargo rule.

## P3 — Build and run the EDGE TEST (the reordered core — answers "does the edge exist?")

### P3.1 Tick-level virtual execution engine — `mt5/Include/A3VirtualExecution.mqh`
States: `IDLE → SIGNAL_PENDING → VIRTUAL_OPEN → VIRTUAL_CLOSED`; terminal alts `CANCELLED`, `INVALID_DATA`,
`RECOVERY_REQUIRED`. Rules:
- Decision on **completed bars only** (after `bar[1]` close). Long fills at first **fresh ask**, short at first
  **fresh bid** after decision; **no same-bar historical fill**. Max entry delay = first fresh tick before the
  next M5 bar closes, else `CANCELLED_NO_FRESH_TICK` (put the exact value in the contract).
- Risk geometry: `risk = max(raw, broker_stops+5, 3×spread_at_fill, 300 XAU pts)`; `TP = fill ± 1.50×risk`.
  Long SL/TP evaluated on bid, short on ask.
- **Cost: do not double-count.** Ask-entry/bid-exit already embeds spread; log `estimated_cost_R` as a
  diagnostic only, do not subtract spread again from net R.
- Per tick: validate monotonic timestamp + quote freshness; update MFE/MAE; check SL/TP on the executable
  side; record gap slippage on the actual quote; write event; persist state. Ambiguous aggregated tick →
  classify explicitly, resolve **adverse-first**.
- Persistence: append-only `a3_sq_virtual_events.csv` + `a3_sq_virtual_trades.csv` + `a3_sq_virtual_state.json`;
  on restart recover from event history; if uncertain → `RECOVERY_REQUIRED` and block new signals.
- **No broker API at all** (no OrderSend/CTrade/TRADE_ACTION_*). One virtual position per candidate.

### P3.2 Shadow-only observer — new EA, do not edit 933300/933400
Files: `mt5/Experts/Account3SignalQualityShadowObserver.mq5`, `mt5/Include/A3SignalQualityPolicy.mqh`,
`mt5/Presets/Account3SignalQualityShadowObserver.safe_xauusd.set`. Locks: hard dry-run; no OrderSend/CTrade/
TRADE_ACTION_*; no position modification; account `1033669` + `Capital.ComMena-Demo` + XAUUSD only;
**isolated observer terminal.** Implements `A3_SQ_COMBINED_V1` (primary) + `A3_SQ_MTF_ONLY_V1` /
`A3_SQ_RETEST_ONLY_V1` (diagnostic). Block-and-log on unavailable data / mixed D1 / neutral slope / timestamp
ambiguity. Each decision row logs: hypothesis id/version/hash, candidate id, base signal id, broker/UTC/Dubai
timestamps, bar timestamps, level type+price, break/retest/confirm indexes, raw OHLC, ATR+EMA values, MTF
booleans, retest-quality booleans, session status, spread, cost_R, mutex would-claim result, accept/block reason.

### P3.3 Independent Python parity — separate codepath (do not import MQL-facing helpers)
Files: `scripts/reproduce_a3_signal_quality.py`, `replay_a3_virtual_execution.py`,
`generate_a3_parity_report.py`, `generate_a3_shadow_performance_report.py`. Gates:
- **Feature parity**: D1 EMA20/50, H1+M15 EMA20 slope, M5 ATR14 (document EMA & Wilder seeding + warm-up),
  session map, break/retest geometry, spread/cost_R.
- **Decision parity ≥ 99%** overall, **100% on accepted primary signals**; classify every mismatch
  (`BAR_ALIGNMENT, TIMEZONE, EMA_INITIALIZATION, ATR_INITIALIZATION, ROUNDING, SESSION_BOUNDARY,
  QUOTE_FRESHNESS, STATE_RECOVERY, DATA_GAP, UNKNOWN`); any `UNKNOWN` on an accepted trade = NO-GO.
- **Execution parity**: same signal id / first eligible tick / direction / fill time; entry/SL/TP within
  1 point; same exit event+timestamp; same net R; same MFE/MAE.
- **Metric parity**: Python independently computes trade count, WR, PF, expectancy R, drawdown R, consecutive
  losses, cost distribution, daily/weekly buckets, concentration, regime coverage — the MQL5 report is **not**
  the sole source of the performance gates.

**P3 exit gate:** observer live in shadow on the isolated terminal · parity ≥99% / 100% accepted · accumulating
toward the locked minimum sample (≥100 trades, ≥20 days, ≥4 weeks, ≥25 long + ≥25 short, ≥3 weeks×15) across
**both a rising and a falling XAU regime**. *This is the gate that decides whether anything below is worth building.*

> **Selectivity-vs-sample risk to watch (neither prior review flagged):** the strict MTF+retest filters exist
> to lift WR, but the tighter they are, the fewer trades fire — and V1 also needs ≥100 trades in ≥4 weeks.
> V1 can fail on the conflict between its own WR gate and its own sample minimum. Keep the observer running
> well past 4 weeks; do not relax filters to reach sample (that would break the lock).

## P4 — Reactivation infrastructure (build ONLY if P3 shows a passing-trend edge)

### P4.1 Account-wide breakout-family mutex — `mt5/Include/A3FamilyMutex.mqh`
Key: `A3MX_<account>_<symbol>_<family>_<direction>_<M5-bar-epoch>` (e.g. `A3MX_1033669_XAUUSD_BR_BUY_1781794500`).
Include family constant `BR`; **never** include magic/candidate/lane (else lanes won't collide). **No level
band in V1** (it would let two lanes trade different levels on the same directional bar = doubled exposure).
Atomic claim via `GlobalVariableSetOnCondition(key, owner_magic, 0)`; reconstruct same-bar exposure from
positions/orders/history before claiming; `OrderSend` only after a successful claim. Release: retain through
M5-bar-end + 60s on success; on failed send still retain through bar (no "rescue"); on restart reconstruct the
current-bar claim; remove stale key only after 15 min **and** no matching exposure/order/deal. Terminal
GlobalVariables suffice within one A3 terminal; cross-data-directory needs an execution-arbiter terminal or a
separately reviewed shared lock. Tests: 3 lanes same key → exactly 1 claim/2 blocked; different account/symbol/
bar → independent; same-second race → 1 winner; failed order → lock held through bar; restart → reconstructed;
stale key → removed only after validation; unknown magic/family → fail closed. **Even with the mutex, only one
A3 breakout lane may ever be broker-action enabled at a time** (defense-in-depth, not permission for correlated lanes).

### P4.2 Containment — `mt5/Include/A3ContainmentPolicy.mqh` + `docs/A3_CONTAINMENT_POLICY_V1.md`
Exposure: one broker-action A3 lane; one breakout-family position total; no duplicate same-bar family entry;
no market-entry pending orders. Trade risk: fixed 0.01 lot; planned risk ≤0.50% day-start equity (if broker
0.01 min exceeds that cap → block the trade); no compounding. Daily (Dubai boundary): max 2 new entries; soft
lock after 2 closed losses OR day PnL ≤ −1.5R OR equity ≤ −1.5% from day-start; soft lock resets next Dubai
day only if no position/order, ledger reconciled, no hard lock. Hard locks (survive restart, require signed
versioned manual reset): 4 consecutive losses; weekly PnL ≤ −4R or weekly DD ≤ −4%; any duplicate broker
entry; mutex uncertainty/failure; unexpected account/symbol/magic. Tests: injected-trigger tests for every
soft/hard lock; restart-persistence of hard locks.

## NO-GO conditions — A3 stays paused if ANY one is true
Pause verification not fail-closed/current · source audit fails · arming audit fails · any armed preset/profile
committed · test suite or CI not green · hypothesis/contract hash mismatch · threshold changed after forward
start · observer has any broker-action surface · mutex missing or unresolved race · any duplicate virtual or
broker family entry · primary sample below locked minimum · any locked performance gate fails · evidence missing
a rising OR a falling regime · decision parity <99% · accepted-signal parity <100% · any unresolved
timestamp/lookahead mismatch · cost_R >0.15R · concentration gates fail · containment missing/untested · any
open A3 position/order at preflight · profit-lock armed · >1 A3 lane proposed · compile not 0/0 · no independent
reviewer signoff · no owner approval of exact source/binary/hypothesis hashes · no profile backup or first-order
reconciliation plan.

## Minimum evidence package before reactivation is even discussed
1. Hardened pause script + verification report. 2. Source safety audit PASS. 3. Arming-layer audit PASS.
4. Full suite + CI PASS. 5. Locked hypothesis + locked implementation contract. 6. Threshold-provenance note.
7. Observer source + safe preset + compile log + attachment report. 8. Tick state-machine test report.
9. Raw tick/bar manifests with SHA256. 10. Python feature/decision/execution/metric parity report.
11. Primary shadow result meeting **every** locked gate. 12. Evidence covering ≥1 rising and ≥1 falling regime.
13. Mutex source + unit + race tests + shadow report. 14. Zero duplicate-family entries. 15. Containment impl +
injected-trigger tests. 16. Current zero-position/zero-order reconciliation. 17. Profit-lock dry-run/disarmed
proof. 18. Independent reviewer signoff. 19. Owner approval of exact source/binary/hypothesis hashes.
20. One-lane 0.01-lot micro-pilot plan with hard end date. 21. First-order + first-day reconciliation checklist.

## Explicitly out of scope
No reactivation of 933200/933300/933400 · no new broker-action A3 lane · no change to A1/A2 · no live/real
capital · no lot increase · no profit-lock rearming · no adding 933300 to the profit-lock manager · no multiple
execution-eligible A3 lanes · no threshold tuning after forward start · no historical A3 trades as V1 pass
evidence · no quarantined bar replay as promotion evidence · no martingale/grid/averaging/recovery logic.

## What Codex does first (immediate, in order)
1. Do not touch MT5 runtime. 2. Harden `apply_a3_emergency_pause.py` (P1.1) + two-tier kill semantics (P1.2).
3. Add the arming-layer audit (P1.3). 4. Correct the status fields (P1.4). 5. Run the full suite + CI.
6. Write + lock the implementation contract + provenance (P2). 7. **Then** build the tick engine → observer →
parity (P3). 8. Build the mutex + containment (P4) **only after** P3 shows a passing-trend edge.

## Files (manifest)
Scripts: `apply_a3_emergency_pause.py`, `audit_phase1_arming.py`, `audit_phase1_safety.py`,
`generate_project_status_summary.py`, `generate_project_status_page.py`, `reproduce_a3_signal_quality.py`,
`replay_a3_virtual_execution.py`, `generate_a3_parity_report.py`, `generate_a3_shadow_performance_report.py`,
`verify_a3_reactivation_artifacts.py`.
MT5: `A3FamilyMutex.mqh`, `A3VirtualExecution.mqh`, `A3SignalQualityPolicy.mqh`, `A3ContainmentPolicy.mqh`,
`Account3SignalQualityShadowObserver.mq5`, `Account3SignalQualityShadowObserver.safe_xauusd.set`.
Docs: `A3_SIGNAL_QUALITY_V1_IMPLEMENTATION_CONTRACT.md`, `A3_SIGNAL_QUALITY_V1_THRESHOLD_PROVENANCE.md`,
`A3_CONTAINMENT_POLICY_V1.md`, `A3_REACTIVATION_GOVERNANCE_V1.md` (+ matching `.sha256.json` manifests).
Tests: `test_apply_a3_emergency_pause.py`, `test_phase1_arming_audit.py`, `test_a3_family_mutex_contract.py`,
`test_a3_family_mutex_races.py`, `test_a3_virtual_execution.py`, `test_a3_signal_quality_policy.py`,
`test_a3_shadow_observer_safety.py`, `test_a3_python_parity.py`, `test_a3_containment_policy.py`,
`test_a3_reactivation_verifier.py`.

**Boundary:** repo-only / shadow-only. Demo only. No reactivation; canonical Phase 2/3 unchanged.
