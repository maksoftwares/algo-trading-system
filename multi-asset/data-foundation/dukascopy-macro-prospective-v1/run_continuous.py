from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.snapshot import completed_hour_floor, parse_utc, run

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config/prospective_macro_v1.json"
DEFAULT_STORAGE = Path("D:/AlgoTradingData/C_DRIVE/DukascopyTickDataFoundationV1")
DEFAULT_HEALTH = Path("D:/AlgoTradingData/prospective/dukascopy-macro-v1/health.json")


def atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def latest_feature(
    storage_root: Path, config: Mapping[str, Any]
) -> tuple[datetime | None, Path | None]:
    directory = storage_root / str(config["output"]["feature_directory"])
    latest: tuple[datetime, Path] | None = None
    for path in directory.glob("MACRO_*_M5_FEATURES_V1.manifest.json"):
        manifest = json.loads(path.read_text(encoding="utf-8"))
        snapshot = json.loads(
            Path(str(manifest["snapshot_manifest"])).read_text(encoding="utf-8")
        )
        item = (parse_utc(snapshot["end_exclusive_utc"]), path)
        if latest is None or item[0] > latest[0]:
            latest = item
    return (None, None) if latest is None else latest


def healthy_payload(
    *,
    decision: str,
    end: datetime,
    manifest: Path | None,
) -> dict[str, Any]:
    return {
        "schema_version": "dukascopy_macro_continuous_health_v1",
        "observed_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "decision": decision,
        "latest_completed_hour_exclusive_utc": end.isoformat().replace("+00:00", "Z"),
        "latest_feature_manifest": (
            None if manifest is None else str(manifest.resolve()).replace("\\", "/")
        ),
        "data_only": True,
        "paid_source_authorized": False,
        "databento_access_authorized": False,
        "strategy_scoring_authorized": False,
        "python_serving_authorized": False,
        "ml_shadow_authorized": False,
        "ea_consumption_authorized": False,
        "broker_action_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
    }


def refresh(
    storage_root: Path,
    health_path: Path,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    observed = datetime.now(UTC) if now is None else now.astimezone(UTC)
    end = completed_hour_floor(observed)
    env_name = str(config["storage_environment_variable"])
    os.environ[env_name] = str(storage_root.resolve())
    prior_end, prior_manifest = latest_feature(storage_root, config)
    if prior_end is not None and prior_end >= end:
        payload = healthy_payload(
            decision="CURRENT", end=prior_end, manifest=prior_manifest
        )
        atomic_json(health_path, payload)
        return payload
    snapshot = run(
        ROOT,
        end,
        int(config["maximum_concurrency"]),
        now=observed,
    )
    snapshot_path = Path(str(snapshot["manifest"]))
    command = [sys.executable, str(ROOT / "build_m5_snapshot.py"), str(snapshot_path)]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )
    updated_end, updated_manifest = latest_feature(storage_root, config)
    if updated_end != end or updated_manifest is None:
        raise ValueError("Macro feature refresh did not reach the completed hour")
    payload = healthy_payload(
        decision="REFRESHED", end=updated_end, manifest=updated_manifest
    )
    payload["snapshot_manifest"] = str(snapshot_path.resolve()).replace("\\", "/")
    payload["builder_output"] = completed.stdout.strip()
    atomic_json(health_path, payload)
    return payload


def failure(health_path: Path, exc: Exception) -> dict[str, Any]:
    payload = {
        "schema_version": "dukascopy_macro_continuous_health_v1",
        "observed_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "decision": "FAILED_CLOSED",
        "error": f"{type(exc).__name__}: {exc}",
        "data_only": True,
        "broker_action_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
    }
    atomic_json(health_path, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Continuously refresh macro M5 data")
    parser.add_argument("--storage-root", type=Path, default=DEFAULT_STORAGE)
    parser.add_argument("--health-path", type=Path, default=DEFAULT_HEALTH)
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--poll-seconds", type=int, default=900)
    args = parser.parse_args()
    while True:
        try:
            payload = refresh(args.storage_root, args.health_path)
        except Exception as exc:  # noqa: BLE001
            payload = failure(args.health_path, exc)
        print(json.dumps(payload, sort_keys=True, allow_nan=False), flush=True)
        if not args.watch:
            return 0 if payload["decision"] != "FAILED_CLOSED" else 1
        time.sleep(max(60, int(args.poll_seconds)))


if __name__ == "__main__":
    raise SystemExit(main())
