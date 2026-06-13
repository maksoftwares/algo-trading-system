# Portfolio & Fixed-EA Deployment Plan — Account 3 Proposal (2026-06-13)

Prepared for external review before Codex implementation. Nothing in this document is
deployed yet. Demo only; no live trading; canonical Phase 2 status unchanged.

Author basis: Reviews 7–13, the entry-failure forensics (728→1,356-trade impulse study),
the June 1–12 counterfactual replay (full-stack and gold-only), and the verified MQL5
source. All performance figures cited are from actual broker history, recomputed
independently.

---

## 1. Purpose and Architecture

We move from "observe the fix in shadow" to "trade the fix forward, against a control."
Three demo accounts, three distinct jobs:

| Account | Login | Role | Contents |
|---|---|---|---|
| A1 "Flow" | 1025742 | **Control / baseline.** Unfixed EAs keep trading as the owner chose (A1/A2/A4/A5 declined). Its unfixed round-family arm is the scientific control for Account 3. | 5-candidate executor set + repair lanes + guardian shadow + full observer net |
| A2 "Edge" | 1033030 | **The proven edge, isolated.** breakout_retest, XAUUSD only, evening-gated, guards armed. Its job: produce the clean track record that real-money authorization will eventually rest on. | 1 EA, frozen rules |
| A3 "Repair" (NEW) | 1033669 | **The treatment arm.** The FIXED weak-lane EA(s), full brake stack, gold only. Its job: prove (or disprove) that the diagnosed failures are repairable, with real fills. | This document |

Decision logic of the whole portfolio: A2 earns the future; A1 documents the past; A3
tests whether anything from A1 deserves to join A2's tier.

---

## 2. Account 3 — EA-by-EA Design

### 2.1 EA-T1: `round_retest_guarded_v1` (the only Phase-A resident)

Base: `symbol_normalized_round_retest_v0` entry kernel, **unchanged** (levels, retest
window, confirmation candle, ATR/floor stop, 1.5R target). We fix the *context*, not the
signal — one variable class at a time, so the result is attributable.

Why this EA: largest historical loss source, but the forensics showed it is specifically
broken as an impulse-fader (23.7% WR fighting fast hours) while genuinely competent
riding them (50.7% WR) — and the gold-only replay showed the veto rehabilitates it to
+77 AED over 183 kept trades. It is the one weak EA with a measured, mechanism-understood
path back. (`round_number_retest_v0` is its byte-clone and is retired, not fixed.
`session_extreme_retest_v0` stayed negative even filtered — no seat. Repair lanes — dead.)

**The guard chain, in evaluation order (all new logic; kernel untouched):**

| # | Guard | Rule | Parameters (locked for the test) |
|---|---|---|---|
| G1 | **Impulse veto** | Block entry if `impulse_alignment < −1.5`, where `ret12_atr = (close[1] − close[13]) / ATR14(M5)` and `impulse_alignment = direction_sign × ret12_atr`. Raw value logged on EVERY signal row regardless of decision. | Threshold −1.5 (pre-registered; −1.0/−2.0 scored offline from logs only — no runtime tuning) |
| G2 | **Family mutex (atomic)** | `GlobalVariableSetOnCondition("FAMMUX_RD_XAUUSD_"+dir+"_"+barTime, magic, 0)` claimed BEFORE OrderSend; expires with the M5 bar. Single-EA account today, but the lock ships so the lane is clone-safe forever and the race defect found on A1 can never recur here. | — |
| G3 | **Streak breaker** | After 3 consecutive SL closes (own magic) within any rolling 2 h → no new entries until the next 4-hour boundary. Counts from broker history, magic-filtered, so it survives EA reload. | 3 losses / 2 h / pause to next 4 h block |
| G4 | **Daily entry stop** | Own-magic realized day PnL ≤ −150 AED → no new entries until next Dubai day. (Entry-blocking only — no position closing in the EA; flattening authority stays with the Guardian.) | −150 AED |
| G5 | **Exposure & quality caps** | Max 1 open position; `InpMaxEstimatedCostR = 0.30`; `InpMaxMeasuredSpreadPoints = 75`; min 60 s between orders; fixed 0.01 lot. | re-armed values from the 06-09 plan |
| G6 | **Scope locks** | XAUUSD only; demo-server marker + account-login allowlist (A3 login only); kill-switch file; dry-run-locked compile default with explicit owner preset to arm. | — |

