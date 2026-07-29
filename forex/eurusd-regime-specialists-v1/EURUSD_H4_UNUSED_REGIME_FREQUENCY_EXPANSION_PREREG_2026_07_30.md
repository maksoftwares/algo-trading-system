# EURUSD H4 unused-regime frequency expansion preregistration

The later-session transfer failed, so this independent expansion keeps the
profitable 00:00-09:00 UTC clock and opens only regimes where the baseline is
currently cash.

The unchanged chop strategy supplies the reference hours, decision hours,
body threshold, 1.75 ATR stop, 1.25R target, 12-hour hold, execution costs,
and first-signal rule. Only regime ownership and the economically aligned
direction change:

- trend-down: SHORT on a break below the reference low;
- trend-up: LONG on a break above the reference high;
- transition: take the first break above or below the reference range;
- unsafe: remain in cash.

Every new regime expert must pass its full-history, cost, chronological,
recent, concentration, and drawdown gates independently. The two-sided
transition expert must also have adequate and non-destructive evidence on
both sides. Every passing expert must be added at 0.5 portfolio risk; no side,
year, or subgroup may be retained selectively. The combined portfolio uses a
causal 2.0R concurrent-risk cap.

The same frozen final portfolio gates as the session transfer apply,
including at least 50% more trades, full PF at least 1.15, stressed PF at
least 1.10, positive chronological blocks and latest six months, delayed
entry robustness, concentration control, and trade/calendar bootstrap lower
bounds above PF 1.

This remains selection-aware historical development and cannot authorize
demo or broker activity.
