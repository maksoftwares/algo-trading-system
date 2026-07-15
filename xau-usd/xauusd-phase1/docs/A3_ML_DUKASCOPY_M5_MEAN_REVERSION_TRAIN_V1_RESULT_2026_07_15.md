# A3 ML Dukascopy M5 Mean Reversion Train V1 Result

Date: `2026-07-15`

Classification: `DUKASCOPY_M5_MEAN_REVERSION_TRAIN_NO_SURVIVOR`

## Decision

Reject all 12 mean-reversion profiles. Do not open validation, test, or new-holdout outcomes for this family.

The campaign produced more than enough trades, but every volatility-band, impulse-exhaustion, and sweep-fade profile had negative expectancy after bid/ask execution and frozen stress costs.

## Reproduction Lock

- Pre-outcome commit: `252e36f2`.
- Verified source months: `37`.
- Training source days: `774`.
- Raw candidates: `76,520`.
- Raw resolved labels: `76,230`.
- Executed profile trades: `18,899`.
- Candidate SHA-256: `e4b7e55f649d288dab72cdac07aee57e4b9c6fe1b15e2e28d67013b6a22f4991`.
- Raw-label SHA-256: `3b6f325fa11e3b71d34885e07ec9c2de81d024e3f6b7b57678ee0ce728f1d319`.
- Executed-label SHA-256: `673b816709e766cf57faaca5fffc81b49ae205d024e2297e822f81ba6f2a55e6`.

An immediate second run reused all 37 caches and reproduced every hash exactly.

## Evidence

All quality gates passed. Frequency ranged from `0.516` to `5.151` trades per source day.

The best profile by stress PF was `impulse_fade_any_rr1p5`:

- trades: `3,165`;
- trades per source day: `4.089`;
- win rate: `37.38%`;
- stress PF: `0.770`;
- average stress return: `-0.1749R`;
- stress net: `-$2,147.21` at fixed `0.01` lot;
- maximum closed drawdown: `$2,148.75`.

All 12 profiles had negative average R and negative net P&L. Their PF range was `0.589` to `0.770`. No profile passed the selection gates.

## Holdout Protection

- selected profile: none;
- reserved outcomes opened: false;
- validation and test authorization: false;
- strategy promotion: prohibited.

## Next Research Direction

The deterministic trend and mean-reversion campaigns now provide large high-quality candidate-label populations with ample frequency but weak unconditional expectancy. The next step is a preregistered causal ML ranker using grouped market events and time-ordered internal splits. It must prove that ranking improves later-period PF and average R while retaining frequency; otherwise it is rejected.

No Python prediction, EA consumption, demo, live, or broker action is authorized.
