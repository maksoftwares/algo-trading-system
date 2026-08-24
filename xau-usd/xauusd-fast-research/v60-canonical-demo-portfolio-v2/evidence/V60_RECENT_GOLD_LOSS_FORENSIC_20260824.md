# V60 Recent Gold Loss Forensic

Date: 2026-08-24 UTC

Scope: Capital.com demo account `1033030`, XAUUSD only. Broker P/L was
converted from AED to USD at `3.6725`.

## Observed performance

| Window | Trades | Wins | Losses | Win rate | Net P/L | Profit factor | Closed DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2026-08-01 through 2026-08-24 | 23 | 10 | 13 | 43.48% | -$12.97 | 0.906 | $74.68 |
| 2026-08-01 through 2026-08-16 | 14 | 9 | 5 | 64.29% | +$54.47 | 1.992 | $13.67 |
| 2026-08-17 through 2026-08-24 | 9 | 1 | 8 | 11.11% | -$67.44 | 0.193 | $67.44 |

August source concentration:

- V57: 20 of 23 trades, 9 wins, 11 losses, `+$3.47`, PF `1.030`.
- R4: one winner, `+$6.40`.
- R1 pullback: one loss, `-$14.53`.
- V7: one loss, `-$8.31`.

The portfolio did not fail uniformly. The recent loss cluster was dominated by
V57, which supplied 87% of August trades.

## What happened

1. Six recent V57 losses had almost no favorable excursion. Trailing stops or
   break-even logic could not have converted them into winners; they needed to
   be rejected before entry or accepted as normal strategy losses.
2. The V57 100-outcome health gate reacted too slowly. It still reported PF
   `1.238`, while the most recent 20 virtual outcomes were 5 wins and 15 losses,
   net `-$67.07`, PF `0.560`. That is near the bottom 5% of historical rolling
   20-trade V57 windows, but similar clusters did occur historically.
3. The first 2026-08-24 Dubai-day loss entered at `2026-08-23T23:37Z`, a
   Sunday-UTC weekly reopen. The 610-trade V57 historical source corpus contains
   zero weekend entries, so live execution had crossed outside its evidence
   domain.
4. The second Dubai-day loss used about `$19.47` initial risk after a `$9.49`
   loss. Its full-stop day loss could exceed the guardian's `-100 AED` budget.
   The trade's volatility/risk was at roughly the 97th percentile of historical
   V57 risk, but high-risk V57 trades remain profitable as a group; a lower
   static risk cap is therefore not supported.
5. MT5 had compiled a guardian with halt-only daily-loss behavior after the
   terminal process started. The running terminal still held the older binary
   in memory and force-closed positions. On both recent guardian closes, the
   source stop was reached seconds later, so this defect was real but was not
   the main cause of the loss cluster.

## Counterfactual checks

| Candidate change | Result | Decision |
|---|---|---|
| V57 weekdays-only evidence domain | Blocks the Sunday loss; changes zero historical V57 trades | Deployed |
| Guardian daily loss halt-only | Preserves source-managed exits; full replay supports it | Reloaded and verified |
| Pre-entry daily stop-risk budget | DD `$238.28` to `$222.59`, but net `$3,603.57` to `$3,195.82` | Rejected |
| Fast 10/20/30-trade V57 health blocker | Reduced net in the 2025 or 2026 holdouts | Rejected |
| Generic individual trailing/break-even | Previously failed the locked recent-period gate | Rejected |
| Post-hoc ML rank veto below 0.30 | August net `-$12.97` to `+$42.64`; DD `$74.68` to `$30.08` | Research only |

The rank veto is the strongest lead, but only 22 prospective scores exist. The
threshold was inspected after the first outcomes. The two later 2026-08-24
losses both ranked below 0.30, which is useful forward confirmation but still
too small to authorize an execution veto without a preregistered sample gate.

## Applied repairs

- V57 now accepts entries only Monday through Friday UTC. Other sources retain
  their own calendar behavior.
- The weekday-domain rule is enforced in both the live executor and tick replay.
- Short-window 5/10/20/100 outcome health is emitted live as observability only;
  it cannot block or alter trades.
- MT5 was restarted. The fresh guardian startup row explicitly records
  `InpDailyLossStopClosePositions=false`.
- The current Dubai-day loss halt remains active and no XAUUSD position is open.

## Verification

- Focused tests: `56 passed`.
- Updated full tick replay: 1,390 closed trades, `$3,603.57` net, PF `1.7107`,
  maximum lifetime closed DD `$223.28`, maximum lifetime equity DD `$238.28`.
- Historical replay metrics are unchanged because no historical V57 candidate
  entered on a weekend.
- Live status: `ACTIVE_DEMO_BROKER_ACTION`, feed ready, zero XAUUSD positions,
  daily halt preserved.
