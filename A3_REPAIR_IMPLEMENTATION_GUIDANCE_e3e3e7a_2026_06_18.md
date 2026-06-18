# A3 Repair — Review of e3e3e7a + Implementation Guidance (2026-06-18)

Reviewer: Claude. Scope: **XAUUSD, A3 `1033669`, demo only.** Reviews commit `e3e3e7a` and gives
prioritized guidance for the remaining repair work. **A3 stays PAUSED; all remaining work is
repo-only / shadow-only. I find no compelling reason to reactivate 933200/933300/933400 — keep them paused.**

## What I verified in e3e3e7a (independently)
- **Hash-lock is real:** I recomputed `sha256` of `A3_SIGNAL_QUALITY_HYPOTHESES_V1_2026_06_18.md` =
  `9cb1f100…f77229`, which matches the manifest exactly (status `LOCKED`). The hypotheses are genuinely frozen.
- **Profit-lock is SLTP-only:** the manager contains only `TRADE_ACTION_SLTP`; no `TRADE_ACTION_DEAL`, no
  `CTrade`, no `#include <Trade>`. It can move stops, never open/close at market.
- **Safety audit is fail-closed for source scope:** canonical scan flags **any** broker-action term in every
  file **not** in `EXPERIMENTAL_POLICIES`; policy-governed files must carry the full safety token set
  (`InpAllowDemoTrading=false`, demo-mode check, kill switch, fixed 0.01 lot…). The two scans share one file
  universe, so every scanned source file is covered by exactly one — unknown source ⇒ canonical ⇒ fails.
- **status_summary v2 separation is clean:** historical owner auth (`SUPERSEDED_BY_EMERGENCY_PAUSE`) vs
  current runtime (all lanes PAUSED, profit-lock DRY_RUN_DISARMED, 0 positions/0 orders) vs effective auth
  (`A3_ENTRY_LANES_PAUSED`). A3 runtime_performance = FAIL (broker-action history: 23 trades, 1 win, −758.79).

The pause is the right call and the commit is sound. Two concerns below (items 7–8), then the roadmap.

---

## Concern with the safety-audit approach (item 7)
The approach is good — keep it — but it has two boundaries to close:
1. **It is SOURCE-scope only; it does not audit the arming layer.** Broker action is actually enabled by
   **presets (`.set`) and chart profiles (`.chr`/`.ini`)** where `broker_action_allowed=true` lives. A source
   file with safe defaults can still be armed by a preset the audit never inspects. **Add a fail-closed
   arming-layer audit**: scan committed `.set`/profile artifacts and fail on any `broker_action_allowed=true` /
   `InpDryRunOnly=false` outside an explicit allowlist. (Today this is only partially covered by separate
   preset tests + the emergency pause.)
2. **Term matching is bypassable.** The script even obfuscates its own terms (`"C"+"Trade"`); a macro, typedef,
   or alternate order API would evade a literal search. Acceptable as a first line **combined with** the runtime
   pause and zero-exposure checks — but (a) confirm `_scan_paths` covers every executable source directory (no
   unscanned tree), and (b) treat the audit as defense-in-depth, not a sole guarantee.

## Concern with the hypotheses thresholds / hash-lock (item 8)
The structure is strong (concentration caps, both-direction sampling, weekly consistency, parity gates). Notes:
1. **Hash-lock immutability caveat (important):** the doc's internal header still says
   `PRE_REGISTERED_LOCK_PENDING_MANIFEST` while the manifest is `LOCKED`. **Do not edit the doc to fix it** —
   any edit changes the hash and breaks the lock. Either leave it byte-frozen and record the correction in the
   manifest/changelog, or cut a **V1.1** with a new hash. Treat the locked file as immutable from here.
2. **`WR ≥ 50%` may be too strict and partly redundant.** Our breakout core historically ran ~47.75% WR yet
   was profitable on payoff. `PF ≥ 1.30` and `expectancy ≥ +0.15R` already enforce profitability; an extra
   `WR ≥ 50%` gate can reject a real low-WR/high-payoff edge and biases toward high-WR/low-payoff. It's frozen
   for V1 (a conservative error, fine for a paused account) — **reconsider for V2** (≈45%, or drop in favor of PF/expectancy).
