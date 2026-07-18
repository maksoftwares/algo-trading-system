from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any, Mapping

import pandas as pd


ROOT = Path(__file__).resolve().parent
RESEARCH_ROOT = ROOT.parent
CONFIG_PATH = ROOT / "config" / "event_reaction_corrected_v4.json"


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


EVENT = _load_module(
    "corrected_event_candidate_engine",
    RESEARCH_ROOT / "macro-event-reaction-replication-v2" / "src" / "event_reaction.py",
)
DATA = _load_module(
    "corrected_event_candidate_data",
    RESEARCH_ROOT / "independent-specialists-v1" / "src" / "data.py",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    if (output / config["outputs"]["contract_lock"]).exists():
        raise RuntimeError("Refusing to rebuild corrected candidates after lock")
    if any(output.glob("*_OUTCOMES_OPENED.json")):
        raise RuntimeError("Refusing to rebuild corrected candidates after outcomes opened")

    base_config = json.loads(
        (ROOT / config["base_contract"]).resolve().read_text(encoding="utf-8")
    )
    source = config["source"]
    storage_root = Path(
        os.environ.get(
            source["storage_environment_variable"], source["default_storage_root"]
        )
    ).resolve()
    macro_config = dict(config)
    macro_config["policies"] = [
        policy for policy in config["policies"] if policy["event_type"] != "PPI"
    ]
    macro_calendar = EVENT.load_event_calendar(macro_config, storage_root)

    ppi_parent = (ROOT / config["ppi_parent_package"]).resolve()
    ppi_output = ppi_parent / "outputs"
    ppi_calendar_path = ppi_output / "PPI_EVENT_CALENDAR.csv"
    ppi_manifest_path = ppi_output / "PPI_EVENT_CALENDAR_MANIFEST.json"
    ppi_manifest = json.loads(ppi_manifest_path.read_text(encoding="utf-8"))
    if _sha256(ppi_calendar_path) != ppi_manifest["calendar_sha256"]:
        raise ValueError("Frozen PPI calendar hash mismatch")
    ppi_calendar = pd.read_csv(ppi_calendar_path, parse_dates=["event_time_utc"])
    ppi_calendar["source_file"] = str(ppi_calendar_path)

    columns = list(macro_calendar.columns)
    calendar = pd.concat(
        [macro_calendar, ppi_calendar.reindex(columns=columns)],
        ignore_index=True,
    ).sort_values(["event_time_utc", "event_type"], kind="mergesort")
    calendar = calendar.reset_index(drop=True)
    if len(calendar) != int(source["expected_calendar_rows"]):
        raise ValueError("Corrected event calendar row count changed")
    if calendar["event_id"].duplicated().any():
        raise ValueError("Duplicate corrected event IDs")
    if set(calendar["event_type"]) != {"NFP", "CPI", "FOMC", "PPI"}:
        raise ValueError("Corrected event calendar type set changed")

    calendar_path = output / config["outputs"]["calendar"]
    temporary_calendar = calendar_path.with_suffix(".csv.part")
    calendar.to_csv(temporary_calendar, index=False, lineterminator="\n")
    os.replace(temporary_calendar, calendar_path)
    calendar_manifest = {
        "schema_version": "xauusd_corrected_event_calendar_manifest_v4",
        "calendar_rows": int(len(calendar)),
        "calendar_sha256": _sha256(calendar_path),
        "rows_by_event_type": {
            str(key): int(value)
            for key, value in calendar["event_type"].value_counts().sort_index().items()
        },
        "first_event_utc": calendar["event_time_utc"].min().isoformat(),
        "last_event_utc": calendar["event_time_utc"].max().isoformat(),
        "ppi_parent_calendar_sha256": _sha256(ppi_calendar_path),
        "contains_outcomes": False,
        "paid_data_request_made": False,
        "databento_used": False,
    }
    _write_json(output / config["outputs"]["calendar_manifest"], calendar_manifest)

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
        raise ValueError(f"Outcome-like candidate columns: {sorted(prohibited)}")
    if len(candidates) != int(source["expected_candidate_rows"]):
        raise ValueError("Corrected candidate row count changed")
    candidate_path = output / config["outputs"]["candidates"]
    temporary_candidate = candidate_path.with_suffix(".parquet.part")
    candidates.to_parquet(temporary_candidate, index=False)
    os.replace(temporary_candidate, candidate_path)
    candidate_manifest = {
        "schema_version": "xauusd_corrected_event_candidate_manifest_v4",
        "candidate_rows": int(len(candidates)),
        "candidate_sha256": _sha256(candidate_path),
        "calendar_sha256": _sha256(calendar_path),
        "rows_by_policy": {
            str(key): int(value)
            for key, value in candidates["policy_id"].value_counts().sort_index().items()
        },
        "rows_by_regime": {
            str(key): int(value)
            for key, value in candidates["regime"].value_counts().sort_index().items()
        },
        "first_decision_utc": candidates["feature_time_utc"].min().isoformat(),
        "last_decision_utc": candidates["feature_time_utc"].max().isoformat(),
        "future_regime_feature_rows": int(
            (
                candidates["regime_feature_time_utc"].notna()
                & candidates["regime_feature_time_utc"].gt(
                    candidates["feature_time_utc"]
                )
            ).sum()
        ),
        "outcome_like_columns": [],
        "contains_price_outcomes": False,
        "strategy_scoring_performed": False,
        "paid_data_request_made": False,
        "databento_used": False,
    }
    _write_json(output / config["outputs"]["candidate_manifest"], candidate_manifest)
    print(
        json.dumps(
            {"calendar": calendar_manifest, "candidates": candidate_manifest},
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
