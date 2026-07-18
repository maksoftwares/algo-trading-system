# XAUUSD M15 Regime Target Campaign V1 Preregistration

## Question

Can an M15 specialist with a mechanism-matched target exit produce robust positive expectancy inside the frozen `CHOP` or `TRANSITION_UNKNOWN` H4 regime over 2010-01-01 through 2026-07-01?

All historical periods are discovery evidence, not untouched holdouts.

## Changed approach

Earlier H1 chop and transition campaigns mostly used a protective stop plus fixed holding horizon. That geometry does not directly test a mean-reversion thesis. This campaign moves entries to M15 and freezes the intended destination at signal time:

- UTC-day anchored VWAP;
- completed Asian-session midpoint;
- prior-day midpoint or current UTC-day open;
- prior rolling mean or range midpoint;
- fixed R target for source-specific transition continuation.

Targets never move after the signal. `UNSAFE_SHOCK` is always ineligible.

## Locked search

- Attempts 17120 through 18119 inclusive.
- 1,000 deterministic definitions: 500 chop and 500 transition.
- Five mechanics per owner, 100 hash-selected definitions per mechanic.
- No same-version changes are allowed after outcomes are opened.

## Causality and execution

- H4 regime labels are attached only from an already completed H4 observation.
- Session ranges, anchored VWAP, prior-day levels, rolling means, regime ancestry, and transition age use information available by the completed M15 signal close.
- Entry is the next contiguous M15 opening quote: ask for long, bid for short.
- Long stops and targets use bid; short stops and targets use ask.
- Gap-through-stop exits at the opening executable quote.
- Favorable target gaps receive only the frozen target price.
- If stop and target are both touched within one M15 bar, the stop wins.
- A target already behind the next opening quote is rejected.
- Maximum spread is 0.15R; ticket, holding, and 0.05R stress costs apply.
- One position per definition and at most six entries per UTC day.

## Economic gates

Every gate is mandatory:

- at least 120 total trades;
- at least 15 trades in each chronological era;
- stress PF at least 1.10 and average stress return at least 0.02R in every era;
- total stress PF at least 1.25;
- closed-trade drawdown no more than 30R;
- positive net stress return after removing the five largest winners.

Daily one-sided p-values and Benjamini-Hochberg q-values at FDR 0.10 are reported. Passing an economic gate is not execution authority.

## Next gate

Only a frozen historical survivor may enter a separately locked raw-tick replay. It must then survive prospective read-only shadow collection before any training or execution decision.
