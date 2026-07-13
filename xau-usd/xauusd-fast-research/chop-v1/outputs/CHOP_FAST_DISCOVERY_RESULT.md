1. Exact branch: `codex/xau-chop-fast-discovery-v1`
2. Exact starting commit and tree: `fe0777c65b78fbb9d6002935221ab404a41dbaad` / `7de88a01a6ddf8d1708ff7e427359469ccad8d5d`
3. Exact ending commit and tree: `PENDING_SINGLE_RESEARCH_COMMIT` (reported exactly in the owner response)
4. Data source: Capital.com XAUUSD processed broker Bid/Ask bars; M30 causally aggregated from M5
5. Requested and actual date range: `2016-07-01T00:00:00+00:00` to `2026-06-30T23:59:59+00:00` / `2016-07-01T00:00:00+00:00` to `2025-07-01T00:00:00+00:00`
6. Cost source: actual per-bar Capital.com Bid/Ask spread; stress uses measured bar P95 spread plus 0.05R slippage
7. Overall verdict: `CHOP_STRATEGY_BORDERLINE_NO_ENGINEERING`

# XAUUSD Chop Fast Discovery V1

## A. Data and implementation status

- Coverage status: `DATA_COVERAGE_PARTIAL_REQUESTED_TAIL_MISSING`; common years: `9.000`.
- Native timeframes: M5, M15, H1, H4. M30 is exact 30-minute OHLC aggregation from six complete M5 bars.
- Missing intervals: `[{"end": "2026-06-30T23:59:59+00:00", "start": "2025-07-01T00:00:00+00:00"}]`.
- Funding: `FUNDING_NOT_INCLUDED_IN_FAST_SCREEN`; rollover-crossing trades remain counted.
- Execution: completed bars, next-bar Bid/Ask entry, adverse stop-first resolution, and causal H4 labels.
- All history is development/research data; no deployment claim is made.

## B. Chop-regime census

- Episodes: `449`.
- Total chop days: `618.83`.
- History classified as chop: `25.88%`.
- Median episode days: `1.17`; P90: `4.33`.
- Volatility subtype bar distribution: `{"HIGH_VOL_CHOP": 938, "LOW_VOL_CHOP": 1394, "MEDIUM_VOL_CHOP": 1268, "VOL_SUBTYPE_UNAVAILABLE": 113}`.
- Range-width subtype bar distribution: `{"MEDIUM_WIDTH_CHOP": 2682, "NARROW_CHOP": 105, "WIDE_CHOP": 926}`.
- Drift subtype bar distribution: `{"DOWNWARD_DRIFT_CHOP": 474, "FLAT_CHOP": 2502, "UPWARD_DRIFT_CHOP": 737}`.
- Yearly chop coverage: `{"2016": 15.77639751552795, "2017": 19.64735516372796, "2018": 30.508474576271187, "2019": 26.55367231638418, "2020": 29.536921151439298, "2021": 30.470219435736677, "2022": 29.260651629072683, "2023": 21.446540880503143, "2024": 26.79575265459088, "2025": 21.601016518424398}`.

## C. Main result matrix

| Strategy | TF | Trades | Setups | Chop episodes | PF | Exp R | Net R | Stress PF | DD R | B+C R | Category |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| CHOP_IMPULSE_EXHAUSTION_REVERSION_V1 | H1 | 21 | 21 | 21 | 0.489 | -0.214 | -4.494 | 0.412 | 6.697 | 0.564 | REJECT |
| CHOP_IMPULSE_EXHAUSTION_REVERSION_V1 | M15 | 161 | 159 | 128 | 0.841 | -0.094 | -15.208 | 0.769 | 25.891 | 0.574 | REJECT |
| CHOP_IMPULSE_EXHAUSTION_REVERSION_V1 | M30 | 91 | 91 | 82 | 0.806 | -0.094 | -8.587 | 0.717 | 14.606 | -1.061 | REJECT |
| CHOP_IMPULSE_EXHAUSTION_REVERSION_V1 | M5 | 205 | 205 | 153 | 0.710 | -0.223 | -45.785 | 0.662 | 60.856 | -3.479 | REJECT |
| CHOP_RANGE_ROTATION_CONTINUATION_V1 | H1 | 38 | 36 | 35 | 1.160 | 0.075 | 2.834 | 1.050 | 3.726 | 4.274 | UNDERPOWERED |
| CHOP_RANGE_ROTATION_CONTINUATION_V1 | M15 | 347 | 315 | 211 | 1.051 | 0.029 | 10.230 | 0.966 | 21.793 | 4.255 | BORDERLINE_DO_NOT_ENGINEER |
| CHOP_RANGE_ROTATION_CONTINUATION_V1 | M30 | 141 | 129 | 118 | 1.261 | 0.126 | 17.813 | 1.142 | 9.000 | 1.015 | BORDERLINE_DO_NOT_ENGINEER |
| CHOP_RANGE_ROTATION_CONTINUATION_V1 | M5 | 598 | 510 | 266 | 0.891 | -0.079 | -47.457 | 0.831 | 89.804 | 16.639 | REJECT |
| CHOP_ROBUST_EQUILIBRIUM_REVERSION_V1 | H1 | 221 | 207 | 171 | 0.995 | -0.002 | -0.439 | 0.886 | 11.720 | -1.442 | REJECT |
| CHOP_ROBUST_EQUILIBRIUM_REVERSION_V1 | M15 | 692 | 622 | 339 | 0.953 | -0.029 | -20.160 | 0.880 | 68.899 | 30.526 | REJECT |
| CHOP_ROBUST_EQUILIBRIUM_REVERSION_V1 | M30 | 438 | 407 | 275 | 1.032 | 0.017 | 7.462 | 0.936 | 28.322 | 23.659 | BORDERLINE_DO_NOT_ENGINEER |
| CHOP_ROBUST_EQUILIBRIUM_REVERSION_V1 | M5 | 908 | 789 | 368 | 0.790 | -0.166 | -151.020 | 0.740 | 215.738 | 55.321 | REJECT |

