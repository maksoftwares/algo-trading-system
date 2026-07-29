# EURUSD Neutral 06:00-08:00 UTC range-breakout transfer preregistration

## Purpose

This is a cross-symbol mechanism transfer, not another EURUSD parameter hunt.
The already frozen USDJPY session seed produced an independently defined
Neutral-normal specialist before this EURUSD candidate was proposed. This
preregistration transfers that market mechanism to EURUSD before generating
the first EURUSD candidate count.

The source evidence is used only to choose a mechanism. No USDJPY trade is
pooled with EURUSD and no EURUSD outcome has selected a parameter, side,
weekday, hour, or subgroup.

## Frozen candidate

On weekdays, construct complete midpoint M15 bars. Freeze the 06:00-08:00 UTC
range from eight complete M15 bars. Between 08:00 and 12:00 UTC, a completed
M15 bar is a LONG signal only if:

- its close is above the range high plus 0.05 current M15 ATR;
- its real body is at least 30% of its range; and
- its close is in the top 35% of its range.

SHORT is the exact mirror. The completed 06:00-08:00 range must be between
0.45 and 3.20 current M15 ATR and at least 0.20 of the prior completed UTC
day's ATR. The current and prior-day ATR periods are both 14.

The signal belongs to this expert only when the latest causal hourly state is
Neutral, unresolved, non-shock, and not jointly compressed in DXY and EURUSD.
The matched state bar must be fully known by signal completion.

## Frozen execution contract

Entry is the first exact M5 open at or after signal completion. Entry includes
the actual bid/ask spread, a 0.7-pip minimum spread, and 0.1 pip of adverse
slippage per side.

The stop is outside the 06:00-08:00 range by at least the maximum of current
M15 ATR, the session range, and three pips. Risk above 90 pips is cash. The
target is 1.5R, the maximum hold is 12 hours, and ambiguous stop/target bars
resolve stop first. Only one position may be open and no more than two entries
may occur on a UTC date.

The 1.5R target follows the user's stated payoff objective. The 12-hour cap is
the existing canonical Neutral research horizon. Neither was selected from
this candidate's EURUSD outcomes.

## Outcome-blind census gates

Before any stop/target path, return, P&L, or oracle row may be opened, the
decision-time candidate census must contain:

- at least 120 risk-eligible candidates on at least 100 dates;
- at least 60 candidates in 2019-2022 development;
- at least 12 candidates in each of 2023, 2024, and 2025;
- at least five candidates in 2026 H1 and in the latest six completed months;
- at least 30 LONG and 30 SHORT candidates; and
- no candidate whose causal state was known more than four hours before its
  signal.

One failed capacity gate closes the exact candidate without opening outcomes.
The thresholds will not be relaxed after counts.

## Performance review if and only if capacity passes

The separately locked execution pass must report development, 2023, 2024,
2025, 2026 H1, both sides, the latest six months, an extra 0.5-pip cost, removal
of the best 5% of winners, maximum drawdown, and one-to-one exact/15-minute
same-side Neutral-oracle resemblance.

Promotion requires all frozen gates, including 45-55% wins, 1.35-1.75
realized payoff, PF at least 1.15 overall, PF above 1.0 in every chronological
window and on both sides, positive stressed and concentration-removed PF, and
positive latest-six-month PF.

Historical success would remain adaptive research evidence. It cannot
authorize broker, demo, or live action without separate prospective
confirmation.

## Census boundary

The census may load only completed, decision-time prices required to form the
signal, causal state, entry quote, and structure risk. It must not walk a
future path or load any trade exit, EURUSD return, P&L, oracle row, or
performance metric.
