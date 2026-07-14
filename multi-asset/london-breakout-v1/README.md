# Multi-Asset London Range Expansion Fast Discovery V1

This lane implements the reviewer-mandated pre-scoring data and contract gate for the frozen London range-expansion hypothesis. The exact branch starts from `68a9988d51d04fe0c5812792e7c347570b75fb27` with tree `a769ab1bcaf3311a2004db7cf6f05928aabfa729`.

The gate stops before strategy scoring because none of the four instruments has complete 2016-07-01 through 2026-06-30 raw Bid/Ask ticks or broker-faithful tick-derived executable M5 bars. GBPUSD also lacks the repository Capital.com H1/M15/M5 history. Existing historical files for the other instruments contain bar OHLC plus one spread field and are explicitly prohibited as promotion-grade execution evidence.

No strategy result, parameter search, instrument selection, EA, deployment, demo/live execution, broker order or risk increase was performed.

Run:

```powershell
python multi-asset/london-breakout-v1/run_data_gate.py --config multi-asset/london-breakout-v1/config/london_breakout_v1.json
python -m pytest multi-asset/london-breakout-v1/tests -q
```
