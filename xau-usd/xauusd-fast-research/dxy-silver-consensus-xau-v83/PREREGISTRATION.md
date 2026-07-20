# V83 DXY-Silver Consensus Preregistration

Date: `2026-07-21`

## Incremental Hypothesis

V72/V73 rejected silver alone and V74/V75 rejected DXY alone. V82 could not test
three-source consensus because its Treasury feed lacked continuous sessions.
V83 asks the still-unanswered joint question: does agreement between the two
continuous sources remove enough source-specific noise to identify XAUUSD
transmission? V83 cannot retune, mirror, or rescue any prior economic outcome.

## Causal Candidate

1. DOLLARIDXUSD is the event clock from 07:00 through 18:00 UTC.
2. A rising DXY implies short XAUUSD; a falling DXY implies long XAUUSD.
3. XAGUSD must move in the implied gold direction over the same horizon.
4. Baselines are at or before `decision_time - horizon` and no more than two
   seconds stale. Current silver is at or before the event and no more than two
   seconds stale.
5. Current XAUUSD is strictly before the event and no more than one second stale.
6. Signed XAU response divided by absolute silver movement must not exceed the
   selected maximum.
7. Only the first qualifying event per UTC date becomes a candidate.

## Outcome-Blind Registry

January 2019 registers exactly `5 x 5 x 5 x 4 x 2 = 1,000` policies:

- horizons: 1, 2, 5, 10, and 20 seconds;
- minimum DXY move: 0.05, 0.10, 0.15, 0.20, or 0.30 bps;
- minimum directional silver move: 0.50, 1.00, 1.50, 2.00, or 3.00 bps;
- maximum signed XAU/silver response: 0.00, 0.25, 0.50, or 0.75; and
- minimum source-quote index advances: 2 or 5.

Selection targets 0.8 candidate per eligible weekday and uses only frequency,
active-day share, direction balance, and the committed tie-break. It cannot see
post-entry XAUUSD prices or any economic outcome.

## Execution And Gates

Entry is the first executable XAUUSD quote within one second. Longs use Ask/Bid
and shorts use Bid/Ask. Stop distance is the largest of 0.5 completed-M5 ATR,
four entry spreads, and USD 1.00. Target is 1.5R; maximum hold is 15 minutes.
Stress adds USD 0.30, USD 0.35 per 24 hours, and 0.05R slippage.

Each stage must pass its frozen sample, 0.65-1.0/day frequency, base PF 1.30,
stress PF 1.20, half-period PF 1.10, positive-month, profitable-day,
winner-removal, drawdown, balance, and bootstrap gates. A failed stage is
terminal. Historical passage still requires the precommitted shared-account
test and prospective shadow evidence.

No model training, Python prediction, EA consumption, demo/live execution, paid
data, or broker action is authorized.
