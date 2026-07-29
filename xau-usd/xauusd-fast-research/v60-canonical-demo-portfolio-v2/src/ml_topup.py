from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping

import numpy as np
import pandas as pd


_CACHE: dict[str, Any] = {}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load ML serving source: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _verified_path(repo_root: Path, item: Mapping[str, Any]) -> Path:
    path = Path(str(item["path"]))
    if not path.is_absolute():
        path = repo_root / path
    actual = sha256_file(path)
    if actual != str(item["sha256"]):
        raise RuntimeError(f"ML artifact identity changed: {path}: {actual}")
    return path


def _load_static_runtime(
    repo_root: Path, settings: Mapping[str, Any], account_login: int, symbol: str
) -> dict[str, Any]:
    cache_key = hashlib.sha256(
        json.dumps(settings, sort_keys=True).encode("utf-8")
    ).hexdigest()
    if _CACHE.get("key") == cache_key:
        return dict(_CACHE["runtime"])

    source_path = _verified_path(repo_root, settings["serving_source"])
    _verified_path(repo_root, settings["implementation_lock"])
    model_path = _verified_path(repo_root, settings["model_bundle"])
    parity_path = _verified_path(repo_root, settings["parity_result"])
    parity = json.loads(parity_path.read_text(encoding="utf-8"))
    if parity.get("decision") != "PASS_PROSPECTIVE_DEMO_INTEGRATION_NOMINATED":
        raise RuntimeError("Portable ML cross-feed parity did not pass")
    if bool(parity.get("outcome_labels_used", True)):
        raise RuntimeError("Portable ML parity used outcome labels")
    if not parity.get("gates") or not all(parity["gates"].values()):
        raise RuntimeError("Portable ML parity contains a failed gate")

    serving = _load_module("v60_portable_ml_topup_serving_v3", source_path)
    bundle = serving.load_bundle(model_path)
    if int(bundle["expected_account_login"]) != int(account_login):
        raise RuntimeError("Portable ML bundle is bound to a different account")
    if str(bundle["expected_symbol"]) != str(symbol):
        raise RuntimeError("Portable ML bundle is bound to a different symbol")
    if str(bundle["failure_policy"]) != "BASELINE_ONLY":
        raise RuntimeError("Portable ML bundle does not fail to baseline only")
    if int(bundle["serving_year"]) != 2026 or len(bundle["models"]) != 40:
        raise RuntimeError("Portable ML serving ensemble identity changed")

    runtime = {
        "ready": True,
        "serving": serving,
        "bundle": bundle,
        "parity_decision": parity["decision"],
        "model_sha256": str(settings["model_bundle"]["sha256"]),
        "source_sha256": str(settings["serving_source"]["sha256"]),
    }
    _CACHE.clear()
    _CACHE.update({"key": cache_key, "runtime": runtime})
    return dict(runtime)


def _completed_feature_bars(
    mt5: Any,
    serving: ModuleType,
    symbol: str,
    point: float,
    history_bars: int,
) -> pd.DataFrame:
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, history_bars)
    frame = pd.DataFrame(rates)
    required = {"time", "high", "low", "close", "spread"}
    if frame.empty or not required.issubset(frame.columns):
        raise RuntimeError("Capital M5 bars are unavailable for portable ML")
    spread = frame["spread"].astype(float) * float(point)
    bars = pd.DataFrame(
        {
            "bar_start_utc": pd.to_datetime(frame["time"], unit="s", utc=True),
            "mid_high": frame["high"].astype(float) + spread / 2.0,
            "mid_low": frame["low"].astype(float) + spread / 2.0,
            "mid_close": frame["close"].astype(float) + spread / 2.0,
        }
    )
    return serving.market_feature_frame(bars)


def prepare_runtime(
    mt5: Any,
    repo_root: Path,
    config: Mapping[str, Any],
    symbol_info: Any,
) -> dict[str, Any]:
    settings = config.get("ml_topup", {})
    if not bool(settings.get("enabled")):
        return {"ready": False, "reason": "ML_TOPUP_DISABLED"}
    try:
        runtime = _load_static_runtime(
            repo_root,
            settings,
            int(config["account"]["expected_login"]),
            str(config["account"]["symbol"]),
        )
        runtime["feature_bars"] = _completed_feature_bars(
            mt5,
            runtime["serving"],
            str(config["account"]["symbol"]),
            float(symbol_info.point),
            int(settings["history_bars"]),
        )
        runtime["feature_rows"] = int(len(runtime["feature_bars"]))
        completed = runtime["feature_bars"].loc[
            runtime["feature_bars"]["decision_time_utc"].le(
                pd.Timestamp.now(tz="UTC")
            )
        ]
        if completed.empty:
            raise RuntimeError("No completed Capital feature bar is available")
        runtime["latest_completed_feature_bar_utc"] = pd.Timestamp(
            completed["decision_time_utc"].iloc[-1]
        ).isoformat()
        return runtime
    except Exception as exc:
        return {
            "ready": False,
            "reason": "ML_RUNTIME_PREPARE_FAILED",
            "detail": f"{type(exc).__name__}: {exc}",
        }


