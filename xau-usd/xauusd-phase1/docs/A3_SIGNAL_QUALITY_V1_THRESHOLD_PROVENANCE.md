# A3 Signal Quality V1 Threshold Provenance

Status: `LOCKED_PENDING_SHADOW_BUILD`

This note explains where the A3 signal-quality V1 thresholds came from. It is report-only provenance and does not change the locked hypothesis file.

## Sources

- `docs/A3_SIGNAL_QUALITY_HYPOTHESES_V1_2026_06_18.md`
- `outputs/manifests/A3_SIGNAL_QUALITY_HYPOTHESES_V1.sha256.json`
- `outputs/reports/MULTI_TIMEFRAME_TREND_ALIGNMENT_REPORT_2026_06_13.json`
- `FINAL_REVIEW_B7EA982_A3_REPAIR_IMPLEMENTATION_PLAN_2026_06_18.md`
- `CODEX_A3_REPAIR_BUILD_PLAN_CANONICAL_2026_06_18.md`

## Provenance Summary

The V1 shadow threshold family is based on the reviewer-identified A3 failure mode: A3 entered too many low-quality breakout-family trades, then accumulated losses one by one. The immediate repair principle is to prove a forward shadow edge before any broker-action reactivation.

The strongest historical lead was the multi-timeframe trend-alignment split for the round-retest family: with-trend behavior was materially stronger than against-trend behavior. This lead is not considered live-ready. It is only eligible for pre-registered shadow validation.

The locked V1 hypotheses separate three candidates:

- combined signal-quality guard;
- MTF-only guard;
- retest-quality-only guard.

Each candidate remains shadow-only, shares one virtual breakout-family position constraint, and must log rejects as evidence rather than hiding them.

## Non-Use Rules

These thresholds must not be revised after forward start under the same V1 label. The provenance file must not be used to justify broker action, owner arming, or runtime attach. It exists only to make later review reproducible.
