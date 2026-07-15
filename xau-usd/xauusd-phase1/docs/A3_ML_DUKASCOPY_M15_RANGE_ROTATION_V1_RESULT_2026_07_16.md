# A3 ML Dukascopy M15 Range Rotation V1 Result

Date: `2026-07-16`

Classification: `DUKASCOPY_M15_RANGE_ROTATION_TRAIN_REJECTED`

## Decision

Reject the M15 range-rotation specialist. It solved the M5 opportunity and spread scarcity but failed the train-only economic gate, so validation, internal test, and exam remained closed.

## Reproduction Lock

- Pre-outcome commit: `cd3f1921`.
- Base causal feature SHA-256: `74ca74f2f6f5b3eaa8bca687fc2cced8dc20140a54506f3a25cb22920b53031b`.
- M15 feature rows: `141,495`.
- Train trades: `525`.
- Baseline PF: `0.537`.
- Baseline average: `-0.2566R`.
- Stressed PF: `0.421`.
- Stressed average: `-0.3566R`.
- Stressed net: `-187.19R`.
- Maximum closed stressed drawdown: `192.47R`.

## Train-Only Path Anatomy

- Midpoint targets: `166`, or 31.6%.
- Structural stops: `274`, or 52.2%.
- Time expiries: `85`, or 16.2%.
- Long stressed PF: `0.448`.
- Short stressed PF: `0.396`.

Both directions failed, so this is not a direction-asymmetry issue. The M15 range classification admitted enough opportunities and the wider risk geometry admitted executable spreads, but fading a fresh excursion was the wrong mechanism.

## Next Locked Hypothesis

Treat a fresh excursion from a low-gap range as a transition/expansion event instead of a mean-reversion event. Test one continuation specialist in the excursion direction with:

- the same causal M15 state and signal timestamps;
- a breakout-specific structural stop behind the signal;
- a fixed reward multiple and time expiry;
- the same actual bid/ask and stress accounting;
- the same train-first chronological firewall;
- deterministic and optional ML-ranked policies evaluated separately.

No Python prediction, EA consumption, demo, live, or broker action is authorized.
