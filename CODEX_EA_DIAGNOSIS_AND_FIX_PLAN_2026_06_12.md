# EA-by-EA Diagnosis and Fix Plan — for Codex (2026-06-12)

Compiled from Reviews 7–13, the verified MQL5 source (Review 8), the actual broker history
2026-06-01 → 2026-06-12 (account 1025742), and the full-path evening dataset of 2026-06-12
(52,247 ten-second snapshots). Every number below was independently recomputed from the
broker CSV or the path log, not taken from dashboards.

Boundaries for all fixes: demo only; shadow-first where marked; runtime changes only
inside owner-authorized maintenance windows; `breakout_retest` entry/stop/TP logic stays
frozen during the locked week; nothing is deleted — retired EAs become observers.

---

## PART 1 — WHY THE WINNER WINS

### EA 1: `breakout_retest` — WORKS (keep, protect, grow carefully)

Evidence: +568 AED dedup, PF 1.70, WR 44.7%, positive 7/7 days (June 1–9 window); evening
XAUUSD +530/16 trades, PF 5.91, WR 69% (through June 11). Survived three review windows
and one regime flip. Lost −179 in the June 12 chop evening (see R5).

**Reasons it works:**

| # | Reason | Mechanism |
|---|---|---|
| W1 | **Entries are anchored to real structure.** Its levels are confirmed swing highs/lows (`add_latest_confirmed_swings`, left=4/right=4). A swing break is a finite, meaningful event — the EA trades only when something actually happened. | Structure filter does the regime work implicitly: swing breaks occur disproportionately at the start of directional moves, so the candle-color direction trigger is usually *with* the move. |
| W2 | **Wide ATR-floored stops** (realized median ~630 pts XAUUSD) put cost_R at ~0.12–0.15 and survive ordinary noise — the same mechanic whose absence killed the family in the old tight-stop backtest (cost_R 1.13). | Stop geometry is the difference between the suspended backtest and the profitable demo. |
| W3 | **Scarcity.** ~9 XAUUSD signals/day vs the round family's ~60. Selectivity is itself a filter: fewer, better-conditioned trades. | Low signal frequency = less churn, less spread paid, fewer chop entries. |
| W4 | **Its edge window is real and externally confirmed**: NY-morning/Dubai-evening concentration matches the funded-window finding from independent Phase 0 research. | Two unrelated methods, same answer — the strongest evidence the project owns. |

**Remaining weaknesses + fixes:**

| # | Weakness | Evidence | Fix | Mode |
|---|---|---|---|---|
| W5 | Chop regimes hurt it: candle-color confirmation flips both ways in two-sided markets. June 12 evening: 7 trades, ~all SL, −179. | Path log: both directions lost evening of 06-12 | Do NOT patch the entry. Shadow-test a chop detector (e.g., M15 ATR vs range-compression ratio) as a *pause* gate, alongside the existing M15/H1 trend veto already collecting in shadow. Promote only on the standard ladder. | SHADOW |
| W6 | Its clone (`swing_`) doubles every trade — leverage without information. | 0.989 PnL correlation, same-second co-fires | Mutex race fix (Part 3, F1) | RUNTIME (approved A3, defect repair) |
| W7 | Exposure is flat across its window; the sizing ladder isn't built. | Review 13 | Implement `CELL_SIZING_SHADOW_v1` (Review 13 §7) to earn 1.5×/2× evening size with evidence. | SHADOW |

---

## PART 2 — WHY THE LOSERS LOSE

### EA 2: `swing_breakout_retest_v0` — works only as a photocopy

Evidence: 75–136 of its trades are same-second duplicates of breakout_retest; unique
remainder is small-n. It is not an EA; it is 2× size on EA 1 wearing a different magic.

| Reason | Fix | Mode |
|---|---|---|
| L2.1 Same kernel, same bars, same levels → same orders. Adds variance, zero information, corrupts attribution. | After mutex fix it becomes harmless but pointless as an executor. Set logger/observer-only; if its parameter differences ever matter, test them as a *cell* of the one kernel, not a second EA. | Owner packet (it is currently broker-action) |

### EA 3 + 4: `symbol_normalized_round_retest_v0` and `round_number_retest_v0` — structural losers

Evidence: the family is the project's largest loss source (−630 dedup through 06-11 for
symbol_normalized; round_number mirror; loses in ALL four time buckets; June 11 −1,070
combined raw; June 12 evening −574 more). 331=331 identical signals/5 days — confirmed
clones of each other.

**Reasons, each with its fix:**

