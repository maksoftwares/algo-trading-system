# V60 Drawdown Recovery V2 Replay

## Verdict

Pass for prospective demo deployment. Live authorization remains false.

## Exact before and after

| Metric | Before | After |
|---|---:|---:|
| Trades | 1,584 | 1,584 |
| Net P/L | $2,628.49 | $2,628.49 |
| Profit factor | 1.4897 | 1.4897 |
| Win rate | 46.53% | 46.53% |
| Maximum closed drawdown | $203.68 | $203.68 |
| Maximum equity drawdown | $218.55 | $218.55 |
| Closed hard stop | $246.92 | $420.00 |
| Floating hard stop | $246.92 | $420.00 |
| Flat suspension deadlock | No | No |

The repaired policy preserved every accepted trade and every performance metric
on the exact 2021-2026 runtime replay. The change affects only the tail-risk path.

## Policy

- Entry exposure remains activation-equity scaled and capped at 6%.
- Fixed-0.01-lot drawdown limits are absolute USD values.
- The $420 hard stop is 1.505 times the fee-stressed $279.04 historical closed drawdown.
- At $225 closed drawdown, normal risk-taking stops and recovery mode begins.
- Recovery permits only R1 pullback or R2 downtrend, one position, one entry per UTC day, and at most $30 initial risk.
- Add-ons and ML top-ups are blocked during recovery.
- The hard stop remains final and closes V60 positions.

The $420 limit is suitable only for continued demo evidence at the current account
size. It would represent excessive percentage risk on a roughly $1,000 live account.
