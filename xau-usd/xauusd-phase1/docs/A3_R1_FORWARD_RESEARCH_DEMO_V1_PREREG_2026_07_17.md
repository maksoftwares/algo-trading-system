# A3 R1 Forward-Research Demo V1 Preregistration

Date: 2026-07-17

## Decision

Prepare one isolated R1 specialist for prospective demo evidence on account `1033669`. This is not strategy promotion, live authorization, an ML model, or a claim that future results will be profitable.

## Why This Lane

The frozen R1 historical comparator was positive over ten years, while the recent high-frequency A2 and M5 research streams were materially negative. R1 is therefore the only defensible execution candidate, but it remains low frequency and failed the strict retention and stability promotion gates.

Reference R1 evidence before the demo risk overlay:

- 310 historical trades.
- Stress net: 10,120.70 in the reference backtest account currency.
- Stress profit factor: 2.75.
- Exact floating drawdown: 1,284.17.
- Approximate frequency: 0.123 trades per trading day.

The earlier 10,000-account demo guard retained only 26.84% of net profit and 58.26% positive six-month blocks. This experiment must therefore collect new evidence; it must not be described as qualified.

## Frozen Signal

- EA: `A1XauM5MomentumContinuationExecutor`.
- Signal mode: `7`, D1 compression followed by H4 expansion.
- Direction: long only.
- Router: strict R1 uptrend only.
- D1 ATR percentile maximum: 80.
- Compression box: 2 days.
- Range-to-median maximum: 1.50.
- H4 minimum body fraction: 0.35.
- H4/D1 supportive-state guard: enabled.
- Stop: max of 2.5 M5 ATR and 350 points, with no ceiling.
- Target: 2R.

No signal parameter may be changed after attachment. Any change creates a new preregistered experiment.

## Demo Risk Overlay

The actual A3 demo account is denominated in AED and showed balance/equity of approximately AED 2,998.45 during preparation. Despite its legacy name, `InpRiskAmountUsd` is calculated from MT5 tick value in account currency.

- Requested maximum risk: AED 30 per trade, approximately 1% of observed equity.
- Maximum lot: 0.01.
- Reject a trade when the broker minimum lot would exceed AED 30 risk.
- Maximum one new entry per broker day.
- Maximum one open R1 position.
- Daily closed-loss stop: AED 60.
- 24-hour cooldown after a losing exit.
- Spread cap: 75 points.
- Estimated cost cap: 0.15R.

These controls intentionally reduce frequency. They may not be relaxed inside this experiment.

## Isolation And Fail-Closed Rules

Before attachment:

1. Confirm login `1033669`, server `Capital.ComMena-Demo`, trade mode demo, and account currency AED.
2. Confirm zero XAUUSD positions and pending orders.
3. Pause the armed `Phase2ExperimentalDemoExecutor` fill-collection chart.
4. Confirm every other chart is non-broker-action or paused.
5. Confirm magic `934100` is unused.
6. Compile with zero errors and zero warnings.
7. Back up the chart profile before editing it.

Runtime must refuse the wrong symbol, non-demo trade mode, wrong login, wrong server marker, present kill-switch file, excessive spread/cost, excessive risk, a second position, or a second daily entry.

## Evidence Policy

Only trades generated after the verified runtime startup timestamp count as prospective evidence. Historical backtest results remain separate. Demo evidence must report signals, guard rejections, orders, deals, realized P&L, maximum floating drawdown, costs, and missed trades caused by the AED 30 minimum-lot risk gate.

No profitability conclusion is allowed from a handful of demo trades. The first operational checkpoint is startup/guard correctness; the first quantitative checkpoint is 30 resolved trades or 90 calendar days, whichever is later.
