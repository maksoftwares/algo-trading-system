# A3 ML Regime Portfolio Continuous Backtest Preregistration

Date: `2026-07-13`

Status: `LOCKED_BEFORE_RUN`

## Objective

Measure one continuous, exact-MT5, fixed-lot XAUUSD research portfolio from
`2016-07-01` through `2026-06-30`. Report closed-trade P/L for the trailing three
months, six months, five years, and ten years ending `2026-06-30`.

## Frozen Portfolio

- R0 shock: no trade.
- R1 uptrend: `r1_box_clean_strict_uptrend` from the clean R1 builder.
- R2 downtrend: `r2_pullback_short_h1_confirm` from the strict R2 builder.
- R3 compression: no trade because no continuous-window specialist has survived.
- R4 chop/undefined: no trade because no specialist has survived.
- Transition: no dedicated trade permission.

Both active specialists use the EA's completed-bar native Router V1 gate, fixed
`0.01` lots, fixed `2R`, and no post-result calendar or previous-P/L masks.

## Fixed Evaluation

- MT5 account currency: USD.
- Initial deposit per isolated component run: USD 1,000.
- Portfolio P/L is the chronological sum of fixed-lot component exits.
- Extra-cost stress: subtract USD 0.30 per completed trade.
- P/L windows use exit timestamps; open P/L at a boundary is excluded.
- Maximum drawdown uses the combined chronological closed-trade equity curve.
- No threshold, source, regime, hour, month, or risk-rule changes after seeing results.

## Gates

- Ten-year stressed profit factor at least `1.40`.
- Last three months and last six months nonnegative after extra-cost stress.
- Combined maximum closed drawdown no more than USD `1,000`.
- At least 75% of complete six-month blocks nonnegative after extra-cost stress.
- Every included trade must come from the frozen R1 or R2 specialist.

Passing these gates creates research evidence only. It does not authorize demo or
live broker action because all history through `2026-06-30` is development data.
