from __future__ import annotations

import json

from run_evaluation import (
    CONFIG_PATH,
    CONTRACT_PATH,
    REPO_ROOT,
    ROOT,
    canonical_hash,
    sha256_file,
)


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if contract["contract_sha256"] != canonical_hash(contract):
        raise ValueError("V16 contract self-hash changed")
    manifest_path = ROOT / config["outputs"]["directory"] / config["outputs"]["manifest"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["definition_contract_sha256"] != contract["contract_sha256"]:
        raise ValueError("V16 manifest contract changed")
    for section in ("inputs", "artifacts"):
        for item in manifest[section].values():
            path = REPO_ROOT / item["path"]
            if not path.is_file() or sha256_file(path) != item["sha256"]:
                raise ValueError(f"V16 {section} changed: {path}")
    if manifest["authorization"] != config["authorization"]:
        raise ValueError("V16 manifest authority changed")
    forbidden = (
        "prospective_scoring_authorized",
        "python_serving_authorized",
        "ml_shadow_authorized",
        "ea_consumption_authorized",
        "demo_authorized",
        "live_authorized",
        "broker_action_authorized",
        "runtime_change_authorized",
    )
    if any(bool(config["authorization"][key]) for key in forbidden):
        raise ValueError("V16 unexpectedly has runtime authority")
    result_path = (
        ROOT / config["outputs"]["directory"] / config["outputs"]["result_json"]
    )
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if (
        result["v14_changed"] is not False
        or result["v15_changed"] is not False
        or result["deployment_eligible"] is not False
    ):
        raise ValueError("V16 result changed authority or frozen lanes")
    print(
        json.dumps(
            {
                "status": "VERIFIED",
                "decision": result["decision"],
                "contract_sha256": contract["contract_sha256"],
                "artifact_count": len(manifest["artifacts"]),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