def _ml_state(state: dict[str, Any]) -> dict[str, Any]:
    value = state.setdefault(
        "ml_topup",
        {
            "schema_version": "xauusd_v60_portable_ml_topup_state_v3",
            "score_history": [],
            "decisions": {},
            "orders": {},
            "daily_topups": {},
        },
    )
    if value.get("schema_version") != "xauusd_v60_portable_ml_topup_state_v3":
        raise ValueError("Unexpected portable ML top-up state schema")
    return value


def evaluate_candidate(
    runtime: Mapping[str, Any],
    config: Mapping[str, Any],
    state: dict[str, Any],
    candidate: Any,
    now: datetime,
) -> dict[str, Any]:
    try:
        ml_state = _ml_state(state)
    except Exception as exc:
        return {
            "candidate_id": candidate.candidate_id,
            "source_id": candidate.source_id,
            "evaluated_at_utc": now.astimezone(UTC)
            .isoformat()
            .replace("+00:00", "Z"),
            "topup": False,
            "reason": "ML_STATE_UNAVAILABLE",
            "detail": f"{type(exc).__name__}: {exc}",
        }
    prior = ml_state["decisions"].get(candidate.candidate_id)
    if prior is not None:
        return dict(prior)
    settings = config["ml_topup"]
    decision: dict[str, Any] = {
        "candidate_id": candidate.candidate_id,
        "source_id": candidate.source_id,
        "evaluated_at_utc": now.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "topup": False,
    }
    try:
        if candidate.source_id not in set(settings["eligible_source_ids"]):
            decision["reason"] = "SOURCE_NOT_HISTORICALLY_RISK_ELIGIBLE"
        elif (
            not math.isfinite(float(candidate.initial_risk_usd))
            or float(candidate.initial_risk_usd) <= 0.0
        ):
            decision["reason"] = "INITIAL_RISK_UNKNOWN"
        elif not bool(runtime.get("ready")):
            decision["reason"] = str(
                runtime.get("reason", "ML_RUNTIME_NOT_READY")
            )
            if runtime.get("detail"):
                decision["detail"] = str(runtime["detail"])
        else:
            serving = runtime["serving"]
            bundle = dict(runtime["bundle"])
            live_history = np.asarray(ml_state["score_history"], dtype=float)
            bundle["historical_oos_score_reference"] = np.concatenate(
                [
                    np.asarray(
                        bundle["historical_oos_score_reference"], dtype=float
                    ),
                    live_history,
                ]
            )
            result = serving.score_candidate(
                bundle,
                runtime["feature_bars"],
                pd.Timestamp(candidate.scheduled_at),
                is_long=candidate.direction == "LONG",
                is_core=candidate.sleeve_type == "CORE",
                maximum_bar_age=pd.Timedelta(
                    minutes=int(settings["maximum_feature_bar_age_minutes"])
                ),
            )
            decision.update(result)
            if result.get("reason") == "SCORE_COMPLETE":
                score = float(result["score"])
                if not math.isfinite(score):
                    decision = {
                        **decision,
                        "topup": False,
                        "reason": "NONFINITE_MODEL_SCORE",
                    }
                else:
                    ml_state["score_history"].append(score)
    except Exception as exc:
        decision.update(
            {
                "topup": False,
                "reason": "MODEL_SCORING_FAILED",
                "detail": f"{type(exc).__name__}: {exc}",
            }
        )
    ml_state["decisions"][candidate.candidate_id] = decision
    return dict(decision)


def topup_comment(candidate: Any) -> str:
    return f"V60ML3:{candidate.candidate_id[:23]}"[:31]


def status_snapshot(
    runtime: Mapping[str, Any], state: Mapping[str, Any]
) -> dict[str, Any]:
    ml_state = state.get("ml_topup", {})
    if not isinstance(ml_state, Mapping):
        ml_state = {}
    decisions = list(ml_state.get("decisions", {}).values())
    orders = list(ml_state.get("orders", {}).values())
    return {
        "ready": bool(runtime.get("ready")),
        "reason": runtime.get("reason"),
        "detail": runtime.get("detail"),
        "parity_decision": runtime.get("parity_decision"),
        "model_sha256": runtime.get("model_sha256"),
        "feature_rows": int(runtime.get("feature_rows", 0)),
        "latest_completed_feature_bar_utc": runtime.get(
            "latest_completed_feature_bar_utc"
        ),
        "scored_candidates": sum(
            row.get("reason") == "SCORE_COMPLETE" for row in decisions
        ),
        "topup_decisions": sum(bool(row.get("topup")) for row in decisions),
        "filled_topups": sum(
            row.get("status") == "ORDER_FILLED" for row in orders
        ),
        "failure_policy": "BASELINE_ONLY",
    }
