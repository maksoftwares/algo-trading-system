# A3 Signal Quality V2 Soft Retest Threshold Provenance

Status: `LOCKED_FOR_COST_APPLIED_FRESH_VALIDATION_ONLY`

Date locked: `2026-06-18`

Account scope: `1033669`

Symbol scope: `XAUUSD`

Candidate ID: `A3_SQ_SOFT_RETEST_W15_B45_C60_RCM05_V2`

## Boundary

This document records how the V2 soft-retest thresholds were discovered. It does not authorize live trading, demo broker action, MT5 attachment, profile edits, preset arming, order placement, position management, lot changes, SL/TP changes, or account changes.

A3 remains paused until a separate fresh validation window, reviewer approval, and owner authorization pass.

## Provenance Summary

The selected thresholds were found through manual targeted geometry searches on the January 2025 through July 2025 phase0 Dukascopy XAUUSD discovery set. They were not pre-registered before discovery and must not be treated as final edge evidence.

Selected rule:

```text
bars_after_break <= 15
confirmation body / range >= 0.45
confirmation directional close location >= 0.60 for long, <= 0.40 for short
retest close margin >= 0.05 ATR beyond the breakout level
```

The threshold values sit between the earlier loose retest family and the stricter V1 retest family. That makes this a plausible candidate for fresh validation, but it also creates threshold-selection risk.

## Search Footprint

Compact soft-retest grid:

```text
5 max-window values
3 invalidation modes
5 confirmation-body values
5 directional-close values
4 penetration values
4 retest-margin values
3 cost values
= 18,000 possible combinations
```

From that compact grid, 4,296 combinations had enough sample to track, and 1,086 passed the V2 registration gates on discovery data.

Stricter drawdown grid:

```text
7 max-window values
3 invalidation modes
7 confirmation-body values
6 directional-close values
4 penetration values
4 retest-margin values
= 14,112 possible combinations
```

Only one stricter drawdown-grid hit met the drawdown <= 8R target:

```text
w<=15 inv=none body>=0.45 dc>=0.60 pen<=999 margin>=0.05
accepted=586
signal_retention_pct=40.3304
opened_virtual_trades=490
virtual_trade_retention_pct=55.3672
median_weekly_trade_retention_pct=59.3750
profit_factor=1.9186
expectancy_r=0.4031
win_rate_pct=56.1224
bad_signal_loss_share_pct=35.8100
bad_signal_loss_share_improvement_pct=28.5230
max_consecutive_losses=6
max_drawdown_r=7.5000
net_r=197.5000
```

The Dukascopy discovery source has zero/unavailable spread fields for this replay, so these figures are not cost-validating edge evidence even though the evaluator now computes PnL gates on net R after subtracting `cost_r`.

## Interpretation

The discovery result is upward-biased by threshold selection. It is valid only as a locked hypothesis to carry into a fresh measured-cost validation window.

Promotion evidence is zero at this stage.

The next gate is forward, tick-level or measured-cost validation on data that was not used in threshold selection. PF, expectancy, net R, drawdown, concentration, cost, frequency, and eligibility must all be evaluated after subtracting `cost_r`.
