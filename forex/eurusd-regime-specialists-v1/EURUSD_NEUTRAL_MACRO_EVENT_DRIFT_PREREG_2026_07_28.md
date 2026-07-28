# EURUSD Neutral macro-event drift preregistration

This contract will be hash-locked before loading an EURUSD trade outcome or
oracle field for this exact event-conditioned rule.

## Hypothesis

Major EUR- and USD-labelled macro releases create an information impulse that
may continue or reverse between the release and the next UTC session boundary.
At 00:00 UTC, both the event and all price bars used by the signal are already
complete.

The source audit rejects Dukascopy's historical numeric surprise fields. This
campaign uses only event time, currency, title, tag, and the completed EURUSD
price response.

## Frozen event taxonomy

For EUR-labelled rows, titles must contain one of:

- ECB;
- Harmonized Index of Consumer Prices;
- Gross Domestic Product;
- Markit Manufacturing PMI;
- Markit Services PMI;
- Retail Sales;
- Unemployment Rate.

For USD-labelled rows, titles must contain one of:

- Nonfarm Payrolls;
- Average Hourly Earnings;
- Consumer Price Index;
- FOMC;
- Fed Interest Rate Decision;
- Fed's Monetary Policy Statement;
- Gross Domestic Product;
- ISM Manufacturing PMI;
- ISM Non-Manufacturing PMI;
- ISM Services PMI;
- Retail Sales;
- Producer Price Index;
- Durable Goods Orders.

Matching is case-insensitive. Dukascopy impact, actual, forecast, previous,
normalized value, historical-count, and effect fields are forbidden.

## Frozen decision rule

- Consider only the existing Regime 1 Neutral 00:00 UTC paired opportunity.
- Search the preceding 24 hours for qualifying event rows.
- If none exists, stay in cash.
- If several rows share the latest timestamp, treat them as one event cluster.
- Use the midpoint close of the last M5 bar fully completed before that event.
- Use the midpoint close of the 23:55 M5 bar completed at the 00:00 entry.
- Define the event impulse as the latter minus the former.
- A zero impulse is cash. There is no magnitude threshold.
- Two mechanism branches are frozen:
  - `MOMENTUM`: trade the sign of the impulse;
  - `REVERSAL`: trade against the sign of the impulse.
- Select one branch once on 2019-2022 development trades by higher PF, then
  higher net R, then `MOMENTUM` on an exact tie.
- Never refit or reselect the branch in 2023-2026.

## Outcome-blind census

| Window | Neutral dates | Candidates | Cash dates | Momentum long |
|---|---:|---:|---:|---:|
| 2019-2022 development | 383 | 254 | 129 | 46.85% |
| 2023 validation | 74 | 46 | 28 | 52.17% |
| 2024 validation | 66 | 50 | 16 | 48.00% |
| 2025 pseudo-OOS | 80 | 58 | 22 | 53.45% |
| 2026 H1 pseudo-OOS | 39 | 31 | 8 | 41.94% |
| Total | 642 | 439 | 203 | 48.06% |

Every traded date has exactly one candidate. Candidate frequency is 0.684 per
Neutral date. The census used only event fields allowed by the source audit
and completed pre-entry prices.

## Execution

Execution remains unchanged from the paired parent:

- executable bid/ask entry at 00:00 UTC;
- 4-pip stop and 6-pip target;
- 12-hour maximum hold;
- 0.7-pip minimum spread;
- 0.1 pip adverse slippage per execution side;
- stop first when stop and target share an M5 bar;
- 0.25 portfolio R per ticket.

## Admission

The selected development branch must contain at least 50 trades, positive net
R, and PF strictly above 1.00.

Each of 2023, 2024, 2025, and 2026 H1 must contain at least 8 trades, have
40-60% wins, preserve a 1.35-1.75 realized payoff ratio, positive net R, and
ticket and daily PF strictly above 1.00.

Across all forward windows, PF must be at least 1.15 and win rate must be
45-55%. The forward ledger must remain positive with PF above 1.00 after an
extra half pip and remain positive after removal of its best 5% of winners.
Daily portfolio drawdown cannot exceed 20R.

The last six months require at least 8 trades, positive net R, and ticket and
daily PF above 1.00. Exact oracle precision must reach 20% and same-side
15-minute precision 40%. Frequency is not an admission gate.

## Evidence status

Existing EURUSD history is adaptive research even though this event source is
new. A complete historical pass remains research-only and requires at least
100 new observations and six post-lock calendar months beginning 2026-07-29.
No broker action is authorized.
