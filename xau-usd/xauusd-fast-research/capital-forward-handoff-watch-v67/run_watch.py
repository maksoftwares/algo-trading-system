from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from handoff import (  # noqa: E402
    failure_status,
    healthy_status,
    inventory_summary,
    load_json,
    sha256_file,
    verify_self_hash,
    write_json_atomic,
)


def load_config() -> dict[str, Any]:
    return load_json(ROOT / "config" / "capital_forward_handoff_watch_v67.json")


def verify_contract(config: Mapping[str, Any]) -> dict[str, Any]:
    output = ROOT / str(config["outputs"]["directory"])
    path = output / str(config["outputs"]["contract_lock"])
    contract = load_json(path)
    verify_self_hash(contract, "contract_sha256", "V67 contract")
    for record in contract["package_files"]:
        package_path = ROOT / str(record["path"])
        if (
            not package_path.is_file()
            or int(package_path.stat().st_size) != int(record["bytes"])
            or sha256_file(package_path) != str(record["sha256"])
        ):
            raise ValueError(f"V67 package file changed: {record['path']}")
    v27_contract_path = REPO_ROOT / str(contract["v27_contract"]["path"])
    if sha256_file(v27_contract_path) != str(contract["v27_contract"]["sha256"]):
        raise ValueError("V67 locked V27 contract file changed")
    return contract


def append_child_log(path: Path, content: str, maximum_bytes: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = content.encode("utf-8", errors="replace")
    retained = b""
    if path.is_file():
        with path.open("rb") as handle:
            size = path.stat().st_size
            if size > maximum_bytes // 2:
                handle.seek(max(0, size - maximum_bytes // 2))
            retained = handle.read()
    combined = retained + encoded
    path.write_bytes(combined[-maximum_bytes:])


def child_command(runner: Path) -> list[str]:
    return [sys.executable, str(runner)]


def load_v27_state(config: Mapping[str, Any], v27_root: Path) -> dict[str, str]:
    source = config["v27"]
    status = load_json(v27_root / str(source["status"]))
    verify_self_hash(status, "status_sha256", "V27 status")
    if str(status.get("contract_sha256")) != str(source["contract_sha256"]):
        raise ValueError("V27 status contract identity changed")

    audits: dict[str, dict[str, Any]] = {}
    for stage in ("validation", "confirmation"):
        path = v27_root / str(source[f"{stage}_audit"])
        if not path.is_file():
            continue
        audit = load_json(path)
        verify_self_hash(audit, "audit_sha256", f"V27 {stage} audit")
        if str(audit.get("contract_sha256")) != str(source["contract_sha256"]):
            raise ValueError(f"V27 {stage} audit contract identity changed")
        audits[stage] = audit
    if "confirmation" in audits and "validation" not in audits:
        raise ValueError("V27 confirmation audit exists without validation audit")
    if "confirmation" in audits:
        latest = audits["confirmation"]
        return {
            "decision": str(latest["decision"]),
            "evidence_kind": "CONFIRMATION_AUDIT",
            "evidence_sha256": str(latest["audit_sha256"]),
        }
    if (
        "validation" in audits
        and str(status.get("waiting_for_stage")) != "CONFIRMATION"
    ):
        latest = audits["validation"]
        return {
            "decision": str(latest["decision"]),
            "evidence_kind": "VALIDATION_AUDIT",
            "evidence_sha256": str(latest["audit_sha256"]),
        }
    return {
        "decision": str(status.get("decision", "UNKNOWN")),
        "evidence_kind": "STATUS",
        "evidence_sha256": str(status["status_sha256"]),
    }


def run_once(config: Mapping[str, Any], contract: Mapping[str, Any]) -> dict[str, Any]:
    v27_root = (REPO_ROOT / str(config["v27"]["root"])).resolve()
    runner = v27_root / str(config["v27"]["runner"])
    started = time.monotonic()
    completed = subprocess.run(
        child_command(runner),
        cwd=v27_root,
        capture_output=True,
        check=False,
        text=True,
        timeout=int(config["runtime"]["child_timeout_seconds"]),
    )
    duration = time.monotonic() - started
    output = ROOT / str(config["outputs"]["directory"])
    log_entry = (
        f"\n=== child exit={completed.returncode} duration={duration:.3f}s ===\n"
        f"STDOUT\n{completed.stdout}\nSTDERR\n{completed.stderr}\n"
    )
    append_child_log(
        output / str(config["outputs"]["child_log"]),
        log_entry,
        int(config["runtime"]["maximum_log_bytes"]),
    )
    if completed.returncode != 0:
        raise RuntimeError(f"V27 child exited {completed.returncode}")

    v27_state = load_v27_state(config, v27_root)
    inventories = {
        name: inventory_summary(REPO_ROOT / str(path))
        for name, path in config["inventories"].items()
    }
    return healthy_status(
        contract_sha256=str(contract["contract_sha256"]),
        child_exit_code=int(completed.returncode),
        child_duration_seconds=duration,
        v27_state=v27_state,
        inventories=inventories,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the fail-closed V67 handoff watch"
    )
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--poll-seconds", type=int)
    args = parser.parse_args()
    config = load_config()
    poll = int(args.poll_seconds or config["runtime"]["poll_seconds"])
    if poll <= 0:
        parser.error("poll interval must be positive")
    output = ROOT / str(config["outputs"]["directory"])
    status_path = output / str(config["outputs"]["status"])
    while True:
        contract_sha256: str | None = None
        try:
            contract = verify_contract(config)
            contract_sha256 = str(contract["contract_sha256"])
            status = run_once(config, contract)
            write_json_atomic(status_path, status)
            print(
                json.dumps(status, allow_nan=False, indent=2, sort_keys=True),
                flush=True,
            )
        except Exception as exc:  # fail closed at the process boundary
            status = failure_status(contract_sha256, exc)
            write_json_atomic(status_path, status)
            print(
                json.dumps(status, indent=2, sort_keys=True),
                file=sys.stderr,
                flush=True,
            )
            if not args.watch:
                return 1
        if not args.watch:
            return 0
        time.sleep(poll)


if __name__ == "__main__":
    raise SystemExit(main())
