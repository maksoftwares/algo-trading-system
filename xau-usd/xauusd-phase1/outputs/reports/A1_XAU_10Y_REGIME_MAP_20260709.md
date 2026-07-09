# A1 XAUUSD 10-Year Regime Map

Generated UTC: `2026-07-09T07:24:28Z`
Analysis window: `2016-07-09` to `2026-07-09`

This is a market-regime analysis, not a strategy backtest. It uses daily OHLC bars to map regimes, then references the exact-MT5 Router V1 recent snapshot as a 2026 cross-check.

## Data Sources

- Historical backbone: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase0\data\processed\bars\capital_com\XAUUSD\D1\XAUUSD_capital_com_D1_20160104_20250701.csv`
- MT5 read-only bridge: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\data\ml\a3_meta_v1\c02\xauusd_c02_multiacct_202607090713_gdb8b1169_c9221d066\raw\A1\bars\XAUUSD_D1.csv`
- MT5 bridge export report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\outputs\reports\C02_BAR_TICK_EXPORT_REPORT_REGIME_20260709.md`
- Recent exact-MT5 router months: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A1_XAU_RECENT_REGIME_SNAPSHOT_AUDIT_20260708_MONTHS.csv`

## Source Cross-Check

| Check | Value |
| --- | ---: |
| `capital_rows` | 2785 |
| `dukascopy_rows` | 3229 |
| `common_dates` | 2740 |
| `median_abs_close_diff` | 0.162 |
| `p95_abs_close_diff` | 2.925 |
| `daily_return_corr` | 0.98999 |

## Classifier Rules

| Regime | Rule |
| --- | --- |
| `shock` | ATR14 percentile >= 95 over a 252-bar window, or a very large one-day / five-day move. This isolates violent volatility bursts before trend labels. |
| `compression` | ATR14 percentile <= 25 and the 20-day high-low range is in the lower 35% of its 252-bar history. |
| `uptrend` | Close > EMA50 > EMA200, EMA50 rising over 20 bars, and 60-day return > +3%. |
| `downtrend` | Close < EMA50 < EMA200, EMA50 falling over 20 bars, and 60-day return < -3%. |
| `transition` | Directional 20-day or 60-day movement is material, but the EMA stack has not confirmed a clean trend. |
| `chop` | Default state: mixed EMA structure, weak directional movement, or range movement without compression. |

## 10-Year Regime Distribution

| Regime | Days | Share % |
| --- | ---: | ---: |
| `uptrend` | 899 | 28.96 |
| `downtrend` | 278 | 8.96 |
| `chop` | 870 | 28.03 |
| `compression` | 494 | 15.91 |
| `shock` | 249 | 8.02 |
| `transition` | 274 | 8.83 |
| `unknown` | 40 | 1.29 |

## Major Regime Episodes