## D. Best numerical cell

`CHOP_RANGE_ROTATION_CONTINUATION_V1 / M30` had the highest baseline expectancy at `0.126R` per trade and `17.813R` net. This is a numerical ranking only.

## E. Best defensible cell

No cell met the complete advancement gate.

## F. Timeframe explanation

- `CHOP_ROBUST_EQUILIBRIUM_REVERSION_V1` - M5: 908 trades, expectancy -0.166R, median cost 0.072R, median MFE/MAE 0.577/1.000R, half-life 11.983h, VR(4h) 0.938. M15: 692 trades, expectancy -0.029R, median cost 0.033R, median MFE/MAE 0.697/1.000R, half-life 11.770h, VR(4h) 0.944. M30: 438 trades, expectancy 0.017R, median cost 0.028R, median MFE/MAE 0.810/1.000R, half-life 11.330h, VR(4h) 0.943. H1: 221 trades, expectancy -0.002R, median cost 0.013R, median MFE/MAE 0.655/0.687R, half-life 9.941h, VR(4h) 0.939.
- `CHOP_IMPULSE_EXHAUSTION_REVERSION_V1` - M5: 205 trades, expectancy -0.223R, median cost 0.045R, median MFE/MAE 0.824/1.000R, half-life 11.983h, VR(4h) 0.938. M15: 161 trades, expectancy -0.094R, median cost 0.033R, median MFE/MAE 0.815/1.000R, half-life 11.770h, VR(4h) 0.944. M30: 91 trades, expectancy -0.094R, median cost 0.025R, median MFE/MAE 0.507/0.793R, half-life 11.330h, VR(4h) 0.943. H1: 21 trades, expectancy -0.214R, median cost 0.013R, median MFE/MAE 0.373/0.757R, half-life 9.941h, VR(4h) 0.939.
- `CHOP_RANGE_ROTATION_CONTINUATION_V1` - M5: 598 trades, expectancy -0.079R, median cost 0.063R, median MFE/MAE 0.690/1.000R, half-life 11.983h, VR(4h) 0.938. M15: 347 trades, expectancy 0.029R, median cost 0.030R, median MFE/MAE 0.935/1.000R, half-life 11.770h, VR(4h) 0.944. M30: 141 trades, expectancy 0.126R, median cost 0.020R, median MFE/MAE 1.017/0.868R, half-life 11.330h, VR(4h) 0.943. H1: 38 trades, expectancy 0.075R, median cost 0.010R, median MFE/MAE 1.017/0.858R, half-life 9.941h, VR(4h) 0.939.

## G. General chop coverage

Subtype results are reported without filtering in `CHOP_SUBTYPE_RESULTS.csv`. Empty and negative buckets are retained; no subtype was removed or used to rescue a cell.

## H. Concentration and fragility

Year, trade, day, direction, and subtype concentration fields are retained in the matrix, yearly, subtype, signal, and trade ledgers. Advancement gates penalize top-ten-winner and single-year concentration.

## I. Final decision

`CHOP_STRATEGY_BORDERLINE_NO_ENGINEERING`

## J. Next action

No tested chop strategy earned further engineering. A future, economically different hypothesis could test passive liquidity/auction imbalance, but it is not implemented here.

## Limitations

- The requested July 2025-June 2026 tail is unavailable in the common Capital.com bar set.
- M1/tick data was not used; ambiguous same-bar stop/target touches are conservatively stop-first.
- Trustworthy swap/funding values were unavailable for this fast screen.
- Boundary-return probabilities are descriptive 12-hour diagnostics and were not used as filters or tuning inputs.
