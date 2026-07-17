# XAUUSD COMEX Session-VWAP Specialists V1 Result

Decision: **REJECT_COMEX_SESSION_VWAP_V1**

Research only. No Python prediction, EA, demo, live, or broker authorization is granted.

| Family | Stage | Eligible | Trades | Trades/day | Stress PF | Avg R | Drawdown R | Top five removed R | Gate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `COMEX_VWAP_PULLBACK_CONTINUATION_V1` | fit | True | 59 | 0.190 | 0.601 | -0.320 | 17.735 | -28.173 | FAIL |
| `COMEX_VWAP_PULLBACK_CONTINUATION_V1` | development | False | 70 | 0.226 | 0.759 | -0.181 | 18.868 | -22.052 | INELIGIBLE |
| `COMEX_VWAP_EXHAUSTION_REVERSION_V1` | fit | True | 142 | 0.458 | 0.538 | -0.351 | 51.619 | -56.639 | FAIL |
| `COMEX_VWAP_EXHAUSTION_REVERSION_V1` | development | False | 157 | 0.506 | 0.662 | -0.233 | 43.553 | -43.515 | INELIGIBLE |

## Interpretation

Neither frozen family passed the chronological fit and development firewall. Do not spend time extending the cache for this version.
