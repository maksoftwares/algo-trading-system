# Claude Review Prompt - A1 XAU M5 Momentum Split-Entry Repair

Claude, please independently review the new split-entry repair candidate. Be rigorous but constructive: the owner wants a frequent intraday strategy with >50% win rate, positive PF, and average win preferably larger than average loss. Do not rubber-stamp it, but also do not reject it merely because it is not perfect.

Boundary: offline review only. No MT5 runtime, preset, chart, order, or position changes.

Primary files:

- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_SPLIT_ENTRY_REPAIR_2026_07_03.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_SPLIT20_202207_202606.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_SPLIT20_202207_202606.json`
- `xau-usd/xauusd-phase1/scripts/run_a1_xau_m5_momentum_backtest_variants.py`
- `xau-usd/xauusd-phase1/mt5/Experts/A1XauM5MomentumContinuationExecutor.mq5`

What changed:

- Added default-off split-entry controls to the EA.
- Strategy Tester variants explicitly enable split-entry with two broker-valid `0.01` tickets when a single `0.01` position cannot be partially closed.
- Ticket 1 targets `0.7R`; ticket 2 targets `2.0R`; runner can move SL to breakeven after the first target threshold.
- The MT5 report parser was fixed to track multiple open positions FIFO by direction because the old single-open-trade parser undercounted split TP1/RUN exits.

Headline recomposed result, with intentional TP1+runner sibling tickets kept together and overlapping component signals de-duplicated within 4 minutes:

| Candidate | Tickets | Signals | WR | Net USD | PF | Avg Win | Avg Loss | W/L | Active Days | Neg Quarters | Neg Rolling-250 | Top200 | Top300 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| split20 all-three | 4950 | 2475 | 52.16% | +7452.44 | 1.49 | 8.75 | -6.40 | 1.37 | 638 | 0 | 124 | +1827.19 | -127.83 |

Comparison:

| Candidate | Trades/Tickets | Signals | WR | Net USD | PF | W/L | Rolling-250 | Quarters | Top300 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| current pure-causal repair | 3156 | 3156 | 66.00% | +2773.63 | 1.42 | 0.73 | 0 negative | 0 negative | -158.91 |
| split20 all-three | 4950 | 2475 | 52.16% | +7452.44 | 1.49 | 1.37 | 124 negative | 0 negative | -127.83 |

Questions to answer:

1. Recompute the split20 metrics directly from the MT5 report/CSV and verify the parser fix is faithful.
2. Is the split-entry design valid, or does two `0.01` tickets create unacceptable exposure inflation compared with the current primary?
3. Does the split20 all-three result satisfy the owner’s goal better than pure-causal repair, despite lower WR and some negative rolling-250 windows?
4. Is top300 `-127.83` acceptable given top200 is strongly positive and all quarters are positive, or should this remain blocked?
5. Should we forward-demo this as an isolated lane at minimum size, or keep it research-only?
6. If you approve forward demo, provide exact frozen forward-test spec, kill rules, and what must not be changed.
7. If you reject, propose the next repair that can preserve frequency while improving rolling-window robustness.

Return a verdict:

`APPROVE_FOR_ISOLATED_FORWARD_DEMO`, `REVISE`, or `REJECT`.

Please explicitly state whether the two-ticket minimum-lot exposure is acceptable for demo experimentation.

