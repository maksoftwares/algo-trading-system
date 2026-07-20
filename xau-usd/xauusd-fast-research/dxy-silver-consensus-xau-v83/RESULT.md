# V83 Terminal Development Result

V83 tested whether agreement between two continuous raw sources could remove the
noise that defeated their individual lead-lag families. DOLLARIDXUSD set the
inverse gold direction, XAGUSD had to confirm it, and causally known XAUUSD had
to remain incomplete relative to silver.

Outcome-blind January 2019 calibration registered exactly 1,000 policies over
22 eligible weekdays. It selected `H05000__DX030__AG300__XR000__QC02`: a
five-second horizon, minimum 0.30 bps DXY move, minimum 3.00 bps directional
silver move, nonpositive signed XAU/silver response, and at least two quote-index
advances. Calibration produced `18/22 = 0.818182/day`, split 8 long and 10
short. Contract SHA-256:
`3d17c8f97080f2f121f89b65f2cc0a7e78b870b1b2610bb8e242dfe97d0353ad`.

Fresh development from February 2019 through June 2021 resolved 505 trades over
615 eligible weekdays (`0.821138/day`), split 248 long and 257 short. Base/stress
net was USD `-309.81/-350.52`; base/stress PF was `0.4014/0.3588`;
first/second-half stress PF was `0.3048/0.4098`; no month was positive;
profitable-day share was `24.39%`; top-five-winners-removed stress net was USD
`-367.03`; stressed closed-trade drawdown was USD `352.23`; and the daily-block
bootstrap p-value was `1.0`.

Decision: `V83_DEVELOPMENT_FAIL_TERMINAL`. Confirmation and all later stages
remain sealed. The DXY-silver consensus catch-up event, direction, thresholds,
timing, response rule, execution, exits, costs, and quota may not be mirrored,
retuned, or rescued. V59/V60 remain byte-identical and outside this rejection.
