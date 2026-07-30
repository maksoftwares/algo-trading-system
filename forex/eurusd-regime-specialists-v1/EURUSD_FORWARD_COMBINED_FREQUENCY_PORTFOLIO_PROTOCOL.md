# EURUSD combined forward frequency portfolio protocol

Frozen before any post-floor observation.

The final research portfolio combines exactly two prospective components:

1. the unchanged M15 chop-plus-compression first-break portfolio; and
2. the one-decision-per-day cross-pair online learner.

Neither component, regime, side, clock, threshold, or allocation may be
deleted or changed after its result is visible.

## Frequency

The denominator is not “active trade days.” It is every Monday-Friday UTC date
after the daily learner completes its fixed 20 resolved-day warmup that has at
least 240 valid prospective EURUSD M5 intervals. Missing or partial days are
reported and never imputed.

Final admission requires:

- at least 160 complete validation weekdays;
- at least 136 executed shadow trades;
- 0.85 through 1.25 trades per complete weekday; and
- trades on at least 65% of complete weekdays.

This makes approximately one trade per trading day an explicit gate instead of
an aspiration.

## Edge

M15 outcomes retain their executable 0.02 chop / 0.01 compression sizing.
Eligible daily-learner outcomes use fixed 0.01 lot and an eight-pip risk, so one
R equals USD 0.80. The pooled portfolio requires base PF at least 1.15,
additional-half-pip PF at least 1.05, positive net P&L, best-5%-removed PF at
least 1.0, both chronological trade halves above PF 1.0, maximum closed-trade
drawdown of USD 75, and no month above 40% of gross profit. M15 and daily
components must separately retain PF 1.15 and 1.10 respectively.

## Overlap and risk

The Capital.com demo account must remain in hedging mode. At a shared
timestamp, causal priority is M15 chop, daily cross-pair, then M15 compression.
At most three positions and USD 15 of concurrent initial risk may be open.
More than 5% risk-cap rejections fails admission.

To keep the portfolio ledger causal and append-only, a validation day is not
finalized until the EURUSD denominator is complete, the daily learner has
written a terminal decision, and no earlier M15 or daily outcome is pending.
Later-resolving trades can therefore extend the ledger but can never reorder or
rewrite an earlier portfolio decision.

## Deployment boundary

Both components must independently pass their economic, MT5-parity, and
shadow-soak gates. The pooled system then needs combined MT5 ordering parity and
a separate combined demo soak. Until all requirements pass,
`demo_order_authorized` is always false.
