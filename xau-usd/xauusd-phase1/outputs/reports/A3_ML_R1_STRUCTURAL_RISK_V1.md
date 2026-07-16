# A3 ML R1 Structural Risk V1

Classification: `STRUCTURAL_RISK_FAIL`

Known-history portfolio engineering only. Demo and broker action remain disabled.

## Profiles

| Profile | Accepted | Stress net | PF | Exact floating DD | Max positions | Max stop risk |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Frozen baseline | 310 | 10120.70 | 2.7496 | 1284.17 (10.83%) | 13 | 1225.62 |
| Demo guard | 215 | 2716.52 | 1.8181 | 783.75 (6.93%) | 8 | 224.38 |

## Controlled Diagnostics

- Rejected: `95` ({'MAX_CONCURRENT_POSITIONS': 2, 'MAX_TOTAL_INITIAL_RISK': 18, 'MAX_TRADE_INITIAL_RISK': 75})
- Top episode profit share: `0.3295`
- Net after removing top three episodes: `$1058.74`
- Positive rolling six-month share: `0.5826`
- Monte Carlo ruin probability: `0.0000`
- Monte Carlo P(DD >= 15%): `0.0010`

## Capital Observations

- `$1000.00`: DD `37.43%`, minimum equity `$852.89`, margin call `NO`
- `$5000.00`: DD `12.43%`, minimum equity `$4852.89`, margin call `NO`
- `$10000.00`: DD `6.93%`, minimum equity `$9852.89`, margin call `NO`

## Gates

- `source_reconciles`: PASS
- `baseline_admits_all_source_trades`: PASS
- `baseline_final_stress_net_reconciles`: PASS
- `tick_exit_prices_reconcile`: PASS
- `baseline_floating_drawdown`: PASS
- `controlled_stress_profit_factor`: PASS
- `controlled_trade_retention`: PASS
- `controlled_net_retention`: FAIL
- `controlled_floating_drawdown`: PASS
- `controlled_episode_concentration`: PASS
- `controlled_top_three_removed_positive`: PASS
- `controlled_six_month_stability`: FAIL
- `controlled_monte_carlo_ruin`: PASS
- `controlled_monte_carlo_drawdown`: PASS
- `risk_limits_respected`: PASS
- `no_margin_call_at_10k`: PASS
- `authorization_closed`: PASS

No authorization flag changed.
