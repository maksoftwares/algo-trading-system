# EURUSD Neutral rates/dollar sign-consensus H4 preregistration

Status: `LOCK_BEFORE_CENSUS_AND_FORWARD_OUTCOMES`

## Question

Can a simple, symmetric cross-asset direction clue trade EURUSD only during
causal Neutral ownership with approximately 50% wins, approximately 1.5
realized payoff, and PF above 1.15?

This is one exact test, not a threshold search. It does not modify the rejected
extreme short-only RatesDollar result.

## Frozen information

Daily TLT/UUP and TLT/SHY proxy observations become usable only at 00:00 UTC on
the next calendar date. H4 indicators and candles use completed bid bars. The
entry owns `NEUTRAL` only when the frozen cross-asset classifier, evaluated from
the prior completed hour, says Neutral and says neither Shock nor Joint
Compression.

The oracle is forbidden during the census, signal creation, and execution. It
may be opened only after trades exist, to measure resemblance.

## Frozen signal

- Long macro consensus: TLT/UUP 5-day, TLT/UUP 20-day, and TLT/SHY 20-day
  changes are all strictly positive.
- Short macro consensus: the same three changes are all strictly negative.
- Long price confirmation: EMA20 > EMA50 > EMA100; the completed H4 low touches
  EMA20 + 0.25 ATR; the candle closes bullish and above EMA20.
- Short price confirmation is the exact mirror.
- Entry hours are the next UTC H4 opens at 00:00, 04:00, 08:00, 12:00, or
  16:00. Late New York and rollover are excluded in advance.
- Both sides are mandatory. Zero is the only macro threshold.

## Frozen exit and execution

- Stop is the wider of the last six completed H4 extremes or 1.05 ATR from the
  signal close.
- Target is exactly 1.50 initial R.
- Maximum hold is 56 wall-clock hours.
- Entry and exit use archived M5 bid/ask bars. A bar touching stop and target is
  a stop. Risk must be between 1 and 100 pips.
- One position may be open; results are normalized to one initial R.
- A further 0.5-pip round-trip haircut is reported.

## Census-first boundary

The census may construct H4 candles, indicators, lagged macro context, and
causal Neutral ownership. It may count timestamps and sides. It must not inspect
any post-entry price, stop/target result, P&L, oracle match, or favorable
calendar subset.

If any capacity gate in
`config/frozen_neutral_rates_dollar_sign_consensus_h4.json` fails, the forward
price paths remain unopened and this exact rule closes.

## Admission

If the census passes, one execution is allowed. Every frozen gate must pass,
including:

- at least 35 executed trades, with both directions and chronological capacity;
- 45-55% overall win rate;
- 1.25-1.75 realized payoff and PF at least 1.15;
- every chronological window profitable;
- both sides profitable;
- PF above 1.05 after removing the top 5% and after an extra 0.5-pip cost;
- drawdown at most 15R; and
- the frozen oracle precision and recall floors.

All archived windows are temporal robustness checks, not pristine holdouts,
because this repository has already inspected historical EURUSD. Only future
data collected after this lock can supply genuinely untouched confirmation.
No historical pass can authorize demo or live trading.
