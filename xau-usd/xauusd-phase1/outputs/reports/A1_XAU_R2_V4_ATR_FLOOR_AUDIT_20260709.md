# A1 XAU R2 V4 ATR Floor Audit

Date: 2026-07-09

Scope: report-only audit from existing exact-MT5 V1/V4 signal, order, and trade CSVs. No new MT5 test and no strategy change.

## Verdict

The ATR floor did what V4 intended: it blocked a very large set of low-ATR bars and narrowed R2 continuation to high-participation downside conditions. The tradeoff is severe concentration: V4 quality improved, but standalone evidence is mostly recent 2026 exposure.

## ATR Floor Block Counts

| Variant | Signal rows | ATR-floor blocks | Block % | Apr 2026 | May 2026 | Jun 2026 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `r2_impulse_body45_atr45` | 282643 | 243317 | 86.09% | 1823 | 2431 | 1972 |
| `r2_impulse_body45_atr50` | 282643 | 250039 | 88.46% | 2414 | 3059 | 2650 |
| `r2_impulse_body45_atr45_daily_loss10` | 282643 | 243317 | 86.09% | 1823 | 2431 | 1972 |

## V1 Trade Impact By ATR Floor

This table is a V1 executed-trade postfilter audit, not a replacement for the exact V4 run. Exact V4 can differ slightly because skipped low-ATR trades can change one-position/open-slot sequencing.

| ATR floor | Kept trades | Kept WR | Kept PF | Kept net | Removed trades | Removed WR | Removed PF | Removed net |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 4.50 | 58 | 56.90% | 2.8234 | 580.20 | 396 | 33.33% | 1.0774 | 86.23 |
| 5.00 | 55 | 58.18% | 2.9532 | 575.36 | 399 | 33.33% | 1.0800 | 91.07 |

## May/June Analog On V1 Trades

| ATR floor | May kept net | May removed net | June kept net | June removed net |
| ---: | ---: | ---: | ---: | ---: |
| 4.50 | 12.98 | -29.11 | 522.85 | 105.94 |
| 5.00 | 12.98 | -29.11 | 518.01 | 110.78 |

## V1 WOULD_SIGNAL ATR Distribution By Year

| Year | Candidates | P25 ATR | Median ATR | P75 ATR | <=4.50 pct | <=5.00 pct |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2022 | 588 | 0.85 | 1.13 | 1.48 | 100.00% | 100.00% |
| 2023 | 1012 | 0.74 | 1.07 | 1.52 | 99.90% | 100.00% |
| 2024 | 971 | 1.15 | 1.55 | 2.25 | 94.64% | 96.50% |
| 2025 | 888 | 1.77 | 2.70 | 4.23 | 77.70% | 82.09% |
| 2026 | 422 | 4.52 | 6.38 | 9.75 | 24.41% | 31.52% |

## V1 Executed Trade ATR Distribution By Year

| Year | Trades | P25 ATR | Median ATR | P75 ATR | <=4.50 pct | <=5.00 pct |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2022 | 191 | 0.81 | 1.03 | 1.38 | 100.00% | 100.00% |
| 2023 | 160 | 0.70 | 0.95 | 1.41 | 100.00% | 100.00% |
| 2024 | 17 | 0.96 | 1.31 | 2.45 | 100.00% | 100.00% |
| 2026 | 86 | 4.29 | 5.70 | 7.10 | 32.56% | 36.05% |

## Key Interpretation

- V4's ATR floor is causally clean as a pre-entry participation gate.
- The audit supports the reviewer view: ATR45/ATR50 are plausible diagnostics, not final production thresholds.
- The floor removes many V1 trades and should not be tuned further inside R2.
- R2 should now remain frozen as V1 raw control plus V4 quality shadow candidates.
- New market coverage should come from a separate chop / failed-breakdown specialist, not another R2 filter.

## Artifacts

- JSON payload: `xau-usd\xauusd-phase1\outputs\reports\A1_XAU_R2_V4_ATR_FLOOR_AUDIT_20260709.json`
- V1 component source: `xau-usd\xauusd-phase1\outputs\reports\A1_XAU_R2_CONTINUATION_SHORT_V1_EXACT_20260709_MT5_COMPONENTS.json`
- V4 component source: `xau-usd\xauusd-phase1\outputs\reports\A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_MT5_COMPONENTS.json`
