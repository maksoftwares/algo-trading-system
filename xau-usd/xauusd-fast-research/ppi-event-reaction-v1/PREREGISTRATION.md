# XAUUSD PPI Event Reaction V1 Preregistration

## Hypothesis

The BLS Producer Price Index release is a scheduled US inflation shock that is
not present in the prior NFP/CPI/FOMC event campaign. V1 transfers the two
unchanged 15-minute event-reaction mechanics from that campaign to PPI:

1. `EVENT_PPI_IMPULSE_RR2`: trade a qualified break beyond the completed
   15-minute event range.
2. `EVENT_PPI_FADE_RR2`: trade a qualified sweep beyond that range followed by
   a close back inside it.

These are attempts 11,100 and 11,101. No PPI price outcome, parameter search,
or PPI-specific threshold selection was used to define them.

## Official Calendar

- Publication dates come from the free BLS PPI archived-news-release index.
- Only direct `https://www.bls.gov/news.release/archives/ppi_MMDDYYYY.htm`
  links are accepted.
- Release time is fixed at 08:30 America/New_York and converted with the IANA
  time-zone database, including daylight-saving transitions.
- The official index is retrieved through a free read-only text transport
  because direct automated retrieval is blocked by BLS. The raw transport copy,
  parsed calendar, source URLs, and hashes are frozen before outcomes.
- No paid data, account creation, credential, or Databento request is used.

## Fixed Execution

- The event range uses three complete native M5 bars from minute 0 through 15.
- Impulse decisions may occur from minute 15 through 60. Fade decisions may
  occur from minute 15 through 90.
- Break buffer and stop buffer are each 0.1 ATR; minimum signal body fraction is
  0.35; target is 2R.
- Entry is the first verified raw Dukascopy quote strictly after the completed
  signal, with a maximum 10-second delay.
- Stops and targets are ordered on raw ticks with stop-first same-tick priority.
- Native spread, $0.30 ticket cost, $0.35 per 24 hours held, and 0.05R stress
  slippage are included. Maximum hold is 72 hours.

## Firewall

- Historical discovery: 2016-07-01 through 2021-12-31.
- Related-data confirmation: 2022-01-01 through 2026-06-30.

Both policies enter historical discovery and receive Holm correction together.
Only unchanged full-gate passers may enter confirmation. The confirmation XAU
period has appeared in other research, so it is not represented as a pristine
blind exam. A confirmation passer still requires independent-era replication,
portfolio-independence testing, and prospective shadow evidence.

Research only. No model training, Python serving, EA use, demo/live orders,
broker action, Databento use, paid acquisition, or trading authority is granted.
