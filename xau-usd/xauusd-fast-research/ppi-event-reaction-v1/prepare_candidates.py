from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
RESEARCH_ROOT = ROOT.parent
CONFIG_PATH = ROOT / "config" / "ppi_event_reaction_v1.json"


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


EVENT = _load_module(
    "ppi_event_reaction_candidate_engine",
    RESEARCH_ROOT / "macro-event-reaction-replication-v2" / "src" / "event_reaction.py",
)
DATA = _load_module(
    "ppi_event_reaction_candidate_data",
    RESEARCH_ROOT / "independent-specialists-v1" / "src" / "data.py",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    base_config = json.loads(
        (ROOT / config["base_contract"]).resolve().read_text(encoding="utf-8")
    )
    output = ROOT / config["outputs"]["directory"]
    lock = output / config["outputs"]["contract_lock"]
    if lock.exists():
        raise RuntimeError("Refusing to rebuild PPI candidates after contract lock")
    calendar_path = output / config["outputs"]["calendar"]
    calendar_manifest_path = output / config["outputs"]["calendar_manifest"]
    if not calendar_path.is_file() or not calendar_manifest_path.is_file():
        raise FileNotFoundError("Run acquire_calendar.py before candidate generation")
    calendar_manifest = json.loads(calendar_manifest_path.read_text(encoding="utf-8"))
    if _sha256(calendar_path) != calendar_manifest["calendar_sha256"]:
        raise ValueError("PPI calendar hash does not match its manifest")
    calendar = pd.read_csv(calendar_path, parse_dates=["event_time_utc"])
    if len(calendar) != int(config["source"]["expected_calendar_rows"]):
        raise ValueError("PPI calendar row count changed")
    if set(calendar["event_type"]) != {"PPI"}:
        raise ValueError("PPI calendar contains another event type")
    bundle = DATA.load_bundle(base_config)
    candidates = EVENT.build_candidates(
        bundle.bars["M5"],
        bundle.bars["H4"],
        base_config,
        calendar,
        config["policies"],
    )
    prohibited = {
        column
        for column in candidates.columns
        if any(
            token in column.lower()
            for token in ("pnl", "profit", "exit_", "stress_", "winner")
        )
    }
    if prohibited:
        raise ValueError(f"Outcome-like candidate columns found: {sorted(prohibited)}")
    candidate_path = output / config["outputs"]["candidates"]
    temporary = candidate_path.with_suffix(candidate_path.suffix + ".part")
    candidates.to_parquet(temporary, index=False)
    os.replace(temporary, candidate_path)
    manifest = {
        "schema_version": "xauusd_ppi_event_candidate_manifest_v1",
        "candidate_rows": int(len(candidates)),
        "candidate_sha256": _sha256(candidate_path),
        "calendar_sha256": _sha256(calendar_path),
        "first_decision_utc": candidates["feature_time_utc"].min().isoformat(),
        "last_decision_utc": candidates["feature_time_utc"].max().isoformat(),
        "rows_by_policy": {
            str(key): int(value)
            for key, value in candidates["policy_id"].value_counts().items()
        },
        "rows_by_regime": {
            str(key): int(value)
            for key, value in candidates["regime"].value_counts().items()
        },
        "future_regime_feature_rows": int(
            (
                candidates["regime_feature_time_utc"].notna()
                & candidates["regime_feature_time_utc"].gt(
                    candidates["feature_time_utc"]
                )
            ).sum()
        ),
        "maximum_feature_lag_minutes": float(
            candidates["feature_lag_minutes"].max()
        ),
        "outcome_like_columns": [],
        "contains_price_outcomes": False,
        "strategy_scoring_performed": False,
        "paid_data_request_made": False,
        "databento_used": False,
    }
    manifest_path = output / config["outputs"]["candidate_manifest"]
    temporary_manifest = manifest_path.with_suffix(manifest_path.suffix + ".part")
    temporary_manifest.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary_manifest, manifest_path)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
