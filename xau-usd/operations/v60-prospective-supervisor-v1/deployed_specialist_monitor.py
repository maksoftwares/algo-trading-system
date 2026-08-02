from __future__ import annotations

import argparse
import csv
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import re
import time
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = (
    REPO_ROOT
    / "xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/config"
    / "v60_canonical_demo_portfolio_v2.json"
)
FEED_BY_SOURCE = {
    "R1_BOX": "R1_BOX",
    "R1_PULLBACK": "R1_PULLBACK",
    "R2_DOWNTREND": "R2_R3",
    "R3_COMPRESSION": "R2_R3",
    "R4_CHOP": "R4",
    "V7_SWING_HEALTH": "ADDONS",
    "V8_RETEST_HEALTH": "ADDONS",
    "V25_CHOP": "ADDONS",
    "V57_BREAK_SWING_H4ADX_HIGH": "ADDONS",
}
DATE_PATTERN = re.compile(r"_(\d{8})\.csv$")
TAIL_BYTES = 64 * 1024


def utc_text(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise TypeError(f"Expected JSON object: {path}")
    return payload


def nested(payload: Mapping[str, Any], dotted_key: str) -> Any:
    current: Any = payload
    for part in dotted_key.split("."):
        if not isinstance(current, Mapping) or part not in current:
            raise KeyError(dotted_key)
        current = current[part]
    return current


def atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def jsonl_summary(
    path: Path,
    source: Mapping[str, Any],
    *,
    allow_not_created: bool,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(path),
        "exists": path.is_file(),
        "complete_rows": 0,
        "matching_rows": 0,
        "last_matching_candidate_time_utc": None,
        "errors": [],
    }
    if not path.is_file():
        if allow_not_created:
            result["not_created_because_no_candidate_has_been_emitted"] = True
        else:
            result["errors"].append("candidate ledger is missing")
        return result
    raw = path.read_bytes()
    if raw and not raw.endswith(b"\n"):
        result["errors"].append("candidate ledger has an incomplete final line")
    time_field = str(source["time_field"])
    source_id = str(source["source_id"])
    specialist_id = str(source["specialist_id"])
    for line in raw.splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            result["errors"].append(f"invalid JSONL row: {exc}")
            continue
        result["complete_rows"] += 1
        identities = {
            str(row.get("source_id", "")),
            str(row.get("specialist_id", "")),
            str(row.get("sleeve_id", "")),
        }
        if source_id not in identities and specialist_id not in identities:
            continue
        result["matching_rows"] += 1
        if row.get(time_field):
            result["last_matching_candidate_time_utc"] = str(row[time_field])
    return result


def last_complete_csv_row(path: Path) -> dict[str, str] | None:
    with path.open("rb") as stream:
        header_raw = stream.readline()
        data_start = stream.tell()
        stream.seek(0, os.SEEK_END)
        end = stream.tell()
        if end <= data_start:
            return None
        start = max(data_start, end - TAIL_BYTES)
        stream.seek(start)
        tail = stream.read()
    lines = tail.splitlines()
    if start > data_start and lines:
        lines = lines[1:]
    if tail and not tail.endswith((b"\n", b"\r")) and lines:
        lines = lines[:-1]
    header = next(csv.reader([header_raw.decode("utf-8-sig").strip()]), [])
    if not header:
        return None
    for raw in reversed(lines):
        if not raw.strip():
            continue
        values = next(csv.reader([raw.decode("utf-8-sig")]), [])
        if len(values) == len(header):
            return dict(zip(header, values, strict=True))
    return None


def latest_tick_transport(config: Mapping[str, Any]) -> dict[str, Any]:
    feed = config["feeds"]
    directory = Path(str(feed["terminal_files_directory"]))
    paths = sorted(directory.glob(str(feed["tick_filename_glob"])))
    result: dict[str, Any] = {
        "latest_path": str(paths[-1]) if paths else None,
        "newest_path": str(paths[-1]) if paths else None,
        "timestamp_utc": None,
        "filename_day_matches_row": False,
        "market_state": "NO_TICKS",
        "skipped_empty_paths": [],
        "errors": [],
    }
    if not paths:
        result["errors"].append("no prospective tick ledger exists")
        return result
    path = None
    last = None
    for candidate in reversed(paths):
        last = last_complete_csv_row(candidate)
        if last is not None:
            path = candidate
            break
        result["skipped_empty_paths"].append(str(candidate))
    if path is None or last is None:
        result["errors"].append("prospective tick ledgers have no complete data rows")
        return result
    result["latest_path"] = str(path)
    result["market_state"] = (
        "MARKET_CLOSED_OR_IDLE" if path != paths[-1] else "ACTIVE"
    )
    match = DATE_PATTERN.search(path.name)
    if match is None:
        result["errors"].append("latest tick filename has no UTC date")
        return result
    timestamp = str(last.get("timestamp_utc", ""))
    result["timestamp_utc"] = timestamp
    try:
        if "." in timestamp[:10]:
            parsed = datetime.strptime(timestamp, "%Y.%m.%d %H:%M:%S.%fZ")
        else:
            parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        observed_day = parsed.strftime("%Y%m%d")
    except ValueError:
        result["errors"].append("latest tick timestamp is invalid")
        return result
    result["filename_day_matches_row"] = observed_day == match.group(1)
    if not result["filename_day_matches_row"]:
        result["errors"].append("latest tick row is stored under the wrong UTC day")
    return result


def build_status() -> dict[str, Any]:
    now = datetime.now(UTC)
    config = read_json(CONFIG_PATH)
    runtime = Path(str(config["runtime"]["directory"]))
    runtime_status_path = runtime / str(config["runtime"]["status_filename"])
    feed_status_path = runtime / str(config["runtime"]["feed_status_filename"])
    errors: list[str] = []
    try:
        runtime_status = read_json(runtime_status_path)
    except Exception as exc:
        runtime_status = {}
        errors.append(f"runtime status unavailable: {type(exc).__name__}: {exc}")
    try:
        feed_status = read_json(feed_status_path)
    except Exception as exc:
        feed_status = {}
        errors.append(f"feed status unavailable: {type(exc).__name__}: {exc}")

    required_runtime = {
        "status": "ACTIVE_DEMO_BROKER_ACTION",
        "account_login": 1033030,
        "execution_enabled": True,
        "equity_fraction_limits_enabled": True,
        "minimum_balance_requirement_enabled": False,
        "profit_protection_close_failures": 0,
        "portfolio_protection.enabled": True,
        "portfolio_protection.policy.open_profit_arm_r": 1.5,
        "portfolio_protection.policy.open_profit_retain_r": 0.5,
        "portfolio_protection.policy.soft_addon_block_drawdown_fraction": 0.2,
        "portfolio_protection.policy.soft_core_concurrency_drawdown_fraction": 0.22,
        "ml_runtime_authorized": True,
        "ml_shadow_authorized": False,
        "live_authorized": False,
    }
    for key, expected in required_runtime.items():
        try:
            actual = nested(runtime_status, key)
        except KeyError:
            errors.append(f"runtime status lacks {key}")
            continue
        if actual != expected:
            errors.append(f"runtime {key}={actual!r}, expected {expected!r}")

    source_rows: list[dict[str, Any]] = []
    reported_feeds = feed_status.get("feeds", {})
    for source in config["sources"]:
        source_id = str(source["source_id"])
        feed_id = FEED_BY_SOURCE[source_id]
        feed_ok = bool(reported_feeds.get(feed_id, {}).get("ok"))
        ledger = jsonl_summary(
            Path(str(source["path"])),
            source,
            allow_not_created=feed_ok,
        )
        source_errors = list(ledger["errors"])
        if not feed_ok:
            source_errors.append(f"feed {feed_id} is not healthy")
        source_rows.append(
            {
                "source_id": source_id,
                "specialist_id": str(source["specialist_id"]),
                "feed_id": feed_id,
                "feed_ok": feed_ok,
                "ledger": ledger,
                "healthy": not source_errors,
                "errors": source_errors,
            }
        )
    if not bool(feed_status.get("all_requested_feeds_ok")):
        errors.append("canonical feed cycle is not healthy")
    if any(not row["healthy"] for row in source_rows):
        errors.append("one or more deployed specialist sources are unhealthy")

    tick_transport = latest_tick_transport(config)
    errors.extend(tick_transport["errors"])
    healthy = not errors
    return {
        "schema_version": "xauusd_v60_deployed_specialist_monitor_v1",
        "updated_at_utc": utc_text(now),
        "status": "ACTIVE" if healthy else "FAILED_CLOSED",
        "healthy": healthy,
        "account_login": 1033030,
        "deployed_source_count": len(source_rows),
        "all_deployed_sources_healthy": all(
            row["healthy"] for row in source_rows
        ),
        "sources": source_rows,
        "tick_transport": tick_transport,
        "errors": errors,
        "strategy_or_risk_parameters_changed": False,
        "broker_action_added": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--poll-seconds", type=int, default=60)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "D:/AlgoTradingData/prospective/"
            "v60-deployed-specialist-monitor-v1/status.json"
        ),
    )
    args = parser.parse_args()
    while True:
        status = build_status()
        atomic_json(args.output, status)
        print(json.dumps(status, sort_keys=True, allow_nan=False), flush=True)
        if not args.watch:
            return 0 if status["healthy"] else 1
        time.sleep(max(30, args.poll_seconds))


if __name__ == "__main__":
    raise SystemExit(main())
