from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from core_shadow import (  # noqa: E402
    load_frozen,
    verify_historical_candidate_parity,
)


DATE_PATTERN = re.compile(r"_ticks_(\d{8})\.csv$")


def canonical_sha(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def build_lock() -> dict[str, Any]:
    frozen = load_frozen(REPO_ROOT, ROOT)
    config = frozen.package_config
    boundary = datetime.fromisoformat(
        config["forward"]["start_inclusive_utc"].replace("Z", "+00:00")
    )
    tick_directory = Path(config["source"]["runtime_directory"]).parent
    forward_files: list[str] = []
    for path in tick_directory.glob("xau_prospective_*_ticks_*.csv"):
        match = DATE_PATTERN.search(path.name)
        if match is None:
            continue
        date = datetime.strptime(match.group(1), "%Y%m%d").replace(tzinfo=timezone.utc)
        if date >= boundary:
            forward_files.append(str(path))
    if forward_files:
        raise RuntimeError(f"V28 lock is after forward files appeared: {forward_files}")
    parity = verify_historical_candidate_parity(frozen)
    payload = {
        "schema_version": "xauusd_capital_core_shadow_v28_contract_lock",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "forward_start_inclusive_utc": config["forward"]["start_inclusive_utc"],
        "rule_dependency_sha256": frozen.dependency_sha256,
        "historical_candidate_parity": parity,
        "forward_tick_files_present_at_lock": forward_files,
        "component_statuses": config["components"],
        "economic_outcomes_opened": False,
        "same_version_tuning_authorized": False,
        "model_training_authorized": False,
        "python_predictions_authorized": False,
        "ea_consumption_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
        "broker_action_authorized": False,
    }
    payload["contract_sha256"] = canonical_sha(payload)
    return payload


def main() -> int:
    config = json.loads(
        (ROOT / "config" / "capital_core_same_period_shadow_v28.json").read_text(
            encoding="utf-8"
        )
    )
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    path = output / config["outputs"]["contract_lock"]
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        frozen = load_frozen(REPO_ROOT, ROOT)
        if existing["rule_dependency_sha256"] != frozen.dependency_sha256:
            raise ValueError("V28 rule dependencies changed after lock")
        signed = dict(existing)
        observed_contract_sha = signed.pop("contract_sha256")
        if observed_contract_sha != canonical_sha(signed):
            raise ValueError("V28 contract payload hash is invalid")
        parity = verify_historical_candidate_parity(frozen)
        if parity != existing["historical_candidate_parity"]:
            raise ValueError("V28 historical parity changed after lock")
        print(json.dumps(existing, sort_keys=True))
        return 0
    payload = build_lock()
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