| # | Reason it loses | Code evidence | Fix | Mode |
|---|---|---|---|---|
| L3.1 | **Direction from one M5 candle color.** `is_long = close[1]>open[1]` — a coin-flip-quality signal in anything but a strong trend. | Executor L458–466; same in Python mirror | Require direction to be confirmed by structure (L3.2) AND not opposed by M15+H1 slope (trend veto, already in shadow with logged raw slopes). | SHADOW → demo on ladder |
| L3.2 | **Round levels are everywhere.** `ceil(price/increment)` guarantees a level just above price in any uptrend — the short-candidate generator never runs dry, so it shorts rallies continuously (June 11: −807 SELL on an up day). And dip-buys downtrends symmetrically. | `round_number_retest_v0.py` L50–58; executor `DemoCandidateLevels` | **Broken-structure requirement**: a round level is only tradeable if it coincides with a confirmed M15 swing break in the trade direction within the last N bars (reuse the breakout kernel's swing logic — this is W1, the thing that makes EA 1 work, transplanted). | SHADOW first |
| L3.3 | **"Break" validation is trivial**: any single bar 15–110 min back closing 0.3×ATR past the level counts — in a trending market, bars from the *approach* satisfy it. | `DemoBreakValid` L219–224 | Same fix as L3.2 — break must be a swing-structure event, not any bar. | SHADOW |
| L3.4 | **Churn frequency**: ~60 signals/day on XAUUSD alone → maximal spread paid, maximal chop exposure, 17.8-min median holds. | Shadow observer counts | Per-instance cooldown (e.g., 30 min after any SL) + max trades/day cap as preset inputs. | Preset, owner window |
| L3.5 | **Two clones double everything.** | 331=331; same-second entries | One family, one executor: round_number retires to observer permanently (it adds zero information); mutex covers residual. | Owner packet |
| L3.6 | **No session discipline**: trades all buckets; nights/mornings are its worst. | Bucket tables, Reviews 7/11 | Session whitelist input per preset (already exists as server-hour gate, currently disabled) — enable per evidence after the locked week. | Preset, owner window |

**Honest option to put in front of the owner:** these two EAs may not be repairable as
independent EAs — every fix above converges them toward being breakout_retest with extra
levels. The cleaner end-state: retire both to observers and add "round-level confluence"
as an optional *feature flag* inside the one validated kernel, tested as a cell.

### EA 5: `session_extreme_retest_v0` — loser with an extra time-base bug

Evidence: PF 0.64, WR 27.3%, −209 dedup (through 06-11); 100% shadow-blocked by current
policy; June 12 evening another −18.

| # | Reason | Evidence | Fix | Mode |
|---|---|---|---|---|
| L5.1 | Same candle-color + trivial-break defects as L3.1/L3.3. | Shared observer code | Same fixes. | SHADOW |
| L5.2 | **Session-extreme levels are computed in SERVER time** (Asia 00–06h, London 07–11h server) while everything else uses Dubai labels — the "session extremes" are not the sessions anyone thinks they are. | `AddSessionExtremeLevels` L377–395 | Recompute windows from `TimeGMT()+offset` with explicit session definitions; document which sessions are intended. This is a correctness bug regardless of the EA's fate. | CODE FIX (observer + executor source) |
| L5.3 | Fading session extremes is counter-trend by construction: in trending markets the session extreme is where continuation happens. | Direction stats | Trend-alignment veto (same shadow lane). | SHADOW |
| L5.4 | Tightest stops in the family (median 4.4 vs 6.3) → noise-stopped most often. | SL-distance table, Review 7 | If the EA survives at all: same ATR-floor policy as breakout. | SHADOW |

### EA 6 + 7: `*_repair_v1` lanes — failed by design, not by luck

Evidence: June 11: 13/13 SELL, 2 wins, −402 (SHORT-only lanes shorting an up day);
June 12 evening: −199 more. Their "good days" (June 10 +396) came only when the regime
happened to match their hard-coded direction.

| # | Reason | Fix | Mode |
|---|---|---|---|
| L6.1 | **Rules compiled from 3–5-trade clusters** (PHASE2_REPAIR_CANDIDATE_RULES.csv) — textbook overfit: calendar+direction permissions with no market-state check. | Delete the SHORT-only window logic from the repair executor. Repairs must be *state-conditional* (trend/structure), never *calendar+direction-conditional*. | Source change, owner window |
| L6.2 | **Deployed against their own `NONE_SHADOW_ONLY` designation** with `InpDryRunOnly=false` default and `_DRY_RUN` labels on live sends. | Governance: repair executors → broker-action OFF (was declined as A2 — re-present with June 11+12 combined evidence: −601 AED across two sessions); add a CI check that any source whose rules CSV says SHADOW_ONLY cannot compile with broker-action default true. | Owner packet + CI test |

### EA 8: `p2weakness_br_v1` — promising, unproven, governance-encumbered

Evidence: raw +200→+562 across windows but n≤9 unique; runs old `930101` source in the
portable runtime (clean `931000` deploy never completed).

| Reason it half-works | Fix | Mode |
|---|---|---|
| It is breakout-family logic with weakness-review constraints — it inherits W1/W2. But n is too small to distinguish from luck, and the runtime≠repo state disqualifies its evidence. | Complete the clean 931000 deployment per the existing Phase 2X procedure, then let it earn n≥30 before any verdict. | Owner window |

### EA 9: WR50 lanes (`BEV0`, `BQV0`, `E1R0`, `WST12`, `WST15`)

Evidence: BEV0 −74/2 with both entries at NIGHT (05:43) from an "Evening" EA; Quality/Exit1R n≤3; WST pair attached 06-09, n≈0.

| # | Reason | Fix | Mode |
|---|---|---|---|
| L9.1 | **Session window not enforced in code** — the EA's name promises what no guard checks. | Add the session gate to WR50 source (server-hour gate exists in the main executor; port it) or retire the lane. | Code fix |
| L9.2 | Lane premise optimizes win rate; project KPI is expectancy. | Keep WST12/WST15 only (they test stop geometry, which is a real question); retire BEV0/BQV0/E1R0 to observers. | Owner packet |

### EA 10: `W1D1MomentumM5Continuation` — correctly never attached

Cross-broker backtest fail (PF 1.04 capital / 0.86 dukascopy); the "active profile" was
chosen for activity over edge. Fix: none. Keep unattached; the lesson (don't trade a
broker-dependent edge) is already encoded in gate G7.

---

## PART 3 — THE CROSS-CUTTING DEFECTS (bigger than any EA)

These four account-level failures did more damage than any single EA's logic:

| # | Defect | Evidence | Fix | Priority |
|---|---|---|---|---|
| F1 | **Mutex race**: clones enter in the same second; check-then-send is not atomic. | 20+ same-second clusters AFTER the A3 deployment (June 12 path data) | `GlobalVariableSetOnCondition("FAMMUX_"+family+symbol+dir+barTime, …)` claimed BEFORE OrderSend, expiring with the bar; startup self-test row. | **P0 — this weekend** |
| F2 | **No armed daily stop**: −1,905 AED day (−42% of account) ran to completion. | Equity path 4,509→2,594; R1 counterfactual −150 | Arm Guardian Stage B (R1 −150 flatten+halt; R2 giveback; weekly −400 breaker) after verifying Stage A's log vs today's path. Kill-switch drill per existing procedure. | **P0 — owner packet** |
| F3 | **No position caps**: 24 concurrent positions, 16 same-direction; cluster stops sweep together. | Path log maxima | Re-present A4 (`InpMaxOpenPositionsPerInstance=1` + spread/cost caps) with tonight's numbers attached. | P1 — owner decision |
| F4 | **Account near margin death**: equity ~2.6k, contaminating all future data via potential STOP_OUT. | Day-low 2,568 | Reset/recapitalize the flow demo account before Monday; record as pre-week operational event. | P0 — owner action |

---

## PART 4 — CODEX WORK ORDER (dependency-sorted)

| # | Task | Type | Gate |
|---|---|---|---|
| 1 | F1 GV-lock mutex fix + self-test + recompile + redeploy | Defect repair of approved A3 | Maintenance window, report trail |
| 2 | F2 Stage-A-vs-path verification script → Stage B arming packet | Analysis + packet | Owner signature to arm |
| 3 | F4 account reset note template + pre-week event record | Ops | Owner action |
| 4 | L5.2 session-time-base fix (server→GMT+offset) in session-extreme level code | Correctness bug | Source fix, both observer and executor copies |
| 5 | L6.1/L6.2 strip SHORT-only windows from repair executor; CI test: SHADOW_ONLY rules ⇒ no broker-action-true defaults | Source + test | Owner window for runtime part |
| 6 | L9.1 WR50 session-gate enforcement (or retirement packet) | Source | Owner choice |
| 7 | F3 re-present A4 packet with June 12 evidence; EA 2/3/4 retirement-to-observer options in the same packet | Packet only | Owner decision |
| 8 | W5 chop-detector shadow column + L3.2 broken-structure shadow variant of the round kernel (one rule, pre-registered, in the existing trend-guarded observer lane) | Shadow research | Standard ladder: 1 fresh week minimum |
| 9 | W7 `CELL_SIZING_SHADOW_v1` per Review 13 §7 | Shadow research | 4-week bar before any size step |
| 10 | EA 8 clean 931000 deployment completion | Ops | Existing Phase 2X procedure |

Rules for Codex: one task per commit/report; nothing touches `breakout_retest` logic;
shadow tasks produce scoreboards, not runtime changes; every runtime task cites its owner
authorization; the locked week's hypotheses file stays untouched.

---

## One-paragraph summary for the owner

The winner wins because its entries require a real structural event, its stops are wide
enough to survive noise, and it trades rarely, in the right window. The losers lose
because their entries require almost nothing (one candle color, a round number that always
exists nearby), so they churn counter-trend trades in every session — and the account
multiplied those losses through clone duplication, uncapped stacking, and the absence of
any daily stop. The fixes are therefore in three layers: make the brakes real (mutex race,
daily stop, caps, account reset), transplant what makes the winner work into anything that
survives (structure requirement, trend alignment, wide stops, session discipline), and
retire what is only a photocopy or a calendar bet. Everything strategic goes through
shadow first; everything mechanical goes through one signed maintenance window.
