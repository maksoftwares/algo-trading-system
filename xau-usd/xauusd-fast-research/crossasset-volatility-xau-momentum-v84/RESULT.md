# V84 Terminal Development Result

V84 tested whether simultaneous absolute movement in DOLLARIDXUSD and XAGUSD
could identify an active market in which causally observed XAUUSD momentum would
continue. The source instruments established volatility only; the sign of the
strictly pre-decision XAUUSD move independently set LONG or SHORT.

Outcome-blind January 2019 calibration registered exactly 1,000 policies over
22 eligible weekdays. It selected `H05000__DX075__AG500__AU200__QC02`: a
five-second horizon, minimum 0.75 bps absolute DXY move, minimum 5.00 bps
absolute silver move, minimum 2.00 bps absolute XAUUSD move, and at least two
source quote-index advances. Calibration produced `18/22 = 0.818182/day`, split
10 long and 8 short. Contract SHA-256:
`fcdba968158636560548ca3d673648859e769b297d650f5bc1fe990987f117f4`.

Fresh development from February 2019 through June 2021 resolved 567 trades over
615 eligible weekdays (`0.921951/day`), split 274 long and 293 short. Base/stress
net was USD `-492.34/-540.01`; base/stress PF was `0.3080/0.2773`;
first/second-half stress PF was `0.3056/0.2518`; no month was positive;
profitable-day share was `23.74%`; top-five-winners-removed stress net was USD
`-558.89`; stressed closed-trade drawdown was USD `540.01`; and the daily-block
bootstrap p-value was `1.0`.

Decision: `V84_DEVELOPMENT_FAIL_TERMINAL`. Confirmation and all later stages
remain sealed. The cross-asset-volatility activation, immediate XAUUSD momentum
direction, thresholds, timing, execution, exits, costs, and daily quota may not
be mirrored, retuned, or rescued. V59/V60 remain byte-identical and outside
this rejection.
