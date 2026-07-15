# A3 ML Historical Backtest Model Card

Status: TRAINED_RESEARCH_ONLY

## Population

- Training: 346 trades (139 wins, 207 losses).
- Out-of-time validation: 290 trades (132 wins, 158 losses).

## Validation

- ROC AUC: 0.615027
- Brier score: 0.240718 (baseline 0.250846)
- Log loss: 0.675629 (baseline 0.69499)
- Threshold coverage: 0.234483
- Threshold-selected win rate: 0.529412

## Limitations

- The model was trained from MT5 Strategy Tester outcomes, not live fills.
- The source strategies were researched on overlapping historical windows, so validation is out-of-time but not a pristine untouched strategy-development holdout.
- The model is specific to these source families: r1_box_clean_strict_uptrend, r2_pullback_short_h1_confirm.
- Live slippage and execution readiness must remain separate from historical model-fit evidence.
- Dukascopy is an independent quote feed, but it covers the same historical market events as the MT5 labels and is not an independent time holdout.

## Boundary

Research only. Python demo predictions, EA consumption, and broker action remain unauthorized.
