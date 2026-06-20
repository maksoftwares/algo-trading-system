# A3 Signal-Quality Repair — Review of ab95b3de + Implementation Plan (2026-06-18)

Reviewer: Claude. Scope: **XAUUSD, A3 `1033669`, demo only.** Reviews commit `ab95b3de`
("Harden A3 repair safety gates") and gives a concrete frequency-preserving signal-quality plan.
**A3 stays PAUSED. No broker action / live attach / preset arming. Shadow-only.**

## Commit state (verified)
`ab95b3de` is P1/P2 of the canonical plan: safety/governance/preflight only. Implementation contract,
threshold provenance, and arming audit all exist; the locked hypothesis hash still holds; A3 paused, 0
exposure. **Signal quality is genuinely not yet addressed** — correct to seek guidance before P3/P4.

## The core tension to resolve (read first)
The locked **V1 `A3_SQ_COMBINED_V1`** requires **D1 + H1 + M15 trend all aligned (±50pt slopes)** *and*
the **strict retest** (break ≥0.30 ATR, penetration ≤0.15 ATR, body ≥0.60, close-loc ≥0.80, first retest
only). That is the **high-quality / low-frequency** end — two strict filters compounded. It will almost
certainly **collapse frequency** (my estimate: single-digit % of baseline signals survive). So V1 likely
*passes quality but fails your "preserve frequency" goal.*

Resolution (anti-overfit-safe): run V1 in shadow as the pre-registered primary **and** run a **diagnostic
sweep of looser variants in parallel** to map the frequency↔quality curve. The variant that gives most of
the quality gain at acceptable frequency becomes a **new locked V2** (never a silent tweak to V1).

---

## Answers to the eight questions

**Q1 — Most likely root cause of bad A3 trades.** In order of evidence weight: (1) **Counter-trend entries**
— the #1 cause, now **cross-regime confirmed**: on the Day-3 down day, counter-trend longs won 8.7% and
lost −728 vs −114 for with-trend; shorts lost on the up-days. A3 took breakout signals against the prevailing
trend with no guard. (2) **Weak/fake retest structure** — noisy retests that aren't real break-and-hold.
(3) **Session/timing** — A3 traded weak windows A2 filters out (but fixing this collapses frequency — see Q3).
(4) **Cost/tight stops** — minor and fragile (the 300pt floor was largely non-binding on the actual trades).
So the fixable signal-quality core is **counter-trend (big) + retest quality (secondary)**; not cost, not session.

**Q2 — Filters that improve quality while preserving frequency.** The best quality-per-frequency lever is a
**moderate trend-alignment guard**, because it targets the #1 root cause and only removes ~half the trades:
- *H1-only alignment* (or a *loose counter-trend veto* that blocks only strongly-against-trend signals) —
  removes the worst losers, keeps ~55–85% of frequency. **This is the frequency-preserving candidate.**
- *Retest-quality* applied **lightly** (e.g., require a clean hold + minimum break size, but not all 10
  strict sub-conditions) as a secondary.
The winner is decided by the sweep (Q5), not assumed.

**Q3 — Filters likely too restrictive — avoid (or down-weight).**
- The **locked V1 triple-MTF (D1+H1+M15 all aligned)** — too strict alone; collapses frequency.
- **Stacking** strict-MTF **and** strict-retest (the V1 combination) — compounds to near-zero trades.
- **Session-gate-to-evening** (the A2 approach) — effective but cuts ~75% of frequency: exactly the collapse you want to avoid.
- **Strict cost cap** as a primary filter — small, fragile (June-10-driven) benefit; not worth the restriction.
- General rule: **one dominant filter at a moderate threshold**, not four strict filters stacked.

**Q4 — Repair breakout/retest, promote round, or combine?** **Repair the breakout/retest lane. Do NOT
promote round-retest. Do NOT combine.** Breakout is the only family with a proven, regime-robust edge
(+1,059 core, survives best-2-days-removed). Round-family is a regime-independent loser (−1,359) — promoting
it re-imports the drag; combining lanes re-imports duplication. Unambiguous from the deduped evidence.

**Q5 — Exact shadow-only test Codex should build next.** A **tick-level shadow observer that scores the
breakout-retest entry under a parallel filter sweep** on A3 XAUUSD M5 (virtual execution, no broker action).
Run these as parallel labeled candidates, each producing its own virtual-trade log:
| id | rule | promotable? | est. frequency vs baseline |
|---|---|---|---|
| `B0_BASELINE` | breakout-retest, no filter | no (reference) | 100% |
| `F_LOOSE_CT_VETO` | block only strongly counter-trend (H1 slope ≥50 against) | diagnostic | ~75–85% |
| `F_H1_ALIGN` | require H1 slope aligned | diagnostic | ~55–65% |
| `F_H1_M15_ALIGN` | require H1 + M15 aligned | diagnostic | ~40–50% |
| `F_RETEST_LIGHT` | minimum break size + clean hold only | diagnostic | ~50–65% |
| `A3_SQ_MTF_ONLY_V1` | locked triple-MTF | diagnostic (locked) | ~15–30% |
| `A3_SQ_RETEST_ONLY_V1` | locked strict retest | diagnostic (locked) | ~40–60% |
| `A3_SQ_COMBINED_V1` | **locked primary** (MTF+retest) | **promotion-eligible** | ~5–15% |
Only `A3_SQ_COMBINED_V1` is promotion-eligible now; the `F_*` rows are **diagnostics** that map the curve.
If a diagnostic wins, **re-register it as locked V2** before it can be promoted. Each candidate logs MFE/MAE
(for Q7), frequency, and the full decision row from the contract.

