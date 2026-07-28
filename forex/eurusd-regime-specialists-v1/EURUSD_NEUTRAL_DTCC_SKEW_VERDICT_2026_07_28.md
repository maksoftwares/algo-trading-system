# EURUSD Neutral DTCC matched-premium-skew verdict

Date: 2026-07-28

Decision: `REJECTED_NEUTRAL_DTCC_SKEW_V1`

The frozen OTC options-surface hypothesis was marginally positive in
development but failed the pseudo-OOS and final quarters. Its fixed full
rule is not eligible for demo or live use.

## Frozen surface and signal

The source retained standalone 14-60 day OTM EUR/USD vanilla options.
Premium was scaled by spot-adjusted notional using only an EURUSD M5
mid-close completed before each option execution. Calls and puts from the
same dissemination date were matched without reuse when tenor differed by
no more than seven days and absolute log moneyness by no more than 0.0025.

The median matched call-minus-put log premium-rate skew was centered on its
preceding 20 eligible sessions. Positive normalized skew selected long and
negative skew selected short at the next 00:00 UTC Neutral opening. The
outcome-blind census contained 48 trades, exactly 24 long and 24 short.

## Chronological results

| Window | Trades | Win rate | Payoff | Profit factor | Net R | Gate |
|---|---:|---:|---:|---:|---:|---|
| Development, 2025 Q4 | 16 | 43.75% | 1.439 | 1.119 | +1.10 | Fail |
| Pseudo-OOS, 2026 Q1 | 18 | 33.33% | 1.439 | 0.720 | -3.45 | Fail |
| Final, 2026 Q2 | 14 | 28.57% | 1.439 | 0.576 | -4.35 | Fail |
| Full rule | 48 | 35.42% | 1.439 | 0.789 | -6.70 | Fail |

Development missed the frozen 45%-55% win-rate gate and became negative
under the extra-half-pip stress. It cannot be selected over the two later
losing windows.

The latest six months contained 32 trades, won 31.25%, returned PF 0.654,
and lost 7.80R. Full-sample maximum drawdown was 14.40R.

## Robustness and oracle resemblance

- Remove the largest 5% of winners: PF 0.650, net -11.13R.
- Add 0.5 pip per round trip: PF 0.644, net -12.70R.
- Exact oracle precision: 35.42%.
- Exact oracle recall: 6.64%.
- Fifteen-minute tolerant precision: 41.67%.

The matched-skew construction is closed without changing tenor, moneyness,
minimum pairs, baseline, direction, or subperiod.

## Reproduce

```powershell
uv run --with pandas --with numpy --with pyarrow python build_neutral_dtcc_skew_source.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_dtcc_skew.py
```
