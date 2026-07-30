# EURUSD residual MT5 shadow bridge deployment — 2026-07-30

## Result

The read-only residual MT5 shadow bridge is frozen and running unattended.
When a pre-outcome signal appears, it captures the real Capital.com demo
bid/ask and records a would-enter receipt. It cannot call any order or position
API.

## Why this is required

The residual research evaluator assumes an entry from its frozen 20:00 outcome
path. The live signal publisher runs shortly afterward. Those are not the same
quote.

Using the research entry for demo-readiness P&L would overstate execution
fidelity. The bridge therefore records the actual quote available when the
live signal is received. Only that captured entry may be used for the
live-only outcome and combined portfolio.

## Frozen safety boundary

The implementation was locked at `2026-07-30T08:52:52Z`, before the
`2026.08.01 00:00:00` UTC evidence floor. At lock time:

- post-floor feature rows: 0;
- live signals: 0;
- MT5 receipts: 0;
- shadow entries: 0;
- order API calls: 0;
- position mutation attempts: 0;
- historical backfill: prohibited; and
- demo-order authorization: false.

The bridge pins:

- MetaTrader5 Python API version `5.0.6070`;
- `C:\MT5PortableProspectiveCollector\terminal64.exe`;
- demo login `1033669`;
- server `Capital.ComMena-Demo`;
- demo trade mode;
- exact symbol `EURUSD`;
- maximum 120-second receipt delay;
- maximum 15-second tick age; and
- maximum two-pip spread.

The lock covers the config, protocol, runner, implementation, tests,
operations scripts, and upstream live-publisher lock.

## Entry receipt

For a valid signal:

- LONG uses the current ask;
- SHORT uses the current bid;
- size is fixed at 0.01 lot;
- stop is eight pips;
- target is 12 pips; and
- maximum hold is six hours.

The immutable receipt contains the terminal tick time, bid, ask, spread,
side, entry, stop, target, and explicit `order_api_called=false` and
`position_mutation_attempted=false` fields.

Cash decisions do not open the MT5 API. Late signals become permanent cash.
Wrong account, server, mode, symbol, stale tick, or invalid quote fails closed.

## Verification

The exact MetaTrader5 API successfully initialized against the running
portable collector terminal. The read-only diagnostic returned:

- login: `1033669`;
- server: `Capital.ComMena-Demo`;
- trade mode: demo (`0`);
- symbol: `EURUSD`; and
- a valid positive bid/ask tick.

No order function was called.

Prestart result:

- status: `WAITING_SIGNALS`;
- published decisions: 0;
- receipts: 0;
- shadow entries captured: 0;
- cash receipts: 0;
- order API calls: 0;
- position mutation attempts: 0; and
- `demo_order_authorized=false`.

Repository and deployed prestart outputs match:

| File | SHA-256 |
|---|---|
| `FORWARD_RESIDUAL_MT5_SHADOW_RECEIPTS.json` | `37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570` |
| `FORWARD_RESIDUAL_MT5_SHADOW_SUMMARY.json` | `eaa7ec4d328d05a706ca54d86753327c3625064480082c99a7b4770d9a1d7cb7` |
| `FORWARD_RESIDUAL_MT5_SHADOW_SUMMARY.md` | `0156345f76b6aa8b5b5815ef6dd0637f668ce480e94ebc94bab3ecb0d57698cb` |

Eight focused tests pass, including long/short quote use, cash without MT5
initialization, late refusal, stale tick and account failure, append-only
receipts, no-order guards, and hash verification. Ruff and both PowerShell
parser checks pass.

## Unattended deployment

Windows task: `Codex-EURUSD-Forward-Residual-MT5-Shadow`

- limited interactive principal;
- daily at 00:04 Dubai / 20:04 UTC;
- one minute after the signal publisher;
- maximum one concurrent instance;
- three automatic retries;
- ten-minute execution limit;
- first manual run result: 0;
- missed runs: 0; and
- next scheduled run at deployment: 2026-07-31 00:04 Dubai.

## Remaining execution proof

This bridge proves an executable demo quote can be captured without placing an
order. It does not yet prove the live residual edge.

The next step must preserve raw broker ticks beginning at the captured tick,
resolve the 8/12-pip path and six-hour timeout from that exact entry, compare
the published selection with the terminal research decision, and feed only
captured live outcomes into the final combined portfolio.
