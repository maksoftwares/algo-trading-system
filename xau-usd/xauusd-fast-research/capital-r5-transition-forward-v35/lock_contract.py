from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from transition_forward import load_frozen, verify_historical_parity  # noqa: E402


def canonical_sha(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
        "ascii"
    )
    return hashlib.sha256(encoded).hexdigest()


def build_lock() -> dict[str, Any]:
    frozen = load_frozen(REPO_ROOT, ROOT)
    config = frozen.package_config
    parity = verify_historical_parity(frozen, REPO_ROOT)
    payload = {
        "schema_version": "xauusd_capital_r5_transition_forward_v35_contract_lock",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace(
            "+00:00", "Z"
        ),
        "forward_start_inclusive_utc": config["forward"]["start_inclusive_utc"],
        "transport_adapter_locked_after_forward_boundary": True,
        "frozen_r5_rules_precede_forward_boundary": True,
        "rule_dependency_sha256": frozen.dependency_sha256,
        "historical_parity": parity,
        "official_macro_source": config["official_macro"],
        "component_attempts": [23925, 24877, 24995, 25048],
        "router_attempt": 27135,
        "post_boundary_economic_outcomes_opened": False,
        "prospective_component_outcome_updates_authorized": False,
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
        observed = signed.pop("contract_sha256")
        if observed != canonical_sha(signed):
            raise ValueError("V35 contract payload hash is invalid")
        if existing["rule_dependency_sha256"] != frozen.dependency_sha256:
            raise ValueError("V35 rule dependencies changed after lock")
        parity = verify_historical_parity(frozen, REPO_ROOT)
        if parity != existing["historical_parity"]:
            raise ValueError("V35 historical parity changed after lock")
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
