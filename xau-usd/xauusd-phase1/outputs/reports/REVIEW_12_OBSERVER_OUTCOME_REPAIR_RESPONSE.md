# Review 12 Observer Outcome Repair Response

Status: `IMPLEMENTED_REVIEW_READY`

This response addresses Review 12 priority items 1, 2, and 4 without changing running demo EAs, chart attachments, order settings, profiles, positions, or MT5 runtime behavior.

## Implemented

- Direction normalization is fixed in `generate_observer_outcome_resolution.py`.
- Observer `LONG`/`SHORT` rows are normalized to broker `BUY`/`SELL` for broker joining and M5 replay only.
- Original observer direction is preserved in the output rows.
- Unknown direction rows are marked `UNRESOLVED_UNKNOWN_DIRECTION`.
- Resolution evidence is split by method:
  - broker-trade join
  - M5 bar replay
  - unresolved
- Replay v2 uses executor-faithful next-M5-open entry, measured spread adjustment, synthetic SL/TP, and adverse-first same-bar ordering.
- Replay v1 plan columns are preserved only for calibration diffing.
- M5 replay bars are exported read-only for the pinned `2026-06-01 00:00:00` through latest available window.
- Bar export continuity reports row count, first/last bar, gaps, max gap, duplicates, and continuity percentage.
- New scoreboard summarizes observer evidence by EA, symbol, session bucket, direction, old shadow action, proposed v2 action, broker joins, replays, unresolved rows, wins, losses, win rate, and broker PnL.
- Because executor_v2 replay calibration remained below the 75% floor, scoreboards are generated in `broker_joined_only` mode and replay rows are descriptive only.

## Latest Evidence

- Outcome report: `xau-usd/xauusd-phase1/outputs/reports/OBSERVER_OUTCOME_RESOLUTION_REPORT.md`
- Scoreboard: `xau-usd/xauusd-phase1/outputs/reports/OBSERVER_SHADOW_POLICY_SCOREBOARD.md`
- Replay calibration: `xau-usd/xauusd-phase1/outputs/reports/OBSERVER_REPLAY_CALIBRATION_REPORT.md`
- Bar export report: `xau-usd/xauusd-phase1/outputs/reports/PHASE2_M5_REPLAY_BAR_EXPORT_REPORT.md`

Latest generated counts:

| Metric | Count |
| --- | ---: |
| Observer would-signal rows | 1,308 |
| Actual broker trade rows | 1,372 |
| Resolved rows | 1,007 |
| Broker-joined rows | 81 |
| M5 replay rows | 926 |
| Unresolved rows | 301 |

Replay calibration:

| Metric | Value |
| --- | ---: |
| Calibration status | PERMANENTLY_QUARANTINED_PENDING_NEW_DESIGN |
| v1 outcome agreement | 53.09% |
| v2 outcome agreement | 60.49% |
| Scoreboard mode | broker_joined_only |

## Boundary

- This is analysis-only evidence repair.
- No trading EA was edited, attached, detached, reconfigured, restarted, or replaced.
- No order, position, profile, preset, or chart state was changed.
- Canonical Phase 2 status is unchanged.
