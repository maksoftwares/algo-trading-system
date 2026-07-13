# A1 XAUUSD Extended-Horizon Exact-MT5 Development Backtests

Generated UTC: `2026-07-10T22:21:29.007796Z`

These are development-data diagnostics. They are not an untouched holdout and authorize no broker action.

| Window | Trades | WR% | W/L | PF | Net USD | Stress net | Max closed DD | +6M rolls | +12M rolls |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `five_year` | 750 | 48.53 | 2.6411 | 2.4905 | 9306.92 | 9081.92 | 889.69 | 45/55 | 44/49 |
| `ten_year` | 1371 | 46.17 | 2.5538 | 2.1905 | 11321.16 | 10909.86 | 889.69 | 76/115 | 87/109 |

## Source Attribution

| Window | Source | Trades | PF | Net | Closed DD | MT5 equity DD |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `five_year` | `h4_d1_long_best_box2_atr80` | 156 | 2.9299 | 6823.25 | 866.37 | 1 733.37 (25.41%) |
| `five_year` | `r1_h1_pullback_long_v1` | 444 | 1.8139 | 1595.67 | 171.62 | 198.90 (11.94%) |
| `five_year` | `r2_continuation_short_v1` | 57 | 2.9081 | 589.46 | 41.85 | 100.07 (6.93%) |
| `five_year` | `r2_pullback_rejection_short_v1` | 93 | 1.6801 | 298.54 | 114.50 | 128.00 (12.69%) |
| `ten_year` | `h4_d1_long_best_box2_atr80` | 307 | 2.4968 | 8159.08 | 866.37 | 1 733.37 (21.25%) |
| `ten_year` | `r1_h1_pullback_long_v1` | 830 | 1.7223 | 2183.21 | 171.62 | 198.90 (8.83%) |
| `ten_year` | `r2_continuation_short_v1` | 58 | 2.7999 | 577.52 | 41.85 | 100.07 (6.99%) |
| `ten_year` | `r2_pullback_rejection_short_v1` | 179 | 1.5791 | 428.62 | 120.16 | 128.00 (11.24%) |

## Execution defects

| Window | Source | Time | Retcode | Description |
| --- | --- | --- | ---: | --- |
| `five_year` | `h4_d1_long_best_box2_atr80` | 2024.10.29 21:00:00 | 10018 | market closed |
| `five_year` | `h4_d1_long_best_box2_atr80` | 2025.03.19 21:00:00 | 10018 | market closed |
| `five_year` | `h4_d1_long_best_box2_atr80` | 2025.03.27 21:00:00 | 10018 | market closed |
| `ten_year` | `h4_d1_long_best_box2_atr80` | 2024.10.29 21:00:00 | 10018 | market closed |
| `ten_year` | `h4_d1_long_best_box2_atr80` | 2025.03.19 21:00:00 | 10018 | market closed |
| `ten_year` | `h4_d1_long_best_box2_atr80` | 2025.03.27 21:00:00 | 10018 | market closed |

## Interpretation boundary

Any recorded order-send failure is a hard NO-GO and is not removed from the evidence. Portfolio drawdown above is closed-equity drawdown after the frozen five-minute ownership rule. Source-level MT5 equity drawdown is retained from each native report. A true integrated portfolio equity-DD result still requires the separately governed integrated MT5 harness.
