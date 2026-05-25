from __future__ import annotations

import csv
from pathlib import Path


EXPECTED_EXPORTS = {
    ("pepperstone", "EURUSD"): ("2019.01.01 00:00", "2021.12.31 23:59"),
    ("pepperstone", "USDJPY"): ("2019.01.01 00:00", "2021.12.31 23:59"),
    ("dukascopy", "EURUSD"): ("2022.01.01 00:00", "2024.12.31 23:59"),
    ("dukascopy", "USDJPY"): ("2022.01.01 00:00", "2024.12.31 23:59"),
}


def test_gold_fx_proxy_export_presets_match_proxy_data_requirements(project_root: Path):
    preset_dir = project_root / "mt5" / "gold_fx_proxy_export_presets"
    manifest_path = preset_dir / "MANIFEST.csv"
    requirement_path = project_root / "docs" / "GOLD_FX_PROXY_DIVERGENCE_V0_DATA_REQUIREMENTS.csv"

    manifest_rows = list(csv.DictReader(manifest_path.open(encoding="utf-8")))
    requirement_rows = list(csv.DictReader(requirement_path.open(encoding="utf-8")))
    proxy_requirements = {
        (row["broker"], row["symbol"]): row
        for row in requirement_rows
        if (row["broker"], row["symbol"]) in EXPECTED_EXPORTS
    }

    assert set(proxy_requirements) == set(EXPECTED_EXPORTS)
    assert {(row["broker"], row["symbol"]) for row in manifest_rows} == set(EXPECTED_EXPORTS)

    for row in manifest_rows:
        broker = row["broker"]
        symbol = row["symbol"]
        start, end = EXPECTED_EXPORTS[(broker, symbol)]
        preset = _read_set_file(preset_dir / row["preset_file"])
        requirement = proxy_requirements[(broker, symbol)]

        assert preset["InpSymbol"] == symbol
        assert preset["InpBrokerLabel"] == broker
        assert preset["InpTimeframes"] == "H1"
        assert preset["InpStartServerTime"] == start
        assert preset["InpEndServerTime"] == end
        assert preset["InpServerToUtcOffsetHours"] == "0"
        assert preset["InpUseCommonFiles"] == "true"
        assert row["timeframe"] == requirement["timeframe"] == "H1"
        assert row["expected_raw_file"] == (
            f"{requirement['raw_dir']}/{requirement['suggested_raw_filename']}"
        )
        assert row["expected_processed_folder"] == (
            f"data/processed/bars/{broker}/{symbol}/H1/"
        )


def _read_set_file(path: Path) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        key, value = line.split("=", 1)
        fields[key] = value
    return fields
