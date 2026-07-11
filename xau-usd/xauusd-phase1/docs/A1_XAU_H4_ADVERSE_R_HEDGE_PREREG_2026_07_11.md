# A1 XAUUSD H4 Adverse-R Hedge Preregistration

Date: 2026-07-11  
Boundary: exact MT5 Strategy Tester development only; no broker action is authorized.

## Objective

Preserve the frozen H4 entry stream, 0.01 lots, original stop, and original 2R target
while reducing the clustered full-stop losses that create approximately 40% native
relative equity drawdown.  Unlike the rejected entry-cap experiments, this overlay
does not remove an H4 signal or shorten an H4 winner's target.

## Locked hedge rule

The owner specified a hedging account that permits simultaneous long and short XAUUSD
positions.  For each frozen H4 long position independently:

1. Calculate R from its entry price to its unchanged hard stop.
2. On the first tick at or below -0.25R unrealized, open one equal-volume XAUUSD short
   under a separate hedge magic.
3. If the H4 long recovers to its entry price, close that short hedge and retain the
   original long and 2R target.
4. If the H4 long closes first, close its matching hedge on the next executable tick.
5. Permit at most one hedge cycle per H4 position; never re-hedge the same ticket.
6. Hedge positions cannot originate H4 signals or count toward the source's entry cap.
7. Fail initialization unless MT5 reports retail-hedging margin mode.

The -0.25R trigger is fixed before results and is not part of a sweep.  Ignoring costs,
a direct stop after the trigger changes an approximately -1R long loss into -0.25R;
a recovery through entry realizes approximately -0.25R on the hedge while preserving
up to +2R on the original long.  Native spread, swap, and execution effects remain in
the MT5 report.

The only other execution repair is permanent expiry of a signal observed while the
symbol's trade session is closed.  No entry, hour, calendar, regime, stop, target,
or known-loss filter is added.

## Exact runs and gates

- USD 1,000 initial deposit, fixed 0.01 primary lots.
- Five-year: 2021-07-01 through 2026-06-30.
- Ten-year: 2016-07-01 through 2026-06-30.
- 98% MT5 history quality and zero primary/hedge execution failures required.

The candidate survives only if:

- ten-year net profit >= USD 8,000;
- five-year net profit >= USD 6,500;
- native maximum relative equity drawdown <= 10.00% in both windows;
- profit factor >= 1.30 in both windows;
- all original executable H4 primary entries remain present apart from permanent
  market-session expiry;
- every primary ticket has at most one hedge cycle and every hedge is reconciled flat.

Failure status is `H4_ADVERSE_R_HEDGE_FAILED`.  The trigger and recovery rule may not
be tuned against a failed result.
