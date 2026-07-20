# V60 Post-Run Exact-Episode Verification

This is a diagnostic performed after the locked V60 M5 result. It did not select,
change, or rescue any trade or gate.

V60 identified a global M5 peak hour beginning `2024-07-17 14:00 UTC` and a
global M5 trough bar beginning `2024-09-10 14:10 UTC`. The corresponding raw
Dukascopy tick files were decoded using cumulative millisecond and quote deltas.
At every tick, completed trades contributed their locked result and all active
trades were marked on bid for longs and ask for shorts, with the same entry-cost
policy used by V60.

## Immutable Inputs

| Episode | Raw file | SHA-256 | Ticks |
|---|---|---|---:|
| Peak hour | `C:/DukascopyTickDataFoundationV1/raw/XAUUSD/year=2024/month=07/2024071714.json` | `6940977ccdeacd9390cc6334bd3271034b6921e86a70618101aee29bcc9c7cef` | 31,495 |
| Trough hour | `C:/DukascopyTickDataFoundationV1/raw/XAUUSD/year=2024/month=09/2024091014.json` | `588c3e0c66f4ae98cf188c7985eb2628e71a662e3eae07c8a291dfc330bb5936` | 20,602 |

## Result

| Scenario | Exact peak UTC | Exact trough UTC | Exact episode DD | V60 M5 DD |
|---|---|---|---:|---:|
| Locked P&L | `2024-07-17 14:00:24.746` | `2024-09-10 14:14:14.463` | USD 328.7742 | USD 329.6442 |
| R1 + USD 0.30 fee stress | `2024-07-17 14:00:24.746` | `2024-09-10 14:14:14.463` | USD 334.4742 | USD 335.3442 |

The raw-tick episode is USD `0.87` below the M5 envelope in both scenarios. This
independently confirms that the locked full-bar M5 boundary rule was conservative
for the identified global episode. The result remains historical research and does
not replace MT5 portfolio parity or sealed prospective shadow evidence.