3. **Document threshold provenance.** The MTF `±50`-point slope and the retest ATR ratios are specific numbers
   with no recorded derivation. Pre-registering is right, but note *how* they were chosen (ATR-relative? prior
   fit? expert prior?) — if fit to recent data, V1 carries latent in-sample bias the forward window will expose.

---

## Prioritized implementation roadmap (my recommended order)

### P1 — Harden the emergency pause **first** (item 6)
Do this **before** the shadow observer. It's small, foundational, and the whole "A3 stays paused" assumption
rests on it. Requirements:
- **Idempotent + fail-closed:** re-runnable; if it cannot *confirm* a lane is disarmed, it reports FAIL (never
  assumes success).
- **Enumerate all surfaces dynamically** — scan the A3 profile/charts for any broker-action EA (don't hardcode
  933200/933300/933400); a future lane must not be able to escape the pause.
- **Post-condition verification:** after pausing, query the terminal and assert **0 open positions, 0 pending
  orders, every chart `dry_run=true`/`broker_action=false`, profit-lock disarmed**; write a signed report; raise on any failure.
- **Kill-switch defense-in-depth:** write `A3_KILL.txt` so EAs self-block even if a chart input is missed.
- **Profile backup first; reversible.** Output `A3_EMERGENCY_PAUSE_VERIFIED_*.json`.

### P2 — Account-wide breakout-family mutex (item 1)
Required before any reactivation — duplication was a root cause (it inflated every prior PnL ~2×).
- **Key = `symbol | direction | M5-bar-open-time` (+ optional level band). Do NOT include magic/family in the
  key** — the point is that different lanes on the *same* signal collide and dedupe to one entry.
- **Atomic claim** via `GlobalVariableSetOnCondition` (test-and-set); first lane claims the bar, others log
  `WOULD_DUPLICATE_FAMILY` and skip. Use `FILE_COMMON` only if cross-terminal is ever needed.
- **Lifecycle:** claim at signal; auto-expire on bar roll / position close; timeout so a crashed EA can't deadlock.
- **Test expectations:** 3 lanes same bar+direction ⇒ exactly 1 claims, 2 logged; different bars ⇒ independent;
  opposite direction same bar ⇒ decide policy (recommend block same symbol+direction+bar, allow opposite only if
  intended); lock releases after bar/close; concurrent tick race ⇒ exactly one winner; in shadow it **logs
  would-block, blocks nothing**.

### P3 — Tick-level virtual execution state-machine (item 3)
The engine the shadow observer runs on.
- **States:** IDLE → SIGNAL_PENDING (completed-bar signal on `bar[1]`) → VIRTUAL_OPEN (fill at first eligible
  tick: **ask** for long, **bid** for short) → evaluate **every tick** (track MFE/MAE) → VIRTUAL_CLOSED (first
  tick crossing SL or TP). One virtual position per candidate.
- **No lookahead:** signal from completed bar, entry from the *next* tick.
- **SL/TP:** baseline post-floor geometry (`max(raw, stops+5, 3×spread, 300 XAU)`; TP = entry ± 1.5R).
- **Ambiguous tick (range spans SL and TP):** resolve **conservatively (SL first)** and log the ambiguity;
  check long-exit on bid, short-exit on ask.
- **No broker API at all** (no OrderSend/CTrade/TRADE_ACTION_*). Pure in-memory + logging; **deterministic and
  replayable** from the tick log (so Python parity can reproduce it).
- Handle missing ticks / session close / weekend gaps / data-unavailable ⇒ block + log.

### P4 — Shadow-only signal-quality observer (item 2)
- Implements `A3_SQ_COMBINED_V1` (primary) + the two ablations (diagnostic only; never promote an ablation if
  primary fails). Decisions on **completed bars only**.
- Enforce the locked baseline invariants + strict MTF (D1/H1/M15 EMA) + strict retest (ATR ratios) exactly as
  hashed; **emit the hypothesis version + hash on every decision row**.
