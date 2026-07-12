from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "analyze_a1_xau_r6_np1c_stop_packet.py"
SPEC = importlib.util.spec_from_file_location("a1_xau_r6_np1d1", SCRIPT)
assert SPEC and SPEC.loader
A = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(A)


def _json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def _bar_rows(timeframe: str, edits: dict[str, dict[str, str]] | None = None) -> list[dict[str, str]]:
    timestamps = {
        "H1": ["2020-01-03T20:00:00", "2020-01-05T22:00:00", "2020-01-05T23:00:00"],
        "H4": ["2020-01-03T20:00:00", "2020-01-05T20:00:00", "2020-01-06T00:00:00"],
        "D1": ["2020-01-03T00:00:00", "2020-01-06T00:00:00", "2020-01-07T00:00:00"],
    }[timeframe]
    rows = []
    for index, timestamp in enumerate(timestamps):
        row = {
            "schema_version": "a1_xau_r6_native_bar_v1", "timeframe": timeframe,
            "open_time_broker": timestamp, "open": str(100 + index), "high": str(101 + index),
            "low": str(99 + index), "close": str(100.5 + index), "tick_volume": str(10 + index),
            "spread": "3", "real_volume": str(1000 + index),
        }
        row.update((edits or {}).get(timestamp, {}))
        rows.append(row)
    return rows


def _write_bars(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=A.BAR_COLUMNS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _report(path: Path, ticks: int) -> None:
    cells = {
        "Period": "M5 (2015.06.01 - 2026.07.01)", "Bars": "779751", "Ticks": str(ticks),
        "Total Trades": "0", "Total Deals": "0",
    }
    body = "".join(f"<tr><td>{key}:</td><td><b>{value}</b></td></tr>" for key, value in cells.items())
    path.write_text(f"<html><table>{body}</table></html>", encoding="utf-8")


def _remake_manifest(raw: Path) -> str:
    artifacts = []
    for path in sorted((item for item in raw.rglob("*") if item.is_file()), key=lambda item: item.relative_to(raw).as_posix()):
        relative = path.relative_to(raw).as_posix()
        if relative in {"manifest.json", "manifest.sha256"}:
            continue
        artifacts.append({"relative_path": relative, "sha256": A.sha256_file(path), "size_bytes": path.stat().st_size})
    _json(raw / "manifest.json", {"artifacts": artifacts, "schema_version": "test"})
    sha = A.sha256_file(raw / "manifest.json")
    (raw / "manifest.sha256").write_text(sha + "\n", encoding="ascii")
    return sha


def _packet(
    root: Path, *, run2_edits: dict[str, dict[str, dict[str, str]]] | None = None,
    run2_extra: dict[str, dict[str, str]] | None = None, status: str = A.EXPECTED_STATUS,
    boundary: dict[str, bool] | None = None,
) -> Path:
    raw = root / "raw_packet"
    for run in ("run1", "run2"):
        run_dir = raw / "runs" / run
        run_dir.mkdir(parents=True, exist_ok=True)
        for timeframe in A.TIMEFRAMES:
            rows = _bar_rows(timeframe, (run2_edits or {}).get(timeframe) if run == "run2" else None)
            if run == "run2" and timeframe in (run2_extra or {}):
                rows.append({**rows[-1], **run2_extra[timeframe]})
            _write_bars(run_dir / f"native_{timeframe.lower()}_bars.tsv", rows)
        _report(run_dir / "native_report.htm", 100 if run == "run1" else 125)
    (raw / "compiled").mkdir(parents=True)
    (raw / "compiled" / "A1XauR6MarketOnlyNativeParityOracle.ex5").write_bytes(b"same-ex5")
    _json(raw / "compiled" / "source_equivalence.json", {"blocks": [{"exact_equal": True}]})
    _json(raw / A.STATUS_FILE, {
        "status": status,
        "boundary": boundary or {"census_generated": False, "pnl_calculated": False, "broker_action": False},
        "errors": {"invalid": ["stopped"], "parity": [], "source": [], "zero_action": []},
    })
    sha = _remake_manifest(raw)
    A.EXPECTED_INNER_MANIFEST_SHA256 = sha
    return root


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_wrong_raw_manifest_sha_fails_closed(tmp_path: Path) -> None:
    root = _packet(tmp_path / "diagnostic")
    A.EXPECTED_INNER_MANIFEST_SHA256 = "0" * 64
    with pytest.raises(ValueError, match="manifest SHA256"):
        A.build_diagnostic(root)


def test_edited_raw_packet_fails_closed(tmp_path: Path) -> None:
    root = _packet(tmp_path / "diagnostic")
    path = root / "raw_packet" / "runs" / "run1" / "native_h1_bars.tsv"
    path.write_text(path.read_text(encoding="utf-8") + "edited\n", encoding="utf-8")
    with pytest.raises(ValueError, match="artifact mismatch"):
        A.build_diagnostic(root)


def test_terminal_status_and_boundary_fail_closed(tmp_path: Path) -> None:
    wrong_status = _packet(tmp_path / "wrong-status", status="PASS")
    with pytest.raises(ValueError, match="terminal status"):
        A.build_diagnostic(wrong_status)
    for field in ("census_generated", "pnl_calculated", "broker_action"):
        boundary = {"census_generated": False, "pnl_calculated": False, "broker_action": False}
        boundary[field] = True
        root = _packet(tmp_path / field, boundary=boundary)
        with pytest.raises(ValueError, match="boundary violation"):
            A.build_diagnostic(root)


def test_identical_files_gap_inventory_and_tick_delta(tmp_path: Path) -> None:
    root = _packet(tmp_path / "diagnostic")
    result = A.build_diagnostic(root)
    assert result["stability_flags"] == ["RUN_FILES_IDENTICAL"]
    assert result["native_report_comparison"]["tick_delta_run2_minus_run1"] == 25
    gaps = list(csv.DictReader((root / "analysis" / "market_gap_inventory.csv").open(encoding="utf-8")))
    h1 = [row for row in gaps if row["timeframe"] == "H1" and row["prior_bar_time"] == "2020-01-03T20:00:00"]
    assert len(h1) == 1
    assert h1[0]["next_bar_time"] == "2020-01-05T22:00:00"
    assert h1[0]["duration_seconds"] == "180000"
    assert h1[0]["present_in_run1"] == h1[0]["present_in_run2"] == "true"


def test_run2_strict_timestamp_superset(tmp_path: Path) -> None:
    extra = {"H1": {"open_time_broker": "2020-01-06T00:00:00", "open": "110", "high": "111", "low": "109", "close": "110.5"}}
    root = _packet(tmp_path / "diagnostic", run2_extra=extra)
    result = A.build_diagnostic(root)
    assert "RUN2_TIMESTAMP_STRICT_SUPERSET" in result["stability_flags"]
    assert result["per_timeframe"]["H1"]["timestamps_only_in_run2"] == 1


@pytest.mark.parametrize(("field", "flag"), [
    ("open", "COMMON_TIMESTAMP_OHLC_DRIFT"),
    ("tick_volume", "COMMON_TIMESTAMP_VOLUME_OR_SPREAD_DRIFT"),
    ("spread", "COMMON_TIMESTAMP_VOLUME_OR_SPREAD_DRIFT"),
])
def test_common_timestamp_drift(field: str, flag: str, tmp_path: Path) -> None:
    edits = {"H1": {"2020-01-05T22:00:00": {field: "999"}}}
    root = _packet(tmp_path / field, run2_edits=edits)
    result = A.build_diagnostic(root)
    assert flag in result["stability_flags"]
    counts = result["per_timeframe"]["H1"]["changed_field_counts"]
    assert counts[field] == 1


def test_first_and_last_difference_calculation(tmp_path: Path) -> None:
    edits = {"H1": {
        "2020-01-03T20:00:00": {"low": "1"},
        "2020-01-05T23:00:00": {"close": "2"},
    }}
    root = _packet(tmp_path / "diagnostic", run2_edits=edits)
    result = A.build_diagnostic(root)
    h1 = result["per_timeframe"]["H1"]
    assert h1["first_differing_timestamp"] == "2020-01-03T20:00:00"
    assert h1["last_differing_timestamp"] == "2020-01-05T23:00:00"


def test_duplicate_timestamp_rejected(tmp_path: Path) -> None:
    root = _packet(tmp_path / "diagnostic")
    raw = root / "raw_packet"
    path = raw / "runs" / "run2" / "native_h1_bars.tsv"
    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join([*lines, lines[-1]]) + "\n", encoding="utf-8")
    A.EXPECTED_INNER_MANIFEST_SHA256 = _remake_manifest(raw)
    with pytest.raises(ValueError, match="duplicate bar timestamp"):
        A.build_diagnostic(root)


