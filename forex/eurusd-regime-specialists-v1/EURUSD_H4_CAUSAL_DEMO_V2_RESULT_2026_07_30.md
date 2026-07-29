# EURUSD causal demo V2 historical result

Status: **NO_STANDALONE_COMPONENT_PASSED**

| Variant | Trades | PF | +0.5 pip PF | Latest-12M PF | Failed checks |
|---|---:|---:|---:|---:|---|
| SHORT_CHOP_H60_PROTECTED | 349 | 1.200 | 1.145 | 1.985 | positive_active_month_share |
| SHORT_CHOP_M15_NEXT_CLOSE | 312 | 1.149 | 1.097 | 1.485 | each_chronological_block_profit_factor, positive_active_month_share, maximum_closed_trade_drawdown |
| SHORT_CHOP_M15_RETEST_REJECT_4 | 209 | 1.172 | 1.119 | 1.549 | each_chronological_block_profit_factor |
| SHORT_COMPRESSION_H60_PROTECTED | 158 | 1.247 | 1.189 | 1.007 | each_chronological_block_profit_factor, positive_active_month_share |
| SHORT_COMPRESSION_M15_NEXT_CLOSE | 167 | 1.224 | 1.167 | 1.534 | positive_active_month_share, maximum_closed_trade_drawdown |
| SHORT_COMPRESSION_M15_RETEST_REJECT_4 | 97 | 1.272 | 1.214 | 3.010 | each_chronological_block_profit_factor, positive_active_month_share |
| LONG_CHOP_M15_IMMEDIATE | 435 | 0.822 | 0.784 | 1.087 | full_profit_factor, extra_0p5pip_profit_factor, each_chronological_block_profit_factor, positive_active_month_share, top_5pct_winners_removed_profit_factor, maximum_closed_trade_drawdown |
| LONG_CHOP_M15_NEXT_CLOSE | 301 | 0.821 | 0.784 | 1.960 | full_profit_factor, extra_0p5pip_profit_factor, each_chronological_block_profit_factor, positive_active_month_share, top_5pct_winners_removed_profit_factor, maximum_closed_trade_drawdown |
| LONG_CHOP_M15_RETEST_REJECT_4 | 208 | 0.838 | 0.800 | 0.926 | full_profit_factor, extra_0p5pip_profit_factor, each_chronological_block_profit_factor, latest_12_month_profit_factor, latest_12_month_net_r, positive_active_month_share, top_5pct_winners_removed_profit_factor, maximum_closed_trade_drawdown |
| LONG_COMPRESSION_M15_IMMEDIATE | 253 | 0.855 | 0.815 | 1.081 | full_profit_factor, extra_0p5pip_profit_factor, each_chronological_block_profit_factor, positive_active_month_share, top_5pct_winners_removed_profit_factor, maximum_closed_trade_drawdown |
| LONG_COMPRESSION_M15_NEXT_CLOSE | 193 | 0.997 | 0.951 | 1.027 | full_profit_factor, extra_0p5pip_profit_factor, each_chronological_block_profit_factor, positive_active_month_share, top_5pct_winners_removed_profit_factor, maximum_closed_trade_drawdown |
| LONG_COMPRESSION_M15_RETEST_REJECT_4 | 116 | 0.894 | 0.852 | 0.929 | full_profit_factor, extra_0p5pip_profit_factor, each_chronological_block_profit_factor, latest_12_month_profit_factor, latest_12_month_net_r, positive_active_month_share, top_5pct_winners_removed_profit_factor |

No portfolio was assembled and no demo promotion is allowed.
