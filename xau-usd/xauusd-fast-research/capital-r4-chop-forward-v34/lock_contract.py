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

from chop_forward import (  # noqa: E402
    load_frozen,
    sha256_file,
    verify_historical_parity,
)


DATE_PATTERN = re.compile(r"_ticks_(\d{8})\.csv$")


def canonical_sha(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
        "ascii"
    )
    return hashlib.sha256(encoded).hexdigest()


def current_forward_sources(config: dict[str, Any]) -> list[str]:
    boundary = datetime.fromisoformat(
        config["forward"]["start_inclusive_utc"].replace("Z", "+00:00")
    )
    rows = []
    for path in Path(config["source"]["tick_directory"]).glob(
        config["source"]["tick_filename_glob"]
    ):
        match = DATE_PATTERN.search(path.name)
        if match is None:
            continue
        date = datetime.strptime(match.group(1), "%Y%m%d").replace(
            tzinfo=timezone.utc
        )
        if date >= boundary:
            rows.append(path.name)
    return sorted(rows)


def build_lock() -> dict[str, Any]:
    frozen = load_frozen(REPO_ROOT, ROOT)
    config = frozen.package_config
    parity = verify_historical_parity(frozen, REPO_ROOT)
    strategy_lock_path = REPO_ROOT / config["source"]["r4_contract_lock"]
    strategy_lock = json.loads(strategy_lock_path.read_text(encoding="utf-8"))
    payload = {
        "schema_version": "xauusd_capital_r4_chop_forward_v34_contract_lock",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace(
            "+00:00", "Z"
        ),
        "forward_start_inclusive_utc": config["forward"]["start_inclusive_utc"],
        "transport_adapter_locked_after_forward_boundary": True,
        "frozen_r4_rules_precede_forward_boundary": True,
        "rule_dependency_sha256": frozen.dependency_sha256,
        "frozen_r4_contract_file_sha256": sha256_file(strategy_lock_path),
        "frozen_r4_contract_sha256": strategy_lock["contract_sha256"],
        "historical_candidate_parity": parity,
        "post_boundary_tick_files_present_at_adapter_lock": current_forward_sources(
            config
        ),
        "post_boundary_economic_outcomes_opened": False,
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
    frozen = load_frozen(REPO_ROOT, ROOT)
    config = frozen.package_config
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    path = output / config["outputs"]["contract_lock"]
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        signed = dict(existing)
        observed_sha = signed.pop("contract_sha256")
        if observed_sha != canonical_sha(signed):
            raise ValueError("V34 contract payload hash is invalid")
        if existing["rule_dependency_sha256"] != frozen.dependency_sha256:
            raise ValueError("V34 rule dependencies changed after lock")
        parity = verify_historical_parity(frozen, REPO_ROOT)
        if parity != existing["historical_candidate_parity"]:
            raise ValueError("V34 historical parity changed after lock")
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
