# V49 Capital Relative-Spread Pullback Forward Preregistration

## Status

V49 is a research-only, outcome-blind calibration followed by sealed prospective
validation. It grants no model, Python prediction, EA, demo order, live order,
account, terminal, payment, or broker authority.

## Hypothesis

After a strong 70-second XAUUSD quote impulse, a bounded 15-second counter-move
followed by a five-second resumption may identify continuation after temporary
liquidity replenishment. V48 correctly failed because its absolute USD 0.35
spread cap excluded every pre-July-2 calibration day after the broker's ordinary
spread changed from USD 0.50 to USD 0.30. V49 makes the admissibility rule
portable: current spread must be no more than 1.10 times a completed, lagged
30-minute median and no more than USD 1.00. V48 opened no outcome, return, or
P/L. This is distinct from V24.1's five-second update imbalance and V26's
post-gap restart mechanism.

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

Exactly 240 policies are registered before candidate counts are opened:

- impulse/scale: 8, 10, 12, 15, or 20;
- maximum retracement: 0.35, 0.50, or 0.65;
- minimum resumption/scale: 1.0, 1.5, 2.0, or 3.0; and
- cooldown: 45, 60, 90, or 120 minutes.

All policies require an opposite pullback of at least 15% of the impulse, a
resumption aligned with the impulse, completed price and spread baselines, and
the fixed relative/absolute spread limits above.

Selection uses candidate facts only. A policy must produce 0.5-1.5 candidates
per eligible weekday, at least 40% active weekdays, at least 20% in each
direction, and 0.3-2.0 candidates/day in both chronological halves. The selector
minimizes distance from 1.0/day and then prefers the stricter impulse,
resumption, retracement, and cooldown settings. If no policy qualifies, V49
fails before forward collection.

## Sealed Forward Evidence

- Source: dense Capital demo tick logger, account 1033669.
- Start: 2026-07-21 00:00 UTC. July 20 is excluded because V49 was not locked at
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

V49 is the fourth registered Capital forward hypothesis. A centered circular
five-weekday block bootstrap therefore uses a Bonferroni one-sided threshold of
0.0125. Historical passage cannot authorize trading; unchanged forward
confirmation remains mandatory.
