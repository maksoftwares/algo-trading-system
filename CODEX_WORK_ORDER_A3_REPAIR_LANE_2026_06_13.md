# CODEX WORK ORDER — Account 3 Repair Lane Build (2026-06-13)

Authorization: owner-approved, two-reviewer reconciled. Governing documents:
`PORTFOLIO_AND_FIXED_EA_DEPLOYMENT_PLAN_2026_06_13.md` (including the v1.1
RECONCILIATION ADDENDUM, which is binding) and
`PORTFOLIO_A3_DEPLOYMENT_PLAN_REVIEW_2026_06_13.md`. Where anything below is ambiguous,
the addendum wins.

## Global boundaries (repeat in every report this work produces)

- A3 demo account login: **1033669**. Use this number everywhere "A3 login" is
  referenced below (T1 G6 `InpAllowedAccountLoginsCsv`, T3 docs/registry, T5 terminal
  config, T7 preflight gates 1 and 3).
- Demo only. No live trading. Canonical Phase 2 status unchanged.
- A2 (`1033030`, breakout_retest) is not touched in any way.
- A1 (`1025742`) is not touched except the separately-owed mutex-race fix (T0 below).
- All committed defaults non-executing. Broker action arms only via local owner preset
  after every preflight gate passes and the owner signs.
- One task per commit, report trail for everything, locked hypotheses are never edited.

---

## T0 — Prerequisite (A1, already owed, do first)

Apply the GV-lock mutex race fix to `Phase2ExperimentalDemoExecutor.mq5` on A1:
`GlobalVariableSetOnCondition("FAMMUX_"+family+symbol+dir+barTime, magic, 0)` claimed
BEFORE OrderSend, released/expired with the M5 bar; startup self-test row proving the GV
namespace works. Maintenance window + before/after report per the existing pattern.
(Without this, A1's control data stays duplicate-contaminated and weakens the A3
comparison.)

## T1 — Source

`xau-usd/xauusd-phase1/mt5/Experts/Account3RoundRetestGuardedExecutor.mq5`

- Copy the `symbol_normalized_round_retest_v0` entry kernel from the experimental
  executor **byte-faithfully** (levels, retest, confirmation, ATR/floor stop, 1.5R TP).
  Do NOT share source/includes with A1's executor — the control must stay byte-stable.
- Add the guard chain, evaluated in this order, each with its distinct reason code:

| Guard | Rule | Locked parameters | Reason code |
|---|---|---|---|
| G1 impulse veto | block if `impulse_alignment < InpImpulseVetoThreshold` where `ret12_atr=(close[1]−close[13])/ATR14(M5)`, `impulse_alignment=dir_sign×ret12_atr`. Log raw `ret12_atr` + `impulse_alignment` on EVERY signal row, vetoed or not | `InpImpulseVetoThreshold = -1.5` | `VETO_IMPULSE` |
| G2 family mutex | atomic `GlobalVariableSetOnCondition("FAMMUX_RD_XAUUSD_"+dir+"_"+barTime, InpMagicNumber, 0)` BEFORE OrderSend; expires with bar | — | `MUTEX_CLAIMED_ELSEWHERE` |
| G3 streak breaker | 3 consecutive SL closes (own magic, from history, reload-safe) within rolling 2 h → no new entries until next 4-h boundary | 3 / 2 h / next 4-h block | `STREAK_PAUSE` |
| G4 daily entry stop | own-magic realized day PnL ≤ −150 AED → no entries until next Dubai day (`TimeGMT()+240min` day boundary). Entry-blocking ONLY — the EA contains no position-closing calls | −150 AED | `DAILY_STOP_PAUSE` |
| G5 caps | max 1 open position; `InpMaxEstimatedCostR=0.15` (execution cap), 0.20 logged as `COST_WARN`, 0.30 absolute reject; `InpMaxMeasuredSpreadPoints=75`; `InpMinSecondsBetweenOrders=60`; `InpFixedLot=0.01` fixed | per addendum #2 | `COST_R_CAP_BLOCK`, `SPREAD_CAP_BLOCK` |
| G6 scope locks | XAUUSD only; demo-server marker; refuse "live"/"real"; `InpAllowedAccountLoginsCsv` (A3 login `1033669` only); kill-switch file `A3_KILL.txt`; `InpDryRunOnly=true` + `InpBrokerActionAllowed=false` committed defaults | — | `SCOPE_LOCK_BLOCK` |

- Magic: `InpMagicNumber = 933000` (band 933000–933099). Comment `RDGUARD_V1`.
- Would-signal logging is first-class: vetoed/blocked signals write full rows with all
  guard values so A1-matching can resolve their outcomes.
