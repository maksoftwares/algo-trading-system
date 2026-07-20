# V82 Joint Macro-Consensus Preregistration

Date: `2026-07-21`

## Hypothesis

The rejected V72-V81 families asked whether one source, or a group of FX pairs,
led XAUUSD. V82 tests a different joint state: a dollar-index move, a Treasury
total-return move, and a silver move must independently imply the same gold
direction. Agreement may remove source-specific noise that defeated each
single-source event. V82 does not retune or mirror any rejected event.

## Causal Event

1. DOLLARIDXUSD is the event clock between 07:00 and 18:00 UTC.
2. The DXY return sign implies the opposite XAUUSD direction.
3. USTBONDTRUSD and XAGUSD returns must both have that implied gold sign.
4. Every baseline quote is at or before `decision_time - horizon` and no more
   than two seconds stale. Current bond and silver quotes are at or before the
   DXY event and no more than two seconds stale.
5. The current XAUUSD quote is strictly before the DXY event and no more than
   one second stale. A quote stamped at or after the decision cannot be used.
6. Signed XAU response is divided by the absolute silver move and must not
   exceed the selected maximum. This defines incomplete XAU transmission.
7. The first qualifying event per UTC date is the only candidate.

## Outcome-Blind Calibration

February 2019 registers exactly `4 x 5 x 5 x 5 x 2 = 1,000` policies:

- horizons: 2, 5, 10, and 20 seconds;
- minimum DXY move: 0.05, 0.10, 0.15, 0.20, or 0.30 bps;
- minimum directional bond move: the same five values;
- minimum directional silver move: 0.50, 1.00, 1.50, 2.00, or 3.00 bps; and
- maximum signed XAU/silver response: 0.00 or 0.25.

At least two source-quote index advances are required. Selection uses only
candidate frequency, active-day share, direction balance, and the frozen
tie-break. Target density is 0.8 candidate per eligible weekday. No stop,
target, future price, P&L, MAE, MFE, or outcome may enter calibration.

## Execution And Gates

Entry is the first executable XAUUSD quote within one second. Longs enter at Ask
and exit at Bid; shorts enter at Bid and exit at Ask. The stop is the larger of
0.5 completed-M5 ATR, four entry spreads, or USD 1.00. Target is 1.5R and the
maximum hold is 15 minutes. Stress adds USD 0.30, USD 0.35 per 24 hours, and
0.05R slippage. Initial risk above USD 50 is ineligible.

Each stage requires its frozen sample and frequency gates, base PF at least
1.30, stressed PF at least 1.20, both half-period stressed PFs at least 1.10,
at least 60% positive months, positive winner-removed stress P&L, and the frozen
bootstrap significance threshold. Failure is terminal for V82.

## Research Boundary

V59/V60 remain immutable. V82 is not authorized for training, prediction,
execution, demo, live, paid data, or broker action. Historical success would
only permit shared-portfolio testing and prospective shadow collection.
