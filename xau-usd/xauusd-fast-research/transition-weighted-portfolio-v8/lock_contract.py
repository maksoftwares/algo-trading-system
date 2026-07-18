from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]

PACKAGE_FILES = (
    ".gitattributes",
    "PREREGISTRATION.md",
    "requirements.txt",
    "config/transition_weighted_portfolio_v8.json",
    "src/__init__.py",
    "src/portfolio.py",
    "prepare_inputs.py",
    "lock_contract.py",
    "run_portfolio.py",
    "tests/test_portfolio.py",
)

DEPENDENCIES = (
    "../macro-regime-routing-v1/src/campaign.py",
    "../macro-regime-routing-v1/src/foundation.py",
    "../independent-specialists-v1/src/data.py",
    "../independent-specialists-v1/src/research.py",
    "../adaptive-h4-specialists-v1/src/adaptive.py",
    "../m15-regime-target-campaign-v1/src/campaign.py",
    "../intraday-macro-specialists-v1/src/data.py",
    "../m15-regime-target-campaign-v2/src/correction.py",
    "../walkforward-state-action-router-v1/src/router.py",
    "../regime-mechanism-campaign-v1/src/campaign.py",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _record(path: Path, base: Path) -> dict[str, Any]:
    resolved = path.resolve()
    resolved.relative_to(base.resolve())
    if not resolved.is_file():
        raise FileNotFoundError(resolved)
    return {
        "path": resolved.relative_to(base.resolve()).as_posix(),
        "bytes": int(resolved.stat().st_size),
        "sha256": sha256_file(resolved),
    }


def _self_hash(payload: Mapping[str, Any]) -> str:
    work = {key: value for key, value in payload.items() if key != "contract_sha256"}
    encoded = json.dumps(
        work, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _source_records(config: Mapping[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    records: list[dict[str, Any]] = []
    residual_lock: dict[str, Any] | None = None
    for source_name in ("macro_source_campaign", "residual_source_campaign"):
        source = config[source_name]
        source_root = (ROOT / source["directory"]).resolve()
        for key in source:
            if key == "directory":
                continue
            path = source_root / source[key]
            records.append(_record(path, REPO))
        if source_name == "residual_source_campaign":
            residual_lock = json.loads(
                (source_root / source["contract_lock"]).read_text(encoding="utf-8")
            )
    if residual_lock is None:
        raise ValueError("Residual source contract was not loaded")
    return records, residual_lock


def main() -> int:
    config = json.loads(
        (ROOT / "config" / "transition_weighted_portfolio_v8.json").read_text(
            encoding="utf-8"
        )
    )
    output = ROOT / config["outputs"]["directory"]
    component_path = output / config["outputs"]["component_trades"]
    manifest_path = output / config["outputs"]["manifest"]
    evidence_path = output / config["outputs"]["input_evidence"]
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    if sha256_file(component_path) != str(evidence["component_trade_sha256"]):
        raise ValueError("Component trade file differs from input evidence")
    if sha256_file(manifest_path) != str(evidence["manifest_sha256"]):
        raise ValueError("Portfolio manifest differs from input evidence")
    source_records, source_lock = _source_records(config)
    lock_path = output / config["outputs"]["contract_lock"]
    if lock_path.exists():
        raise FileExistsError("V8 contract lock already exists")
    payload: dict[str, Any] = {
        "schema_version": "xauusd_transition_weighted_portfolio_v8_contract",
        "components": config["components"],
        "selection": config["selection"],
        "windows": config["windows"],
        "execution": config["execution"],
        "economic_gates": config["economic_gates"],
        "component_trade_file": _record(component_path, REPO),
        "manifest_file": _record(manifest_path, REPO),
        "input_evidence": _record(evidence_path, REPO),
        "package_files": [
            _record((ROOT / name).resolve(), REPO) for name in PACKAGE_FILES
        ],
        "dependency_files": [
            _record((ROOT / name).resolve(), REPO) for name in DEPENDENCIES
        ],
        "source_campaign_files": source_records,
        "external_files": source_lock["external_files"],
        "external_storage_root": str(source_lock.get("external_storage_root", "C:/DukascopyTickDataFoundationV1")),
        "components_selected_after_outcomes": True,
        "portfolio_outcomes_opened": False,
        "selection_adjustment_count": int(
            config["selection"]["selection_adjustment_count"]
        ),
        "paid_data_used": False,
        "training_authorized": False,
        "execution_authorized": False,
    }
    payload["contract_sha256"] = _self_hash(payload)
    lock_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    print(payload["contract_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

