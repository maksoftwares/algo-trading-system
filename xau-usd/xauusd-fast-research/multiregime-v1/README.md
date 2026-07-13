# XAUUSD Multi-Regime Fast Discovery V1

This isolated research lane implements the reviewer-authorized, frozen XAUUSD multi-regime screen. Completed H4 bars own the regime, completed H1 bars supply tactical structure, completed M15 bars form signals, and ordered M5 Bid/Ask bars replay execution. It does not authorize MT5 trading, EA work, deployment, threshold changes, or a timeframe sweep.

The existing Capital.com processed history supplies 2016-07-01 through 2025-06-30. A read-only MT5 acquisition appends the same-broker 2025-07-01 through 2026-06-30 tail to an ignored cache under `data/cache/`. No account order is sent or modified.

The frozen screen abandons the direction with no rescue. No family passes its standalone gate, so the portfolio admission rule correctly admits no family to a combined portfolio. Standalone diagnostics remain available in `outputs/`, including all trade/signal ledgers, segment results, rolling results, gate audit and a portable SHA-256 manifest. The captured contract snapshot records the broker's read-only `OrderCalcProfit` and `OrderCalcMargin` evidence used for the $1,000 / 0.5% risk audit.

Run:

```powershell
python -m pytest xau-usd/xauusd-fast-research/multiregime-v1/tests -q
python xau-usd/xauusd-fast-research/multiregime-v1/run_multiregime_fast_discovery_v1.py --config xau-usd/xauusd-fast-research/multiregime-v1/config/multiregime_fast_discovery_v1.json
```
