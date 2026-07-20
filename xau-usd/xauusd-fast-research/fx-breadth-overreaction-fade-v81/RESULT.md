# V81 Terminal Development Result

V81 tested a materially distinct interpretation of synchronized dollar breadth.
EURUSD, GBPUSD, and USDJPY first had to agree on USD direction, while XAUUSD had
to have already overreacted in the inverse-dollar direction. The candidate then
faded the completed XAUUSD overreaction. Outcome-blind July-August 2018
calibration registered exactly 1,000 policies and selected
`H01000__LM025__BS075__RR150__QC05`: a one-second horizon, at least 0.25 bps per
FX leg, at least 0.75 bps summed breadth, at least 1.50 signed XAU response ratio,
and at least five source quotes. It produced `40/44 = 0.909091` candidates per
eligible weekday, split 19 long and 21 short. Contract SHA-256:
`0df6e9791dd0aea289187c27b114eaeca48be0fb5f50157e0103993776716aca`.

Fresh development from September 2018 through June 2021 resolved `646` trades
over `723` eligible weekdays (`0.893499/day`), split 321 long and 325 short.
Base/stress net was USD `-451.31/-500.67`; base/stress PF was
`0.2567/0.2223`; first/second-half stress PF was `0.1953/0.2406`; no month was
positive; profitable-day share was `22.54%`; top-five-winners-removed stress net
was USD `-513.43`; stressed closed-trade DD was USD `500.67`; and the daily-block
bootstrap p-value was `1.0`.

Decision: `V81_DEVELOPMENT_FAIL_TERMINAL`. Confirmation, validation, exam,
forward confirmation, and forward final remain sealed. The locked FX breadth
overreaction-fade mechanism, direction, event thresholds, timing, exits, costs,
and quota may not be tuned, mirrored, or rescued on these outcomes. V59/V60
remain byte-identical and outside this rejection.