**Q6 — Pass/fail metrics before any live attach.** The locked gates (WR ≥50%, PF ≥1.30, expectancy ≥+0.15R,
concentration caps, ≥100 trades / ≥20 days / ≥4 weeks / ≥25 long + 25 short, across an up **and** a down
regime) **plus a frequency floor**: the promoted filter must retain **≥40% of baseline signals** *and* still
reach the ≥100-trade minimum. A filter that passes quality only by dropping to a handful of trades **fails**.
This operationalizes "don't solve losses by blocking everything."

**Q7 — Separate "bad signal" from "bad exit/management" losses.** Use MFE per virtual loss:
- `MFE < +0.5R` → **bad signal** (entry was wrong; price went against immediately) → fix with entry filters.
- `MFE ≥ +0.75R then SL` → **bad exit / give-back** (signal fine, management failed) → fix with exit handling.
From the existing MFE/MAE data ~23–32% of losers first reached +0.5–0.75R, so roughly **a quarter to a third
of A3's losses are exit/give-back, and two-thirds-plus are bad-signal.** Report this split per candidate so we
invest in entries vs exits in the right proportion (entries first for A3, but a give-back lock matters too).

**Q8 — Minimum evidence before reactivating A3.** The canonical reactivation boundary (one lane, 0.01 lot,
mutex active, containment, reviewer signoff, owner approval of exact version+hash, compile 0/0, zero-exposure
baseline, CI green) **plus**: a **locked V2** (if the winning filter isn't V1), the **frequency floor met**,
the **signal-vs-exit split** showing the entry fix actually moved the bad-signal share, and Python parity ≥99%.

---

## Concrete Codex plan (one task per commit, report-trail preserved)

### Files to ADD
- `mt5/Include/A3VirtualExecution.mqh` — tick-level virtual state machine (from the canonical plan: completed-bar
  signal → first-fresh-tick fill → per-tick MFE/MAE → SL/TP exit; no broker API; deterministic/replayable).
- `mt5/Include/A3SignalQualityFilters.mqh` — the filter library: `LooseCounterTrendVeto`, `H1Align`,
  `H1M15Align`, `RetestLight`, plus the locked `MTF_Triple` and `RetestStrict`. Pure functions, completed bars only.
- `mt5/Experts/Account3SignalQualityShadowObserver.mq5` + `…safe_xauusd.set` — hard dry-run, no OrderSend/
  CTrade/TRADE_ACTION_*, login 1033669 + demo + XAUUSD only, isolated observer terminal. Runs **all sweep
  candidates in parallel**, one virtual position per candidate.
- `scripts/reproduce_a3_signal_quality.py` — independent Python reimplementation (separate codepath) of every
  filter + the virtual execution, for parity.
- `scripts/generate_a3_sweep_report.py` — builds the frequency↔quality table + MFE/MAE loss-split per candidate.
- `docs/A3_SIGNAL_QUALITY_V2_<id>.md` + `outputs/manifests/…sha256.json` — **only if** a diagnostic wins; a new
  locked hypothesis. Do **not** edit V1.

### Files to MODIFY
- `scripts/generate_project_status_summary.py` — add `shadow_candidate_performance_status` + sweep status.
- Test manifest (below). No entry-EA edits; no preset arming.

### Tests to ADD
`test_a3_virtual_execution.py`, `test_a3_signal_quality_filters.py` (each filter's accept/block on fixtures +
frequency direction), `test_a3_shadow_observer_safety.py` (no broker surface), `test_a3_python_parity.py`
(≥99% decision, 100% on the promotable candidate, entry/SL/TP within 1 pt), `test_a3_sweep_report.py`.

### Proposed guard/filter rules (start moderate)
Primary frequency-preserving candidate to characterize: **`F_H1_ALIGN`** (long only if H1 EMA20 slope ≥ +X over
N bars; short symmetric) — single-timeframe, moderate. Secondary: **`F_LOOSE_CT_VETO`** (block only strongly
counter-trend). Keep retest **light** unless the sweep shows strict retest adds net quality without gutting frequency.

### Expected effect on frequency
Map the full curve (table in Q5). Decision target: the candidate with the **highest expectancy among those
retaining ≥40% of baseline frequency and ≥100 trades**. Expect that to be `F_H1_ALIGN` or `F_LOOSE_CT_VETO`,
not the locked V1.

### Required reports
`A3_SIGNAL_QUALITY_SWEEP_<date>.md` (frequency↔quality table, per candidate, per regime, best-day-removed) ·
`A3_LOSS_ATTRIBUTION_<date>.md` (signal-vs-exit split via MFE) · `A3_PARITY_<date>.md` (≥99%) · rolling
`A3_SHADOW_FORWARD_<date>.md`.

### Required backtest/shadow metrics (per candidate)
frequency (count + % of baseline) · win rate · expectancy R · PF (after cost) · net R · max consecutive losses
· drawdown R · concentration (largest/top-5/best-day) · MFE/MAE loss-split · regime coverage · cost_R P95.

### GO / NO-GO for A3 reactivation
**GO only if:** a promotion-eligible candidate (V1 or a newly-locked V2) passes **all** locked gates **and**
the frequency floor (≥40% baseline, ≥100 trades) **and** covers an up + a down regime, with parity ≥99%, mutex
+ containment built and tested, reviewer signoff, owner approval of exact version+hash, compile 0/0, CI green,
zero-exposure baseline. **NO-GO if:** the only passing candidate is below the frequency floor (quality bought by
blocking everything) · any gate fails · evidence is one-regime · parity <99% · it's an unlocked diagnostic ·
A3 has any exposure · more than one lane proposed.

**Boundary:** review/plan only. Demo only. Shadow-only. No reactivation; A3 stays paused; canonical Phase 2/3 unchanged.
