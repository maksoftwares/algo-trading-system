# C58 DEMO FILL COLLECTION & C03 LIFT REVIEW
Date: 2026-07-02 | Reviewer: Independent (Claude) | Recomputed from deals.csv + status reports.

## VERDICT: WORKING_AS_DESIGNED — KEEP RUNNING, with 3 actions (one owner decision)

## 1. Attach status (verified)
- A3 (1033669) fill-collection lane ATTACHED_AND_RUNTIME_CONFIRMED since 2026-06-25
  (`A3_ML_DEMO_FILL_COLLECTION_ATTACH_STATUS.md`): compile 0/0, demo server confirmed,
  trade_mode demo, exposure zero at attach, kill switch not triggered, single chart.
- Caps verified in template: 0.01 lot, max 3 orders/day (instance AND account), 1 open position,
  300s between orders, cost gate 0.15R, spread cap 75pt. InpBrokerActionAllowed=true is correct
  and expected FOR THIS LANE ONLY (demo fill collection is its purpose); canonical broker_action,
  training, and Python-prediction authorizations remain false everywhere — confirmed in C03/C28 reports.
- Money truth confirms collection: 6 A3 closed trades entered on/after Jun 25 in the latest C02
  snapshot (Jun 25: 3, Jun 26: 3 — at the daily cap). Rate ≈ 12–15 fills/week. Net −72 AED across 6;
  irrelevant to P&L purpose — this lane buys slippage/fill data at controlled cost (~50 AED/week
  observed; caps bound worst case).

## 2. C03 gate arithmetic (report of 2026-06-27, latest data Jun 26)
| Gate | Now | Needs | Fill-dependent? | ETA at current rate |
|---|---|---|---|---|
| market_setup_groups | 323/300 PASS | — | — | done |
| minority_labels | 302/90 PASS | — | — | done |
| both_directions | PASS | — | — | done |
| leakage | 0 PASS | — | — | done |
| active_weeks | 4.07 | ≥8 | yes (calendar) | ~4 more weeks → ~Jul 27 |
| slippage A1 | ADEQUATE | — | — | done |
| slippage A3 | INSUFFICIENT (24 req-price / 84 entries) | adequate coverage | yes — C58 logs request prices | grows 12–15/wk; weeks, not days |
| slippage A2 | INSUFFICIENT (22 req-price / 25 entries) | adequate coverage | **BLOCKED — no A2 lane attached** | indefinite unless acted on |
| at_least_two_regimes | FALLING only | ≥2 | market-dependent | unknowable; do NOT backfill via replay (quarantine stands) |
| feature_budget | 0/6 | ≥6 | **NO — code/spec work** | can start today |
| dataset_status | PIPELINE_ONLY | ≥EXPLORATORY_MODEL | derivative of the above | follows |

## 3. Actions
1. OWNER DECISION REQUIRED — A2: the A2 template exists (same guards) but only A3 was attached.
   Either (a) approve manual attach of the A2 lane, or (b) re-scope the slippage gate to A1+A3 with
   a documented rationale. Doing neither leaves C03 blocked on A2 indefinitely. Reviewer leans (a):
   marginal cost is bounded by the same caps, and A2 (tier1) fills are the scarcest data in the program.
2. CODEX — refresh the evidence loop: latest C02 snapshot is Jun 26 (6 days stale) and the
   shadow-health report (Jun 25) still shows observers stale/"collecting: no" while deals prove fills
   are landing. Rerun C02 export → C33 → C03 now, and weekly thereafter, so active_weeks/coverage
   progress is visible and the observer-freshness contradiction is resolved.
3. CODEX — start feature_budget work in parallel (0/6 is not fill-blocked): register the candidate
   feature list with leakage screens against the existing 323 setup groups now, so features are
   pre-cleared when data gates pass instead of serializing after them.

## 4. Honest ETA for C03 GO
Best case ~4–5 weeks (A2 attached this week + regime gate luckily satisfied by a non-FALLING July).
The regime gate is the one nobody can schedule; if gold stays one-regime, C03 stays NO_GO and that
is the gate working correctly — not a failure to fix with replay data (PERMANENTLY_QUARANTINED stands).

## 5. Consistency note
C03 progress since last review is real: market_setup_groups 223→323, minority_labels now passing,
active_weeks 3.37→4.07. The pipeline is doing what it should; the bottleneck is, as before, time
and real fills — now with a live collection lane actually feeding it.
