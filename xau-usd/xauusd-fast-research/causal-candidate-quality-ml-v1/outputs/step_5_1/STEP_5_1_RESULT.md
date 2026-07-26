# Step 5.1 AED Account-Currency Correction

Decision: `STEP_5_1_AED_PORTFOLIO_GATE_FAIL`

Starting account equity: `3627.19 AED`.
USD/AED profit conversion: `3.671500`; loss conversion: `3.674000`.

| Window | Entries | Entries/weekday | Net AED | PF | Floating DD AED |
|---|---:|---:|---:|---:|---:|
| FULL | 389 | 0.090 | 879.24 | 1.241 | 393.61 |
| 10Y | 293 | 0.112 | 17.62 | 1.007 | 393.61 |
| 5Y | 0 | 0.000 | 0.00 | n/a | 0.00 |
| 2Y | 0 | 0.000 | 0.00 | n/a | 0.00 |
| 1Y | 0 | 0.000 | 0.00 | n/a | 0.00 |
| 6M | 0 | 0.000 | 0.00 | n/a | 0.00 |
| 3M | 0 | 0.000 | 0.00 | n/a | 0.00 |

Acceptance checks: `5` / `18` passed.
Failed checks: `profit_factor_1Y, profit_factor_2Y, profit_factor_5Y, profit_factor_10Y, net_account_1Y, net_account_2Y, net_account_5Y, entries_per_weekday_1Y, entries_per_weekday_2Y, entries_per_weekday_5Y, positive_six_month_blocks, top_winners_removed_net_5Y, top_winners_removed_net_10Y`.

This correction supersedes Step 5 only for AED account-specific risk and drawdown claims. No broker action or runtime change was made.
