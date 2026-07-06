# A1 XAU H4/D1 Stop-Ceiling One Iteration

Generated UTC: `2026-07-06T08:49:50Z`

Scope: one exact-MT5 Strategy Tester run in the isolated backtest root, followed by exact-ledger recomposition. No live/demo runtime, chart, preset, order, position, or broker state was changed.

Status: `REJECT_STOPCEIL3000_BREAKS_OR_FAILS_FRONTIER`
Preregistration: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\A1_XAU_H4_D1_STOPCEIL3000_ONE_ITERATION_PREREG_2026_07_06.md`

## Standalone MT5 Component

| Variant | Trades | WR% | W/L | Active% | PF | Net USD | Max DD | Last12 WR/WL/Active |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `long_box2_atr80_range150_body035_stopceil3000` | 70 | 54.29 | 2.0684 | 5.56 | 2.4562 | 1039.02 | 198.54 | 100.00/0.0000/0.38 |

## Recomposed Hybrid

| Book | Signals | WR% | W/L | Active% | PF | Net USD | Max DD | Positive weeks% | Worst week | Positive months% | Worst month | June 2026 | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `baseline_f67_h16_no_f33` | 3751 | 50.23 | 2.0002 | 86.39 | 2.0336 | 22294.46 | 1583.72 | 58.65 | -609.41 | 60.42 | -1055.98 | -222.84 | `CORE_SHAPE_ACTIVITY_GAP_WEEKLY_NOT_FIXED` |
| `replace_h4_best_with_stopceil3000` | 3638 | 50.25 | 1.9408 | 85.91 | 1.9754 | 17760.44 | 727.02 | 59.62 | -429.39 | 70.83 | -520.20 | 368.84 | `REJECT_BREAKS_CORE_SHAPE` |

## Tail Reliance

| Book | Ex-top-1% removed | Ex-top-1% W/L | Ex-top-1% PF | Ex-top-1% net | Ex-top-2% removed | Ex-top-2% W/L | Ex-top-2% PF | Ex-top-2% net |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `baseline` | 19 | 1.7798 | 1.7913 | 17068.48 | 38 | 1.6194 | 1.6133 | 13228.44 |
| `replacement` | 19 | 1.6899 | 1.7021 | 12784.42 | 37 | 1.5486 | 1.5443 | 9911.26 |

## Verdict

The replacement did not improve the current frontier enough. This argues against simple stop-ceiling filtering as the fast path; the next useful move is a true stop/risk geometry edit, not more ceiling filters.

## Artifacts

- md: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A1_XAU_H4_D1_STOPCEIL3000_ONE_ITERATION_202207_202606.md`
- json: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A1_XAU_H4_D1_STOPCEIL3000_ONE_ITERATION_202207_202606.json`
- replacement_kept_csv: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A1_XAU_H4_D1_STOPCEIL3000_ONE_ITERATION_202207_202606_REPLACEMENT_KEPT.csv`
- replacement_dropped_csv: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A1_XAU_H4_D1_STOPCEIL3000_ONE_ITERATION_202207_202606_REPLACEMENT_DROPPED.csv`
- repo_short_mt5_trade_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_D1_STOPCEIL3000_ONE_ITERATION_MT5_TRADES.csv`
- mt5_trade_csv: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_d1_stopceil3000_one_iteration_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_D1_STOPCEIL3000_ONE_ITERATION_202207_202606_XAUUSD_M5_long_box2_atr80_range150_body035_stopceil3000_trades.csv`
- mt5_html_report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_d1_stopceil3000_one_iteration_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_D1_STOPCEIL3000_ONE_ITERATION_202207_202606_XAUUSD_M5_long_box2_atr80_range150_body035_stopceil3000.htm`