| Start | End | Episode | Dominant | Return % | Read | Specialist implication |
| --- | --- | --- | --- | ---: | --- | --- |
| 2016-07-09 | 2016-09-30 | post-spike compression / range | `compression` (100.00%) | -3.14 | Gold paused after the 2016 upside move; volatility contracted and direction was unreliable. | R3 compression or R4 range; avoid chasing trend continuation. |
| 2016-10-01 | 2016-12-31 | downtrend selloff | `downtrend` (44.87%) | -12.45 | Clean downside repricing into year-end. | R2 short continuation / pullback rejection. |
| 2017-01-01 | 2018-05-31 | broad chop with short trend bursts | `chop` (48.97%) | 13.19 | Range-dominant structure with intermittent upside legs that did not persist cleanly. | R4 range/reclaim first; R1 only when router confirms a clean uptrend sub-state. |
| 2018-06-01 | 2018-09-30 | compression into downtrend | `downtrend` (64.42%) | -8.30 | Low-volatility squeeze resolved into a persistent bearish leg. | R3 compression-break followed by R2 downtrend short. |
| 2018-10-01 | 2019-05-31 | base-building chop | `chop` (57.28%) | 8.37 | Gold stopped falling, but trend quality stayed mixed before the 2019 breakout. | R4 range/reversal; wait for R1 breakout confirmation. |
| 2019-06-01 | 2020-09-30 | major bull expansion with shock bursts | `uptrend` (54.46%) | 45.34 | The first major decade bull leg; shock months appeared inside the upside trend. | R1 uptrend long, with R0 shock throttle during violent expansion. |
| 2020-10-01 | 2021-03-31 | post-bull correction / chop-to-downtrend | `chop` (62.99%) | -10.71 | The 2020 bull leg cooled into range, then downside pressure. | R4 range defense first; R2 only after structural downtrend confirms. |
| 2021-04-01 | 2022-01-31 | compression and range rotation | `compression` (43.08%) | 4.67 | Mostly low-volatility compression/range with false directional starts. | R3 compression and R4 failed-break specialists. |
| 2022-02-01 | 2022-03-31 | upside event shock | `shock` (45.10%) | 7.64 | Fast geopolitical/inflation repricing; volatility dominated normal trend logic. | R0 event/shock handling; R1 only after volatility normalizes. |
| 2022-04-01 | 2022-10-31 | Fed/USD downtrend | `downtrend` (53.30%) | -15.21 | Persistent bearish regime after the event spike failed. | R2 short specialist; long continuation should be routed off. |
| 2022-11-01 | 2023-05-31 | recovery uptrend with shock rally | `uptrend` (39.11%) | 19.87 | Reversal from the 2022 lows into renewed upside trend. | R1 long after transition; R0 around shock spikes. |
| 2023-06-01 | 2023-10-31 | compression then violent reversal | `compression` (60.31%) | 1.49 | Summer compression broke down, then reversed sharply in October. | R3/R4; avoid assuming downtrend continuation after extended compression breaks. |
| 2023-11-01 | 2024-05-31 | fresh bull breakout / high-vol uptrend | `uptrend` (55.56%) | 18.39 | New upside leg with March-April acceleration. | R1 long, with shock throttle during acceleration. |
| 2024-06-01 | 2024-12-31 | bull trend with mid-year chop and year-end pause | `uptrend` (55.19%) | 12.04 | Trend remained constructive, but entry quality depended heavily on regime routing. | R1 when clean; R4 during pauses. |
| 2025-01-01 | 2026-02-28 | extreme bull expansion / crowded upside | `uptrend` (60.22%) | 101.15 | The strongest upside phase in the sample; this is where the long specialist harvest came from. | R1 long was the correct engine; R0 throttle needed during shock months. |
| 2026-03-01 | 2026-07-09 | bull break into chop/downtrend | `transition` (50.00%) | -23.81 | The market stopped rewarding long continuation; exact-MT5 router confirms chop in Mar-May and downtrend in June. | R1 off; R2 downtrend plus R4 chop are the missing coverage. |

## Detailed Monthly Segments

