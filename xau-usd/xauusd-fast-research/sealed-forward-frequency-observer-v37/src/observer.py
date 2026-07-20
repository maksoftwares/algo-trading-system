from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "sealed_forward_frequency_observer_v37.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def load_config() -> dict[str, Any]:
    return load_json(CONFIG_PATH)


def resolve(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (ROOT / path).resolve()


def verify_locked_dependencies(config: dict[str, Any]) -> dict[str, str]:
    observed = {}
    for name, spec in config["locked_dependencies"].items():
        path = resolve(str(spec["path"]))
        digest = sha256_file(path)
        if digest != str(spec["sha256"]):
            raise ValueError(f"Locked dependency mismatch for {name}: {digest}")
        observed[name] = digest
    return observed


def candidate_count(status: dict[str, Any], key: str, mode: str) -> int:
    value = status.get(key, {} if mode == "dictionary_sum" else 0)
    if mode == "dictionary_sum":
        if not isinstance(value, dict):
            raise ValueError(f"Candidate count {key} is not a dictionary")
        return sum(int(item) for item in value.values())
    if mode == "integer":
        return int(value)
    raise KeyError(f"Unknown candidate count mode: {mode}")


def should_refresh(eligible_counts: list[int], stop_at: int) -> bool:
    return bool(eligible_counts) and max(eligible_counts) < stop_at


def refresh_forward_inventories(
    config: dict[str, Any], inventories: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    eligible = [
        int(inventory.get(spec["eligible_count_key"], 0))
        for spec, inventory in zip(config["forward_families"], inventories)
    ]
    if not should_refresh(
        eligible, int(config["automatic_refresh_stop_eligible_weekdays"])
    ):
        return [
            {
                "status": "SKIPPED_STAGE_OPEN_GUARD",
                "eligible_counts_before_refresh": eligible,
            }
        ]
    results = []
    for spec in config["forward_families"]:
        runner = resolve(str(spec["runner_path"]))
        completed = subprocess.run(
            [sys.executable, str(runner)],
            cwd=runner.parent,
            check=False,
            capture_output=True,
            text=True,
            timeout=300,
        )
        results.append(
            {
                "source_id": spec["source_id"],
                "returncode": completed.returncode,
                "stdout": completed.stdout[-2000:],
                "stderr": completed.stderr[-2000:],
            }
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"Inventory refresh failed for {spec['source_id']}: "
                f"{completed.stderr[-500:]}"
            )
    return results


def build_status(
    config: dict[str, Any],
    now_utc: str,
    refresh_results: list[dict[str, Any]],
) -> dict[str, Any]:
    now = __import__("datetime").datetime.fromisoformat(now_utc.replace("Z", "+00:00"))
    maximum_age = float(config["maximum_status_age_seconds"])
    source_rows = []
    failures = []
    counts = []
    for spec in config["collectors"]:
        path = resolve(str(spec["status_path"]))
        status = load_json(path)
        updated = __import__("datetime").datetime.fromisoformat(
            str(status["updated_at_utc"]).replace("Z", "+00:00")
        )
        age = (now - updated).total_seconds()
        count = candidate_count(
            status, str(spec["candidate_count_key"]), str(spec["candidate_count_mode"])
        )
        row = {
            "source_id": spec["source_id"],
            "source_type": "CORE_SPECIALIST_CLOCK",
            "candidate_count": count,
            "status": status.get("status"),
            "updated_at_utc": status["updated_at_utc"],
            "status_age_seconds": age,
            "stale": age > maximum_age,
            "economic_outcomes_opened": bool(
                status.get("economic_outcomes_opened", False)
            ),
            "python_execution_authorized": bool(
                status.get("python_execution_authorized", False)
            ),
            "broker_action_allowed": bool(status.get("broker_action_allowed", False)),
            "trade_permission": bool(status.get("trade_permission", False)),
        }
        source_rows.append(row)
        counts.append(count)
        if row["stale"]:
            failures.append(f"STALE_{spec['source_id']}")
        if any(
            row[key]
            for key in (
                "economic_outcomes_opened",
                "python_execution_authorized",
                "broker_action_allowed",
                "trade_permission",
            )
        ):
            failures.append(f"AUTHORITY_OR_OUTCOME_VIOLATION_{spec['source_id']}")

    eligible_counts = []
    for spec in config["forward_families"]:
        path = resolve(str(spec["inventory_path"]))
        inventory = load_json(path)
        count = int(inventory.get(spec["candidate_count_key"], 0))
        eligible = int(inventory.get(spec["eligible_count_key"], 0))
        economic_opened = bool(inventory.get(spec["economic_open_key"], False))
        row = {
            "source_id": spec["source_id"],
            "source_type": "SEALED_FORWARD_SATELLITE_CLOCK",
            "candidate_count": count,
            "eligible_full_weekday_count": eligible,
            "economic_outcomes_opened": economic_opened,
            "inventory_path": str(path),
            "inventory_sha256": sha256_file(path),
        }
        source_rows.append(row)
        counts.append(count)
        eligible_counts.append(eligible)
        if economic_opened:
            failures.append(f"ECONOMIC_OUTCOME_OPENED_{spec['source_id']}")

    raw_total = sum(counts)
    payload = {
        "schema_version": config["schema_version"],
        "updated_at_utc": now_utc,
        "forward_boundary_utc": config["forward_boundary_utc"],
        "status": "PASS_READ_ONLY_SEALED" if not failures else "FAIL_CLOSED",
        "failures": failures,
        "sources": source_rows,
        "source_candidate_counts": {
            row["source_id"]: row["candidate_count"] for row in source_rows
        },
        "raw_component_candidate_supply": raw_total,
        "minimum_unique_candidate_lower_bound": max(counts, default=0),
        "maximum_unique_candidate_upper_bound": raw_total,
        "candidate_frequency_authorized": False,
        "candidate_frequency_reason": (
            "Partial periods, cross-clock overlap, and shared-account constraints "
            "are unresolved."
        ),
        "eligible_full_weekdays": min(eligible_counts, default=0),
        "automatic_inventory_refresh_allowed": should_refresh(
            eligible_counts,
            int(config["automatic_refresh_stop_eligible_weekdays"]),
        ),
        "economic_outcomes_opened": any(
            bool(row.get("economic_outcomes_opened", False)) for row in source_rows
        ),
        "refresh_results": refresh_results,
        "authorization": config["authorization"],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    payload["status_sha256"] = hashlib.sha256(canonical).hexdigest()
    return payload


def write_status(config: dict[str, Any], payload: dict[str, Any]) -> Path:
    runtime = resolve(str(config["runtime_directory"]))
    runtime.mkdir(parents=True, exist_ok=True)
    status_path = runtime / config["outputs"]["runtime_status"]
    history_path = runtime / config["outputs"]["runtime_history"]
    status_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with history_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")
    return status_path
