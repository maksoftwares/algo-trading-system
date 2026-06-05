# Phase 2 Demo Shadow Filter Report

Overall status: SHADOW_ONLY_REVIEW_READY

This report measures a proposed filter without changing MT5, EA settings, orders, charts, or live behavior.

Source terminal: `C:\Program Files\MetaTrader 5\terminal64.exe`
Account: `1025742 / Capital.ComMena-Demo / AED`
History window: `2026-06-01 00:00:00` to `2026-06-04 17:46:50`

## Shadow Policy

- Keep all EAs running unchanged.
- Measure a hypothetical block for `session_extreme_retest_v0`.
- Measure a hypothetical block for XAUUSD trades entered in Morning `06:00-11:59` or Afternoon `12:00-15:59`.
- Keep evening/night XAUUSD and all non-XAUUSD trades unless blocked by the provisional-EA rule above.

## Result

| View | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Baseline duplicate-hidden | 125 | 2 | 48 | 77 | 38.40% | -56.41 | 0.96 | 27.12 | -17.64 |
| Would keep | 61 | 2 | 29 | 32 | 47.54% | 318.11 | 1.62 | 28.73 | -16.10 |
| Would block | 64 | 0 | 19 | 45 | 29.69% | -374.52 | 0.56 | 24.65 | -18.73 |

Shadow delta versus baseline: `374.52 AED`.

## Block Reason Counts

| Reason | Count |
|---|---:|
| BLOCK_PROVISIONAL_SESSION_EXTREME_RETEST | 32 |
| BLOCK_XAUUSD_MORNING_AFTERNOON | 32 |

## Would Keep by EA

| candidate | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| breakout_retest | 31 | 2 | 15 | 16 | 48.39% | 281.37 | 2.98 | 28.25 | -8.90 |
| swing_breakout_retest_v0 | 3 | 0 | 1 | 2 | 33.33% | 60.80 | 20.49 | 63.92 | -1.56 |
| symbol_normalized_round_retest_v0 | 27 | 0 | 13 | 14 | 48.15% | -24.06 | 0.93 | 26.58 | -26.40 |

## Would Block by EA

| candidate | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| session_extreme_retest_v0 | 32 | 0 | 11 | 21 | 34.38% | -28.21 | 0.90 | 22.63 | -13.20 |
| breakout_retest | 9 | 0 | 3 | 6 | 33.33% | -32.92 | 0.73 | 29.13 | -20.05 |
| symbol_normalized_round_retest_v0 | 23 | 0 | 5 | 18 | 21.74% | -313.39 | 0.30 | 26.40 | -24.74 |

## Would Block by Symbol and Time

| symbol | time_bucket | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| XAUUSD | Evening 16:00-19:59 | 4 | 0 | 2 | 2 | 50.00% | 13.95 | 1.28 | 32.33 | -25.35 |
| EURUSD | Night 20:00-05:59 | 3 | 0 | 2 | 1 | 66.67% | 7.15 | 2.87 | 5.49 | -3.83 |
| EURUSD | Afternoon 12:00-15:59 | 2 | 0 | 1 | 1 | 50.00% | 1.84 | 1.50 | 5.51 | -3.67 |
| USDJPY | Night 20:00-05:59 | 1 | 0 | 0 | 1 | 0.00% | -1.60 | 0.00 | n/a | -1.60 |
| USDJPY | Afternoon 12:00-15:59 | 3 | 0 | 1 | 2 | 33.33% | -2.58 | 0.40 | 1.72 | -2.15 |
| EURUSD | Evening 16:00-19:59 | 1 | 0 | 0 | 1 | 0.00% | -3.64 | 0.00 | n/a | -3.64 |
| XAUUSD | Night 20:00-05:59 | 7 | 0 | 1 | 6 | 14.29% | -64.71 | 0.44 | 50.19 | -19.15 |
| XAUUSD | Afternoon 12:00-15:59 | 21 | 0 | 6 | 15 | 28.57% | -79.90 | 0.69 | 29.98 | -17.32 |
| XAUUSD | Morning 06:00-11:59 | 22 | 0 | 6 | 16 | 27.27% | -245.03 | 0.39 | 25.90 | -25.03 |

## Boundary

- Shadow-only report; not enforced.
- Does not authorize canonical Phase 2.
- Does not change demo executor behavior.
- Requires larger sample before any router/session filter decision.
