# Codex Work Order — Addendum 2: EA-T2 Build, EA-T3 Diagnosis, G5 Fix, Trend Research (2026-06-13)

Authorization: owner-approved (Ali), demo-only, fail-fast. Additive to
`CODEX_WORK_ORDER_A3_REPAIR_LANE_2026_06_13.md` (T0-T8) and
`CODEX_ADDENDUM_EVENING_SESSION_AND_CONFLUENCE_2026_06_13.md` (T9-T12). Does not remove or
weaken any existing task.

## Owner decisions recorded here (so the record is honest)

1. **EA-T2 attaches alongside EA-T1 on Monday**, rather than waiting the reviewer's
   precautionary 2-week sequential window. Accepted trade-off: if both EAs underperform at
   the same time, isolating which mechanism (impulse-veto vs. structure-filter) is
   responsible takes more weeks of data — mitigated by per-magic attribution (T15), which
   keeps each EA's PnL/WR independently readable regardless of what else runs on A3.
2. **"Fail fast" applies to ceremony, not to safety.** T6/T7's 14-gate owner-authorization
   packet is consolidated into one combined preflight checklist (T17) covering EA-T1+EA-T2
   together. The hard safety/scope gates — non-executing committed defaults, demo-login
   allowlist (1033669 only), no `PositionClose`/`PositionModify`/`OrderDelete`, kill-switch
   file, magic-band correctness, GV-mutex-before-OrderSend — remain **mandatory and
   unchanged**. These are cheap to verify and prevent bugs regardless of demo/live.
3. **EA-T3 does not exist yet.** T14 below is a diagnosis-only task (a report), not an EA.
   No EA-T3 code is written in this batch. "Three EAs ready Monday" is not accurate — this
   batch targets **two** (EA-T1 + EA-T2) attaching Monday, with EA-T3's diagnostic work
   running in parallel so it can queue for the *next* attach window if it produces a real
   fix.

---

## T13 — Build EA-T2: `Account3RoundRetestStructuredExecutor.mq5`

- **Source kernel**: copy the entry kernel from `symbol_normalized_round_retest_v0`
  byte-faithfully — same levels, retest window, confirmation candle, ATR/floor stop, 1.5R
  target as EA-T1's T1 kernel. Do not share source/includes with A1's executor or with
  EA-T1's file — each stays independently byte-stable.
- **The one new variable**: structural confirmation. Only allow entry if M15 shows a
  confirmed swing break in the trade direction within the lookback window defined in
  `PORTFOLIO_AND_FIXED_EA_DEPLOYMENT_PLAN_2026_06_13.md` §2.2 ("Phase B" / EA-T2
  pre-registration). If that write-up under-specifies the exact bar count/threshold for
  "confirmed M15 swing break," **reuse the swing-detection logic already implemented for
  `swing_breakout_retest_v0`** (same repo, same definition) rather than inventing new
  swing math — and flag in the report exactly which constants were carried over, for my
  review.
- **EA-T2 does NOT include G1 (impulse veto).** This keeps EA-T1 (context/impulse fix) and
  EA-T2 (structure fix) as two independent single-variable tests, each cleanly
  attributable via magic number — consistent with the per-EA-attribution discussion.
- **Guard chain G2-G6**, same pattern as EA-T1's T1 table, EA-T2's own namespace:
  - G2 family mutex: `GlobalVariableSetOnCondition("FAMMUX_RDSTRUCT_XAUUSD_"+dir+"_"+barTime, magic, 0)` claimed before OrderSend, expires with the M5 bar.
  - G3 streak breaker: 3 consecutive SL closes (own magic) within rolling 2h → pause to
    next 4h boundary.
  - G4 daily entry stop: own-magic realized day PnL ≤ -150 AED → pause to next Dubai day.
  - G5 caps: **max 1 open position per magic** (T15) — `InpMaxEstimatedCostR=0.15`
    execution cap / 0.20 warn / 0.30 reject, `InpMaxMeasuredSpreadPoints=75`,
    `InpMinSecondsBetweenOrders=60`, `InpFixedLot=0.01`.
  - G6 scope locks: XAUUSD only, demo-server marker, `InpAllowedAccountLoginsCsv` = `1033669`
    only, kill-switch file (reuse `A3_KILL.txt`, shared across both EAs on A3 — a kill on
    A3 should stop everything on A3), `InpDryRunOnly=true` + `InpBrokerActionAllowed=false`
    committed defaults.
- **Magic**: `InpMagicNumber = 933100` (new band 933100-933199). Comment `RDSTRUCT_V1`.
- **Would-signal logging first-class**: log the structural-confirmation raw values (swing
  bar index/time, break direction, distance from level) on EVERY signal row regardless of
  pass/block. Reason code for blocks: `STRUCT_FILTER_BLOCK`.
- Session policy: all sessions, no session filter (same rationale as EA-T1).

## T14 — `session_extreme_retest_v0` entry-failure forensics (report only, no EA code)

- Apply the same forensics methodology as
  `CODEX_ENTRY_FAILURE_FORENSICS_2026_06_12.md` to `session_extreme_retest_v0`'s full trade
  history (94 kept + its duplicate clones, all-time).
