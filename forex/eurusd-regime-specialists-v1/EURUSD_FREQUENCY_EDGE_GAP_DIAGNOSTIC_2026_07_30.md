# EURUSD frequency-edge gap diagnostic

Date: 2026-07-30

Status: **GOAL_NOT_HIT — MISSING INDEPENDENT EDGE CAPACITY**

Demo-order authorization: **false**

## Plain-English conclusion

The data and backtest machinery are not the blockage. The protected strategy
has a real but narrow historical edge. It trades only a small part of the
market, and the extra trades found outside that part have lost money in honest
validation.

Changing the protected strategy from H4 to the first M15 break improves entry
timing, but it mostly trades the same dates. It is not an independent second
edge. Filling empty dates with weak trades can reach the frequency target, but
it destroys profit factor, stress robustness, or chronological transfer.

## Exact gap

The broker window contains 522 weekdays.

| Requirement | Needed | Protected result | Shortfall |
|---|---:|---:|---:|
| Minimum frequency, 0.85 trades/weekday | 444 trades | 106 trades | 338 trades |
| Central goal, 1.00 trade/weekday | 522 trades | 106 trades | 416 trades |
| Minimum 65% weekday coverage | 340 active weekdays | 98 active weekdays | 242 active weekdays |

The protected broker replay achieved:

| Metric | Result |
|---|---:|
| Trades per weekday | 0.2031 |
| Weekday coverage | 18.77% |
| Win rate | 49.06% |
| Payoff ratio | 1.4648 |
| Profit factor | 1.4105 |
| PF after cost stress | 1.3405 |
| Best-5%-removed PF | 1.1068 |
| Net P&L | +$61.60 |

## Where the current edge actually lives

The broker result is concentrated in one regime:

| Protected regime | Trades | PF | Net P&L |
|---|---:|---:|---:|
| Chop | 74 | 1.5882 | +$67.06 |
| Compression | 32 | 0.8486 | -$5.46 |

The portfolio result is profitable, but it is not yet a broad collection of
profitable regime experts. In this broker window, the chop expert earns more
than the entire portfolio and the compression expert subtracts from it.

The protected rule is also structurally narrow: short only, first break per
regime date, and a 06:00–10:00 UTC decision window. That geometry cannot
produce approximately one independent trade every weekday by itself.

## Why related frequency variants do not solve it

The H4 protected and M15 first-break research ledgers share 82 of the H4
ledger's 85 active dates in the recent two-year window: 96.47% overlap.

| Research ledgers, 2024-07 through 2026-06 | H4 protected | M15 first break |
|---|---:|---:|
| Trades | 90 | 122 |
| Active dates | 85 | 113 |
| Shared active dates | 82 | 82 |
| New dates contributed by M15 | — | 31 |
| Union active dates | 116 | 116 |
| Union coverage over 522 weekdays | 22.22% | 22.22% |

These are useful implementation variants of the same economic idea, not two
independent sleeves. Adding both would double-count correlated exposure and
would still leave most weekdays empty.

Same-day re-entry and additional decision-hour ladders confirmed the same
ceiling. They raised the full-history rate only from 0.205 to approximately
0.214–0.223 trades per FX day, and the predeclared frequency or robustness
gates rejected them.

## What happened when frequency was forced

| Attempt | Frequency achieved | Edge result | Decision |
|---|---:|---|---|
| Online dense residual router | 0.824 combined trades/weekday | Residual PF 0.764; combined PF 1.091; stress PF 1.006; best-5%-removed PF 0.669 | Rejected |
| Chronological RSI regime selector | 1.341 combined trades/weekday | RSI lost $20.31 in locked year; combined PF 1.007; stress PF 0.924; payoff 0.951 | Rejected |
| H4 trend-down short expert | 194 full-history trades | PF 0.863; stress PF 0.820 | Rejected |
| H4 trend-up long expert | 166 full-history trades | PF 0.765; stress PF 0.728 | Rejected |
| H4 transition two-sided expert | 208 full-history trades | PF 0.917; stress PF 0.875 | Rejected |

This is the central bottleneck: the system can generate enough signals, but
the signals on currently empty dates have negative or near-zero expectancy.
The profitable protected sleeve then masks their losses in combined results.

## What is missing

We need genuinely different, positive-expectancy experts for market states and
times not owned by the chop breakout:

1. a trend-up long expert;
2. a trend-down continuation or pullback expert;
3. a transition/shock expert;
4. a repaired compression expert;
5. later-session or overnight mechanisms that do not repeat the 06:00–10:00
   first-break exposure.

No single new expert needs to trade every day. To add the missing 0.647
trades/weekday above the 0.85 floor without one weak sleeve dominating, the
practical requirement is several independent experts contributing roughly
0.15–0.25 trades/weekday each and passing their own validation gates.

## Correct next research direction

Do not relax the profitable chop rule, stack its H4 and M15 variants, or route
every empty date. Freeze one distinct economic mechanism per missing regime,
select it only in a development period, and judge it unchanged in a locked
later period. A sleeve may join the portfolio only if its own PF, stressed PF,
winner-removal PF, chronological halves, and date-overlap checks pass. The
protected M15 sleeve remains the benchmark and stays disarmed for demo orders
until prospective confirmation is available.

