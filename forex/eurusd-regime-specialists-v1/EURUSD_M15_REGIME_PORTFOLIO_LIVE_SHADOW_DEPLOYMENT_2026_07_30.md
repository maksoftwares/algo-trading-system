# EURUSD M15 regime-portfolio live shadow deployment

Deployment verified: `2026-07-30 06:57:52 UTC`

Status: **PASS_RUNNING_PRESTART / NO ORDER AUTHORIZATION**

## Runtime

- Terminal root: `C:\MT5PortableM15RegimeShadow`
- Terminal build: `6061`
- Process at verification: `35060`
- Demo account: `1033669`
- Server: `Capital.ComMena-Demo`
- Account mode: hedging
- Synchronized positions/orders: `0 / 0`
- Chart: `EURUSD M15`
- Expert: `EurUsdM15RegimePortfolioControlledDemo`
- Deployed EX5 SHA-256:
  `72fc36da10691e6fa9077300748abb632b70134cba0ba04f91aadcb8ee7fdf90`

The terminal startup configuration globally enforces
`AllowLiveTrading=0` and `AllowDllImport=0`. The loaded preset independently
enforces shadow mode, disabled orders, active emergency stop, disabled tester
orders, a disarmed token, and the untouched `2026-08-01 00:00 UTC` forward
floor.

## Prestart audit

The live ledger contains exactly the expected `INIT_OK` and `STARTUP_LATCH`
events. All 16 audit checks pass:

- exact run, account, server, symbol, and time parsing;
- shadow true, orders false, and emergency stop true;
- successful initialization and startup latch;
- no initialization failure;
- no order send or position-management action;
- no signal before the forward floor; and
- every future shadow signal must have a matching
  `ORDER_BLOCKED=shadow_or_orders_disabled` record.

The frozen logger omitted its CSV header row. The health auditor supplies the
fixed 18-column schema and refuses malformed rows; no strategy rerun or rule
change was made.

## Unattended guard

Windows task `Codex-EURUSD-M15-Regime-Shadow-Health` runs every five minutes
with limited privileges and interactive logon. Its first scheduled execution
completed with result `0`. The guard:

1. verifies the deployed EA, preset, and startup configuration against the
   packaged SHA-256 values;
2. verifies all independent no-order settings;
3. restarts only this exact portable terminal if it stops;
4. audits every shadow ledger row; and
5. returns failure if any order action, pre-floor signal, identity mismatch,
   malformed row, or configuration drift appears.

The same five-minute cycle also runs the hash-locked forward adjudicator. It
matches future signals to the independent prospective EURUSD M5 bid/ask
collector, resolves stop first then target, enforces the 12-hour hold, and
refuses any change to a prior terminal outcome. Its verified prestart state is
zero signals, zero resolved trades, zero invalid outcomes, and
`WAITING_MINIMUM_EVIDENCE`; demo-order authorization is false.

The cycle now also runs the separately hash-locked combined frequency
portfolio validator. It causally merges the M15 regime portfolio with the
daily cross-pair learner, applies the frozen USD 15 / three-position risk cap,
and measures both edge and the explicit 0.85-to-1.25-trades-per-complete-day
target. It finalizes only complete days with terminal component evidence, so a
late outcome can never reorder or rewrite the append-only portfolio ledger.
The updated scheduled task ran at `2026-07-30 07:24:31 UTC` with result `0`;
its prestart state is zero complete validation days, zero portfolio trades,
`WAITING_MINIMUM_EVIDENCE`, and no order authorization.

This proves a safe, unattended prospective shadow deployment. It does not
authorize orders and does not close the remaining frequency gap.
