# XAUUSD Chop and Transition Mechanisms V2 Preregistration

## Decision question

Can changed, causally distinct mechanism families produce an economically robust H1 specialist for the frozen `CHOP` or `TRANSITION_UNKNOWN` regime over 2010-01-01 through 2026-07-01?

This is a discovery campaign. All four chronological eras have been used by prior research and are not untouched holdouts.

## Why this is a changed approach

The V1 generic z-score, RSI, edge fade, breakout, candle momentum, return momentum, EMA pullback, exhaustion fade, and session continuation families failed. V2 does not retune those definitions. It introduces completed-session structure and causal regime ancestry:

- completed 00:00-05:59 UTC Asian range and inventory;
- UTC-day anchored tick-count-weighted typical-price VWAP;
- weak-breakout anti-signals;
- the last resolved regime before a transition;
- elapsed H1 bars in the current transition run;
- failed-trend and first-transition-block behavior.

`UNSAFE_SHOCK` remains an abstain state and is never eligible.

## Locked attempts

- Attempt numbers: 15120 through 17119 inclusive.
- Total definitions: 2,000.
- Owners: 1,000 `CHOP`, 1,000 `TRANSITION`.
- Five mechanics per owner and 200 deterministic hash-selected definitions per mechanic.
- Parameter definitions and ordering are generated before outcomes are opened.
- No same-version tuning is authorized after outcomes exist.

## Causality

Signals are evaluated at a completed H1 close. Entry is the next verified H1 opening quote. Asian-session fields are used only from 06:00 UTC onward and are accumulated from already completed bars. Anchored VWAP is cumulative through the signal bar. Regime ancestry is forward-filled only from resolved regimes already observed. Transition age is a backward-looking run count.

No future bar, future regime, future session extreme, future volatility, or outcome value is permitted in a signal.

## Screen execution

- Long entry uses ask; long exits and stops use bid.
- Short entry uses bid; short exits and stops use ask.
- Entry spread must be no more than 0.15R.
- Protective stop is 0.8R to 2.0R according to the locked definition.
- Exit is stop or fixed horizon.
- Gap-through-stop exits at the executable H1 open.
- Same-position overlap is prohibited.
- Maximum four entries per UTC day per definition.
- Costs include USD 0.30 ticket, USD 0.35 per 24 hours, and 0.05R stress slippage.

H1 screening is intentionally conservative but not final execution evidence. Any survivor requires a separately locked raw-tick replay.

## Economic gates

A definition passes only if all are true:

- at least 60 total trades;
- at least 8 trades in each of four chronological eras;
- stress profit factor at least 1.10 in every era;
- average stress return at least 0.03R in every era;
- total stress profit factor at least 1.25;
- closed-trade drawdown no more than 20R;
- net stress return remains positive after removing the five largest winners.

Daily one-sided p-values and Benjamini-Hochberg q-values at FDR 0.10 are reported, but statistical support does not override an economic gate.

## Authorization

No result in this campaign authorizes model training, demo execution, or live execution. A historical survivor must pass separately locked raw-tick replay and prospective read-only shadow observation before promotion is considered.
