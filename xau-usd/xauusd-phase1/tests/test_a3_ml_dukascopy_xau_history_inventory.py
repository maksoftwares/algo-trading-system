from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.a3_meta_v1.dukascopy_xau_history_inventory import (  # noqa: E402
    acquire_missing_history,
    inventory_history,
    month_range,
    validate_contract,
)


class FakeFoundationError(RuntimeError):
    pass


def _foundation(valid: set[str], calls: list[str]) -> SimpleNamespace:
    def validate(storage: Path, symbol: str, year: int, month: int) -> None:
        key = f"{year:04d}-{month:02d}"
        if key not in valid:
            raise FakeFoundationError("missing")

    def acquire(storage: Path, symbol: str, year: int, month: int, concurrency: int):
        key = f"{year:04d}-{month:02d}"
        calls.append(key)
        valid.add(key)
        return [{"status": "DOWNLOADED_VALID"}]

    def write_manifest(*args):
        return Path("manifest.json")

    def freeze(*args):
        return {"complete": True}

    return SimpleNamespace(
        FoundationError=FakeFoundationError,
        validate_month_acquisition_manifest=validate,
        acquire_month=acquire,
        write_month_acquisition_manifest=write_manifest,
        freeze_raw_month=freeze,
    )


def test_locked_range_has_exactly_120_months() -> None:
    months = month_range("2016-07", "2026-06")
    assert len(months) == 120
    assert months[0] == (2016, 7)
    assert months[-1] == (2026, 6)


def test_inventory_is_read_only_and_classifies_missing(tmp_path: Path) -> None:
    valid = {"2020-01"}
    foundation = _foundation(valid, [])
    root = tmp_path / "raw" / "XAUUSD" / "year=2020" / "month=01"
    root.mkdir(parents=True)
    marker = root / "marker.txt"
    marker.write_text("unchanged", encoding="ascii")
    before = marker.stat().st_mtime_ns
    report = inventory_history(tmp_path, "XAUUSD", [(2020, 1), (2020, 2)], foundation)
    assert report["valid_months"] == 1
    assert report["missing_months"] == 1
    assert marker.read_text(encoding="ascii") == "unchanged"
    assert marker.stat().st_mtime_ns == before


def test_acquisition_skips_valid_months(tmp_path: Path) -> None:
    valid = {"2020-01"}
    calls: list[str] = []
    foundation = _foundation(valid, calls)
    result = acquire_missing_history(
        tmp_path,
        "XAUUSD",
        [(2020, 1), (2020, 2)],
        foundation,
        concurrency=2,
    )
    assert calls == ["2020-02"]
    assert result["before"]["valid_months"] == 1
    assert result["after"]["valid_months"] == 2
    assert result["attempts"][0]["status"] == "ACQUIRED_VALID"


def test_contract_binds_sources_inputs_and_forbids_execution() -> None:
    path = ROOT / "config" / "ml" / "a3_ml_r1_r2_dukascopy_portability_v1.json"
    contract = json.loads(path.read_text(encoding="utf-8"))
    validate_contract(ROOT, contract)
    changed = copy.deepcopy(contract)
    changed["authorization"]["broker_action_authorized"] = True
    with pytest.raises(ValueError, match="forbidden authorization"):
        validate_contract(ROOT, changed)
