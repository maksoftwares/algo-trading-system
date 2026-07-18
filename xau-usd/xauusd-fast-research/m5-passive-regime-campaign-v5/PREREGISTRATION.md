# XAUUSD M5 Passive Regime Campaign V5 Preregistration

## Purpose

All completed chop campaigns used market or stop entries. The original chop
research explicitly identified passive liquidity as an economically different,
unimplemented hypothesis. V5 tests whether price improvement from conservative
pending-limit entries can make range reversion viable, and whether passive
pullback or breakout-retest entries can improve transition expectancy.

## Frozen Search

Attempts 21,120 through 22,119 contain exactly 1,000 deterministic definitions:
100 variants for each of five chop and five transition mechanics.

Chop mechanics:

1. VWAP-deviation passive fade.
2. Rolling-range edge passive fade.
3. Completed Asian-range edge passive fade.
4. Prior-day value edge passive fade.
5. Momentum-exhaustion passive fade.

Transition mechanics:

1. Trend-ancestry EMA pullback limit.
2. Post-compression breakout retest limit.
3. Post-chop breakout retest limit.
4. Momentum pullback limit.
5. Momentum-exhaustion passive fade.

## Conservative Fill Contract

- Signals use completed M15 features; pending orders activate on the first M5
  bar starting at or after the decision.
- A buy limit fills only when native Ask touches the limit. A sell limit fills
  only when native Bid touches it.
- Gap improvement is not credited: every fill is recorded at the limit price.
- A stop touched on the fill M5 bar is charged. A target touched on the fill bar
  is never credited because intrabar order is unknown.
- Later same-bar stop/target ambiguity is stop first. Gap-through stops use the
  worse executable opposite-quote open.
- Native spread is embedded through entry and opposite-quote exit sides. Ticket
  cost, holding cost, and stress slippage are also charged.
- Unfilled orders expire mechanically. Each definition holds one position at a
  time and takes at most six filled trades per UTC day.
- `UNSAFE_SHOCK` is never eligible.

## Frozen Gates

The inherited gates require 120 trades overall, 15 in each of four eras,
stressed PF at least 1.10 and average stressed R at least 0.02 in every era,
total PF at least 1.25, drawdown no more than 30R, and positive net R after the
five largest winners are removed. Benjamini-Hochberg q-values are reported over
all 1,000 definitions.

Historical periods are discovery evidence only. A finalist requires separate
exact-tick confirmation and prospective shadow observation. V5 grants no model
training, Python serving, EA, demo, live, broker, network, Databento, or paid-data
authority.
