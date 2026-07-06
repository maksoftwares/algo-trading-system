# Forex MT5 USDJPY London120 M15 Strict Review Packet

Date: 2026-07-04
Status: **WATCHLIST ONLY / DEMO BLOCKED**
Scope: **Forex only, USDJPY only, actual MT5 Strategy Tester evidence only**

## Candidate

- Symbol: `USDJPY`
- Variant: `london120_break_m15`
- EA: `forex-research/mt5/Experts/ForexSessionBreakoutScout.mq5`
- Logic: broker-server `06:00-08:00` range, M15 breakout decisions from `08:00` for four hours, both directions, RR `1.00`, fixed `0.01` lot.
- Discovery discipline: no long-only promotion, no blocked-hour tuning, no RR/session retune after discovery.

## Verdict

The Claude strict review is accepted. The candidate remains the best Forex diversification lead, but it is **not demo-ready**. The strongest fact is broad 2020-2026 consistency; the decisive weakness is recent-regime softness.

## Independent Manual P&L Basis

All numbers below are recomputed from the MT5 trade CSV entry/exit prices, not copied from the MT5 report. USDJPY manual P&L formula:

```text
direction * (exit_price - entry_price) * lots * 100000 / exit_price
```

Slippage stress subtracts extra round-trip pip cost per trade:

```text
extra_pips * 0.01 * lots * 100000 / exit_price
```

## Core Windows

| Window | Trades | WR | Manual net | Manual PF | Gross profit | Gross loss |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2022-2026 MT5 run | 521 | 57.77% | $232.06 | 1.3918 | $824.39 | $592.33 |
| 2020-2026 MT5 run | 859 | 56.00% | $289.45 | 1.3028 | $1,245.24 | $955.79 |
| 2018-2026 MT5 run | 1144 | 53.50% | $273.16 | 1.2231 | $1,497.45 | $1,224.29 |
| Trailing 12M 2025-06-30 to 2026-06-29 | 145 | 53.10% | $23.54 | 1.1505 | $180.01 | $156.47 |
| Trailing 18M 2024-12-28 to 2026-06-29 | 222 | 53.15% | $40.72 | 1.1524 | $307.98 | $267.26 |
| Recent 2025-2026 to 2026-07-02 | 218 | 52.75% | $33.20 | 1.1247 | $299.52 | $266.32 |

## Slippage Stress

### 2022-2026

| Extra round-trip slippage | Trades | WR | Net | PF | Gross profit | Gross loss |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.0 pip | 521 | 57.77% | $232.06 | 1.3918 | $824.39 | $592.33 |
| 0.3 pip | 521 | 57.77% | $221.48 | 1.3711 | $818.27 | $596.79 |
| 0.5 pip | 521 | 57.77% | $214.42 | 1.3575 | $814.19 | $599.76 |
| 1.0 pip | 521 | 57.77% | $196.79 | 1.3241 | $803.99 | $607.20 |

### 2020-2026

| Extra round-trip slippage | Trades | WR | Net | PF | Gross profit | Gross loss |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.0 pip | 859 | 56.00% | $289.45 | 1.3028 | $1,245.24 | $955.79 |
| 0.3 pip | 859 | 56.00% | $269.65 | 1.2796 | $1,234.21 | $964.56 |
| 0.5 pip | 859 | 56.00% | $256.44 | 1.2643 | $1,226.85 | $970.41 |
| 1.0 pip | 859 | 56.00% | $223.43 | 1.2268 | $1,208.47 | $985.04 |

### 2018-2026

| Extra round-trip slippage | Trades | WR | Net | PF | Gross profit | Gross loss |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.0 pip | 1144 | 53.50% | $273.16 | 1.2231 | $1,497.45 | $1,224.29 |
| 0.3 pip | 1144 | 53.50% | $245.56 | 1.1985 | $1,482.83 | $1,237.27 |
| 0.5 pip | 1144 | 53.50% | $227.16 | 1.1823 | $1,473.08 | $1,245.92 |
| 1.0 pip | 1144 | 53.50% | $181.16 | 1.1429 | $1,448.72 | $1,267.56 |

### Trailing 12M

| Extra round-trip slippage | Trades | WR | Net | PF | Gross profit | Gross loss |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.0 pip | 145 | 53.10% | $23.54 | 1.1505 | $180.01 | $156.47 |
| 0.3 pip | 145 | 53.10% | $20.73 | 1.1314 | $178.52 | $157.79 |
| 0.5 pip | 145 | 53.10% | $18.85 | 1.1188 | $177.52 | $158.67 |
| 1.0 pip | 145 | 53.10% | $14.16 | 1.0880 | $175.03 | $160.87 |

### Recent 2025-2026