- Session policy: all sessions (no session filter in Phase A — addendum/“what not to do” #6).

## T2 — Presets

- `mt5/Presets/Account3RoundRetestGuardedExecutor.safe_xauusd.set` — committed:
  `InpDryRunOnly=true`, `InpBrokerActionAllowed=false`, lot 0.01, XAUUSD, magic 933000.
- Owner-authorized execution preset: **local only, never committed**; add a pytest that
  fails if any committed preset contains `InpBrokerActionAllowed=true` for this EA.

## T3 — Docs & registry

- `docs/A3_ROUND_RETEST_GUARDED_HYPOTHESIS_2026_06_13.md` — H-A3.1 (FULL-STACK outcome:
  PF ≥ 1.2, ≥2 weeks, ≥30 closed trades, beats A1 unfixed round family dup-hidden
  same-period by ≥200 AED or ≥0.3 PF), H-A3.2 (veto efficacy: ≥60% of G1-vetoed signals
  are losers via A1 matching), H-A3.3 (brake efficacy). Decision matrix incl. the
  reviewer amendment (H-A3.1 pass + H-A3.2 fail ⇒ stack promising, veto NOT validated,
  one 2-week extension) and the permanent-retirement clause (initial+extension ≈4 weeks,
  ≥60 trades, fails control AND PF<1.0 ⇒ retire forever; only pre-registered Phase B
  remains; Phase B failure closes the family).
- `docs/A3_HYPOTHESIS_HASH_MANIFEST.json` — sha256, commit, `locked_before_first_trade`.
  **No manifest ⇒ no arming.**
- `docs/A3_OWNER_AUTHORIZATION_PACKET_TEMPLATE.md` — must include verbatim: the A1
  control-loss acknowledgment (reviewer Change 5), the A1 pause floor (equity <1,500 AED
  or −1,000 from window start ⇒ control obligation pauses), and the week-1
  entry-blocking-only acknowledgment if Guardian Stage B is not yet armed.
- `docs/A3_DEMO_BOUNDARY.md`, `docs/A3_DEPLOYMENT_RUNBOOK.md`,
  `docs/A3_MANUAL_EMERGENCY_FLATTEN_PROCEDURE.md`.
- Update `MAGIC_NUMBERS.md` (933000–933099) and `EXPERT_LIFECYCLE.md` (A3 state).

## T4 — Tests (pytest, source-level, all must pass pre-attach)

1. Committed defaults non-executing. 2. Magic in 933000–933099. 3. No committed
execution-enabled preset. 4. Login-allowlist guard present. 5. Demo-server guard +
live/real refusal. 6. Kill-switch guard. 7. Impulse formula string present AND raw value
logged on every signal row. 8. All reason codes present: `VETO_IMPULSE`,
`MUTEX_CLAIMED_ELSEWHERE`, `STREAK_PAUSE`, `DAILY_STOP_PAUSE`, `SPREAD_CAP_BLOCK`,
`COST_R_CAP_BLOCK`, `COST_WARN`, `SCOPE_LOCK_BLOCK`. 9. GV mutex claim occurs before
OrderSend (order-of-source assertion). 10. **No `PositionClose`/`PositionModify`/
`OrderDelete` anywhere.** 11. No non-XAUUSD allowance. 12. Streak/daily-stop constants
match locked parameters.

## T5 — Terminal, observers, decommission

- New portable root `C:\MT5PortableRepairLane` via the existing attach-script pattern
  (profile backup, scratch compile, startup verification, JSON+MD report). A3 demo login
  (`1033669`) documented; investor-password note for any observer terminal.
- Second `Phase2PositionPathObserver` instance for the A3 login (own portable root or the
  repair-lane terminal, telemetry-only) + heartbeat lane `a3_repair_lane` + include A3 in
  the weekly packet generator.
- **Decommission (hard gate):** stop/archive the WR50 portable lane and the old
  P2WEAKNESS portable runtime; verify no 930101 positions/orders and no stale committed
  execution presets → `A3_DECOMMISSION_REPORT.md = PASS` required before arming.

## T6 — Reports to generate (names fixed)

`A3_PREFLIGHT_REPORT.md`, `A3_DRY_RUN_SESSION_REPORT.md`,
`A3_OWNER_AUTHORIZATION_STATUS.md`, `A3_RUNTIME_RECONCILIATION.md`,
`A3_KILL_SWITCH_DRILL_REPORT.md`, `A3_DECOMMISSION_REPORT.md`,
`A3_COST_CAP_BLOCK_REPORT.md` (on demand),
`A3_GUARD_ATTRIBUTION_DAILY_YYYY_MM_DD.md` (per-guard PnL impact G1/G3/G4 separately,
combined stack, overlap counts — addendum #4),
`A3_WEEKLY_REVIEW_PACKET.md`, `A3_VS_A1_TREATMENT_CONTROL_REPORT.md` (dup-hidden,
per-signal matching, same-period).

## T7 — Preflight gates (ALL must be PASS before owner arming; reviewer §7 verbatim)

1. A3 demo login (`1033669`) documented. 2. Server marker Demo/Practice. 3. Login
allowlist exactly matches `1033669`. 4. Safe preset committed + non-executing. 5. Owner preset local-only. 6. Magic 933000 no
collision. 7. Hypothesis SHA-locked before first trade. 8. All T4 tests pass. 9. Kill-
switch drill PASS. 10. Dry-run ≥1 active session, zero orders, veto values plausible in
logs. 11. Guardian Stage A startup PASS on A3. 12. Decommission report PASS. 13. A1+A2
state snapshot documented. 14. Owner signs the demo-only packet.

## T8 — Deployment order

compile + T4 tests → external code review (same bar as Reviews 9/10) → hypothesis lock +
manifest → preflight gates → dry-run session → owner arms via local preset → locked
2-week window begins (no mid-week changes; daily guard-attribution report; weekly packet).

## What NOT to do (reviewer §9, binding)

No touching A2; no impulse veto on breakout_retest; no arming without the packet; no
committed execution presets; no Phase B build during Phase A; no session filter in Phase
A; no threshold changes after seeing A3 results; no lot >0.01; A3 is not canonical Phase
2 and not live-readiness evidence; no same-family diversification claims; broker-joined
evidence outranks everything for final attribution.
