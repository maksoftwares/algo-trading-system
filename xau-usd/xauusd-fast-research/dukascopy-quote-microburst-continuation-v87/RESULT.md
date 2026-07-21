# V87 Terminal Development Result

V87 replicated the still-sealed Capital V24.1 quote-microburst continuation
hypothesis on verified Dukascopy XAUUSD history. It used only trailing quote
updates, same-direction displacement, spread, and quote continuity at the
candidate timestamp. The first causal gate crossing per UTC date set direction.

Outcome-blind January 2019 calibration registered exactly 1,000 policies over
22 eligible weekdays. It selected `LB02000__UC05__IM70__DP300__SP300`: a
two-second lookback, at least five nonzero mid updates, minimum 0.70 absolute
update imbalance, minimum 3.00 bps displacement, and maximum 3.00 bps spread.
Calibration produced `21/22 = 0.954545/day`, split 10 long and 11 short.
Contract SHA-256:
`bff36479657de8f404c7ef78f15f61cf23e84c96f88fc40ec76a874365f00e26`.

Fresh development from February 2019 through June 2021 resolved 566 trades over
617 eligible weekdays (`0.917342/day`), split 267 long and 299 short. Base/stress
net was USD `-441.78/-554.98`; base/stress PF was `0.1002/0.0596`;
first/second-half stress PF was `0.0704/0.0493`; no month was positive;
profitable-day share was `9.08%`; top-five-winners-removed stress net was USD
`-564.98`; stressed closed-trade drawdown was USD `554.98`; and the daily-block
bootstrap p-value was `1.0`.

Decision: `V87_DEVELOPMENT_FAIL_TERMINAL`. Confirmation and all later stages
remain sealed. The continuous quote-microburst continuation direction, timing,
threshold registry, two-minute hold, execution, costs, and one-event daily quota
may not be mirrored, retuned, or rescued. V59/V60 and the Capital V24.1 sealed
forward collector remain unchanged.
