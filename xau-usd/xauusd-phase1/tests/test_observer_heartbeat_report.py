from __future__ import annotations

import csv
import importlib.util
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_observer_heartbeat_report_passes_for_fresh_files(tmp_path: Path):
    module = _load_module()
    now = datetime(2026, 6, 12, 8, 0, tzinfo=timezone.utc)
    files_dir = tmp_path / "files"
    files_dir.mkdir()
    for index in range(2):
        _write_csv(files_dir / f"observer_{index}.csv", [{"a": "1"}])
        _set_mtime(files_dir / f"observer_{index}.csv", now - timedelta(minutes=2))

    lane = module.ObserverLane("test_lane", files_dir, ("observer_*.csv",), expected_min_files=2, warn_after_minutes=15)
    output = module.generate_observer_heartbeat_report(tmp_path, lanes=(lane,), now=now)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "PASS"
    assert payload["lanes"][0]["file_count"] == 2
    assert payload["lanes"][0]["files"][0]["row_count"] == 1


def test_observer_heartbeat_report_warns_for_stale_files(tmp_path: Path):
    module = _load_module()
    now = datetime(2026, 6, 12, 8, 0, tzinfo=timezone.utc)
    files_dir = tmp_path / "files"
    files_dir.mkdir()
    _write_csv(files_dir / "observer.csv", [{"a": "1"}])
    _set_mtime(files_dir / "observer.csv", now - timedelta(minutes=45))

    lane = module.ObserverLane("test_lane", files_dir, ("observer.csv",), expected_min_files=1, warn_after_minutes=15)
    output = module.generate_observer_heartbeat_report(tmp_path, lanes=(lane,), now=now)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "WARN"
    assert payload["lanes"][0]["checks"][1]["status"] == "WARN"


def test_observer_heartbeat_report_fails_when_expected_files_are_missing(tmp_path: Path):
    module = _load_module()
    now = datetime(2026, 6, 12, 8, 0, tzinfo=timezone.utc)
    files_dir = tmp_path / "missing"

    lane = module.ObserverLane("test_lane", files_dir, ("observer.csv",), expected_min_files=1, warn_after_minutes=15)
    output = module.generate_observer_heartbeat_report(tmp_path, lanes=(lane,), now=now)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "FAIL"
    assert payload["lanes"][0]["checks"][0]["status"] == "FAIL"


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["a"])
        writer.writeheader()
        writer.writerows(rows)


def _set_mtime(path: Path, value: datetime) -> None:
    timestamp = value.timestamp()
    os.utime(path, (timestamp, timestamp))


def _load_module():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "generate_observer_heartbeat_report.py"
    spec = importlib.util.spec_from_file_location("generate_observer_heartbeat_report", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_observer_heartbeat_report"] = module
    spec.loader.exec_module(module)
    return module
