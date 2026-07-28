# EURUSD Neutral official BLS schedule cross-check

Date: `2026-07-28`

Status: `FROZEN_BEFORE_PROSPECTIVE_START_AND_FIRST_SIGNAL`

The prospective macro specialist obtains forecast and event identity from
append-only TradingView captures. This independent guardrail verifies the
scheduled release time against the official U.S. Bureau of Labor Statistics
calendar before any event can be treated as correctly timed.

## Official evidence

Source:
`https://www.bls.gov/schedule/2026/08_sched_list.htm`

The page was observed at `2026-07-28T16:48:57.533Z`. It identified itself as
the August 2026 selected-release schedule, stated that all times are Eastern,
and reported a last-modified date of June 10, 2026.

Direct scripted HTTP access returned `403` because BLS blocks this automated
schedule retrieval. The three relevant visible DOM rows were therefore
observed through the in-app browser and normalized without claiming that raw
HTML was archived. The compact, sorted-key UTF-8 JSON payload is frozen as
SHA-256
`03816009f06ff96b330486c3333e2b52fd3ce0949e72f0b1c0869d53df4eedee`.

| Family | Official release | Official Eastern time | Frozen UTC time |
|---|---|---|---|
| NFP | Employment Situation for July 2026 | Aug 7, 08:30 | Aug 7, 12:30 |
| CPI | Consumer Price Index for July 2026 | Aug 12, 08:30 | Aug 12, 12:30 |
| PPI | Producer Price Index for July 2026 | Aug 13, 08:30 | Aug 13, 12:30 |

All three exactly matched the latest immutable TradingView watchlist observed
at `2026-07-28T15:50:54Z`, including family, provider event ID, ticker, and UTC
timestamp.

## Fail-closed policy

The offline verifier hash-validates this contract, revalidates every
TradingView manifest and referenced snapshot through the locked operations
planner, converts the frozen official Eastern rows using
`America/New_York`, and requires an exact three-family match.

Any missing event, duplicate family, extra family, event-ID drift, ticker
drift, or timestamp drift produces
`BLOCKED_OFFICIAL_SCHEDULE_MISMATCH_NO_TRADE`.

Because the BLS calendar may be updated, the official page must be checked
again no later than 24 hours before the first release, at
`2026-08-06T12:30:00Z`. A later check is new schedule evidence, not permission
to alter the trading rule.

The offline verifier makes no network request, loads no P&L, and cannot call a
broker.