def test_deterministic_output_and_raw_packet_is_read_only(tmp_path: Path) -> None:
    root1 = _packet(tmp_path / "one")
    raw_hashes_before = {path.relative_to(root1).as_posix(): A.sha256_file(path) for path in (root1 / "raw_packet").rglob("*") if path.is_file()}
    result1 = A.build_diagnostic(root1)
    raw_hashes_after = {path.relative_to(root1).as_posix(): A.sha256_file(path) for path in (root1 / "raw_packet").rglob("*") if path.is_file()}
    assert raw_hashes_before == raw_hashes_after
    root2 = tmp_path / "two"
    shutil.copytree(root1 / "raw_packet", root2 / "raw_packet")
    A.EXPECTED_INNER_MANIFEST_SHA256 = A.sha256_file(root2 / "raw_packet" / "manifest.json")
    result2 = A.build_diagnostic(root2)
    assert result1 == result2
    files1 = {p.relative_to(root1).as_posix(): p.read_bytes() for p in root1.rglob("*") if p.is_file() and "raw_packet" not in p.parts}
    files2 = {p.relative_to(root2).as_posix(): p.read_bytes() for p in root2.rglob("*") if p.is_file() and "raw_packet" not in p.parts}
    assert files1 == files2


def test_no_mt5_runtime_or_result_research_surface() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert "subprocess" not in source
    assert "MetaTrader5" not in source
    assert "terminal64" not in source
    assert "OrderSend" not in source
    assert all(token not in source for token in ("net_profit", "profit_factor", "mfe", "mae"))


def test_outer_nonrecursive_manifest_verification(tmp_path: Path) -> None:
    root = _packet(tmp_path / "diagnostic")
    A.build_diagnostic(root)
    A.verify_nonrecursive_manifest(root)
    (root / "analysis" / "bar_file_hashes.csv").write_text("tampered\n", encoding="utf-8")
    with pytest.raises(ValueError, match="artifact mismatch"):
        A.verify_nonrecursive_manifest(root)