Every guard outcome writes a distinct reason code (`VETO_IMPULSE`, `MUTEX_CLAIMED_ELSEWHERE`,
`STREAK_PAUSE`, `DAILY_STOP_PAUSE`, …) so the weekly packet can attribute every untaken
trade. Untaken-trade logging is first-class: the EA writes a would-signal row with the
impulse value even when vetoed — Account 1's identical unfixed EA provides the realized
outcome of those vetoed signals. That pairing is the experiment.

Identity: new magic band **933000–933099** (registry entry required; no collision —
930xxx WR50, 931xxx P2W, 932xxx W1D1 are taken). Comment `RDGUARD_V1`. Session policy
Phase A: **all sessions** (the veto is the filter under test; stacking a session filter on
top would confound attribution).

### 2.2 EA-T2 (Phase B, NOT deployed now): `round_retest_structured_v1`

The deeper repair from the forensics (S2): a round level is only tradeable after a
confirmed M15 swing break in the trade direction — transplanting the exact ingredient
that makes breakout_retest robust. Held back deliberately: Phase A must run alone for ≥2
weeks first, or we cannot tell which repair worked. Pre-registered here so it cannot be
accused of being invented after seeing Phase A's results.

### 2.3 What is explicitly NOT on Account 3

`round_number_retest_v0` (clone — retired), `session_extreme_retest_v0` (+ repair —
negative even filtered), both `*_repair_v1` lanes (overfit SHORT-only construction, Review
8), WR50 lanes (no edge, KPI mismatch), W1D1 (cross-broker fail), and `breakout_retest`
(does not need the cure — its counter-impulse trades WIN 50%; the veto would damage it;
it lives on A2).

---

## 3. Account-Level Risk Design (A3)

| Layer | Mechanism | Value |
|---|---|---|
| Per trade | fixed lot / ATR-floor stop (kernel) | 0.01, ~20–25 AED risk |
| Per lane | G3 streak breaker | 3 SL / 2 h → pause |
| Per day | G4 entry stop + Guardian R1 (armed, flatten+halt) | −150 AED both |
| Per week | weekly breaker: account ≤ −400 AED → EA to observer mode pending review | −400 AED |
| Account | Guardian R2 giveback (arm +150, 40%), kill-switch file, login allowlist | per spec v0 |
| Monitoring | own path-observer instance (10 s snapshots), heartbeat lane, weekly packet section | from day one |

Guardian Stage B on A3 requires its own kill-switch drill before arming (existing Phase 2X
procedure). Until the drill passes, G4 entry-blocking is the daily stop.

## 4. Portfolio-Level Rules (all three accounts)

1. **Complexity budget — additions are paid for by retirements.** A3 comes online; the WR50 portable lane and the stale old-P2WEAKNESS portable runtime are decommissioned the same weekend. Net terminal count stays flat.
2. **One weekly review packet covers all three accounts** (extend the existing weekly export): per-account PnL/PF/WR, A3-vs-A1-round-family treatment table, guard-attribution table (what each guard blocked and what those signals did on A1), guardian events, heartbeats.
3. **Freeze discipline:** nothing on any account changes mid-week. Changes land in weekend maintenance windows with owner packets, as now.
4. **Sizing ladder remains future work** (Review 13 §7): no account trades above 0.01 until its own 4-week bar clears. A2 is first in line, not A3.
5. **Evidence hierarchy unchanged:** broker fills > path-observer data > shadow scoring > replay (quarantined). A3 exists precisely to generate top-tier evidence for the repair question.

## 5. Evaluation — pre-registered before deployment