| Extra round-trip slippage | Trades | WR | Net | PF | Gross profit | Gross loss |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.0 pip | 218 | 52.75% | $33.20 | 1.1247 | $299.52 | $266.32 |
| 0.3 pip | 218 | 52.75% | $28.92 | 1.1078 | $297.26 | $268.35 |
| 0.5 pip | 218 | 52.75% | $26.06 | 1.0966 | $295.76 | $269.70 |
| 1.0 pip | 218 | 52.75% | $18.92 | 1.0693 | $291.99 | $273.07 |

## Manual vs MT5 CSV Check

| Window | Trades | Manual net | MT5 CSV net | Delta | Max abs trade delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| full_2022_2026 | 521 | $232.06 | $232.03 | $0.03 | $0.01 |
| full_2020_2026 | 859 | $289.45 | $289.44 | $0.01 | $0.01 |
| full_2018_2026 | 1144 | $273.16 | $273.09 | $0.07 | $0.01 |

## MT5 Tester Proof

- Runner writes `Period=M5`, `Optimization=0`, `Model=0` every tick in `forex-research/scripts/run_forex_mt5_frequency_scout.py` lines `416`, `417`, `418`.
- Full 2018-2026 MT5 report metadata: History Quality `100%`, Bars `632969`, Ticks `200044273`, MT5 PF `1.21`, MT5 net `255.26`, MT5 trades `1144`.

## EA / Methodology Audit

- Tester-only guard: `MQL_TESTER` check at EA line `523`.
- New-bar gate: `OnTick()` at EA line `556` calls completed-signal-bar evaluation.
- Completed-bar signal function starts at EA line `408`.
- Session range builder starts at EA line `314` and range ATR guard is at line `389`.
- Risk/execution guards include own-position guard line `451`, daily cap line `456`, spread guard line `466`.
- Order sends are at EA lines `510` and `512`, inside Strategy Tester only.

Audit read: **PASS for research/tester use**, still requiring external source review before any demo spec.

## Survivorship Ledger

Minimum logged raw session-breakout denominator: **40 cells**. This is larger than the reviewer shorthand `~25-30`, so the survivorship discount remains fully valid.

| Artifact | Cells | Symbols | SHA256 |
| --- | ---: | --- | --- |
| `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_CURRENT_2024_2026_SESSION_BREAKOUT_M15_RAW_FREQ_SWEEP.json` | 12 | `EURUSD,GBPUSD,USDJPY` | `673005789f06bb8fb5b5b8b63e6e19f913642f33a06823471846f7060172e333` |
| `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_CURRENT_2024_2026_SESSION_BREAKOUT_M30_RAW_FREQ_FIRST.json` | 12 | `EURUSD,GBPUSD,USDJPY` | `cf79673e32dce8dc87aa580e18d8d4d514d2838c80ba8b10f49d1c88ff889a03` |
| `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_CURRENT_2024_2026_EXTRA_MAJORS_SESSION_BREAKOUT_M15_RAW_FREQ_SWEEP.json` | 16 | `AUDUSD,NZDUSD,USDCAD,USDCHF` | `6c1cd3e207831dcddaef6563cd8c3c29dc6a45051c137d76120ccecc6f65f8a7` |

## Alternate-History Validation Status

Dukascopy exact replay is **blocked**, not passed. Local files show USDJPY Dukascopy H1 data only:

- `xau-usd/xauusd-phase0/data/raw/dukascopy/USDJPY_H1_20220101_20241231_dukascopy.csv` exists: `True`
- `xau-usd/xauusd-phase0/data/processed/bars/dukascopy/USDJPY/H1/USDJPY_dukascopy_H1_20220103_20241231.csv` exists: `True`
- Local Dukascopy M15 folder exists: `False`
- Local Dukascopy M5 folder exists: `False`

The frozen candidate needs M15 signal bars and M5/every-tick execution behavior. Do not call any H1-only replay a valid Dukascopy alternate-history test.

Capital.com M15/M5 raw files do exist in the old phase0 tree, but that is not an alternate-vendor validation.

## Gate Read

- Demo-ready: **NO**.
- Main blocker: trailing/recent standalone edge is not strong enough yet under the owner's recency priority.
- Trailing 12M PF is `1.1505` with net `$23.54` over `145` trades.
- Trailing 12M after `+0.5` pip round-trip stress: PF `1.1188`, net `$18.85`.
- Full 2022-2026 after `+0.5` pip round-trip stress: PF `1.3575`, net `$214.42`.

## Next Actions

1. Acquire or export USDJPY Dukascopy M15/M5/tick data, then replay the frozen rule without tuning.
2. Pre-declare exactly one range-quality guard threshold and hash the spec before running one MT5 2018-2026 test.
3. Keep monthly frozen-rule recent-regime watch; demo discussion opens only if trailing-12M PF is at least `1.15` and net remains positive after `+0.5` pip stress.

Artifacts:

- JSON: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_USDJPY_LONDON120_M15_STRICT_REVIEW_PACKET_2026_07_04.json`
- Markdown: `forex-research/docs/FOREX_MT5_USDJPY_LONDON120_M15_STRICT_REVIEW_PACKET_2026_07_04.md`