- Minimum breakdowns: win/loss by time-of-day bucket; by which session-extreme level type
  triggered (session high vs. session low, crossed against direction); by
  `impulse_alignment` at entry (use T12's refreshed M5 bars); by distance from session
  open; any other dimension the existing observer logs already capture for this candidate.
- **Output**: `docs/SESSION_EXTREME_ENTRY_FORENSICS_2026_06_13.md` — findings only, plus a
  candidate fix hypothesis IF the data supports one. This is EA-T3's design input for my
  review. **Magic band 933200-933299 is RESERVED for EA-T3 but not used** until a fix is
  designed, reviewed, and pre-registered the same way EA-T1/EA-T2 were.

## T15 — G5 per-magic position cap (EA-T1 + EA-T2)

- Change G5's "max 1 open position" to **"max 1 open position per magic number"** for both
  EA-T1 (933000) and EA-T2 (933100) on A3. Update T1's G5 spec to match (EA-T1 was
  originally specified as account-wide max-1; this addendum supersedes that for A3 only).
- Account-level controls (Guardian Stage A/B, weekly -400 AED breaker, kill-switch) remain
  **account-wide** — shared-fate circuit breakers across whatever runs on A3, by design.

## T16 — Multi-timeframe trend-context research (data + analysis only, no code change)

- Export H1, H4, and D1 OHLC bars for XAUUSD (and EURUSD/GBPUSD/USDJPY if cheap to include
  in the same pull) covering 2026-06-01 through current time, alongside T12's M5 refresh.
- For every closed **kept** trade in `PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv`, compute the H1
  and H4 trend direction at entry time. Use the cheapest consistent trend-direction
  primitive available in the repo already (e.g., price vs. a moving average, or
  prior-swing-high/low on that timeframe) — **state explicitly which definition was used**
  so it can be reviewed/replaced if needed, rather than silently picking one.
- Tag each trade WITH-trend or AGAINST-trend on H1 and on H4.
- **Output**: `docs/MULTI_TIMEFRAME_TREND_ALIGNMENT_REPORT_2026_06_13.md` — WR/PnL split by
  (with-trend vs. against-trend) × (H1, H4), per family. This is the evidence test for
  whether a shared trend-context filter would help, and for which EAs/timeframes. No EA
  changes until reviewed — this could become a future shared guard applied across multiple
  EAs (including a possible future revision of EA-T1/EA-T2), not a one-off.

## T17 — Combined preflight + attach (EA-T1 + EA-T2 together)

Single combined checklist replacing the per-EA T6/T7 ceremony for this batch:

1. T4-equivalent tests pass for **both** EA-T1 and EA-T2: non-executing committed
   defaults; magic bands 933000-933099 (EA-T1) and 933100-933199 (EA-T2) — no collision
   with each other or with 933200-933299 (reserved) or any existing band; login allowlist
   = `1033669` for both; demo-server marker + live/real refusal for both; kill-switch
   guard for both; no `PositionClose`/`PositionModify`/`OrderDelete` anywhere in either
   file; GV-mutex-claim-before-OrderSend for both; all reason codes present for each
   (EA-T1's existing set + EA-T2's `STRUCT_FILTER_BLOCK`).
2. Hypothesis files hash-locked for both: EA-T1's (existing,
   `A3_ROUND_RETEST_GUARDED_HYPOTHESIS_2026_06_13.md`) and EA-T2's (formalize the Phase B
   pre-registration from `PORTFOLIO_AND_FIXED_EA_DEPLOYMENT_PLAN_2026_06_13.md` §2.2 into
   its own dated, hash-locked hypothesis file — same H-A3.1/H-A3.2/H-A3.3-style structure,
   adapted: H-A3.2-equivalent for EA-T2 is about `STRUCT_FILTER_BLOCK` efficacy, not
   `VETO_IMPULSE`).
3. `A3_DECOMMISSION_REPORT.md = PASS` (WR50 lane + old P2WEAKNESS portable runtime stopped
   — unchanged hard gate from the main work order).
4. Dry-run session: both EAs attached, ≥1 active session, zero orders, EA-T1's
   impulse-veto values AND EA-T2's structural-confirmation values both plausible in logs.
5. Once 1-4 are PASS → attach both EA-T1 and EA-T2 to A3 (1033669) via owner preset →
   ready for Monday open.

---

## Deployment order (this addendum)

T0 (A1 mutex fix, already owed) → T1 (EA-T1) and T13 (EA-T2) build in parallel, both
incorporating T15's per-magic G5 → T9-T12 (evening ledger, stand-down shadow, confluence
log, bar refresh) → T17 combined preflight → attach both, Monday. T14 and T16 (research
reports) run in parallel on whatever schedule is convenient — they do not block T17 or the
Monday attach; their outputs queue future work (EA-T3, possible shared trend filter).

## What NOT to do (carries over)

No touching A2. No lot >0.01 anywhere on A3. No `PositionClose`/`PositionModify`/
`OrderDelete` in EA-T1 or EA-T2. No EA-T3 code until T14 produces a reviewed, pre-registered
fix. No threshold changes to EA-T1's -1.5 veto or EA-T2's structural lookback after seeing
results. Broker-joined evidence outranks everything for final attribution.