Hypothesis (to be commit-locked in a dated file before A3's first trade):

> H-A3.1: `round_retest_guarded_v1` on XAUUSD achieves PF ≥ 1.2 and positive net PnL over
> ≥ 2 calendar weeks and ≥ 30 closed trades, AND outperforms Account 1's unfixed
> round-family (duplicate-hidden, same period, same symbol) by ≥ 200 AED or ≥ 0.3 PF.
> H-A3.2: ≥ 60% of G1-vetoed signals, matched to A1's realized outcomes, are losers
> (the veto blocks bad trades, not random trades).
> H-A3.3: guard activations (G3/G4) are followed by net-negative would-have-been PnL more
> often than not (the brakes brake at the right times).

Decision matrix after the window:

| Outcome | Action |
|---|---|
| H-A3.1 + H-A3.2 pass | Veto promoted to "validated repair"; Phase B (structure variant) may start; A1's unfixed copy retires to observer |
| Mixed (profitable but not better than control, or vice versa) | One extension window of 2 weeks, same config, no tuning |
| Fail | EA-T1 retires with clean evidence; round family closed as unrepairable-by-context; only Phase B's structural rebuild remains eligible |

Known bias to disclose to the second reviewer: the −1.5 threshold was fitted on June 1–12
data. H-A3.1's bar (PF 1.2, beat control) is deliberately set below the replay's
in-sample result (PF ~1.4 equivalent) to absorb expected shrinkage, but a regime unlike
June could still fail an honest rule. That is the point of forward testing.

## 6. Codex Implementation Spec (after both reviewers agree)

1. **Source:** new file `Phase3RoundRetestGuardedExecutor.mq5` (copy kernel from the
   experimental executor; add G1–G6; do NOT share source with A1's executor — the control
   must stay byte-stable). Inputs for every parameter above; all defaults non-executing
   (`InpDryRunOnly=true`, `InpBrokerActionAllowed=false`); arming only via owner preset.
2. **Tests (pytest, source-text level like the observer suites):** forbidden-pattern scan
   (no PositionClose/Modify — entry-blocking only), guard reason-code presence, veto
   formula string, magic band 933000–933099, login-allowlist guard, GV mutex claim before
   OrderSend, defaults non-executing.
3. **Registry/docs:** MAGIC_NUMBERS.md entry, lifecycle doc, hypothesis file (commit-locked),
   A3 owner authorization packet (account login, preset hash, arming signature).
4. **Terminal:** new portable root `C:\MT5PortableRepairLane`, prepared by the existing
   attach-script pattern (profile backup, scratch compile, startup verification, JSON+MD
   report). Plus a second path-observer instance pointed at A3's login, and heartbeat lane.
5. **Deployment order:** compile + tests → my code review (same bar as Reviews 9/10) →
   owner signs packet → attach in dry-run for 1 session (signal rows, veto values
   plausible, zero orders) → owner arms via preset → trading begins.
6. **Simultaneously decommission:** WR50 portable lane, old-P2WEAKNESS portable runtime
   (archive logs, document in the same maintenance report).

## 7. Timeline

| When | What |
|---|---|
| Weekend | Reviewer #2 comments → reconcile → Codex builds → tests + my review |
| Before Monday open | A1 mutex-race fix (already owed), A3 hypothesis lock committed |
| Mon–Tue | A3 dry-run session, owner arms if clean |
| Weeks 1–2 | Locked A3 window runs in parallel with the (already locked) A1/A2 week |
| End of week 2 | Decision matrix applied; Phase B go/no-go |

## 8. Questions the Second Reviewer Should Pressure-Test

1. Is running G1 (veto) and G3/G4 (brakes) together in Phase A acceptable, or should brakes-only run first? (My position: brakes are risk infrastructure, not treatment — they don't confound the veto's attribution because vetoed-signal outcomes are measured against A1, not against A3's own brakes.)
2. Is the −1.5 threshold lock right, vs locking −1.0 (more protective in-sample but lower kept-share)?
3. Is "all sessions" correct for Phase A (my position: yes, to avoid confounding), or should A3 inherit the evening focus immediately?
4. Is the control comparison fair given A1's round family still runs 2 clones at different effective exposure? (Mitigation: compare duplicate-hidden, per-signal, not per-account.)
5. Should Phase B's structure variant be built now-but-idle (faster later, risk of temptation) or only after Phase A's verdict (cleaner, slower)?

---

# RECONCILIATION ADDENDUM — v1.1 (2026-06-13)

Second reviewer returned **APPROVE WITH CHANGES**
(`PORTFOLIO_A3_DEPLOYMENT_PLAN_REVIEW_2026_06_13.md`). All seven amendments are
**ACCEPTED** and are binding on the Codex implementation. Where this addendum conflicts
with the body above, the addendum wins.

## Binding amendments

| # | Amendment | Resolution |
|---|---|---|
| 1 | Rename executor — no "Phase3" while canonical Phase 2 is blocked | **`Account3RoundRetestGuardedExecutor.mq5`** everywhere; "A3" prefix for all reports |
| 2 | Cost cap ladder instead of flat 0.30 | `InpMaxEstimatedCostR = 0.15` execution cap; 0.20 reporting-warn; 0.30 hard reject. If 0.15 over-blocks, generate `A3_COST_CAP_BLOCK_REPORT.md` and decide openly — never silently raise |
| 3 | Kill-switch / guardian readiness is a PRE-ARM gate | `A3_KILL_SWITCH_DRILL_REPORT.md = PASS`, `A3_GUARDIAN_STAGE_A_STARTUP_REPORT.md = PASS`, and `A3_MANUAL_EMERGENCY_FLATTEN_PROCEDURE.md` required before broker action. If Stage B flatten is not yet armed, the owner packet must contain the explicit acknowledgment that week-1 protection is entry-blocking only |
| 4 | Attribution split | H-A3.1 is redefined as the **full-stack** outcome; H-A3.2 = veto-only efficacy (G1-vetoed signals vs A1 realized outcomes); H-A3.3 = brake-only efficacy. Weekly packet must show per-guard PnL impact (G1/G3/G4 separately), combined result, and multi-guard overlap counts |
| 5 | A1 control losses owner-accepted, with a pause floor | Owner packet carries the reviewer's acknowledgment text verbatim. Concrete pause trigger added: if A1 equity falls below **1,500 AED** (or −1,000 AED from comparison-window start, whichever first), the control obligation pauses and the experiment is reviewed rather than letting A1 die for science |
| 6 | Decommission is a hard preflight gate | `A3_DECOMMISSION_REPORT.md = PASS` (WR50 lane + old P2WEAKNESS runtime stopped/archived, no 930101 residue, no stale committed execution presets) required before arming |
| 7 | Machine-verifiable hypothesis lock | `A3_ROUND_RETEST_GUARDED_HYPOTHESIS_2026_06_13.md` + `A3_HYPOTHESIS_HASH_MANIFEST.json` (SHA256, commit hash, locked_before_first_trade). No hash manifest ⇒ no arming |
| + | Decision-matrix amendment | If H-A3.1 passes but H-A3.2 fails: the veto is NOT called validated; the stack is called promising; one 2-week extension, same config |

## Answers to the reviewer's open questions (first reviewer's positions)

1. Treatment-vs-control design: valid — both reviewers concur.
2. **Brakes stay active in Phase A.** Removing safety to purify attribution is backwards on a system that just printed a −42% day; Change 4's attribution split resolves the confound in reporting, where it belongs.
3. −1.5 threshold: acceptable as fitted-but-disclosed-and-forward-tested; −1.0/−2.0 scored offline from logged raw values only.
4. H-A3.1 is appropriate once redefined as full-stack (Change 4).
5. Cost cap 0.15 (per Change 2).
6. G4 entry-blocking + manual flatten procedure + passed kill drill is sufficient for week 1 with the explicit owner acknowledgment; Stage B should arm as soon as its drill passes, target inside week 1.
7. A1 control: worth it, with the §5 pause floor.
8. `Account3RoundRetestGuardedExecutor` — agreed.
9. A3 does not wait for greenfield-v2; greenfield proceeds in parallel and inherits A3's answer either way.
10. **Permanent retirement condition:** if after the initial window plus one extension (≈4 weeks, ≥60 closed trades) the full stack fails to beat the A1 control AND absolute PF < 1.0, `round_retest_guarded_v1` retires permanently. The family then has exactly one remaining life: the pre-registered Phase B structural variant. If that also fails its window, the round family is closed for good — no third lives.

## Status

`RECONCILED_AWAITING_OWNER_GO`. On the owner's word, the Codex work order is: reviewer's
§6 deliverables + §7 preflight gates, under this addendum's amendments, with the §8
two-week evaluation plan. Nothing is armed until every §7 gate is PASS and the owner signs.
