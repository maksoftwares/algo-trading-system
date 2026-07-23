# EURUSD Frequency V2 Controlled Demo Runbook

## Decision

`EURUSD_FREQUENCY_V2_REGIME_OVERLAY` is eligible for a controlled Capital.com
shadow-demo rehearsal. It is not approved for live trading.

The portfolio has two independently owned sleeves:

1. M15 RSI-extreme long entries at 0.01 lots, with an additional 0.01 lots
   only when the completed H4 classifier is in `trend_up` or `trend_down`;
2. the frozen H1 Asia/London chop short control at 0.01 lots.

The two sleeves have different magic numbers and may overlap. Each sleeve owns
at most one position, so portfolio concurrency cannot exceed two.

## Capital.com real-tick evidence

Period: 2024-07-01 through 2026-07-02. History quality: 98%.

- 697 completed trades over 615 active broker dates;
- 1.133 completed trades per active date;
- 403 wins and 294 losses;
- 57.82% win rate;
- $119.42 net profit at the declared lots;
- 1.3075 portfolio profit factor;
- $28.45 maximum closed-trade drawdown, 0.285% of a $10,000 balance;
- 64% profitable active months;
- 1.019 profit factor after removing the best 5% of trades;
- maximum two concurrent positions.

The profit-factor target remains 1.45. The achieved 1.3075 passes the frozen
1.30 controlled-demo floor but is not described as equivalent to the
62-trade control.

## Shadow setup

1. Attach `ForexMeanReversionScout.ex5` to an EURUSD M5 chart and load
   `EURUSD_FREQUENCY_V2_M15_SHADOW_DEMO.set`.
2. Attach `EurUsdV4AsiaLondonCompressionShort.ex5` to a separate EURUSD H1
   chart and load `EURUSD_V4_SHADOW_DEMO.set`.
3. Confirm both startup logs report the intended demo server, symbol, magic
   number, and shadow status.
4. Keep automated trading disabled for the first shadow observation.
5. Reconcile signals weekly against broker time, spread, and expected regime.

## Ordering rehearsal

Ordering remains fail-closed. It requires both:

- replacing the account-login placeholder in the owner-authorized template;
- setting shadow mode false and demo orders true.

Do this only on `Capital.ComMena-Demo`. Both EAs reject non-demo accounts.
Use a $10,000 demo balance so the tested fixed-lot drawdown scale remains
comparable.

## Promotion requirements

Do not consider live use until prospective evidence confirms:

- at least 100 shadow/demo trades;
- realized PF >= 1.20 and positive expectancy;
- no unexplained signal, lot, stop, target, or regime-routing mismatches;
- maximum concurrency remains two;
- no safety-gate or account-identity failures.
