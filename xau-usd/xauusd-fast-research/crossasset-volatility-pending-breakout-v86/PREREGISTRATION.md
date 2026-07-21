# V86 Cross-Asset Volatility Pending Breakout Preregistration

Date: `2026-07-21`

## Incremental Hypothesis

V84 rejected immediate continuation after XAUUSD had already moved during a
cross-asset volatility event. V86 does not enter that event or mirror its
direction. It asks whether DXY/silver volatility can announce a pending state
while XAUUSD is still quiet, followed by a later, self-confirmed XAUUSD breakout
that creates a new decision clock.

## Causal Candidate

1. DOLLARIDXUSD is the source-event clock from 07:00 through 18:00 UTC.
2. Absolute DXY and XAGUSD movement over the selected horizon must exceed their
   selected thresholds; source direction is irrelevant.
3. Strictly pre-event XAUUSD movement must remain below the selected quiet
   threshold, always at most 1.00 bps.
4. After the source event, XAUUSD has 60 seconds to cross 2.00 or 3.00 bps from
   its pre-event anchor. No trade exists if it does not cross.
5. The first crossing quote is the decision time and its sign sets LONG or
   SHORT. Entry remains the first executable quote after that decision.
6. Baselines and source quotes obey the registered staleness and quote-count
   rules. Only the first qualifying trigger per UTC date becomes a candidate.

## Outcome-Blind Registry

January 2019 registers exactly `4 x 5 x 5 x 5 x 2 = 1,000` policies:

- source horizons: 5, 10, 20, or 60 seconds;
- minimum absolute DXY move: 0.10, 0.20, 0.30, 0.50, or 0.75 bps;
- minimum absolute silver move: 1.00, 2.00, 3.00, 5.00, or 7.50 bps;
- maximum initial absolute XAUUSD move: 0.10, 0.25, 0.50, 0.75, or 1.00 bps;
- later XAUUSD breakout: 2.00 or 3.00 bps.

Selection targets 0.8 candidate per eligible weekday using only density,
active-day share, direction balance, and the committed strictness tie-break.
Calibration cannot see any XAUUSD quote after the breakout decision.

## Execution And Gates

Longs execute Ask/Bid and shorts Bid/Ask. Stop distance is the largest of 0.75
completed-M5 ATR, four entry spreads, and USD 1.00. Target is 2R and maximum
hold is 60 minutes. Stress includes ticket, holding, and 0.05R slippage costs.

Every stage must pass its frozen density, base/stress PF, half-period PF,
profitable-day, positive-month, direction-balance, winner-removal, drawdown, and
bootstrap gates. A failed stage is terminal. Historical passage still requires
the precommitted single-account V59/V60 test and prospective shadow evidence.

No model training, Python prediction, EA consumption, demo/live execution, paid
data, or broker action is authorized.
