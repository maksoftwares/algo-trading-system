# XAU/XAG Relative Value Export Presets

These presets collect the XAGUSD H1 feeds required by `xau_xag_relative_value_v0`.

Use them with:

```text
mt5/PassiveBarExporter_Phase0.mq5
```

## Presets

| Preset | Broker | Symbol | Window |
| --- | --- | --- | --- |
| `XAGUSD_H1_20160101_20181231_capital_com.set` | capital_com | XAGUSD | 2016.01.01 00:00 through 2018.12.31 23:59 |
| `XAGUSD_H1_20190101_20211231_pepperstone.set` | pepperstone | XAGUSD | 2019.01.01 00:00 through 2021.12.31 23:59 |
| `XAGUSD_H1_20220101_20241231_dukascopy.set` | dukascopy | XAGUSD | 2022.01.01 00:00 through 2024.12.31 23:59 |

## Verify

After export and normalization, run:

```powershell
.\.venv\Scripts\phase0.exe generate-xau-xag-relative-data-readiness
```

Do not run a research matrix for `xau_xag_relative_value_v0` until readiness is `PASS`.
