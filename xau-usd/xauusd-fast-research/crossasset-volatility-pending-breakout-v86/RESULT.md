# V86 Terminal Development Result

V86 tested whether DOLLARIDXUSD and XAGUSD absolute coactivation could announce
cross-asset volatility while XAUUSD remained quiet, followed by a separately
confirmed XAUUSD breakout. The source instruments established volatility only;
the sign of the first later XAUUSD threshold crossing set LONG or SHORT.

Outcome-blind January 2019 calibration registered exactly 1,000 policies over
22 eligible weekdays. It selected `H20000__DX075__AG300__XI010__BO200`: a
20-second horizon, minimum 0.75 bps absolute DXY move, minimum 3.00 bps
absolute silver move, maximum 0.10 bps initial XAUUSD move, and a later 2.00
bps XAUUSD breakout. Calibration produced `18/22 = 0.818182/day`, split 8 long
and 10 short. Contract SHA-256:
`fe332c21a62d10cda3b1b75ce7202394ca5bf5ae36af1ee9476185aa3002a7e1`.

Fresh development from February 2019 through June 2021 resolved 509 trades over
615 eligible weekdays (`0.827642/day`), split 249 long and 260 short. Base/stress
net was USD `-399.72/-442.24`; base/stress PF was `0.4439/0.4112`;
first/second-half stress PF was `0.3995/0.4224`; no month was positive;
profitable-day share was `21.14%`; top-five-winners-removed stress net was USD
`-469.30`; stressed closed-trade drawdown was USD `443.48`; and the daily-block
bootstrap p-value was `1.0`.

Decision: `V86_DEVELOPMENT_FAIL_TERMINAL`. Confirmation and all later stages
remain sealed. The cross-asset-volatility activation, delayed XAUUSD breakout
confirmation, thresholds, timing, execution, exits, costs, and daily quota may
not be mirrored, retuned, or rescued. V59/V60 remain byte-identical and outside
this rejection.