| Start | End | Months | Regime | Regime-day share % | Return % | Best month % | Worst month % |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: |
| 2016-07 | 2016-07 | 1 | `unknown` | 100.00 | -1.01 | -1.01 | -1.01 |
| 2016-08 | 2016-09 | 2 | `compression` | 60.38 | -2.00 | 0.95 | -2.73 |
| 2016-10 | 2016-10 | 1 | `transition` | 65.38 | -2.96 | -2.96 | -2.96 |
| 2016-11 | 2016-12 | 2 | `downtrend` | 67.31 | -9.75 | -1.60 | -6.75 |
| 2017-01 | 2017-01 | 1 | `transition` | 56.00 | 3.97 | 3.97 | 3.97 |
| 2017-02 | 2017-03 | 2 | `chop` | 56.86 | 2.67 | 3.39 | -0.12 |
| 2017-04 | 2017-04 | 1 | `uptrend` | 50.00 | 1.52 | 1.52 | 1.52 |
| 2017-05 | 2017-08 | 4 | `chop` | 55.66 | 2.91 | 3.13 | -1.75 |
| 2017-09 | 2017-09 | 1 | `uptrend` | 69.23 | -3.16 | -3.16 | -3.16 |
| 2017-10 | 2017-10 | 1 | `chop` | 50.00 | -0.14 | -0.14 | -0.14 |
| 2017-11 | 2017-11 | 1 | `compression` | 57.69 | 1.30 | 1.30 | 1.30 |
| 2017-12 | 2017-12 | 1 | `chop` | 87.50 | 2.12 | 2.12 | 2.12 |
| 2018-01 | 2018-02 | 2 | `uptrend` | 67.35 | -0.24 | 1.44 | -2.13 |
| 2018-03 | 2018-05 | 3 | `chop` | 83.33 | -0.97 | 0.74 | -0.96 |
| 2018-06 | 2018-06 | 1 | `compression` | 69.23 | -3.58 | -3.58 | -3.58 |
| 2018-07 | 2018-09 | 3 | `downtrend` | 75.64 | -4.93 | -0.77 | -2.46 |
| 2018-10 | 2018-12 | 3 | `chop` | 71.79 | 7.42 | 4.68 | 0.65 |
| 2019-01 | 2019-02 | 2 | `uptrend` | 80.00 | 3.15 | 2.95 | -0.06 |
| 2019-03 | 2019-05 | 3 | `chop` | 79.49 | -1.73 | 0.57 | -1.61 |
| 2019-06 | 2019-07 | 2 | `shock` | 61.54 | 9.62 | 8.03 | 2.78 |
| 2019-08 | 2019-09 | 2 | `uptrend` | 78.85 | 5.96 | 7.68 | -2.15 |
| 2019-10 | 2019-12 | 3 | `chop` | 82.05 | 2.87 | 3.74 | -3.23 |
| 2020-01 | 2020-02 | 2 | `uptrend` | 90.20 | 4.24 | 3.55 | -0.26 |
| 2020-03 | 2020-03 | 1 | `shock` | 100.00 | 1.19 | 1.19 | 1.19 |
| 2020-04 | 2020-09 | 6 | `uptrend` | 76.92 | 20.18 | 9.76 | -3.61 |
| 2020-10 | 2021-02 | 5 | `chop` | 76.38 | -8.15 | 6.61 | -6.50 |
| 2021-03 | 2021-03 | 1 | `downtrend` | 70.37 | -3.03 | -3.03 | -3.03 |
| 2021-04 | 2021-05 | 2 | `compression` | 54.90 | 11.50 | 7.63 | 3.85 |
| 2021-06 | 2021-06 | 1 | `transition` | 42.31 | -7.69 | -7.69 | -7.69 |
| 2021-07 | 2021-07 | 1 | `compression` | 70.37 | 2.61 | 2.61 | 2.61 |
| 2021-08 | 2021-08 | 1 | `downtrend` | 46.15 | -0.19 | -0.19 | -0.19 |
| 2021-09 | 2021-09 | 1 | `compression` | 38.46 | -4.72 | -4.72 | -4.72 |
| 2021-10 | 2021-11 | 2 | `chop` | 61.54 | 1.82 | 1.70 | 0.19 |
| 2021-12 | 2022-01 | 2 | `compression` | 63.46 | 0.54 | 2.20 | -2.25 |
| 2022-02 | 2022-02 | 1 | `uptrend` | 50.00 | 6.72 | 6.72 | 6.72 |
| 2022-03 | 2022-03 | 1 | `shock` | 74.07 | 1.50 | 1.50 | 1.50 |
| 2022-04 | 2022-04 | 1 | `uptrend` | 68.00 | -2.08 | -2.08 | -2.08 |
| 2022-05 | 2022-06 | 2 | `chop` | 59.62 | -4.13 | -0.96 | -2.36 |
| 2022-07 | 2022-10 | 4 | `downtrend` | 84.76 | -9.10 | -1.12 | -2.59 |
| 2022-11 | 2022-11 | 1 | `transition` | 61.54 | 7.18 | 7.18 | 7.18 |
| 2022-12 | 2022-12 | 1 | `chop` | 34.62 | 2.55 | 2.55 | 2.55 |
| 2023-01 | 2023-01 | 1 | `uptrend` | 88.00 | 5.03 | 5.03 | 5.03 |
| 2023-02 | 2023-02 | 1 | `transition` | 41.67 | -5.76 | -5.76 | -5.76 |
| 2023-03 | 2023-03 | 1 | `shock` | 44.44 | 8.50 | 8.50 | 8.50 |
| 2023-04 | 2023-05 | 2 | `uptrend` | 68.63 | -0.55 | 1.02 | -1.43 |
| 2023-06 | 2023-06 | 1 | `chop` | 57.69 | -2.93 | -2.93 | -2.93 |
| 2023-07 | 2023-09 | 3 | `compression` | 87.34 | -3.67 | 2.02 | -4.70 |
| 2023-10 | 2023-10 | 1 | `downtrend` | 42.31 | 7.97 | 7.97 | 7.97 |
| 2023-11 | 2023-12 | 2 | `uptrend` | 70.59 | 4.20 | 3.37 | 1.03 |
| 2024-01 | 2024-02 | 2 | `chop` | 70.59 | -1.52 | -0.32 | -1.42 |
| 2024-03 | 2024-03 | 1 | `uptrend` | 88.00 | 9.26 | 9.26 | 9.26 |
| 2024-04 | 2024-04 | 1 | `shock` | 84.62 | 3.88 | 3.88 | 3.88 |
| 2024-05 | 2024-05 | 1 | `uptrend` | 100.00 | 2.30 | 2.30 | 2.30 |
| 2024-06 | 2024-07 | 2 | `chop` | 61.54 | 3.54 | 3.65 | -0.05 |
| 2024-08 | 2024-11 | 4 | `uptrend` | 82.86 | 8.37 | 6.42 | -3.45 |
| 2024-12 | 2024-12 | 1 | `chop` | 84.62 | -1.13 | -1.13 | -1.13 |
| 2025-01 | 2025-01 | 1 | `compression` | 66.67 | 6.53 | 6.53 | 6.53 |
| 2025-02 | 2025-03 | 2 | `uptrend` | 92.00 | 10.39 | 8.05 | 2.81 |
| 2025-04 | 2025-04 | 1 | `shock` | 88.00 | 6.30 | 6.30 | 6.30 |
| 2025-05 | 2025-06 | 2 | `uptrend` | 75.00 | -0.27 | 0.49 | -1.40 |
| 2025-07 | 2025-08 | 2 | `chop` | 62.26 | 3.29 | 2.53 | -1.48 |
| 2025-09 | 2025-09 | 1 | `uptrend` | 100.00 | 11.03 | 11.03 | 11.03 |
| 2025-10 | 2025-10 | 1 | `shock` | 51.85 | 3.60 | 3.60 | 3.60 |
| 2025-11 | 2026-01 | 3 | `uptrend` | 80.77 | 22.89 | 12.47 | 2.16 |
| 2026-02 | 2026-02 | 1 | `shock` | 58.33 | 11.34 | 11.34 | 11.34 |
| 2026-03 | 2026-03 | 1 | `uptrend` | 51.85 | -12.82 | -12.82 | -12.82 |
| 2026-04 | 2026-06 | 3 | `transition` | 68.83 | -16.27 | -1.62 | -10.68 |
| 2026-07 | 2026-07 | 1 | `downtrend` | 100.00 | 1.72 | 1.72 | 1.72 |

