# V84 Cross-Asset Volatility XAU Momentum Preregistration

Date: `2026-07-21`

## Incremental Hypothesis

V83 showed that prescribing XAUUSD direction from DXY and silver consensus had
negative expectancy. V84 asks a different question: can simultaneous absolute
movement in two continuous macro sources identify a sufficiently active market
for the already-observed, causal XAUUSD move to continue? DXY and silver do not
vote on direction. V84 cannot mirror, retune, or rescue any prior economic
outcome.

## Causal Candidate

1. DOLLARIDXUSD is the event clock from 07:00 through 18:00 UTC.
2. Absolute DOLLARIDXUSD and XAGUSD movement over the selected horizon must
   exceed their selected thresholds.
3. Absolute XAUUSD movement over the same horizon must exceed its selected
   threshold; its sign sets LONG or SHORT.
4. Baselines are at or before `decision_time - horizon` and no more than two
   seconds stale. Current silver is at or before the event and no more than two
   seconds stale.
5. Current XAUUSD is strictly before the event and no more than one second
   stale. A quote at or after the event cannot select direction.
6. DXY/silver directional agreement is recorded for audit but never filters,
   ranks, or changes a candidate.
7. Only the first qualifying event per UTC date becomes a candidate.

## Outcome-Blind Registry

January 2019 registers exactly `4 x 5 x 5 x 5 x 2 = 1,000` policies:

- horizons: 5, 10, 20, or 60 seconds;
- minimum absolute DXY move: 0.10, 0.20, 0.30, 0.50, or 0.75 bps;
- minimum absolute silver move: 1.00, 2.00, 3.00, 5.00, or 7.50 bps;
- minimum absolute XAUUSD move: 0.50, 1.00, 2.00, 3.00, or 5.00 bps; and
- minimum source-quote index advances: 2 or 5.

Selection targets 0.8 candidate per eligible weekday and uses only frequency,
active-day share, direction balance, and the committed tie-break. Ties prefer
stricter DXY, silver, XAUUSD, and quote-count thresholds, then the shorter
horizon and policy ID. Calibration cannot see any post-entry XAUUSD price or
economic outcome.

## Execution And Gates

Entry is the first executable XAUUSD quote within one second. Longs use Ask/Bid
and shorts use Bid/Ask. Stop distance is the largest of 0.5 completed-M5 ATR,
four entry spreads, and USD 1.00. Target is 1.5R; maximum hold is 15 minutes.
Stress adds USD 0.30, USD 0.35 per 24 hours, and 0.05R slippage.

Each stage must pass its frozen sample, 0.65-1.0/day frequency, base PF 1.30,
stress PF 1.20, half-period PF 1.10, positive-month, profitable-day,
winner-removal, drawdown, direction-balance, and bootstrap gates. A failed
stage is terminal. Historical passage still requires the precommitted
single-account test and prospective shadow evidence.

No model training, Python prediction, EA consumption, demo/live execution, paid
data, or broker action is authorized.
