# XAUUSD Macro Composite Risk-State Portability V1

Date: `2026-07-17`

## Question

Does the already registered `h4_macro_composite_risk_state_v0` mechanism retain
positive expectancy when it is reproduced on one continuous ten-year Dukascopy
XAUUSD bid/ask feed with explicit publication lags and the current cost-stressed
M5 execution engine?

This is a portability audit of an archived rule, not a fresh search. The original
nine-cell first pass was positive in every cell but failed its promotion gates:
six of nine cells reached PF 1.30, three early cells had only 34 trades, and all
cells failed concentration and activity requirements.

## Frozen Mechanical Rule

1. Decisions use completed UTC H4 bars.
2. External inputs are FRED 10-year real yield, broad dollar index, 5-year
   breakeven inflation, 2-year Treasury yield, 10Y-2Y curve, Baa credit spread,
   VIX, GVZ, and NFCI.
3. Market observations are unavailable until one calendar day after their FRED
   observation date. The broad dollar index and weekly NFCI use seven calendar
   days. No backward or forward fill may cross an availability timestamp.
4. The seven bullish and seven bearish votes, thresholds, H4 EMA40 confirmation,
   six-H4 return confirmation, `1.20 ATR(14)` stop, `1.65R` target, and 36-hour
   maximum hold are unchanged from the archived implementation.
5. There is at most one candidate per UTC day and direction. Execution permits
   one open family position and one selected trade per UTC day.

## Execution

- Entry is the next contiguous XAUUSD M5 open, long at Ask and short at Bid.
- Long exits use Bid; short exits use Ask.
- Stop/target collisions are stop-first.
- Stress includes native spread, `$0.30` extra execution cost, `$0.35` per 24
  hours held, and `0.05R` slippage.
- Fixed research size is 0.01 lot, represented as one ounce of XAUUSD exposure.

## Chronological Firewall

- Replication fit: 2016-07-01 through 2021-07-01.
- Development: 2021-07-01 through 2024-07-01.
- Exam: 2024-07-01 through 2026-05-22, capped by the frozen FRED snapshot.

The repository has previously inspected all retrospective periods. No window is
described as untouched. A later stage cannot rescue a failed earlier stage.

## Gates

Each stage has frozen minimum sample, activity, stressed PF, average R,
positive-active-month share, closed-trade drawdown, and top-five-winners-removed
requirements. The exam requires at least 20 trades, PF 1.30, average 0.08R,
drawdown no greater than 10R, and positive P&L after the five largest winners are
removed.

## Interpretation And Authorization

A full retrospective pass is only a portability survivor. It still requires
revision-vintage review, exact-tick parity, cost sensitivity, and prospective
shadow evidence. It is not authorized for Python prediction, EA consumption,
demo, or live execution. Same-version post-outcome tuning is forbidden.
