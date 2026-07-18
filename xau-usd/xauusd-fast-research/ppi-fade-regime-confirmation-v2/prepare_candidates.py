from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

import pandas as pd


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config" / "ppi_fade_regime_confirmation_v2.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_hash(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("ascii")
    ).hexdigest()


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _verify_parent(parent: Path) -> dict[str, Any]:
    output = parent / "outputs"
    lock_path = output / "PPI_EVENT_CONTRACT_LOCK.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    claimed = str(lock["contract_sha256"])
    body = dict(lock)
    body.pop("contract_sha256")
    if _canonical_hash(body) != claimed:
        raise ValueError("Parent PPI V1 contract hash mismatch")
    if (output / "PPI_EVENT_RELATED_CONFIRMATION_OUTCOMES_OPENED.json").exists():
        raise RuntimeError("Parent PPI confirmation was already opened")
    result = json.loads(
        (output / "PPI_EVENT_HISTORICAL_DISCOVERY_RESULT.json").read_text(
            encoding="utf-8"
        )
    )
    if result["contract_sha256"] != claimed:
        raise ValueError("Parent historical result contract mismatch")
    return lock


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    if (output / config["outputs"]["contract_lock"]).exists():
        raise RuntimeError("Refusing to rebuild V2 candidates after contract lock")
    if any(output.glob("*_OUTCOMES_OPENED.json")):
        raise RuntimeError("Refusing to rebuild V2 candidates after outcomes opened")

    parent = (ROOT / config["parent_package"]).resolve()
    parent_lock = _verify_parent(parent)
    parent_output = parent / "outputs"
    parent_candidate_path = parent_output / "PPI_EVENT_CANDIDATES.parquet"
    parent_manifest_path = parent_output / "PPI_EVENT_CANDIDATE_MANIFEST.json"
    parent_manifest = json.loads(parent_manifest_path.read_text(encoding="utf-8"))
    if _sha256(parent_candidate_path) != parent_manifest["candidate_sha256"]:
        raise ValueError("Parent PPI candidate ledger hash mismatch")

    candidates = pd.read_parquet(parent_candidate_path)
    prohibited = {
        column
        for column in candidates.columns
        if any(
            token in column.lower()
            for token in ("pnl", "profit", "exit_", "stress_", "winner")
        )
    }
    if prohibited:
        raise ValueError(f"Outcome-like parent candidate columns: {sorted(prohibited)}")

    source = config["source"]
    policy = config["policy"]
    start = pd.Timestamp(source["start_utc"])
    end = pd.Timestamp(source["end_exclusive_utc"])
    selected = candidates.loc[
        candidates["policy_id"].eq(policy["source_policy_id"])
        & candidates["feature_time_utc"].ge(start)
        & candidates["feature_time_utc"].lt(end)
        & candidates["regime"].isin(policy["allowed_regimes"])
    ].copy()
    if len(selected) != int(source["expected_candidate_rows"]):
        raise ValueError(
            f"Expected {source['expected_candidate_rows']} outcome-free candidates, "
            f"found {len(selected)}"
        )
    selected["candidate_id"] = selected["candidate_id"].map(
        lambda value: hashlib.sha256(
            f"{policy['policy_id']}|{value}".encode("ascii")
        ).hexdigest()
    )
    selected["policy_id"] = str(policy["policy_id"])
    selected = selected.sort_values(
        ["feature_time_utc", "candidate_id"], kind="mergesort"
    ).reset_index(drop=True)
    if selected["candidate_id"].duplicated().any():
        raise ValueError("Duplicate V2 candidate IDs")
    if (
        selected["regime_feature_time_utc"].notna()
        & selected["regime_feature_time_utc"].gt(selected["feature_time_utc"])
    ).any():
        raise ValueError("Future regime feature in V2 candidates")

    candidate_path = output / config["outputs"]["candidates"]
    temporary = candidate_path.with_suffix(candidate_path.suffix + ".part")
    selected.to_parquet(temporary, index=False)
    os.replace(temporary, candidate_path)
    manifest = {
        "schema_version": "xauusd_ppi_fade_regime_candidate_manifest_v2",
        "parent_contract_sha256": parent_lock["contract_sha256"],
        "parent_candidate_sha256": _sha256(parent_candidate_path),
        "candidate_rows": int(len(selected)),
        "candidate_sha256": _sha256(candidate_path),
        "policy_id": str(policy["policy_id"]),
        "allowed_regimes": list(policy["allowed_regimes"]),
        "rows_by_regime": {
            str(key): int(value)
            for key, value in selected["regime"].value_counts().sort_index().items()
        },
        "first_decision_utc": selected["feature_time_utc"].min().isoformat(),
        "last_decision_utc": selected["feature_time_utc"].max().isoformat(),
        "future_regime_feature_rows": 0,
        "outcome_like_columns": [],
        "contains_price_outcomes": False,
        "strategy_scoring_performed": False,
        "paid_data_request_made": False,
        "databento_used": False,
    }
    _write_json(output / config["outputs"]["candidate_manifest"], manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
