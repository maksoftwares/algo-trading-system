from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
DEFAULT_CONFIG = ROOT / "config" / "runtime_supervisor_v1.json"


def utc_text(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_utc(value: Any) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"Timestamp is not timezone aware: {value}")
    return parsed.astimezone(timezone.utc)


def resolve_path(value: str, repo_root: Path = REPO_ROOT) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def nested_value(payload: Mapping[str, Any], dotted_key: str) -> Any:
    current: Any = payload
    for part in dotted_key.split("."):
        if not isinstance(current, Mapping) or part not in current:
            raise KeyError(dotted_key)
        current = current[part]
    return current


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise TypeError(f"Expected JSON object: {path}")
    return payload


def atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def inspect_health_source(
    source: Mapping[str, Any],
    *,
    now: datetime,
    repo_root: Path,
) -> dict[str, Any]:
    path = resolve_path(str(source["path"]), repo_root)
    result: dict[str, Any] = {
        "id": str(source["id"]),
        "path": str(path),
        "healthy": False,
        "errors": [],
    }
    try:
        payload = read_json(path)
    except Exception as exc:
        result["errors"].append(f"{type(exc).__name__}: {exc}")
        return result

    timestamp = None
    for field in source.get("timestamp_fields", []):
        try:
            timestamp = parse_utc(nested_value(payload, str(field)))
            break
        except (KeyError, TypeError, ValueError):
            continue
    if timestamp is None:
        result["errors"].append("No valid health timestamp")
    else:
        age_seconds = max(0.0, (now - timestamp).total_seconds())
        result["updated_at_utc"] = utc_text(timestamp)
        result["age_seconds"] = age_seconds
        if age_seconds > float(source["maximum_age_seconds"]):
            result["errors"].append(
                f"Stale by {age_seconds:.1f}s "
                f"(limit {source['maximum_age_seconds']}s)"
            )

    for key, expected in source.get("required_values", {}).items():
        try:
            actual = nested_value(payload, str(key))
        except KeyError:
            result["errors"].append(f"Missing required value: {key}")
            continue
        if actual != expected:
            result["errors"].append(
                f"Required value mismatch: {key}={actual!r}, expected {expected!r}"
            )

    for key, allowed in source.get("allowed_status_values", {}).items():
        try:
            actual = nested_value(payload, str(key))
        except KeyError:
            result["errors"].append(f"Missing allowed-status value: {key}")
            continue
        if actual not in allowed:
            result["errors"].append(
                f"Unexpected value: {key}={actual!r}, allowed={allowed!r}"
            )

    for key, forbidden in source.get("forbidden_status_values", {}).items():
        try:
            actual = nested_value(payload, str(key))
        except KeyError:
            result["errors"].append(f"Missing forbidden-status value: {key}")
            continue
        if actual in forbidden:
            result["errors"].append(f"Forbidden value: {key}={actual!r}")

    result["reported_status"] = payload.get("status", payload.get("decision"))
    result["healthy"] = not result["errors"]
    return result


def build_status(
    config: Mapping[str, Any],
    *,
    now: datetime | None = None,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    observed = now or datetime.now(timezone.utc)
    runtime = config["runtime"]
    runtime_directory = resolve_path(str(runtime["directory"]), repo_root)
    process_state_path = runtime_directory / str(runtime["process_state"])

    process_errors: list[str] = []
    process_state: dict[str, Any] = {}
    try:
        process_state = read_json(process_state_path)
        process_updated = parse_utc(process_state["updated_at_utc"])
        process_age = max(0.0, (observed - process_updated).total_seconds())
        if process_age > max(180.0, float(config["poll_seconds"]) * 3.0):
            process_errors.append(f"Process state is stale by {process_age:.1f}s")
        if not bool(process_state.get("terminal_running")):
            process_errors.append("Capital MT5 terminal is not running")
        if not bool(process_state.get("all_workers_running")):
            process_errors.append("One or more supervised workers are not running")
    except Exception as exc:
        process_errors.append(f"{type(exc).__name__}: {exc}")

    sources = [
        inspect_health_source(source, now=observed, repo_root=repo_root)
        for source in config["health_sources"]
    ]
    healthy = not process_errors and all(item["healthy"] for item in sources)
    return {
        "schema_version": str(config["schema_version"]),
        "updated_at_utc": utc_text(observed),
        "status": "READY" if healthy else "NOT_READY",
        "healthy": healthy,
        "strategy_or_risk_parameters_changed": False,
        "broker_action_added": False,
        "process_state_path": str(process_state_path),
        "process_errors": process_errors,
        "process_state": process_state,
        "health_sources": sources,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Consolidate V60 runtime health")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    config = read_json(args.config.resolve())
    status = build_status(config)
    if args.write:
        runtime = config["runtime"]
        output = resolve_path(str(runtime["directory"])) / str(runtime["status"])
        atomic_json(output, status)
    print(json.dumps(status, sort_keys=True, allow_nan=False), flush=True)
    return 0 if status["healthy"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
