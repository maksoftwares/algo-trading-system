# WR50 Deployment Checklist

Document date: 2026-06-04

Do not attach any WR50 EA to a chart until every item is checked by a human reviewer.

## Pre-Deployment

1. Confirm demo account only.
2. Confirm account number/server match owner authorization.
3. Confirm no live account login.
4. Confirm fixed lot/min lot.
5. Confirm max spread points.
6. Confirm all three EAs have unique magic numbers.
7. Confirm each EA is attached to intended chart only.
8. Confirm Algo Trading enabled only for demo terminal.
9. Confirm no existing observed EA was modified.
10. Confirm logs are being written.
11. Confirm first trade has correct magic/comment.
12. Confirm daily report can parse trade history.

## Runtime Files

Copy the runtime registry CSV into the terminal data folder:

```text
<MQL5 data folder>/MQL5/Files/WR50/wr50_runtime_registry.csv
```

Optional allowlist file:

```text
<MQL5 data folder>/MQL5/Files/WR50/wr50_account_allowlist.csv
```

## Compile Instructions

Adjust the MetaEditor path if needed:

```powershell
$repo = "C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system"
$metaeditor = "C:\Program Files\MetaTrader 5\metaeditor64.exe"
& $metaeditor /compile:"$repo\xau-usd\xauusd-wr50-experimental\mt5\Experts\WR50_BreakoutEvening_v0.mq5" /log:"$repo\xau-usd\xauusd-wr50-experimental\outputs\reports\compile_BEV0.log"
& $metaeditor /compile:"$repo\xau-usd\xauusd-wr50-experimental\mt5\Experts\WR50_BreakoutQuality_v0.mq5" /log:"$repo\xau-usd\xauusd-wr50-experimental\outputs\reports\compile_BQV0.log"
& $metaeditor /compile:"$repo\xau-usd\xauusd-wr50-experimental\mt5\Experts\WR50_BreakoutExit1R_v0.mq5" /log:"$repo\xau-usd\xauusd-wr50-experimental\outputs\reports\compile_E1R0.log"
```

If direct compilation from the repo path is not supported, copy files to:

```text
<MQL5 data folder>/MQL5/Experts/WR50/
<MQL5 data folder>/MQL5/Include/WR50/
```

Do not deploy to a live terminal.

