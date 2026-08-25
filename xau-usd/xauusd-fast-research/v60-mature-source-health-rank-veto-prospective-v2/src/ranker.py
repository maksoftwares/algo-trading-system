from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def verified_path(repo_root: Path, item: Mapping[str, Any]) -> Path:
    path = Path(str(item["path"]))
    if not path.is_absolute():
        path = repo_root / path
    actual = sha256_file(path)
    if actual != str(item["sha256"]):
        raise ValueError(f"Observer-ranker input changed: {path}: {actual}")
    return path


def prepare_runtime(
    mt5: Any,
    repo_root: Path,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    settings = config["observer_ranker"]
    if not bool(settings.get("enabled")):
        raise ValueError("All-source observer ranker is disabled")
    overlay_path = verified_path(repo_root, settings["ml_overlay"])
    runtime_source = verified_path(repo_root, settings["ml_runtime_source"])
    overlay = json.loads(overlay_path.read_text(encoding="utf-8"))
    base_path = verified_path(repo_root, overlay["base_config"])
    portfolio_config = json.loads(base_path.read_text(encoding="utf-8"))
    portfolio_config = deepcopy(portfolio_config)
    portfolio_config["ml_topup"] = overlay["ml_topup"]
    ml_runtime = load_module("v60_v2_observer_ml_runtime", runtime_source)
    symbol = str(config["account"]["symbol"])
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        raise RuntimeError(f"MT5 symbol information is unavailable: {symbol}")
    runtime = ml_runtime.prepare_runtime(
        mt5, repo_root, portfolio_config, symbol_info
    )
    if not bool(runtime.get("ready")):
        raise RuntimeError(
            f"All-source observer ranker is unavailable: {runtime.get('reason')}: "
            f"{runtime.get('detail')}"
        )
    return runtime


def score_candidates(
    runtime: Mapping[str, Any],
    candidates: Sequence[Mapping[str, Any]],
    settings: Mapping[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    start = pd.Timestamp(settings["score_start_inclusive_utc"])
    if start.tzinfo is None:
        raise ValueError("Observer rank start must be timezone-aware")
    maximum_age = pd.Timedelta(
        minutes=int(settings["maximum_feature_bar_age_minutes"])
    )
    ordered = sorted(
        (
            (pd.Timestamp(row["scheduled_entry_time_utc"]), str(row["candidate_id"]), row)
            for row in candidates
            if pd.Timestamp(row["scheduled_entry_time_utc"]) >= start
        ),
        key=lambda item: (item[0], item[1]),
    )
    base_bundle = dict(runtime["bundle"])
    historical_reference = np.asarray(
        base_bundle["historical_oos_score_reference"], dtype=float
    )
    prior_scores: list[float] = []
    decisions: dict[str, dict[str, Any]] = {}
    reasons: Counter[str] = Counter()
    index = 0
    while index < len(ordered):
        timestamp = ordered[index][0]
        batch = []
        while index < len(ordered) and ordered[index][0] == timestamp:
            batch.append(ordered[index])
            index += 1
        reference = np.concatenate(
            [historical_reference, np.asarray(prior_scores, dtype=float)]
        )
        completed_scores = []
        for _, candidate_id, candidate in batch:
            bundle = dict(base_bundle)
            bundle["historical_oos_score_reference"] = reference
            result = runtime["serving"].score_candidate(
                bundle,
                runtime["feature_bars"],
                timestamp,
                is_long=str(candidate["direction"]).upper() == "LONG",
                is_core=str(candidate.get("sleeve_type", "CORE")).upper() == "CORE",
                maximum_bar_age=maximum_age,
            )
            reason = str(result.get("reason", "UNKNOWN"))
            reasons[reason] += 1
            decision = {
                **result,
                "candidate_id": candidate_id,
                "source_id": str(candidate["specialist_id"]),
                "decision_time_utc": timestamp.isoformat(),
                "observer_only": True,
                "broker_action_authorized": False,
                "topup": False,
            }
            decisions[candidate_id] = decision
            if reason == "SCORE_COMPLETE":
                score = float(result["score"])
                if not np.isfinite(score):
                    raise ValueError(f"Nonfinite observer score: {candidate_id}")
                completed_scores.append(score)
        prior_scores.extend(completed_scores)

    ranks = [
        float(row["rank"])
        for row in decisions.values()
        if row.get("reason") == "SCORE_COMPLETE"
    ]
    audit = {
        "schema_version": "v60_v2_all_source_observer_ranker_v1",
        "observer_only": True,
        "broker_action_authorized": False,
        "score_start_inclusive_utc": start.isoformat(),
        "candidate_rows": len(ordered),
        "scored_candidate_rows": len(ranks),
        "reason_counts": dict(sorted(reasons.items())),
        "historical_reference_rows": int(len(historical_reference)),
        "expanding_observer_score_rows": len(prior_scores),
        "minimum_rank": min(ranks) if ranks else None,
        "maximum_rank": max(ranks) if ranks else None,
        "model_sha256": str(runtime.get("model_sha256")),
        "feature_rows": int(runtime.get("feature_rows", 0)),
        "latest_completed_feature_bar_utc": runtime.get(
            "latest_completed_feature_bar_utc"
        ),
    }
    return decisions, audit
