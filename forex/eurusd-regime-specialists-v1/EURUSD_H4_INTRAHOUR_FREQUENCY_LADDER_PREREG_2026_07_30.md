# EURUSD H4 intrahour frequency ladder preregistration

The protected H1 rule sees only completed hourly closes. This ladder tests
whether the same first range break can be observed earlier at 30- or
15-minute resolution.

Every resolution uses:

- the exact completed 00:00-05:59 UTC reference range;
- the exact 06:00-09:59 decision window;
- the first qualifying break per regime and UTC date;
- the H4 regime available at the signal bar's start;
- the latest completed H1 ATR available when the signal bar closes;
- unchanged body threshold, SHORT side, 1.75 ATR stop, 1.25R target,
  12-hour hold, bid/ask costs, stop-first execution, and quarantine.

The ladder contains only H60, M30, and M15. A finer resolution must add at
least 20% more trades and pass every full-history, chronological, recent,
cost, delay, concentration, drawdown, and bootstrap gate. The finest passing
resolution is selected; otherwise H60 remains protected.

This is historical development, not pristine confirmation, and cannot
authorize demo or broker activity.
