# EURUSD Neutral official two-year rate-differential source audit

The source was acquired without loading EURUSD prices, returns, oracle rows, or
P&L.

## Accepted sources

- U.S. Treasury official Daily Treasury Par Yield Curve XML feeds, 2019 through
  2026, field `BC_2YEAR`.
- ECB Data Portal official daily euro-area AAA two-year spot-rate series
  `YC.B.U2.EUR.4F.G_N_A.SV_C_YM.SR_2Y`.

Every raw response, request URL, request clock, provider header, byte count, and
SHA-256 is preserved under
`D:/AlgoTradingData/research/eurusd-neutral-rate-differential-v1`.

The normalized source contains 1,874 U.S. observations, 1,912 ECB
observations, and 1,847 exact common observation dates from January 2019
through June 2026. There are 496 common-date spread changes with absolute size
of at least five basis points. The source is accepted for an outcome-blind
signal census.

This is a current official historical snapshot, not a vintage database.
Consequently, any later backtest is retrospective-causal rather than pristine
point-in-time evidence. A conservative two-calendar-day observation lag is
mandatory before a value can enter a decision.
