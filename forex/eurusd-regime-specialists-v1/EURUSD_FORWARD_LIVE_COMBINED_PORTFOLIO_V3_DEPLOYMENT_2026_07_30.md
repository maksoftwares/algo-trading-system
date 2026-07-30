# EURUSD live-only combined forward portfolio v3 deployment — 2026-07-30

## Result

The final live-only frequency and economic admission ledger is frozen and
running unattended.

V3 consumes only:

- prospective protected M15 outcomes; and
- residual outcomes resolved from an immutable pre-outcome signal, the exact
  MT5 demo entry quote, and raw broker ticks.

It consumes zero research residual outcomes and zero rejected daily-learner
trades. It has no order path and always reports
`demo_order_authorized=false`.

## Why V2 was not sufficient

V2 correctly measured the target geometry, but its residual P&L came from the
later research evaluator. That was suitable for prospective strategy research,
not final execution admission. The 20:00 decision could only become tradable
after a separate publisher, MT5 quote bridge, raw-tick outcome adjudicator, and
selection-parity ledger existed.

Those layers now exist. V3 refuses the research residual ledger entirely.

The rejected daily learner is intentionally excluded. Its exact diagnostic
found 34 trades over 2,571 post-warmup weekdays, 0.013 trade per weekday,
PF 0.909, and negative net R. Including it would add negligible frequency while
weakening the portfolio.

## Frozen target

V3 admits only after all of:

- 160 complete prospective weekdays;
- at least 136 combined trades and 50 live residual trades;
- 0.85 through 1.25 trades per complete weekday;
- at least 65% weekday trade coverage;
- 45% through 60% wins;
- payoff at least 1.25;
- PF at least 1.15 and stressed PF at least 1.05;
- robust winner-removal and chronological-half PF;
- positive net P&L;
- maximum USD 75 closed-trade drawdown;
- maximum 40% single-month gross-profit share;
- M15 and live-residual PF of at least 1.15;
- zero invalid outcomes and zero selection mismatches;
- independent component admissions, MT5 parity, and soak; and
- combined ordering parity and combined disarmed-demo soak.

M15 chop and compression retain priority under overlap. The portfolio does not
force a trade on a cash day.

## Frozen prestart boundary

The contract was frozen at `2026-07-30T09:15:29Z`, before the
`2026.08.01 00:00:00` UTC floor, with:

- post-floor feature rows: 0;
- M15 terminal outcomes: 0;
- residual live outcomes: 0;
- residual selection-parity rows: 0;
- portfolio decisions: 0;
- historical backtesting prohibited; and
- demo-order authorization false.

The lock covers the V3 contract, implementation, tests, operations scripts,
the unchanged M15 normalization engine, the protected M15 lock, and all three
live residual execution locks.

## Prestart verification

Repository and deployed prestart outputs match exactly:

| File | SHA-256 |
|---|---|
| `FORWARD_LIVE_PORTFOLIO_LEDGER.json` | `37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570` |
| `FORWARD_LIVE_SUMMARY.json` | `7a70b5a2dd4dc7b10d87599935116d9d0d91b0aab342916093c4abbecb555f26` |
| `FORWARD_LIVE_SUMMARY.md` | `ce918dc57fdab4509ed2c339051aa7ebb4aa4b71791b5cbb30a38e927eccdfcb` |

The result is:

- status: `WAITING_MINIMUM_LIVE_EVIDENCE`;
- complete weekdays: 0;
- trades: 0;
- frequency: 0.000000;
- coverage: 0.000000;
- research residual outcomes consumed: 0;
- daily-learner trades consumed: 0; and
- demo-order authorization: false.

Verification completed with:

- 12 focused V3 tests;
- 32 combined-validator regression tests;
- 50 prospective residual-pipeline tests;
- Ruff clean;
- both PowerShell parsers clean; and
- frozen hash verification clean.

## Unattended operation

Windows task: `Codex-EURUSD-Forward-Live-Combined-V3`

- limited interactive principal;
- daily at 06:30 Dubai / 02:30 UTC;
- ten minutes after the raw-tick outcome adjudicator;
- maximum one concurrent instance;
- three automatic retries;
- 15-minute execution limit;
- first task result: 0;
- missed runs: 0; and
- next run at deployment: 2026-07-31 06:30 Dubai.

The deployed state is
`C:\MT5PortableM15RegimeShadow\EURUSDM15ShadowState\combined_live_v3`.

## Meaning

The monitoring and evidence pipeline is ready for disarmed demo observation.
The trading system is not yet admitted for demo orders. The remaining gap is
genuine forward evidence: the residual expert must actually supply the missing
weekday coverage while both components retain their edge. If it fails, the
correct result is rejection rather than another round of post-result tuning.
