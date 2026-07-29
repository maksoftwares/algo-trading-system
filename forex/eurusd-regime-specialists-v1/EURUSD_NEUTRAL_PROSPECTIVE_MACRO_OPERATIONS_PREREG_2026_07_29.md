# EURUSD Neutral prospective macro operations preregistration

Date: `2026-07-29`

Status: `FROZEN_BEFORE_FIRST_FUTURE_AUTOMATED_OPERATION`

This is an operations-only runner for the already-frozen EURUSD Neutral
macro/cross-asset prospective campaign. It changes no event family, forecast,
surprise threshold, cross-asset rule, direction, entry, stop, target, cost,
ownership definition, oracle definition, or admission gate.

The runner:

- verifies the immutable V1.4 planner and this operations lock before acting;
- accepts only the exact bounded command families in the frozen planner;
- executes one operation and then replans from immutable evidence;
- materializes a scheduled command only from the frozen planner configuration;
- runs a forecast request 15 seconds before its planned polling clock to leave
  network-completion margin while preserving the frozen minimum 60-second
  pre-release lead;
- refuses a forecast request after the frozen release-minus-60-second deadline;
- never loads historical EURUSD P&L; and
- has no broker or order capability.

At freeze, the ownership cache has zero missing safely completed symbol-hours,
the planner reports `WAITING_FOR_NEXT_SAFE_ACTION`, there are zero signals and
zero trades, the next cache operation is `2026-07-29T06:01:00Z`, and the first
calendar forecast poll is `2026-07-29T15:50:54Z`.
