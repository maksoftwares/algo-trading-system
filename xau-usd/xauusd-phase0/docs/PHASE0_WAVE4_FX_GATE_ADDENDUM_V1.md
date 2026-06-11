# PHASE0_WAVE4_FX_GATE_ADDENDUM_V1 — locked before any Wave-4 run

Date: 2026-06-11
Author: Claude (independent technical reviewer, acting researcher under owner direction)
Status: LOCKED (SHA256 sidecar: PHASE0_WAVE4_FX_GATE_ADDENDUM_V1.sha256.json)

Applies to: Wave-4 EURUSD candidates. Pepperstone has no offline EURUSD export (the passive
MT5 exporter is forbidden for research tasks), so the matrix is SIX cells: capital_com and
dukascopy x best/median/p95 configured EURUSD costs, full windows 2016-01-01 through
2025-06-30, true holdout untouched. Dukascopy EURUSD M15/H1/H4/D1 are derived uniformly
from the continuity-clean M5 series (same correction as XAUUSD).

Locked gate adaptation relative to PHASE0_WAVE2_GATE_SET_V1 (all other gates unchanged,
frequency-aware branch rule unchanged):

1. G1 PF survival: PF >= 1.30 in at least 5 of 6 cells.
2. G7 cross-venue floor: dukascopy PF >= 1.20 in every cost model (capital_com is the
   primary venue; dukascopy is the independent check).
3. G8 modern-era integrity: 2022-2025-06-30 median-cost PF >= 1.10 in BOTH brokers.
4. DATA_VENUE_ASYMMETRY_PRESENT must be disclosed on all outputs; a pass without a third
   venue cannot reach PASS_APPROVED_FUTURE_EXPERT_CANDIDATE until a third-venue check or
   owner acceptance is recorded (same pattern as the Pepperstone partial-data decision).

Verdict rule and no-tuning law unchanged: any gate FAIL is final for the version.
Changing this file after any Wave-4 result exists invalidates the wave.
