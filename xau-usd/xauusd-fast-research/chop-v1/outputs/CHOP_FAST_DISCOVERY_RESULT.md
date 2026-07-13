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
| CHOP_IMPULSE_EXHAUSTION_REVERSION_V1 | H1 | 21 | 21 | 21 | 0.614 | -0.157 | -3.289 | 0.524 | 5.493 | 0.501 | REJECT |
| CHOP_IMPULSE_EXHAUSTION_REVERSION_V1 | M15 | 161 | 159 | 128 | 0.795 | -0.127 | -20.421 | 0.729 | 31.323 | -0.128 | REJECT |
| CHOP_IMPULSE_EXHAUSTION_REVERSION_V1 | M30 | 91 | 91 | 82 | 0.741 | -0.138 | -12.581 | 0.659 | 15.988 | -1.132 | REJECT |
| CHOP_IMPULSE_EXHAUSTION_REVERSION_V1 | M5 | 205 | 205 | 153 | 0.660 | -0.270 | -55.382 | 0.616 | 70.332 | -4.020 | REJECT |
| CHOP_RANGE_ROTATION_CONTINUATION_V1 | H1 | 38 | 36 | 35 | 1.133 | 0.065 | 2.459 | 1.029 | 3.789 | 4.157 | UNDERPOWERED |
| CHOP_RANGE_ROTATION_CONTINUATION_V1 | M15 | 347 | 315 | 211 | 1.041 | 0.024 | 8.313 | 0.958 | 20.880 | 1.869 | BORDERLINE_DO_NOT_ENGINEER |
| CHOP_RANGE_ROTATION_CONTINUATION_V1 | M30 | 141 | 129 | 118 | 1.303 | 0.147 | 20.770 | 1.177 | 9.000 | 1.012 | BORDERLINE_DO_NOT_ENGINEER |
| CHOP_RANGE_ROTATION_CONTINUATION_V1 | M5 | 598 | 510 | 266 | 0.898 | -0.074 | -44.510 | 0.837 | 85.757 | 15.523 | REJECT |
| CHOP_ROBUST_EQUILIBRIUM_REVERSION_V1 | H1 | 220 | 206 | 171 | 0.927 | -0.034 | -7.454 | 0.830 | 15.740 | -2.332 | REJECT |
| CHOP_ROBUST_EQUILIBRIUM_REVERSION_V1 | M15 | 691 | 621 | 339 | 0.953 | -0.030 | -20.516 | 0.880 | 66.799 | 33.151 | REJECT |
| CHOP_ROBUST_EQUILIBRIUM_REVERSION_V1 | M30 | 437 | 406 | 275 | 0.996 | -0.002 | -1.080 | 0.901 | 33.835 | 25.940 | REJECT |
| CHOP_ROBUST_EQUILIBRIUM_REVERSION_V1 | M5 | 907 | 788 | 368 | 0.798 | -0.161 | -146.034 | 0.748 | 210.098 | 56.677 | REJECT |

## D. Best numerical cell

`CHOP_RANGE_ROTATION_CONTINUATION_V1 / M30` had the highest baseline expectancy at `0.147R` per trade and `20.770R` net. This is a numerical ranking only.

## E. Best defensible cell

No cell met the complete advancement gate.

## F. Timeframe explanation

- `CHOP_ROBUST_EQUILIBRIUM_REVERSION_V1` - M5: 907 trades, expectancy -0.161R, median cost 0.072R, median MFE/MAE 0.700/1.178R, half-life 4.579h, VR(4h) 0.978. M15: 691 trades, expectancy -0.030R, median cost 0.033R, median MFE/MAE 0.828/1.071R, half-life 4.503h, VR(4h) 0.981. M30: 437 trades, expectancy -0.002R, median cost 0.028R, median MFE/MAE 0.882/1.030R, half-life 4.310h, VR(4h) 0.980. H1: 220 trades, expectancy -0.034R, median cost 0.013R, median MFE/MAE 0.728/0.752R, half-life 4.201h, VR(4h) 0.989.
- `CHOP_IMPULSE_EXHAUSTION_REVERSION_V1` - M5: 205 trades, expectancy -0.270R, median cost 0.045R, median MFE/MAE 0.858/1.177R, half-life 4.579h, VR(4h) 0.978. M15: 161 trades, expectancy -0.127R, median cost 0.033R, median MFE/MAE 0.881/1.055R, half-life 4.503h, VR(4h) 0.981. M30: 91 trades, expectancy -0.138R, median cost 0.027R, median MFE/MAE 0.510/0.847R, half-life 4.310h, VR(4h) 0.980. H1: 21 trades, expectancy -0.157R, median cost 0.013R, median MFE/MAE 0.373/0.757R, half-life 4.201h, VR(4h) 0.989.
- `CHOP_RANGE_ROTATION_CONTINUATION_V1` - M5: 598 trades, expectancy -0.074R, median cost 0.063R, median MFE/MAE 0.769/1.141R, half-life 4.579h, VR(4h) 0.978. M15: 347 trades, expectancy 0.024R, median cost 0.031R, median MFE/MAE 0.979/1.058R, half-life 4.503h, VR(4h) 0.981. M30: 141 trades, expectancy 0.147R, median cost 0.021R, median MFE/MAE 1.155/0.948R, half-life 4.310h, VR(4h) 0.980. H1: 38 trades, expectancy 0.065R, median cost 0.011R, median MFE/MAE 1.019/0.930R, half-life 4.201h, VR(4h) 0.989.

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
