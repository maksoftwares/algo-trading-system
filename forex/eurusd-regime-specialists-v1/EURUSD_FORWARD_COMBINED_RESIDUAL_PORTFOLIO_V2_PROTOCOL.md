# EURUSD combined residual forward portfolio v2 protocol

## Purpose

This successor monitor measures the exact requested end state: approximately
one EURUSD trade per complete trading weekday without sacrificing the protected
M15 edge. It combines the unchanged M15 portfolio, any eligible frozen daily
learner trades, and the new forward-only residual-regime specialist.

It is an admission monitor, not an order router. The campaign and its thresholds
were frozen before the `2026.08.01 00:00:00` UTC evidence floor with zero
post-floor feature rows and zero portfolio decisions.

## Components

1. `M15_REGIME` retains its frozen sizing, signals, execution assumptions, and
   independent admission requirements.
2. `DAILY_CROSSPAIR` remains available under its frozen rules. While it has
   zero participating trades it cannot block the other components; once it
   contributes any trade, its own PF, economic admission, parity, and soak are
   mandatory.
3. `RESIDUAL_REGIME` uses fixed 0.01 lot, eight-pip risk, the frozen 20-day
   residual warm-up, and only its eligible forward decisions.

No component can be retrospectively deleted or reweighted.

## Calendar denominator

Validation starts only after both online learners have completed their frozen
20-resolved-day warm-ups. A complete weekday must have at least 240 valid
prospective EURUSD M5 intervals. The date must also have terminal daily and
residual decisions, and no earlier M15 or daily outcome may still be pending.

Missing or partial days are not imputed. Frequency is accepted combined trades
divided by complete validation weekdays. Coverage is the share of complete
weekdays with at least one accepted trade.

## Causal risk

At the same timestamp, protected M15 chop and compression opportunities have
priority over the daily and residual research components. The portfolio allows
at most three concurrent positions and USD 15 of concurrent initial risk.
More than 5% causal risk-cap rejections fails admission.

## Frozen admission

At least the following are required:

- 160 complete validation weekdays;
- 136 combined accepted trades;
- 50 accepted residual trades;
- 0.85 through 1.25 trades per complete weekday;
- trades on at least 65% of complete weekdays;
- win rate from 45% through 60%;
- payoff ratio at least 1.25;
- PF at least 1.15;
- PF at least 1.05 after an additional 0.5-pip round-trip stress;
- best-5%-removed PF at least 1.00;
- both chronological trade halves above PF 1.00;
- positive net P&L and maximum USD 75 closed-trade drawdown;
- no month above 40% of gross positive P&L;
- M15 component PF at least 1.15;
- residual component PF at least 1.15;
- daily component PF at least 1.10 if it participates;
- independent M15 and residual economic admission;
- independent daily economic admission if it participates;
- all participating component MT5 parity and shadow soak;
- combined MT5 ordering parity; and
- combined disarmed demo soak.

The monitor can report readiness, but it always writes
`demo_order_authorized=false`. A separately reviewed guarded demo package is
required after every gate passes.

## Prohibitions

No historical input, component deletion, component reweighting, denominator
change, priority change, threshold tuning, forced trade, outcome rewrite, or
order routing is allowed.
