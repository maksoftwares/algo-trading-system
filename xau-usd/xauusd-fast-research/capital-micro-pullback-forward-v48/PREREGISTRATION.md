# V48 Capital Micro-Pullback Forward Preregistration

## Status

V48 is a research-only, outcome-blind calibration followed by sealed prospective
validation. It grants no model, Python prediction, EA, demo order, live order,
account, terminal, payment, or broker authority.

## Hypothesis

After a strong 70-second XAUUSD quote impulse, a bounded 15-second counter-move
followed by a five-second resumption may identify continuation after temporary
liquidity replenishment. This is distinct from V24.1's five-second update
imbalance and V26's post-gap restart mechanism.

## Calibration Boundary

- Source: Capital live-account five-second spread logger, account 121409.
- Window: 2026-05-27 through 2026-07-17 inclusive.
- Use: quote/schema quality and candidate-frequency calibration only.
- Forbidden: every price after a candidate, return, entry, exit, P/L, win rate,
  profit factor, MFE, MAE, or model target.

Each five-second observation is the latest quote at or before a fixed UTC
five-second boundary. Quotes older than six seconds are unavailable. The robust
scale at decision time uses absolute five-second changes ending at least 90
seconds earlier; impulse, pullback, and resumption windows are fully completed.

## Registered Family

Exactly 108 policies are registered before candidate counts are opened:

- impulse/scale: 4, 6, 8, or 10;
- maximum retracement: 0.45, 0.60, or 0.75;
- minimum resumption/scale: 0.5, 1.0, or 1.5; and
- cooldown: 30, 45, or 60 minutes.

All policies require an opposite pullback of at least 15% of the impulse, a
resumption aligned with the impulse, completed baseline history, and spread no
greater than USD 0.35.

Selection uses candidate facts only. A policy must produce 0.5-1.5 candidates
per eligible weekday, at least 40% active weekdays, at least 20% in each
direction, and 0.3-2.0 candidates/day in both chronological halves. The selector
minimizes distance from 1.0/day and then prefers the stricter impulse,
resumption, retracement, and cooldown settings. If no policy qualifies, V48
fails before forward collection.

## Sealed Forward Evidence

- Source: dense Capital demo tick logger, account 1033669.
- Start: 2026-07-21 00:00 UTC. July 20 is excluded because V48 was not locked at
  its start.
- Validation: first 20 eligible full weekdays.
- Confirmation: next 20 eligible full weekdays, opened only after validation
  passes.
- Direction: continuation in the impulse direction.
- Entry: first quote strictly after the decision, within two seconds.
- Exit: first quote at or after 300 seconds, within two seconds.
- Long enters at ask and exits at bid; short enters at bid and exits at ask.
- Base/stress slippage: USD 0.05/USD 0.15 per side.

Each stage requires 0.5-1.5 trades/day, at least 40% active days, at least 20%
in each direction, PF at least 1.20 base and 1.05 stress, positive base/stress
net, at least 50% profitable days, both half PFs at least 1.0, recovery factor
at least 1.0, and closed drawdown no greater than USD 100.

V48 is the third registered Capital forward hypothesis. A centered circular
five-weekday block bootstrap therefore uses a Bonferroni one-sided threshold of
0.0166666667. Historical passage cannot authorize trading; unchanged forward
confirmation remains mandatory.
