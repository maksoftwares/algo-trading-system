# EURUSD Thousand-Strategy Campaign V1 Preregistration

Frozen before outcome inspection: `2026-07-23`.

## Objective

Run one broad but bounded discovery campaign instead of repeatedly repairing
the weak RSI/Bollinger close-fade family. Exactly 1,000 variants are evaluated:
100 variants in each of ten mechanically distinct archetypes.

1. trend pullback continuation, long;
2. trend pullback continuation, short;
3. range breakout, long;
4. range breakout, short;
5. compression breakout, long;
6. compression breakout, short;
7. low-efficiency z-score reversion, long;
8. low-efficiency z-score reversion, short;
9. failed downside break reversion, long;
10. failed upside break reversion, short.

Each family combines five frozen signal thresholds, four ATR stop distances,
and five reward/risk targets. No same-version repair or post-outcome parameter
change is allowed.

## Data and chronology

- source: frozen Dukascopy hourly EURUSD bid/ask JSON;
- source interval: `[2016-07-01, 2026-07-01)`;
- discovery fit: `[2016-07-01, 2018-07-01)`;
- discovery confirm: `[2018-07-01, 2020-07-01)`;
- validation quarantine: `[2020-07-01, 2022-07-01)`;
- internal-test quarantine: `[2022-07-01, 2024-07-01)`;
- exam quarantine: `[2024-07-01, 2026-07-01)`.

V1 opens only the two discovery windows. Later windows remain quarantined until
a discovery shortlist is frozen in a separate commit.

## Execution contract

- completed H1 signal bar only;
- first tick approximation is the next contiguous H1 bid/ask open;
- long entries use Ask; short entries use Bid;
- long exits use Bid; short exits use Ask;
- 0.2 pip adverse slippage on entry and exit;
- spread is therefore included natively;
- stop and target are fixed from signal-bar ATR;
- same-bar stop and target collision resolves stop first;
- time exit occurs at the frozen family holding limit;
- one open position per variant;
- entry spread must be at most 2.0 pips;
- primary stress subtracts another 0.5 pip from every trade.

## Discovery gates

Both discovery windows must independently satisfy:

- at least 60 filled trades;
- stressed PF at least 1.10;
- positive stressed net pips;
- at least 50% positive active months;
- PF at least 1.00 after removing the five largest winners.

The maximum of the two one-sided mean-return p-values is adjusted across all
1,000 attempts with Benjamini-Hochberg. Adjusted p-value must be at most 0.10.
At most three variants per archetype may advance, ranked by the weaker stressed
PF across the two discovery windows.

## Boundary

This is a coarse rejection screen. Passing it does not establish an edge and
does not authorize implementation. A frozen shortlist would require exact M5
bid/ask path validation in the quarantined windows, then independent MT5
replication and prospective evidence.

No broker action, chart/demo/live/shadow runtime, paid data, or reviewer
submission is authorized.
