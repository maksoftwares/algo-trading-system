from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from pullback import canonical_sha, dependency_sha256, utc_text  # noqa: E402
from verify_historical_parity import build_report, load_config  # noqa: E402


UTC = timezone.utc


def build_lock() -> tuple[dict[str, Any], dict[str, Any]]:
    config = load_config()
    now = datetime.now(UTC)
    boundary = datetime.fromisoformat(
        config["source"]["forward_start_inclusive_utc"].replace("Z", "+00:00")
    )
    if now >= boundary:
        raise RuntimeError(
            f"V29 cannot be newly locked after its forward boundary: {utc_text(boundary)}"
        )
    report = build_report()
    if not report["parity"]["pass"]:
        raise ValueError("V29 historical parity failed")
    payload = {
        "schema_version": "xauusd_capital_r1_pullback_v29_contract_lock",
        "created_at_utc": utc_text(now),
        "forward_start_inclusive_utc": config["source"]["forward_start_inclusive_utc"],
        "rule_dependency_sha256": dependency_sha256(
            REPO_ROOT, config["contract_scope"]
        ),
        "source_artifacts": report["source_artifacts"],
        "history_fingerprints": report["history"],
        "historical_parity": report["parity"],
        "historical_status": config["authority"]["historical_status"],
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
    return payload, report


def verify_existing(existing: dict[str, Any]) -> None:
    config = load_config()
    observed = dependency_sha256(REPO_ROOT, config["contract_scope"])
    if existing["rule_dependency_sha256"] != observed:
        raise ValueError("V29 rule dependencies changed after lock")
    signed = dict(existing)
    contract_sha = signed.pop("contract_sha256")
    if contract_sha != canonical_sha(signed):
        raise ValueError("V29 contract payload hash is invalid")
    report = build_report()
    if not report["parity"]["pass"]:
        raise ValueError("V29 historical parity failed after lock")
    if report["parity"] != existing["historical_parity"]:
        raise ValueError("V29 historical parity changed after lock")
    if report["source_artifacts"] != existing["source_artifacts"]:
        raise ValueError("V29 source artifacts changed after lock")
    if report["history"] != existing["history_fingerprints"]:
        raise ValueError("V29 MT5 history fingerprints changed after lock")


def main() -> int:
    config = load_config()
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    lock_path = output / config["outputs"]["contract_lock"]
    if lock_path.exists():
        existing = json.loads(lock_path.read_text(encoding="utf-8"))
        verify_existing(existing)
        print(json.dumps(existing, sort_keys=True))
        return 0
    payload, report = build_lock()
    parity_path = output / config["outputs"]["parity_report"]
    parity_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    lock_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
