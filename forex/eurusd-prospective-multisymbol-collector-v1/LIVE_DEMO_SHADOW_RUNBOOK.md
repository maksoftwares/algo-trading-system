# Live demo shadow runbook

This runbook starts the prospective collector on a dedicated MetaTrader 5
portable terminal. It does not authorize or enable trading.

## Immutable safety conditions

- The collector source and compiled artifact contain no order function.
- The terminal startup configuration sets `AllowLiveTrading=0`.
- DLL imports are disabled.
- The collector accepts only Strategy Tester or a demo account.
- The configured forward floor is `2026.08.01 00:00 UTC`.
- The collector writes raw observations only; it does not emit a trade signal.

## Dedicated terminal layout

Copy, without renaming:

- `mt5/Experts/EurUsdProspectiveMultiSymbolCollector.ex5` to
  `MQL5/Experts/`
- `mt5/Presets/EURUSD_PROSPECTIVE_MULTISYMBOL_COLLECTOR_DEMO.set` to
  `MQL5/Presets/`
- `mt5/Config/EURUSD_PROSPECTIVE_MULTISYMBOL_COLLECTOR_LIVE_DEMO_SHADOW.ini`
  to a dedicated filename under `Config/`

Start the dedicated terminal using:

```powershell
terminal64.exe /portable /config:path\to\collector_startup.ini
```

MetaTrader opens EURUSD M5 and attaches the observer using the safe preset. The
terminal must already contain the intended demo account credentials. If the
stored account is not demo, the EA refuses startup.

## First-session acceptance

The Common Files environment CSV must show:

- `evidence_scope=PROSPECTIVE_DEMO`
- `chart_period=PERIOD_M5`
- `trade_permission=NONE_READ_ONLY`
- the exact eight-source reference list
- `account_trade_mode=0` (`ACCOUNT_TRADE_MODE_DEMO`)
- a `STARTUP_LATCH` heartbeat

Compare `observed_current_minus_gmt_seconds` with
`InpBrokerUtcOffsetSeconds`. If they differ, stop before the forward floor and
freeze a corrected owner-specific preset. Do not rewrite timestamps after
collection begins.

## Kill conditions

Stop the dedicated terminal and preserve its logs if:

- the account is not demo;
- the EA is attached to anything other than the configured EURUSD M5 chart;
- the configured UTC offset is wrong after the forward floor;
- the heartbeat is absent for more than five minutes while quotes are flowing;
- files become unwritable;
- duplicate-instance protection rejects startup; or
- any file contains an evidence scope other than `PROSPECTIVE_DEMO`.

An unavailable cross-pair is not filled or silently renamed. Record the broker's
exact symbol and freeze an owner-specific source map before using that feed.
