# Forex Regime-Specialist Campaign Verdict — 2026-07-27

Status: `NO_PORTFOLIO_FORMED`

Boundary: offline research only. No MT5, broker, account, chart, EA attachment, or order action occurred.

## Outcome

| Specialist | Signals | Trades | PF | Net R | Max DD R | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| R1 USD trend synchronization | 227 | 199 | 0.7717 | -31.7190 | 31.7021 | `REJECTED_STANDALONE` |
| R2 cross-asset compression release | 238 | 222 | 0.7408 | -39.6579 | 41.6356 | `REJECTED_STANDALONE` |

## Chronological Standalone Evidence

### R1 USD trend synchronization

| Window | Trades | PF | Net R | Expectancy R |
| --- | ---: | ---: | ---: | ---: |
| design | 56 | 0.3920 | -27.1020 | -0.4840 |
| validation | 82 | 1.2415 | 12.0073 | 0.1464 |
| adaptive_exam | 61 | 0.6277 | -16.6242 | -0.2725 |

- Top-5%-winner removal net: -51.6919R.
- Additional 0.5-pip round-trip stress net: -36.7924R.

### R2 cross-asset compression release

| Window | Trades | PF | Net R | Expectancy R |
| --- | ---: | ---: | ---: | ---: |
| design | 53 | 0.5584 | -17.5495 | -0.3311 |
| validation | 99 | 0.8191 | -12.1019 | -0.1222 |
| adaptive_exam | 70 | 0.7841 | -10.0064 | -0.1429 |

- Top-5%-winner removal net: -63.6165R.
- Additional 0.5-pip round-trip stress net: -46.2670R.

## Router

- Admitted specialists: none.
- Router decision: `NO_PORTFOLIO_FORMED`.
- Routed trades: 0.
- Routed PF: 0.0000.
- Trades per active FX day: 0.0000 versus the diagnostic target of 1.0.

A failed component was not rescued by combination. If no expert passed standalone admission, no portfolio was formed.

## Interpretation

This campaign applies the Gold regime-specialist discipline, but it does not assume that the Gold result or these Forex mechanisms are valid. The frozen thresholds were evaluated once. No outcome-driven repair is included in this verdict.

All historical windows are development evidence. Even a research survivor would require a separately preregistered confirmation and broker-authoritative parity work before any demo discussion.

## Reproduction

Run from the repository root with the project environment that provides pandas, NumPy, and PyArrow:

```powershell
python run_fx_regime_specialists.py
```

Preregistration hashes verified: `{'FOREX_REGIME_SPECIALIST_CAMPAIGN_PREREG_2026_07_27.md': '3a946e24fdc9991fb4fc14961d2b3c8354c8212bfe0c60be18227faa9691ee79', 'config/frozen_campaign.json': '7fee4e0e8995fd98319da91d21f1305a756f2b26d07564a1e41d5ccd602c6a3c'}`.
Frozen config SHA-256: `7fee4e0e8995fd98319da91d21f1305a756f2b26d07564a1e41d5ccd602c6a3c`.
