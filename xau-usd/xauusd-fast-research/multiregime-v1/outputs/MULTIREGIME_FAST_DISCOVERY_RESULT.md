# XAUUSD Multi-Regime Fast Discovery V1

- Branch: `codex/xau-multiregime-fast-discovery-v1`
- Base commit: `50bf9b5dbcc563a20254e9041e41ec0762c86f6e`
- Exact period: `2016-07-01T00:00:00+00:00` to `2026-07-01T00:00:00+00:00` (exclusive).
- Data status: `COMPLETE_EXACT_PERIOD`.
- Decision: `MULTIREGIME_V1_ABANDONED_NO_RESCUE`.
- Families admitted to combined portfolio: `NONE`.
- Engineering/deployment authorization: `NOT_AUTHORIZED`.

## Portfolio

| Trades | Trades/year | Median/month | PF | Exp R | Net R | Stress PF | Stress exp R | Stress net R | Floating DD R |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0.00 | 0.0 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## Standalone families

| Family | Trades | PF | Exp R | Net R | Stress PF | Stress exp R | DD R | Gate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| MR_TREND_PULLBACK_CONTINUATION_V1 | 112 | 0.901 | -0.065 | -7.304 | 0.706 | -0.225 | 22.124 | False |
| MR_COMPRESSION_BREAKOUT_V1 | 63 | 0.973 | -0.017 | -1.089 | 0.742 | -0.194 | 8.198 | False |
| MR_FAILED_AUCTION_REVERSAL_V1 | 209 | 0.855 | -0.103 | -21.512 | 0.668 | -0.280 | 26.650 | False |

## Segments

| Scope | Segment | Trades | PF | Exp R | Net R | Stress net R |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| PORTFOLIO | A | 0 | N/A | 0.000 | 0.000 | 0.000 |
| PORTFOLIO | B | 0 | N/A | 0.000 | 0.000 | 0.000 |
| PORTFOLIO | C | 0 | N/A | 0.000 | 0.000 | 0.000 |
| PORTFOLIO | D | 0 | N/A | 0.000 | 0.000 | 0.000 |
| MR_TREND_PULLBACK_CONTINUATION_V1 | A | 66 | 0.634 | -0.268 | -17.716 | -28.349 |
| MR_TREND_PULLBACK_CONTINUATION_V1 | B | 31 | 1.586 | 0.309 | 9.577 | 4.019 |
| MR_TREND_PULLBACK_CONTINUATION_V1 | C | 15 | 1.091 | 0.056 | 0.835 | -0.890 |
| MR_TREND_PULLBACK_CONTINUATION_V1 | D | 0 | N/A | 0.000 | 0.000 | 0.000 |
| MR_COMPRESSION_BREAKOUT_V1 | A | 44 | 1.160 | 0.096 | 4.236 | -3.419 |
| MR_COMPRESSION_BREAKOUT_V1 | B | 16 | 0.535 | -0.333 | -5.325 | -8.476 |
| MR_COMPRESSION_BREAKOUT_V1 | C | 2 | 2.000 | 0.500 | 1.000 | 0.731 |
| MR_COMPRESSION_BREAKOUT_V1 | D | 1 | 0.000 | -1.000 | -1.000 | -1.063 |
| MR_FAILED_AUCTION_REVERSAL_V1 | A | 121 | 1.043 | 0.028 | 3.435 | -17.857 |
| MR_FAILED_AUCTION_REVERSAL_V1 | B | 56 | 0.763 | -0.175 | -9.788 | -20.923 |
| MR_FAILED_AUCTION_REVERSAL_V1 | C | 28 | 0.410 | -0.489 | -13.691 | -17.890 |
| MR_FAILED_AUCTION_REVERSAL_V1 | D | 4 | 0.511 | -0.367 | -1.468 | -1.804 |

## $1,000 account and 100x leverage

- Risk budget per trade: `$5.00` (0.50%).
- Contract-granularity rejects: `105` / `489` (`21.47%`).
- Leverage is used only for margin estimation and does not scale R returns.
- Position risk uses captured native XAUUSD OrderCalcProfit parity; margin uses the broker-captured OrderCalcMargin result on the 100x account.

## Cost and data notes

- Baseline execution uses actual per-bar Bid/Ask spread. Stress uses the development-period P95 spread plus 0.05R slippage.
- Funding uses the broker-observed interest-current swap snapshot frozen before scoring; historical swap-rate changes were not available and are not fabricated.
- M5 sequencing is stop-first on ambiguous bars, stop gaps fill at the worse open, and target gaps fill at the frozen target.
- Segment D is the same-broker Capital.com MT5 tail and is scored without parameter changes.

## Abandonment reasons

- `PORTFOLIO_FREQUENCY_BELOW_120_PER_YEAR`
- `NO_FAMILY_PASSES_STANDALONE_GATES`
- `BASELINE_PORTFOLIO_PF_BELOW_1P20`
- `BASELINE_PORTFOLIO_EXPECTANCY_BELOW_0P05R`
- `STRESS_PORTFOLIO_PF_AT_OR_BELOW_1P00`
- `SEGMENT_D_NEGATIVE_OR_PF_BELOW_1P05`
- `XAUUSD_1000_ACCOUNT_CONTRACT_GRANULARITY_INADEQUATE`

There is no rescue variant for this direction.
