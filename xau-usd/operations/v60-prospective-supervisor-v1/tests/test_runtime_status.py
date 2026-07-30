from __future__ import annotations

from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "v60_prospective_runtime_status",
    ROOT / "runtime_status.py",
)
assert SPEC is not None and SPEC.loader is not None
runtime_status = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runtime_status
SPEC.loader.exec_module(runtime_status)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def fixture_config(tmp_path: Path, now: datetime) -> dict[str, Any]:
    runtime = tmp_path / "runtime"
    write_json(
        runtime / "process_state.json",
        {
            "updated_at_utc": runtime_status.utc_text(now),
            "terminal_running": True,
            "all_workers_running": True,
            "workers": [],
        },
    )
    write_json(
        tmp_path / "health.json",
        {
            "updated_at_utc": runtime_status.utc_text(now),
            "status": "ACTIVE",
            "account_login": 1033030,
            "ml_runtime_authorized": False,
        },
    )
    return {
        "schema_version": "test_runtime_supervisor",
        "poll_seconds": 60,
        "runtime": {
            "directory": str(runtime),
            "process_state": "process_state.json",
            "status": "status.json",
        },
        "health_sources": [
            {
                "id": "TEST",
                "path": str(tmp_path / "health.json"),
                "timestamp_fields": ["updated_at_utc"],
                "maximum_age_seconds": 120,
                "required_values": {
                    "account_login": 1033030,
                    "ml_runtime_authorized": False,
                },
                "forbidden_status_values": {"status": ["FAILED_CLOSED"]},
            }
        ],
    }


def test_ready_when_processes_and_health_are_current(tmp_path: Path) -> None:
    now = datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc)
    status = runtime_status.build_status(
        fixture_config(tmp_path, now),
        now=now,
        repo_root=tmp_path,
    )
    assert status["status"] == "READY"
    assert status["healthy"] is True


def test_stale_health_fails_closed(tmp_path: Path) -> None:
    now = datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc)
    config = fixture_config(tmp_path, now)
    health_path = tmp_path / "health.json"
    payload = json.loads(health_path.read_text(encoding="utf-8"))
    payload["updated_at_utc"] = runtime_status.utc_text(
        now - timedelta(minutes=10)
    )
    write_json(health_path, payload)

    status = runtime_status.build_status(config, now=now, repo_root=tmp_path)
    assert status["status"] == "NOT_READY"
    assert "Stale" in status["health_sources"][0]["errors"][0]


def test_failed_closed_source_is_rejected(tmp_path: Path) -> None:
    now = datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc)
    config = fixture_config(tmp_path, now)
    health_path = tmp_path / "health.json"
    payload = json.loads(health_path.read_text(encoding="utf-8"))
    payload["status"] = "FAILED_CLOSED"
    write_json(health_path, payload)

    status = runtime_status.build_status(config, now=now, repo_root=tmp_path)
    assert status["status"] == "NOT_READY"
    assert "Forbidden value" in status["health_sources"][0]["errors"][0]


def test_missing_worker_is_rejected(tmp_path: Path) -> None:
    now = datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc)
    config = fixture_config(tmp_path, now)
    process_path = tmp_path / "runtime" / "process_state.json"
    payload = json.loads(process_path.read_text(encoding="utf-8"))
    payload["all_workers_running"] = False
    write_json(process_path, payload)

    status = runtime_status.build_status(config, now=now, repo_root=tmp_path)
    assert status["status"] == "NOT_READY"
    assert "supervised workers" in status["process_errors"][0]


def test_windows_utf8_bom_process_state_is_accepted(tmp_path: Path) -> None:
    now = datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc)
    config = fixture_config(tmp_path, now)
    process_path = tmp_path / "runtime" / "process_state.json"
    payload = process_path.read_text(encoding="utf-8")
    process_path.write_text(payload, encoding="utf-8-sig")

    status = runtime_status.build_status(config, now=now, repo_root=tmp_path)
    assert status["status"] == "READY"


def test_only_deployed_demo_workers_are_supervised() -> None:
    config = runtime_status.read_json(
        ROOT / "config" / "runtime_supervisor_v1.json"
    )
    workers = {str(row["id"]): row for row in config["workers"]}
    sources = {str(row["id"]): row for row in config["health_sources"]}
    assert set(workers) == {
        "V60_FEEDS",
        "V60_PORTFOLIO",
        "V60_DEPLOYED_SPECIALIST_MONITOR",
    }
    assert set(sources) == {
        "V60_STATUS",
        "V60_FEED_STATUS",
        "V60_DEPLOYED_SPECIALIST_STATUS",
    }
    assert workers["V60_PORTFOLIO"]["args"][-1].endswith(
        "v60_portable_ml_topup_v4_overlay.json"
    )


def test_v60_health_requires_clear_risk_state_and_no_entry_halt() -> None:
    config = runtime_status.read_json(
        ROOT / "config" / "runtime_supervisor_v1.json"
    )
    sources = {str(row["id"]): row for row in config["health_sources"]}
    required = sources["V60_STATUS"]["required_values"]
    assert required["drawdown_suspended"] is False
    assert required["hard_floating_stop"] is False
    assert required["combined_closed_drawdown_hard_stop"] is False
    assert required["active_entry_halt_files"] == []
    assert required["emergency_close_failures"] == 0
    assert required["equity_fraction_limits_enabled"] is True
    assert required["minimum_balance_requirement_enabled"] is False
    assert required["ml_runtime_authorized"] is True
    assert required["ml_topup.ready"] is True