## 2026 Exact-MT5 Router Cross-Check

| Month | Router dominant | Share % | Uptrend % | Downtrend % | Chop % | Shock % | Compression % |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-01 | `uptrend` | 51.51 | 51.51 | 0.00 | 19.77 | 28.72 | 0.00 |
| 2026-02 | `shock` | 51.15 | 26.89 | 0.00 | 21.97 | 51.15 | 0.00 |
| 2026-03 | `chop` | 77.76 | 10.63 | 10.63 | 77.76 | 0.98 | 0.00 |
| 2026-04 | `chop` | 83.00 | 0.00 | 16.17 | 83.00 | 0.83 | 0.00 |
| 2026-05 | `chop` | 58.79 | 0.00 | 40.79 | 58.79 | 0.42 | 0.00 |
| 2026-06 | `downtrend` | 58.87 | 0.00 | 58.87 | 35.49 | 5.64 | 0.00 |

## Strategy Implication

- XAUUSD has not been one market. It rotated through clean bull legs, corrections/downtrends, high-volatility shocks, low-volatility compression, and long mixed chop.
- A single long specialist can work in the bull/uptrend segments, but it should be expected to go quiet or lose edge in chop/downtrend/shock unless routed off.
- The recent 2026 exact-MT5 snapshot is mostly chop/downtrend after January. That matches why the long edge went dormant in the last three months.
- The specialist roadmap should therefore be regime-first: R1 uptrend long, R2 downtrend short, R3 compression breakout, R4 chop/range fade, and R0 shock no-trade/event handling.

## Artifacts

- report_md: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A1_XAU_10Y_REGIME_MAP_20260709.md`
- report_json: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A1_XAU_10Y_REGIME_MAP_20260709.json`
- daily_csv: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A1_XAU_10Y_REGIME_MAP_20260709_DAYS.csv`
- monthly_csv: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A1_XAU_10Y_REGIME_MAP_20260709_MONTHS.csv`
- segments_csv: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A1_XAU_10Y_REGIME_MAP_20260709_SEGMENTS.csv`