- **Block-and-log** on missing indicator / timestamp / mixed-HTF / unavailable data.
- Feeds accepted signals into the P3 state-machine. **No CTrade, no OrderSend, no SL/TP modification.**
- **Run it on an isolated observer terminal** (like the existing path observers), never the A3 trading terminal,
  so there is literally no broker-action surface.

### P5 — Python parity / replay harness (item 4)
- **Independent** reimplementation (separate codepath) of the decision logic: EMA20/50 on D1/H1/M15, ATR14 on
  M5, MTF conditions, retest rules, session map (`TimeGMT()+240`), cost_R.
- Replays the **same completed-bar data**; must match MQL5 **≥99%** of decisions; **classify every mismatch**;
  **no unresolved lookahead/timestamp mismatch**; entry/SL/TP within **1 symbol point**.
- Independently re-derive the gate metrics (WR, PF, expectancy, concentration) from the virtual-trade log so the
  performance gates are not self-reported by the MQL5 side. This is the anti-self-deception layer.

### P6 — Containment rules (item 5) — define now, enforce before any reactivation
The hypotheses doc's 11-point boundary **plus**: family mutex ACTIVE; emergency pause hardened+tested;
**micro-pilot caps** (auto-disarm at a daily-loss limit, max consecutive losses, max trades/day, fixed 0.01 lot,
single lane only, hard pilot end-date, equity-floor auto-pause); kill switch + equity guardian live;
zero-exposure baseline + first-order/first-day reconciliation; reviewer signoff + owner approval of the exact
version+hash.

---

## NO-GO conditions that keep A3 paused (item 9) — any one is disqualifying
- Family mutex `NOT_IMPLEMENTED` (current state). • Emergency pause not hardened/verified fail-closed.
- Shadow observer not built, or **any** performance gate unmet, or sample below ≥100 trades / ≥20 days /
  ≥4 weeks / ≥25 long / ≥25 short / ≥3 weeks×15. • Evidence not spanning **both an up and a down regime**.
- Python parity `<99%`, or **any** unresolved lookahead/timestamp mismatch. • Concentration breach (any day
  >30%, top-5 >40%, largest >10%). • Any open A3 position/order, or profit-lock not disarmed.
- Safety/arming audit fails, or an armed preset/profile is committed. • Any threshold changed mid-window
  (invalidates the pre-registration). • Missing reviewer signoff / owner approval of exact version+hash /
  compile 0-0 / zero-exposure baseline / defined micro-pilot limit. • runtime_performance still FAIL.

## Minimum evidence package before even discussing broker-action reactivation (item 10)
1. Locked hypothesis (have it) + observer + state-machine + Python-parity harness, all built and committed.
2. Shadow results passing **all** performance gates on the full minimum sample, across ≥1 up and ≥1 down regime.
3. Python-parity report ≥99%, all mismatches classified, zero lookahead.
4. Family mutex implemented + test suite green (exactly-one-claims).
5. Emergency pause hardened + a tested disarm/reconcile report.
6. Containment / micro-pilot plan with explicit numeric caps.
7. The already-pending forward-week evidence closed (round-quarantine impact, protected-core, afternoon residual,
   A1/A2/A3 reconciliations — per `next_evidence_required`).
8. Independent reviewer signoff + owner approval of the **exact version + hash**; compile 0/0; profile backup;
   zero-exposure baseline.
Only with **all** of that is a **single-lane, 0.01-lot, capped micro-pilot** reactivation even a discussion.

## Bottom line
Keep 933200 / 933300 / 933400 **PAUSED**. A3's only broker-action evidence is a loss (−758.79, 1/23 wins),
the family mutex that would prevent the duplication root cause is still unbuilt, and there is zero shadow
evidence yet. Order of work: **harden the pause → family mutex → tick state-machine → shadow observer → Python
parity → containment.** Everything repo-only/shadow-only until the full evidence package and gates clear.

**Boundary:** review/guidance only. Demo only. No MT5 runtime, EA, preset, chart, order, or account change is
authorized. No reactivation authorized; canonical Phase 2/3 unchanged.
