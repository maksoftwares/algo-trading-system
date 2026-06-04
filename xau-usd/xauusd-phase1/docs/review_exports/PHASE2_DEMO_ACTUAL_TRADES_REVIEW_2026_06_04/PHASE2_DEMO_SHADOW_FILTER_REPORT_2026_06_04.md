# Phase 2 Demo Shadow Filter Report

Overall status: SHADOW_ONLY_REVIEW_READY

This report measures a proposed filter without changing MT5, EA settings, orders, charts, or live behavior.

Source terminal: `C:\Program Files\MetaTrader 5\terminal64.exe`
Account: `1025742 / Capital.ComMena-Demo / AED`
History window: `2026-06-01 00:00:00` to `2026-06-04 11:03:11`

## Shadow Policy

- Keep all EAs running unchanged.
- Measure a hypothetical block for `session_extreme_retest_v0`.
- Measure a hypothetical block for XAUUSD trades entered in Morning `06:00-11:59` or Afternoon `12:00-15:59`.
- Keep evening/night XAUUSD and all non-XAUUSD trades unless blocked by the provisional-EA rule above.

## Result

| View | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Baseline duplicate-hidden | 116 | 3 | 43 | 73 | 37.07% | -135.38 | 0.90 | 27.02 | -17.77 |
| Would keep | 57 | 2 | 27 | 30 | 47.37% | 279.86 | 1.55 | 29.26 | -17.01 |
| Would block | 59 | 1 | 16 | 43 | 27.12% | -415.24 | 0.47 | 23.23 | -18.30 |

Shadow delta versus baseline: `415.24 AED`.

## Block Reason Counts

| Reason | Count |
|---|---:|
| BLOCK_PROVISIONAL_SESSION_EXTREME_RETEST | 31 |
| BLOCK_XAUUSD_MORNING_AFTERNOON | 29 |

## Would Keep by EA

| candidate | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| breakout_retest | 29 | 1 | 14 | 15 | 48.28% | 247.07 | 2.78 | 27.56 | -9.25 |
| swing_breakout_retest_v0 | 2 | 0 | 1 | 1 | 50.00% | 61.95 | 32.45 | 63.92 | -1.97 |
| symbol_normalized_round_retest_v0 | 26 | 1 | 12 | 14 | 46.15% | -29.16 | 0.92 | 28.37 | -26.40 |

## Would Block by EA

| candidate | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| session_extreme_retest_v0 | 31 | 0 | 10 | 21 | 32.26% | -66.47 | 0.76 | 21.07 | -13.20 |
| breakout_retest | 8 | 0 | 2 | 6 | 25.00% | -67.14 | 0.44 | 26.58 | -20.05 |
| symbol_normalized_round_retest_v0 | 20 | 1 | 4 | 16 | 20.00% | -281.63 | 0.28 | 26.94 | -24.34 |

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
| XAUUSD | Afternoon 12:00-15:59 | 19 | 0 | 4 | 15 | 21.05% | -152.38 | 0.41 | 26.85 | -17.32 |
| XAUUSD | Morning 06:00-11:59 | 19 | 1 | 5 | 14 | 26.32% | -213.27 | 0.38 | 26.24 | -24.60 |

## Boundary

- Shadow-only report; not enforced.
- Does not authorize canonical Phase 2.
- Does not change demo executor behavior.
- Requires larger sample before any router/session filter decision.
