# EURUSD Neutral prospective macro/cross-asset agreement

## Frozen status

`PREREGISTERED_PROSPECTIVE_ONLY_WAITING_FOR_EVIDENCE`

This is a new Regime 1 specialist, frozen before its first eligible
prospective signal. It receives no historical backtest and no historical P&L.
Its purpose is to test a causal mechanism without selecting another attractive
historical subperiod.

It is shadow research only. It cannot place a demo or live order.

## Owned opportunity

The strategy owns only a UTC date that the unchanged parent classifier labels
Neutral using information available by 00:00 UTC. It then considers only CPI
MoM, PPI MoM, and NFP releases with:

1. an immutable forecast captured at least 60 seconds before release;
2. an exactly linked actual observed at least 60 seconds after release; and
3. matching TradingView event id, ticker, and scheduled UTC timestamp.

Any missing or ambiguous field means cash.

## Frozen signal

After three fully completed post-release M5 bars, one side must be supported by
all three independent components:

| Component | LONG EURUSD | SHORT EURUSD |
|---|---|---|
| US macro surprise | actual below forecast | actual above forecast |
| EURUSD reaction | EURUSD midpoint rises | EURUSD midpoint falls |
| Cross-asset reaction | DXY falls and Treasury price rises | DXY rises and Treasury price falls |

Zero changes and any disagreement mean cash. No magnitude threshold, family
weight, time filter, weekday filter, side reversal, fitted model, or trade
quota exists. Lower frequency is acceptable; profitability and robustness are
the gates.

The entry is the first EURUSD M5 open after the three observation bars. The
entry bar is excluded from every confirmation input. The stop is the
observation extreme plus 0.5 pip, floored at 4 pips and capped at 25 pips. The
target is 1.5R and the maximum hold is 12 hours.

Execution assumes at least 0.7 pip spread, 0.1 pip slippage per side,
stop-first ambiguity, one open position, and a fixed 0.01-lot reporting size.

## Prospective admission

No conclusion is allowed until both 12 calendar months and 30 closed trades
exist. Every following check must then pass:

- win rate from 45% through 55%;
- realized payoff ratio from 1.35 through 1.75;
- profit factor at least 1.15;
- at least eight LONG and eight SHORT trades, each side with PF at least 1.0;
- maximum drawdown no worse than 15R;
- PF at least 1.0 after another 0.5 pip round-trip cost;
- PF at least 1.0 after removing the top 5% of winners; and
- same-day, same-side Neutral-oracle precision at least 50%.

Passing these gates triggers research review only. It does not automatically
authorize broker action. Failure rejects this exact rule without retuning.

## Immutable inputs

- Parent Neutral classifier config:
  `eaea7e0fe4f32186e2a08fd56787f8d9909aa3360e005076d0cf93a8880203c8`.
- Parent paired source:
  `c082aa11b5cb94f6e5101479cefeeb81db749ca94afa9b806a2a309d8e8c7cd1`.
- Base data/classifier contract:
  `4dd6c409764dd81f6b879b6b4895587f1e874769ac8c69ab7f391d9d3264a7e6`.
- Cross-asset M5 schema reference:
  `3982a3bb56741a5c5139f0381696d4ec4f50d7b1be7588a0efa2664bbf51ffa4`.
- Cross-asset manifest:
  `d1250292258d64ac3d052d4cb90691d9415bd638dd03a31f0fdc2a50845c10c8`.
- Cross-asset timestamp contract:
  `e368416625445fc670a3633f9d8a542ea0e328a0cb822eeb003c75a86005c496`.

The historical cross-asset file establishes schema and timestamp semantics
only. Prospective bars must be captured append-only and individually hashed;
historical returns are forbidden from this strategy's evaluation.
